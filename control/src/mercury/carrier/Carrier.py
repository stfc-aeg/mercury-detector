from odin_devices.gpio_bus import GPIO_ZynqMP
from odin_devices.firefly import FireFly
import odin_devices.pac1921 as pac1921
from odin_devices.max5306 import MAX5306
from odin_devices.si534x import SI5344
from odin_devices.bme280 import BME280
from odin_devices.i2c_device import I2CException
from odin_devices.spi_device import SPIDevice

from .asic import Asic, ASICDisabledError

try:
    from odin_devices.ltc2986 import LTC2986, LTCSensorException
except ModuleNotFoundError:
    # Allow init to continue without LTC2987 temperature sensor support build in
    # (driver not progressed due to hardware fault)
    pass

from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError
from tornado.ioloop import IOLoop

import logging
import time
import sys
import os
import copy
import psutil
import datetime
from enum import Enum as _Enum, auto as _auto

PLOTTING_SUPPORTED=False
try:
    import numpy as np
    import io
    from PIL import Image
    import matplotlib.pyplot as plt
    PLOTTING_SUPPORTED=True
except ModuleNotFoundError:
    pass

logging.basicConfig(encoding='utf-8', level=logging.DEBUG)

# If true, derive power from PAC1921 IV readings if they are being taken instead of reading it
_RAIL_MONITOR_DERIVE_POWER = True

vdddcntrl_rail_name = 'VDDDCNTRL'
vdddasic_rail_name = 'VDDD ASIC'
vddaasic_rail_name = 'VDDA ASIC'

class Carrier_Interface():
    def __init__(self, i2c_device_bus,
                 spidev_id_mercury, spidev_id_ltc, spidev_id_max,
                 pin_firefly_1, pin_firefly_2, pin_nRead_int, pin_sync,
                 pin_sync_sel, pin_asic_nrst, pin_vreg_en, pin_temp_nrst):
        self.i2c_device_bus = i2c_device_bus
        self.spidev_id_mercury = spidev_id_mercury
        self.spidev_id_ltc = spidev_id_ltc
        self.spidev_id_max = spidev_id_max
        self.pin_firefly_1 = pin_firefly_1
        self.pin_firefly_2 = pin_firefly_2
        self.pin_nRead_int = pin_nRead_int
        self.pin_sync = pin_sync
        self.pin_sync_sel = pin_sync_sel
        self.pin_asic_nrst = pin_asic_nrst
        self.pin_vreg_en = pin_vreg_en
        self.pin_temp_nrst = pin_temp_nrst


_interface_definition_default = Carrier_Interface(
        i2c_device_bus=1,             # TODO check
        spidev_id_mercury=(0, 1),     # TODO check
        spidev_id_ltc=(1, 0),
        spidev_id_max=(1, 1),
        pin_firefly_1=6,
        pin_firefly_2=7,
        pin_nRead_int=11,
        pin_sync=0,
        pin_sync_sel=10,
        pin_asic_nrst=3,
        pin_vreg_en=2,
        pin_temp_nrst=8
        )

_vcal_default = 1.5     # TODO check this

_ltc2986_pt100_channel = 6
_ltc2986_diode_channel = 2

_LVDS_sync_idle_state = 0   # TODO Check polarity
_LVDS_sync_duration = 0.1   # TODO Check duration


class Carrier():

    class _Rail_Monitor_Mode (_Enum):
        POWER_ONLY = _auto()
        POWER_AND_IV = _auto()

    def __init__(self, si5344_config_directory, si5344_config_filename,
                 power_monitor_IV,
                 critical_temp_limit,
                 override_critical_temp_bme,
                 interface_definition=_interface_definition_default,
                 vcal=_vcal_default,
                 asic_spi_speed_hz=2000000):

        self._POWER_CYCLING = True
        self._PARAMTREE_FIRSTINIT = True

        self._interface_definition = interface_definition
        if power_monitor_IV:
            self._rail_monitor_mode = self._Rail_Monitor_Mode.POWER_AND_IV
        else:
            self._rail_monitor_mode = self._Rail_Monitor_Mode.POWER_ONLY

        self._si5344_config_directory = si5344_config_directory
        self._si5344_config_filename = si5344_config_filename

        # Set VCAL to default or argument
        self._vcal = vcal
        self.vcal_limit = 1.8       # Over 1.8v can damage MERCURY

        # Set the critical temperature limit
        self._critical_temperature_limit = critical_temp_limit
        self._override_critical_temp_bme = override_critical_temp_bme
        self._temperature_iscritical = False     # Start assuming temperature critical until checked

        # Get LOKI GPIO pin bus
        self._gpio_bus = GPIO_ZynqMP

        # Claim standalone control pins
        self._gpiod_sync = GPIO_ZynqMP.get_pin(self._interface_definition.pin_sync,
                                               GPIO_ZynqMP.DIR_OUTPUT)
        self._gpiod_sync_sel = GPIO_ZynqMP.get_pin(self._interface_definition.pin_sync_sel,
                                                   GPIO_ZynqMP.DIR_OUTPUT)
        self._gpiod_asic_nrst = GPIO_ZynqMP.get_pin(self._interface_definition.pin_asic_nrst,
                                                    GPIO_ZynqMP.DIR_OUTPUT)
        self._gpiod_ltc_nrst = GPIO_ZynqMP.get_pin(self._interface_definition.pin_temp_nrst,
                                                    GPIO_ZynqMP.DIR_OUTPUT)

        # The LTC will never be disabled
        self._gpiod_ltc_nrst.set_value(1)

        # Put nRST in safe state before vreg_en forced off (may occur after allocation when run after failure)
        self._gpiod_asic_nrst.set_value(0)

        # Claim vreg enable control pin, as pull-up (will set disabled until written)
        #TODO add the pull-up
        self._gpiod_vreg_en = GPIO_ZynqMP.get_pin(self._interface_definition.pin_vreg_en,
                                                  GPIO_ZynqMP.DIR_OUTPUT,
                                                #   pull_up=True)     # Do not power up immediately
                                                    )
        self.set_vreg_en(False)

        # Define device-specific control pins
        self._gpiod_firefly_1 = GPIO_ZynqMP.get_pin(self._interface_definition.pin_firefly_1,
                                                    GPIO_ZynqMP.DIR_OUTPUT)
        self._gpiod_firefly_2 = GPIO_ZynqMP.get_pin(self._interface_definition.pin_firefly_2,
                                                    GPIO_ZynqMP.DIR_OUTPUT)
        self._gpiod_nRead_int = GPIO_ZynqMP.get_pin(self._interface_definition.pin_nRead_int,
                                                    GPIO_ZynqMP.DIR_OUTPUT)

        # Init ASIC
        self.asic = Asic(
            self._gpiod_asic_nrst, self._gpiod_sync_sel, self._gpiod_sync,
            bus=interface_definition.spidev_id_mercury[0],
            device=interface_definition.spidev_id_mercury[1],
            # hz=30000000)    # 30M -> 15M: nope
            #hz=20000000)    # 20M -> 10M: nope
            # hz=16000000)    # 16M -> 8M: nope
            # hz=8000000)    # 8M -> 4M: ok
            # hz=5000000)    # 5M -> 2.5M: ok
            # hz=2000000)    # 2M -> 1M: ok
            hz=asic_spi_speed_hz)

        '''
        Speed (code)    |   Speed (actual)  | 2m Printer    | 1m 'fast' Printer |
        2M              |   1M              | OK            |   OK
        5M              |   2.5M            | OK            |   OK
        8M              |   4M              | OK            |   OK
        16M             |   8M              | No            |   OK 
        20M             |   10M             | No            |   OK 
        30M             |   15M             | No            |   No

        '''

        self._segment_capture_due = None        # Set to a sector number when one should be read
        self._segment_ready = False             # True when the last capture request is complete
        self._segment_vmax = None
        self._segment_vmin = None

        self._asic_cal_highlight_div = None
        self._asic_cal_highlight_sec = None

        # Set default pin states
        self._gpiod_sync.set_value(_LVDS_sync_idle_state)
        self.set_sync_sel_aux(False)                        # Set sync Zynq-controlled
        self.set_asic_rst(True)                             # Init device in reset
        logging.warning('triggering first power cycle')
        #self.vreg_power_cycle_init(None)                    # Contains device setup
        self._POWER_CYCLING=True

        self._firefly_1 = None
        self._firefly_2 = None
        self._ltc2986 = None
        self._max5306 = None
        self._bme280 = None
        self._pac1921_array = None
        self._asic_temp = None  # Init cached ASIC temperature to None
        self._pt100_temp = None  # Init cached PT100 temperature to None
        self._paramtree_setup()


    def _gen_FireFly_Tree(self, ff_num):
        channels_tree = self._gen_FireFlyChannels_Tree(ff_num)

        tree = {
            "TEMPERATURE":(lambda: self.get_firefly_temperature(ff_num), None, {"description":"FireFly Temperature", "units":"C"}),
            "PARTNUMBER":(lambda: self.get_firefly_partnumber(ff_num), None, {"description":"FireFly Part Number"}),
            "VENDORID":(lambda: self.get_firefly_vendornumber(ff_num), None, {"description":"FireFly Vendor ID"}),
            "OUI":(lambda: self.get_firefly_oui(ff_num), None, {"description":"FireFly OUI"}),
            "CHANNELS":channels_tree
        }

        return tree

    def _gen_FireFlyChannels_Tree(self, ff_num):
        tree = {}
        for ch_num in range(0, 12):
            tree["CH{}".format(ch_num)] = {
                    "Disabled":(
                        # Create the lambdas, different for each channel num and firefly num. Lambda
                        # layering used to prevent sharing ch_num reference by changing the scope
                        # after the internal lambda is created. If this is not done, all lambdas
                        # will reference the same channel number 11
                        (lambda ch_num_internal: lambda: self.get_firefly_tx_channel_disabled(ff_num, ch_num_internal))(ch_num),
                        (lambda ch_num_internal: lambda dis: self.set_firefly_tx_channel_disabled(ff_num, ch_num_internal, dis))(ch_num),
                        {"description": "Channel {} disable".format(ch_num)}
                )
            }

        return tree

    def _gen_RailMonitor_Tree(self, VDDD_cntrl_chipname, VDDD_ASIC_chipname, VDDA_ASIC_chipname, include_IV, reading_function):
        tree = {}

        for rail_treename, rail_chipname in [
                ("DIG_CTRL", VDDD_cntrl_chipname),
                ("DIG", VDDD_ASIC_chipname),
                ("ANALOGUE", VDDA_ASIC_chipname)]:

            # Double lambdas used to correct scope issues with rail_chipname.
            tmp_railtree = {"POWER":(
                (lambda chipname_internal: lambda: reading_function()[chipname_internal]['POWER'])(rail_chipname),
                None, {"description":rail_chipname+" supply power", "units":"W"})}

            # Only include voltage and current if configured for free-running
            if (include_IV == self._Rail_Monitor_Mode.POWER_AND_IV):
                tmp_railtree["VOLTAGE"] = (
                        (lambda chipname_internal: lambda: reading_function()[chipname_internal]['VOLTAGE'])(rail_chipname),
                        None, {"description":rail_chipname+" supply voltage", "units":"V"})
                tmp_railtree["CURRENT"] = (
                        (lambda chipname_internal: lambda: reading_function()[chipname_internal]['CURRENT'])(rail_chipname),
                        None, {"description":rail_chipname+" supply current", "units":"A"})

            tree[rail_treename] = tmp_railtree

        return tree

    def _gen_loki_performance_tree(self):
        tree = {}

        tree['LOAD'] = (psutil.getloadavg, None , {"description":"Load Average, last 1 minute, 5 minutes, and 15 minutes"})

        tree['MEM'] = {
                'FREE': (lambda: psutil.virtual_memory().free, None, {"description":"Free memory in bytes"}),
                'AVAILABLE': (lambda: psutil.virtual_memory().available, None, {"description":"Available memory in bytes"}),
                'TOTAL': (lambda: psutil.virtual_memory().total, None, {"description":"Total memory in bytes"})
                }

        tree['UPTIME'] = (lambda: str(datetime.timedelta(seconds=int(time.time() - psutil.boot_time()))), None, {})

        tree['TEMPERATURES'] = {
                    "PS":(lambda: self.get_zynq_ams_temp('0_ps'), None, {"description":"Zynq system PS Temperature", "units":"C"}),
                    "REMOTE":(lambda: self.get_zynq_ams_temp('1_remote'), None, {"description":"Zynq system Remote Temperature", "units":"C"}),
                    "PL":(lambda: self.get_zynq_ams_temp('2_pl'), None, {"description":"Zynq system PL Temperature", "units":"C"}),
                }

        return tree

    def get(self, path, wants_metadata=False):
        """Main get method for the parameter tree"""
        try:
            return self._param_tree.get(path, wants_metadata)
        except AttributeError:
            raise ParameterTreeError

    def set(self, path, data):
        """Main set method for the parameter tree"""
        try:
            return self._param_tree.set(path, data)
        except AttributeError:
            raise ParameterTreeError

    def POR_init_devices(self):
        """Init the devices on the board after a power-on-reset with current configuration"""

        # Init FireFlies and power down all channels
        try:
            self._firefly_1 = FireFly(base_address=0x50, select_line=self._gpiod_firefly_1)
            self._firefly_1.disable_tx_channels(FireFly.CHANNEL_ALL)
        except (OSError, I2CException):
            logging.error("Error init FireFly 1 with GPIO {}: {}".format(
                self._gpiod_firefly_1, sys.exc_info()[1]))
            self._firefly_1 = None

        try:
            self._firefly_2 = FireFly(base_address=0x50, select_line=self._gpiod_firefly_2)
            self._firefly_2.disable_tx_channels(FireFly.CHANNEL_ALL)
        except (OSError, I2CException):
            logging.error("Error init FireFly 2: with GPIO {}: {}".format(
                self._gpiod_firefly_2, sys.exc_info()[1]))
            self._firefly_2 = None

        # Init PAC1921 monitors in power mode (generic settings)
        try:
            self._pac1921_u3 = pac1921.PAC1921(address_resistance=470,
                                               name=vdddcntrl_rail_name,
                                               r_sense=0.02,
                                               measurement_type=pac1921.Measurement_Type.POWER)
            self._pac1921_u2 = pac1921.PAC1921(address_resistance=620,
                                               name=vdddasic_rail_name,
                                               r_sense=0.02,
                                               measurement_type=pac1921.Measurement_Type.POWER)
            self._pac1921_u1 = pac1921.PAC1921(address_resistance=820,
                                               name=vddaasic_rail_name,
                                               r_sense=0.02,
                                               measurement_type=pac1921.Measurement_Type.POWER)
            self._pac1921_u3.config_gain(di_gain=1, dv_gain=8)
            self._pac1921_u2.config_gain(di_gain=1, dv_gain=8)
            self._pac1921_u1.config_gain(di_gain=1, dv_gain=8)

            # PAC1921 Rail monitor mode settings
            if self._rail_monitor_mode == self._Rail_Monitor_Mode.POWER_AND_IV:
                # Init PAC1921 devices to cycle readings in free-run mode (V and I are free-run only)
                # TODO
                # Use a simple array of instances rather than the array class
                self._pac1921_array = [self._pac1921_u3, self._pac1921_u2, self._pac1921_u1]

                # Initially, devices will all be set in power mode.
                self._pac1921_array_current_measurement = pac1921.Measurement_Type.POWER

                # Start all devices free-running
                free_run_sample_num = 512
                self._pac1921_u3.config_freerun_integration_mode(free_run_sample_num)
                self._pac1921_u2.config_freerun_integration_mode(free_run_sample_num)
                self._pac1921_u1.config_freerun_integration_mode(free_run_sample_num)

            elif self._rail_monitor_mode == self._Rail_Monitor_Mode.POWER_ONLY:
                # Init PAC1921 Power Monitors as a pin-controlled array ready for readings
                self._pac1921_array = pac1921.PAC1921_Synchronised_Array(integration_time_ms=750,
                                                                         nRead_int_pin=self._gpiod_nRead_int)
                self._pac1921_array.add_device(self._pac1921_u3)
                self._pac1921_array.add_device(self._pac1921_u2)
                self._pac1921_array.add_device(self._pac1921_u1)
            else:
                logging.error("Rail monitor mode not recognised")
        except Exception as e:
            logging.error("PAC1921 power monitors could not be init: {}".format(e))
            self._pac1921_array = None

        # Init MAX5306
        try:
            max5306_bus, max5306_device = self._interface_definition.spidev_id_max
            self._max5306 = MAX5306(Vref=2.048, bus=max5306_bus, device=max5306_device)
            self._max5306.set_output(1, self._vcal)
        except Exception as e:
            logging.error("MAX5306 init failed: {}".format(e))
            self._max5306 = None

        # Init LTC2986
        try:
            ltc2986_bus, ltc2986_device = self._interface_definition.spidev_id_ltc
            self._ltc2986 = LTC2986(bus=ltc2986_bus, device=ltc2986_device)
            self._ltc2986.add_rtd_channel(LTC2986.Sensor_Type.SENSOR_TYPE_RTD_PT100,
                                          LTC2986.RTD_RSense_Channel.CH4_CH3,
                                          2000,
                                          LTC2986.RTD_Num_Wires.NUM_2_WIRES,
                                          #LTC2986.RTD_Excitation_Mode.NO_ROTATION_SHARING,
                                          LTC2986.RTD_Excitation_Mode.NO_ROTATION_NO_SHARING,
                                          LTC2986.RTD_Excitation_Current.CURRENT_500UA,
                                          LTC2986.RTD_Curve.EUROPEAN,
                                          _ltc2986_pt100_channel)
            self._ltc2986.add_diode_channel(endedness=LTC2986.Diode_Endedness.DIFFERENTIAL,
                                            conversion_cycles=LTC2986.Diode_Conversion_Cycles.CYCLES_2,
                                            average_en=LTC2986.Diode_Running_Average_En.OFF,
                                            excitation_current=LTC2986.Diode_Excitation_Current.CUR_80UA_320UA_640UA,
                                            diode_non_ideality=1.0,
                                            channel_num=_ltc2986_diode_channel)
            # raise Exception()
        except Exception as e:
            logging.error("LTC2986 init failed: {}".format(e))
            self._ltc2986 = None
            # exit()  # Temp
        self._asic_temp = None  # Init cached ASIC temperature to None
        self._pt100_temp =None  # Init cached PT100 temperature to None

        # Init SI5344 with clocks specified on the schematic. This requires a config file
        self._si5344 = SI5344(i2c_address=0x68)
        try:
            self._si5344.apply_register_map(self._si5344_config_directory + self._si5344_config_filename)
        except FileNotFoundError:
            raise

        # Init BME280 as I2C device on address 0x77
        try:
            self._bme280 = BME280(use_spi=False, bus=self._interface_definition.i2c_device_bus)
        except Exception as e:
            logging.error("BME280 failed init: {}".format(e))
            self._bme280 = None

        logging.debug("Devices Init: FF1: {}, FF2: {}, LTC: {}, MAX: {}, BME: {}, PACs: {}, SI: {}".format(
            self._firefly_1,
            self._firefly_2,
            self._ltc2986,
            self._max5306,
            self._bme280,
            self._pac1921_array,
            self._si5344))

    def sync_power_readings(self):
        # Sync power readings only if the regulators are enabled (for now)
        if self.get_vreg_en() and not self._POWER_CYCLING:
            self._sync_power_supply_readings()
        else:
            logging.critical('will update power supply readings to be None...')
            try:
                self._power_supply_readings = copy.deepcopy(self._POWER_SUPPLY_READINGS_EMPTY)
            except AttributeError:
                # May be encountered if sync attempts to run before paramtree setup complete
                logging.critical('Could not find self._POWER_SUPPLY_READINGS_EMPTY')
                self._power_supply_readings = None
                pass
            logging.critical('PSU readings are now: {}'.format(self.get_power_supply_readings()))

    def sync_firefly_readings(self):
        if self.get_vreg_en() and not self._POWER_CYCLING:
            self._sync_firefly_tx_channels_disabled(1)
            self._sync_firefly_tx_channels_disabled(2)

    def sync_temperature_readings(self):
        # Wait until VREG_EN complete, or request will bork the bus
        if self.get_vreg_en() and not self._POWER_CYCLING:
            self._sync_critical_temp_monitor()

    ''' Zynq System '''

    def get_zynq_ams_temp(self, temp_name):
        # Temp sensor name should be 0_ps, 1_remote, or 2_pl.
        with open('/sys/bus/iio/devices/iio:device0/in_temp{}_temp_raw'.format(temp_name), 'r') as f:
            temp_raw = int(f.read())

        with open('/sys/bus/iio/devices/iio:device0/in_temp{}_temp_offset'.format(temp_name), 'r') as f:
            temp_offset = int(f.read())

        with open('/sys/bus/iio/devices/iio:device0/in_temp{}_temp_scale'.format(temp_name), 'r') as f:
            temp_scale = float(f.read())

        return round(((temp_raw+temp_offset)*temp_scale)/1000, 2)

    ''' Critical temperature monitoring '''
    def _sync_critical_temp_monitor(self):

        #TODO Without VREG_EN enabled, the temperature cannot (currently) be checked
        if (not self.get_vreg_en()) or self._POWER_CYCLING:
            logging.warning('ASIC temp could not be read due to disabled regulators:' + \
                    '\nRegulators Enabled: {}\nTemp Critical: {}'.format(
                        self.get_vreg_en(), self._temperature_iscritical))
            logging.warning('Power cycle vreg after fixing cooling to recover')
            self._pt100_temp = None
            self._asic_temp = None
            return

        try:
            logging.debug('self.override_critical_temp_bme: {}'.format(self._override_critical_temp_bme))

            # Update cached ASIC temperature
            self._sync_asic_temperature()

            if not self._override_critical_temp_bme:
                current_temperature = self.get_cached_asic_temperature()
            else:
                current_temperature = self.get_ambient_temperature()

            if current_temperature is None:
                raise Exception('ASIC temperature read as None')

            logging.info('Current primary temperature: {} (BME?: {}) (Critical: {})'.format(
                current_temperature, self._override_critical_temp_bme, self._critical_temperature_limit))

            if current_temperature >= self._critical_temperature_limit:
                self._temperature_iscritical = True

                # If temperature is critical, force disable VREG_EN
                self.set_vreg_en(False)
                logging.critical('Temperature too high ({}C), ASIC disabled'.format(current_temperature))
            else:
                self._temperature_iscritical = False
                # Do not automatically re-enable, should cycle VREG_EN instead
                logging.debug('ASIC temperature ({}C) below critical ({}C)'.format(current_temperature, self._critical_temperature_limit))
        except Exception as e:
            # Force regulator low anyway
            logging.critical('Failed to get ASIC temperature ({}), disabling'.format(e))
            self.set_vreg_en(False)
            # raise

    def get_critical_temp_status(self):
        return self._temperature_iscritical

    ''' PAC1921 '''

    def _sync_power_supply_readings(self):
        if self._pac1921_array is None:
            logging.error("PAC1921 array is not present, cannot read")
            return

        if self._rail_monitor_mode == self._Rail_Monitor_Mode.POWER_AND_IV:
            current_meas = self._pac1921_array_current_measurement
            logging.debug("mode was POWER_AND_IV, current meas set to {}".format(current_meas))

            # Get Parameter Tree measurement type name
            current_meas_name = {pac1921.Measurement_Type.POWER: 'POWER',
                        pac1921.Measurement_Type.CURRENT: 'CURRENT',
                        pac1921.Measurement_Type.VBUS: 'VOLTAGE'}[current_meas]

            logging.debug("Measurement name is {}".format(current_meas_name))

            # Get readings from current measurement for all monitors
            for monitor in self._pac1921_array:
                val = monitor.read()
                self._power_supply_readings[monitor.get_name()][current_meas_name] = val

                if _RAIL_MONITOR_DERIVE_POWER:
                    try:
                        self._power_supply_readings[monitor.get_name()]['POWER'] = (
                                self._power_supply_readings[monitor.get_name()]['VOLTAGE'] *
                                self._power_supply_readings[monitor.get_name()]['CURRENT'])
                    except TypeError as e:
                        if 'NoneType' in str(e):
                            logging.info('Voltage or current for {} was None, calculating Power as None'.format(monitor))
                            self._power_supply_readings[monitor.get_name()]['POWER'] = None
                        else:
                            raise



            logging.debug("Readings taken, {}".format(self._power_supply_readings))

            # Advance to next measurement
            if _RAIL_MONITOR_DERIVE_POWER:
                next_measurement = {
                    pac1921.Measurement_Type.POWER: pac1921.Measurement_Type.CURRENT,
                    pac1921.Measurement_Type.VBUS: pac1921.Measurement_Type.CURRENT,
                    # Do not measure power directly
                    pac1921.Measurement_Type.CURRENT: pac1921.Measurement_Type.VBUS}[current_meas]
            else:
                next_measurement = {
                    pac1921.Measurement_Type.POWER: pac1921.Measurement_Type.CURRENT,
                    pac1921.Measurement_Type.CURRENT: pac1921.Measurement_Type.VBUS,
                    pac1921.Measurement_Type.VBUS: pac1921.Measurement_Type.POWER}[current_meas]

            for monitor in self._pac1921_array:
                monitor.set_measurement_type(next_measurement)
                monitor.config_freerun_integration_mode()

            self._pac1921_array_current_measurement = next_measurement

        elif self._rail_monitor_mode == self._Rail_Monitor_Mode.POWER_ONLY:
            logging.debug("mode was POWER ONLY")

            # Read power from all devices with pin controlled integration
            psr_titles, psr_values = self._pac1921_array.read_devices()

            value_index = 0
            for title in psr_titles:
                self._power_supply_readings[title]['POWER'] = psr_values[value_index]
                value_index += 1

    def get_power_supply_readings(self):
        return self._power_supply_readings

    ''' BME280 '''

    def get_ambient_temperature(self):
        if self._bme280 is None:
            return None
        if self.get_vreg_en() and not self._POWER_CYCLING:
            return self._bme280.temperature

    def get_ambient_pressure(self):
        if self._bme280 is None:
            return None
        if self.get_vreg_en() and not self._POWER_CYCLING:
            return self._bme280.pressure

    def get_ambient_humidity(self):
        if self._bme280 is None:
            return None
        if self.get_vreg_en() and not self._POWER_CYCLING:
            return self._bme280.humidity

    ''' FireFlies '''

    def _get_firefly(self, ff_num):
        if ff_num == 1:
            return self._firefly_1
        elif ff_num == 2:
            return self._firefly_2
        else:
            raise Exception("No firefly with number {}".format(ff_num))

    def _sync_firefly_info(self, ff_num):
        ff = self._get_firefly(ff_num)
        pn, vn, oui = ff.get_device_info()
        self._firefly_info[ff_num]['PN'] = pn
        self._firefly_info[ff_num]['VN'] = vn
        self._firefly_info[ff_num]['OUI'] = oui

    def get_firefly_temperature(self, ff_num):
        if self.get_vreg_en() and not self._POWER_CYCLING:
            ff = self._get_firefly(ff_num)
            return ff.get_temperature()

    def get_firefly_partnumber(self, ff_num):
        # This will not change during run, so only repeat the values read at boot
        return self._firefly_info[ff_num]['PN']

    def get_firefly_vendornumber(self, ff_num):
        # This will not change during run, so only repeat the values read at boot
        return self._firefly_info[ff_num]['VN']

    def get_firefly_oui(self, ff_num):
        # This will not change during run, so only repeat the values read at boot
        return self._firefly_info[ff_num]['OUI']

    def _sync_firefly_tx_channels_disabled(self, ff_num):
        ff = self._get_firefly(ff_num)

        # Do not sync an unmounted device
        if (ff is None):
            return

        self._firefly_channelstates[ff_num] = ff.get_disabled_tx_channels()

    def get_firefly_tx_channel_disabled(self, ff_num, channel_num):
        if self.get_vreg_en() and not self._POWER_CYCLING:

            # Sync if it has not yet been completed
            if self._firefly_channelstates[ff_num] == {}:
                self._sync_firefly_tx_channels_disabled(ff_num)

            return self._firefly_channelstates[ff_num][channel_num]

    def set_firefly_tx_channel_disabled(self, ff_num, channel_num, disabled):
        if self.get_vreg_en() and not self._POWER_CYCLING:
            ff = self._get_firefly(ff_num)

            channel_bitfield = FireFly.CHANNEL_00 << channel_num

            if (disabled):
                ff.disable_tx_channels(channel_bitfield)
            else:
                ff.enable_tx_channels(channel_bitfield)

    ''' LTC2986 '''

    def get_cached_pt100_temperature(self):
        return self._pt100_temp

    def _sync_asic_temperature(self):
        self._asic_temp = None
        self._pt100_temp =None

        if self._ltc2986 is not None:
            try:
                self._asic_temp = (self._ltc2986.measure_channel(_ltc2986_diode_channel))
            except LTCSensorException as e:
                logging.error("LTC2986 ASIC sensor failure: {}".format(e))
                self._asic_temp =None
            try:
                self._pt100_temp = (self._ltc2986.measure_channel(_ltc2986_pt100_channel))
            except LTCSensorException as e:
                logging.error("LTC2986 PT100 sensor failure: {}".format(e))
                self._pt100_temp =None
        else:
            logging.warning('LTC2986 was not read; not initialised at start')
            self._asic_temp = None
            self._pt100_temp =None

    def get_cached_asic_temperature(self):
        return self._asic_temp

    ''' MAX5306 '''

    def get_vcal_in(self):
        if self._max5306 is None:
            logging.error("Could not get MAX5306, was not init")
            return

        return self._vcal

    def set_vcal_in(self, value):
        if self._max5306 is None:
            logging.error("Could not set MAX5306, was not init")
            return

        if self.get_vreg_en() and not self._POWER_CYCLING:
            if value <= self.vcal_limit:
                self._max5306.set_output(1, value)
                self._vcal = value
                logging.info("Vcal changed to {}".format(value))

    ''' SI5344 Clock Generator Control '''

    def get_clk_config_avail(self):
        configlist = []
        for configfile in os.listdir(self._si5344_config_directory):
            if configfile.endswith('.txt'):
                configlist.append(configfile)
        return configlist

    def set_clk_config(self, value):
        try:
            self._si5344.apply_register_map(self._si5344_config_directory + value)
            self._si5344_config_filename = value
        except Exception as e:
            logging.error('Failed to set SI5344 config: {}'.format(e))

    def get_clk_config(self):
        return self._si5344_config_filename

    def step_clk(self, clock_num, direction_upwards):
        if direction_upwards:
            self._si5344.increment_channel_frequency(clock_num)
        else:
            self._si5344.decrement_channel_frequency(clock_num)

    ''' Direct GPIO Control '''

    def get_sync(self):
        # Convert to int
        return 1 if self.asic.get_sync() else 0

    def send_sync(self):
        LVDS_sync_active_state = 0 if (_LVDS_sync_idle_state == 1) else 1
        self._gpiod_sync.set_value(LVDS_sync_active_state)
        time.sleep(_LVDS_sync_duration)
        self._gpiod_sync.set_value(_LVDS_sync_idle_state)

    def set_sync_sel_aux(self, value):
        self.asic.set_sync_source_aux(value)

    def get_sync_sel_aux(self):
        # Convert to int
        return 1 if self.asic.get_sync_source_aux() else 0

    def set_asic_rst(self, value):
        # Will eventually be called by ASIC paramtree?
        if (value):
            self.asic.disable()
        else:
            self.asic.enable()

    def get_asic_rst(self):
        # Will eventually be called by ASIC paramtree?
        asic_enabled = self.asic.get_enabled()
        return not asic_enabled

    def set_vreg_en(self, enable):
        self._vreg_en_state = bool(enable)

        # Actions prior to setting pin
        if not enable:      # Disable
            # Deactivate any tasks that might attempt to communicate with devices
            self._POWER_CYCLING = True

            # Always Put ASIC GPIO in safe state (low for CMOS) if VREG is being disabled
            try:
                # Attempt to use the ASIC's own version, which will reset internal state
                self.asic.disable()
                self.asic.set_sync(False)
            except AttributeError:
                # Manually toggle pins
                self._gpiod_asic_nrst.set_value(0)  # nRST low
                self._gpiod_sync.set_value(0)       # sync low
        else:               # Enabled
            pass

        pin_state = 0 if (enable) else 1     # Reverse logic
        self._gpiod_vreg_en.set_value(pin_state)

        # Actions post setting pin
        if not enable:      # Disable
            pass
        else:               # Enabled
            # Allow time for devices to come up
            time.sleep(1)

            # Re-init the board devices
            logging.info("Board VREG power cycled, re-init devices")
            self.POR_init_devices()

            # Re-configure the device tree (some things depend on up-to-date device info
            self._paramtree_setup()

            # Re-activate any tasks that might attempt to communicate with devices
            logging.info("Device init complete, allowing communication")
            self._POWER_CYCLING = False


    def get_vreg_en(self):
        return self._vreg_en_state

    def vreg_power_cycle_init(self, value):
        """
        Power cycle VREG EN, and then re-init devices and the parameter tree to place
        the board in a stable and configured state.
        """

        # Perform the power cycle
        logging.warning("\n\n\n\nPower cycling board VREG")
        self.set_vreg_en(False)                              # Power up regulators

        # Schedule the enable to take place after a delay that does not block
        IOLoop.instance().call_later(2.0, self.set_vreg_en, True)

        logging.warning("Regulator enable will be called in 2s")

    ''' ASIC Control '''
    def set_asic_mode(self, value):
        if value == "global":
            self.asic.enter_global_mode()
            logging.info("Entering global mode")
        #elif value == "local":
        #    pass
        else:
            logging.warning("Mode {} is not supported by ASIC".format(value))

    def set_asic_integration_time(self, value):
        self.asic.set_integration_time(value)

    def get_asic_integration_time(self):
        try:
            # Read cached value from the ASIC
            return self.asic.get_integration_time(direct=False)
        except ASICDisabledError:
            return None

    def set_asic_frame_length(self, value):
        self.asic.set_frame_length(value)

    def get_asic_frame_length(self):
        try:
            # Read cached value from the ASIC
            return self.asic.get_frame_length(direct=False)
        except ASICDisabledError:
            return None

    def set_asic_feedback_capacitance(self, value):
        self.asic.set_feedback_capacitance(value)

    def get_asic_feedback_capacitance(self):
        try:
            # Read cached value from the ASIC
            return self.asic.get_feedback_capacitance(direct=False)
        except ASICDisabledError:
            return None

    def set_asic_serialiser_mode(self, value):
        # Mode can be set with a string or integer value
        self.asic.set_global_serialiser_mode(value)

    def get_asic_serialiser_mode(self):
        try:
            # Read cached value from the ASIC
            return self.asic.get_global_serialiser_mode(bits_only=False, direct=False)
        except ASICDisabledError:
            return None

    def set_asic_all_serialiser_pattern(self, value):
        self.asic.set_all_serialiser_pattern(value)

    def get_asic_all_serialiser_pattern(self):
        try:
            # Read cached value from the ASIC
            return self.asic.get_all_serialiser_pattern(direct=False)
        except ASICDisabledError:
            return None

    def get_asic_cal_pattern_en(self):
        try:
            # Read cached value from the ASIC
            return self.asic.get_calibration_test_pattern_enabled(direct=False)
        except ASICDisabledError:
            return None

    def set_asic_cal_pattern_en(self, enable=True):
        try:
            self.asic.enable_calibration_test_pattern(enable=enable)
        except ASICDisabledError:
            return None

    def set_asic_cal_pattern(self, pattern_name):
        try:
            if pattern_name == "default":
                self.asic.cal_pattern_set_default()
            elif pattern_name == "highlight":
                if self._asic_cal_highlight_div is not None and self._asic_cal_highlight_sec:
                    self.asic.cal_pattern_highlight_sector_division(
                            sector=self._asic_cal_highlight_sec,
                            division=self._asic_cal_highlight_div)
                else:
                    logging.error("Could not request sector/division highlight, please configure first")
            else:
                logging.error("Unsupported calibration pattern name. Please choose default or highlight")

        except ASICDisabledError:
            return None

    def cfg_asic_highlight(self, division=None, sector=None):
        if division is not None:
            self._asic_cal_highlight_div = division
        if sector is not None:
            self._asic_cal_highlight_sec = sector


    def set_segment_color_scale(self, vmax=None, vmin=None):
        if vmax is not None:
            if vmax == -1:
                self._segment_vmax = None
            else:
                self._segment_vmax = vmax
        if vmin is not None:
            if vmin == -1:
                self._segment_vmin = None
            else:
                self._segment_vmin = vmin

    def trigger_asic_segment_capture(self, segment):
        if not PLOTTING_SUPPORTED:
            logging.warning('ASIC segment readout triggered, but cannot be supported by available modules')
        self._segment_ready = False
        self._segment_capture_due = segment
        logging.info('ASIC segment read for segment {} has been scheduled'.format(segment))
        return None

    def _segment_capture_loop(self):
        if self._segment_capture_due is not None:
            self.perform_asic_segment_capture(self._segment_capture_due)
            self._segment_capture_due = None

    def perform_asic_segment_capture(self, segment):
        logging.info('Capturing image from segment {}'.format(segment))

        try:
            # Get the segment pattern read from the ASIC, 320 pixel values
            patternout_12bit = self.asic.read_test_pattern(segment)
            logging.warning('Pattern out: {}'.format(patternout_12bit))

            # Re-order the data with numpy
            reshaped = np.empty((4,80), dtype=np.uint16)
            for scol in range(20):
                idx = scol*16
                ridx = scol*4
                reshaped[::, ridx:ridx+4] = np.array(patternout_12bit)[idx:idx+16].reshape(4,4)

            logging.warning('Reshaped array: {}'.format(reshaped))

            # Plot the reshaped array as color mapped mesh
            #plt.rcParams["figure.figsize"] = (15,2)
            fig, ax = plt.subplots(1, 1)
            plt.title('Segment {}'.format(segment))
            ax.set_xticks(range(0,80, 4))
            ax.set_yticks(range(0,4,2))
            #mesh = ax.pcolormesh(reshaped, vmin=None, vmax=None, )
            mesh = ax.imshow(reshaped, vmin=self._segment_vmin, vmax=self._segment_vmax)
            fig.colorbar(mesh, orientation='horizontal', fraction=0.1)

            # Write output to file
            time_now = time.localtime()
            tstamp = "{:04d}{:02d}{:02d}_{:02d}{:02d}{:02d}".format(time_now.tm_year,
                                                                    time_now.tm_mon,
                                                                    time_now.tm_mday,
                                                                    time_now.tm_hour,
                                                                    time_now.tm_min,
                                                                    time_now.tm_sec,
                                                                    int((time.time() % 1) * 1000))
            #filename = '/opt/loki-detector/exports/{}_seg{}.png'.format(tstamp, segment)
            filename = 'test/static/imgout/segment.png'.format(tstamp, segment)
            plt.savefig(filename, dpi=400, transparent=True, bbox_inches='tight')

            self._segment_ready = True

        except ASICDisabledError:
            logging.error('Could not trigger segment readout due to disabled ASIC')
            return None

    def _paramtree_setup(self):

        # Sync single-read items
        self._firefly_info = {1: {}, 2: {}}
        if self._firefly_1 is not None:
            self._sync_firefly_info(1)
        if self._firefly_2 is not None:
            self._sync_firefly_info(2)

        # Sync repeating readings
        self._POWER_SUPPLY_READINGS_EMPTY = {
            vdddcntrl_rail_name: {'POWER': None, 'VOLTAGE': None, 'CURRENT': None}, # u3
            vdddasic_rail_name: {'POWER': None, 'VOLTAGE': None, 'CURRENT': None},  # u2
            vddaasic_rail_name: {'POWER': None, 'VOLTAGE': None, 'CURRENT': None}}  # u1
        if self._PARAMTREE_FIRSTINIT:
            self._power_supply_readings = copy.deepcopy(self._POWER_SUPPLY_READINGS_EMPTY)

        rail_monitor_tree = self._gen_RailMonitor_Tree(
                vdddcntrl_rail_name, vdddasic_rail_name, vddaasic_rail_name,
                self._rail_monitor_mode,
                self.get_power_supply_readings)

        # Define ParameterTree Sub-dictionaries
        self._firefly_channelstates = {1: {}, 2: {}}
        self.sync_firefly_readings()
        firefly_tree_1 = self._gen_FireFly_Tree(1) if self._firefly_1 is not None else {}
        firefly_tree_2 = self._gen_FireFly_Tree(2) if self._firefly_2 is not None else {}
        loki_performance_tree = self._gen_loki_performance_tree()

        logging.info(rail_monitor_tree)

        # Define the ParameterTree
        self._param_tree = ParameterTree({
            "PSU": rail_monitor_tree,
            "FIREFLY1": firefly_tree_1,
            "FIREFLY2": firefly_tree_2,
            "TEMPERATURES":{
                "AMBIENT":(self.get_ambient_temperature, None, {"description":"Board ambient temperature from BME280", "units":"C"}),
                "PT100":(self.get_cached_pt100_temperature, None, {"description":"PT100 temperature", "units":"C"}),
                "ASIC":(self.get_cached_asic_temperature, None, {"description":"ASIC internal diode temperature", "units":"C"}),
                "HUMIDITY":(self.get_ambient_humidity, None, {"description":"Board ambient humidity from BME280", "units":"%RH"})
            },
            "CRITICAL_TEMP": (self.get_critical_temp_status, None, {"description":"Read 1 if system has a critical temperature"}),
            "VCAL": (self.get_vcal_in, self.set_vcal_in, {"description":"Analogue VCAL_IN", "units":"V"}),
            "SYNC": (self.get_sync, self.send_sync, {"description":"Write to send sync to ASIC. Ignore read"}),
            "SYNC_SEL_AUX": (self.get_sync_sel_aux, self.set_sync_sel_aux, {"description":"Set true to get sync signal externally"}),
            "ASIC_RST":(self.get_asic_rst, self.set_asic_rst, {"description":"Set true to enter ASIC reset"}),
            "ASIC_MODE":(None, self.set_asic_mode, {"description":"Init the ASIC with a specific mode (e.g. global)"}),
            "ASIC_INTEGRATION_TIME":(self.get_asic_integration_time, self.set_asic_integration_time, {"description":"ASIC Integration Time (in frames)"}),
            "ASIC_FRAME_LENGTH":(self.get_asic_frame_length, self.set_asic_frame_length, {"description":"ASIC Frame Length (in cycles)"}),
            "ASIC_FEEDBACK_CAPACITANCE":(self.get_asic_feedback_capacitance, self.set_asic_feedback_capacitance, {"description":"ASIC Preamo feedback capacitance"}),
            "ASIC_SER_MODE":(self.get_asic_serialiser_mode, self.set_asic_serialiser_mode, {"description":"ASIC Serialiser mode (init, bonding or data) as str"}),
            "ASIC_SER_PATTERN":(self.get_asic_all_serialiser_pattern, self.set_asic_all_serialiser_pattern, {"description":"ASIC Serialiser pattern (0 for serial, 7 for PRBS, 1-5 for clock div)"}),
            "ASIC_SEGMENT_CAPTURE":(lambda: {True:1, False:0}[self._segment_ready], self.trigger_asic_segment_capture, {}),
            "ASIC_SEGMENT_VMAX":(lambda: self._segment_vmax, lambda maxval: self.set_segment_color_scale(vmax=maxval), {"description":"Maximum for segment colour scale"}),
            "ASIC_SEGMENT_VMIN":(lambda: self._segment_vmin, lambda minval: self.set_segment_color_scale(vmin=minval), {"description":"Minimum for segment colour scale"}),
            "ASIC_CAL_PATTERN":{
                "ENABLE":(self.get_asic_cal_pattern_en, self.set_asic_cal_pattern_en, {"description":"Enable ASIC calibration pattern injection"}),
                "PATTERN":(None, self.set_asic_cal_pattern, {"description":"Selection of pattern type: default or highlight"}),
                "HIGHLIGHT_DIVISION":(lambda: self._asic_cal_highlight_div, lambda division: self.cfg_asic_highlight(division=division), {"description":"Division chosen for 4x4 grid highlighting via calibration pattern"}),
                "HIGHLIGHT_SECTOR":(lambda: self._asic_cal_highlight_sec, lambda sector: self.cfg_asic_highlight(sector=sector), {"description":"Sector chosen for 4x4 grid highlighting via calibration pattern"}),
            },
            "VREG_EN":(self.get_vreg_en, self.set_vreg_en, {"description":"Set false to disable on-pcb supplies. To power up, use VREG_CYCLE (contains device init)"}),
            "VREG_CYCLE":(self.get_vreg_en, self.vreg_power_cycle_init, {"description":"Set to power cycle the VREG_EN and re-init devices. Read will return VREG enable state"}),
            "CLKGEN":{
                "CONFIG_AVAIL":(self.get_clk_config_avail, None, {"description":"Available SI5344 config files"}),
                "CONFIG_SELECT":(self.get_clk_config, self.set_clk_config, {"description":"Currently selected SI5344 config"}),
                "CKTDC_STEP":(None, lambda dir: self.step_clk(0, dir), {"description": "Step frequency of TDC clock up or down"}),
                "CKSER_STEP":(None, lambda dir: self.step_clk(1, dir), {"description": "Step frequency of SER clock up or down"}),
                "CK200_STEP":(None, lambda dir: self.step_clk(2, dir), {"description": "Step frequency of 200 clock up or down"}),
                "CKDBG_STEP":(None, lambda dir: self.step_clk(3, dir), {"description": "Step frequency of the debug header clock up or down"}),
            },
            "LOKI_PERFORMANCE": loki_performance_tree
        })

        self._PARAMTREE_FIRSTINIT = False
        logging.info(self._param_tree)
