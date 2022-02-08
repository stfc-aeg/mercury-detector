from odin_devices.gpio_bus import GPIO_ZynqMP
from odin_devices.firefly import FireFly
import odin_devices.pac1921 as pac1921
from odin_devices.max5306 import MAX5306
from odin_devices.si534x import SI5344
from odin_devices.bme280 import BME280
from odin_devices.i2c_device import I2CException
from odin_devices.spi_device import SPIDevice

from .asic import Asic

try:
    from odin_devices.ltc2986 import LTC2986, LTCSensorException
except ModuleNotFoundError:
    # Allow init to continue without LTC2987 temperature sensor support build in
    # (driver not progressed due to hardware fault)
    pass

from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError

import logging
import time
import sys
import os
from enum import Enum as _Enum, auto as _auto

logging.basicConfig(encoding='utf-8', level=logging.INFO)

# If true, derive power from PAC1921 IV readings if they are being taken instead of reading it
_RAIL_MONITOR_DERIVE_POWER = True

class Carrier_Interface():
    def __init__(self, i2c_device_bus,
                 spidev_id_mercury, spidev_id_ltc, spidev_id_max,
                 pin_firefly_1, pin_firefly_2, pin_nRead_int, pin_sync,
                 pin_sync_sel, pin_asic_nrst, pin_vreg_en):
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
        pin_vreg_en=2
        )

_vcal_default = 1.5     # TODO check this

_ltc2986_pt100_channel = 6
_ltc2986_temp1_channel = 2
_ltc2986_temp2_channel = 1

_LVDS_sync_idle_state = 0   # TODO Check polarity
_LVDS_sync_duration = 0.1   # TODO Check duration


class Carrier():

    class _Rail_Monitor_Mode (_Enum):
        POWER_ONLY = _auto()
        POWER_AND_IV = _auto()

    def __init__(self, si5344_config_directory, si5344_config_filename,
                 power_monitor_IV,
                 interface_definition=_interface_definition_default,
                 vcal=_vcal_default):

        self._POWER_CYCLING = False

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

        # Get LOKI GPIO pin bus
        self._gpio_bus = GPIO_ZynqMP

        # Claim standalone control pins
        self._gpiod_sync = GPIO_ZynqMP.get_pin(self._interface_definition.pin_sync,
                                               GPIO_ZynqMP.DIR_OUTPUT)
        self._gpiod_sync_sel = GPIO_ZynqMP.get_pin(self._interface_definition.pin_sync_sel,
                                                   GPIO_ZynqMP.DIR_OUTPUT)
        self._gpiod_asic_nrst = GPIO_ZynqMP.get_pin(self._interface_definition.pin_asic_nrst,
                                                    GPIO_ZynqMP.DIR_OUTPUT)
        self._gpiod_vreg_en = GPIO_ZynqMP.get_pin(self._interface_definition.pin_vreg_en,
                                                  GPIO_ZynqMP.DIR_OUTPUT)

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
            hz=2000000)

        # Set default pin states
        self._gpiod_sync.set_value(_LVDS_sync_idle_state)
        self.set_sync_sel_aux(False)                        # Set sync Zynq-controlled
        self.set_asic_rst(True)                             # Init device in reset
        self.vreg_power_cycle_init(None)                    # Contains device setup


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

    def get(self, path, wants_metadata=False):
        """Main get method for the parameter tree"""
        return self._param_tree.get(path, wants_metadata)
    def set(self, path, data):
        """Main set method for the parameter tree"""
        return self._param_tree.set(path, data)

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
                                               name='VDDDCNTRL',
                                               r_sense=0.02,
                                               measurement_type=pac1921.Measurement_Type.POWER)
            self._pac1921_u2 = pac1921.PAC1921(address_resistance=620,
                                               name='VDDD ASIC',
                                               r_sense=0.02,
                                               measurement_type=pac1921.Measurement_Type.POWER)
            self._pac1921_u1 = pac1921.PAC1921(address_resistance=820,
                                               name='VDDA ASIC',
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
                                          LTC2986.RTD_Excitation_Mode.NO_ROTATION_NO_SHARING,
                                          LTC2986.RTD_Excitation_Current.CURRENT_500UA,
                                          LTC2986.RTD_Curve.EUROPEAN,
                                          _ltc2986_pt100_channel)
            # TODO add diode sensor channels for ASIC once more info available. Use _ltc2986_temp1_channel,_ltc2986_temp2_channel
        except Exception as e:
            logging.error("LTC2986 init failed: {}".format(e))
            self._ltc2986 = None

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
        self._sync_power_supply_readings()

    def sync_firefly_readings(self):
        self._sync_firefly_tx_channels_disabled(1)
        self._sync_firefly_tx_channels_disabled(2)

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

    ''' PAC1921 '''

    def _sync_power_supply_readings(self):
        if self._pac1921_array is None:
            logging.error("PAC1921 array is not present, cannot read")
            return

        if self._rail_monitor_mode == self._Rail_Monitor_Mode.POWER_AND_IV:
            current_meas = self._pac1921_array_current_measurement
            logging.warning("mode was POWER_AND_IV, current meas set to {}".format(current_meas))

            # Get Parameter Tree measurement type name
            current_meas_name = {pac1921.Measurement_Type.POWER: 'POWER',
                        pac1921.Measurement_Type.CURRENT: 'CURRENT',
                        pac1921.Measurement_Type.VBUS: 'VOLTAGE'}[current_meas]

            logging.warning("Measurement name is {}".format(current_meas_name))

            # Get readings from current measurement for all monitors
            for monitor in self._pac1921_array:
                val = monitor.read()
                self._power_supply_readings[monitor.get_name()][current_meas_name] = val

                if _RAIL_MONITOR_DERIVE_POWER:
                    self._power_supply_readings[monitor.get_name()]['POWER'] = (
                            self._power_supply_readings[monitor.get_name()]['VOLTAGE'] *
                            self._power_supply_readings[monitor.get_name()]['CURRENT'])


            logging.warning("Readings taken, {}".format(self._power_supply_readings))

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
            logging.warning("mode was POWER ONLY")

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
        return self._bme280.temperature

    def get_ambient_pressure(self):
        if self._bme280 is None:
            return None
        return self._bme280.pressure

    def get_ambient_humidity(self):
        if self._bme280 is None:
            return None
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
        return self._firefly_channelstates[ff_num][channel_num]

    def set_firefly_tx_channel_disabled(self, ff_num, channel_num, disabled):
        ff = self._get_firefly(ff_num)

        channel_bitfield = FireFly.CHANNEL_00 << channel_num

        if (disabled):
            ff.disable_tx_channels(channel_bitfield)
        else:
            ff.enable_tx_channels(channel_bitfield)

    ''' LTC2986 '''

    def get_pt100_temperature(self):
        if self._ltc2986 is not None:
            try:
                return (self._ltc2986.measure_channel(_ltc2986_pt100_channel))
            except LTCSensorException as e:
                logging.error("LTC2986 sensor failure: {}".format(e))
                return None
        else:
            return None

    def get_asic_temp1_temperature(self):
        if self._ltc2986 is not None:
            try:
                return (self._ltc2986.measure_channel(_ltc2986_temp1_channel))
            except LTCSensorException as e:
                logging.error("LTC2986 sensor failure: {}".format(e))
                return None
        else:
            return None

    def get_asic_temp2_temperature(self):
        if self._ltc2986 is not None:
            try:
                return (self._ltc2986.measure_channel(_ltc2986_temp2_channel))
            except LTCSensorException as e:
                logging.error("LTC2986 sensor failure: {}".format(e))
                return None
        else:
            return None

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

        if value <= self.vcal_limit:
            self._max5306.set_output(1, value)
            self._vcal = value
            logging.debug("Vcal changed to {}".format(value))

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

    def send_sync(self):
        LVDS_sync_active_state = 0 if (_LVDS_sync_idle_state == 1) else 1
        self._gpiod_sync.set_value(LVDS_sync_active_state)
        time.sleep(_LVDS_sync_duration)
        self._gpiod_sync.set_value(_LVDS_sync_idle_state)

    def set_sync_sel_aux(self, value):
        self._sync_sel_aux_state = bool(value)
        pin_state = 0 if (value) else 1
        self._gpiod_sync_sel.set_value(pin_state)

    def get_sync_sel_aux(self):
        return self._sync_sel_aux_state

    def set_asic_rst(self, value):
        # Will eventually be called by ASIC paramtree?
        if (value):
            self.asic.disable()
        else:
            self.asic.enable()

    def get_asic_rst(self):
        # Will eventually be called by ASIC paramtree?
        return not self.asic.get_enabled()

    def set_vreg_en(self, value):
        self._vreg_en_state = bool(value)
        pin_state = 0 if (value) else 1     # Reverse logic
        self._gpiod_vreg_en.set_value(pin_state)

    def get_vreg_en(self):
        return self._vreg_en_state

    def vreg_power_cycle_init(self, value):
        """
        Power cycle VREG EN, and then re-init devices and the parameter tree to place
        the board in a stable and configured state.
        """

        # Deactivate any tasks that might attempt to communicate with devices
        self._POWER_CYCLING = True

        # Put ASIC GPIO in safe state (low for CMOS)
        self._gpiod_asic_nrst.set_value(0)

        # Perform the power cycle
        logging.debug("\n\n\n\nPower cycling board VREG")
        self.set_vreg_en(False)                              # Power up regulators
        time.sleep(2)
        self.set_vreg_en(True)                              # Power up regulators

        # Allow time for devices to come up
        time.sleep(1)

        # Re-init the board devices
        logging.debug("Board VREG power cycled, re-init devices")
        self.POR_init_devices()

        # Re-configure the device tree (some things depend on up-to-date device info
        self._paramtree_setup()

        # Re-activate any tasks that might attempt to communicate with devices
        self._POWER_CYCLING = False

    def _paramtree_setup(self):

        # Sync single-read items
        self._firefly_info = {1: {}, 2: {}}
        if self._firefly_1 is not None:
            self._sync_firefly_info(1)
        if self._firefly_2 is not None:
            self._sync_firefly_info(2)

        # Sync repeating readings
        self._power_supply_readings = {
                self._pac1921_u3.get_name(): {'POWER': 0, 'VOLTAGE': 0, 'CURRENT': 0},
                self._pac1921_u2.get_name(): {'POWER': 0, 'VOLTAGE': 0, 'CURRENT': 0},
                self._pac1921_u1.get_name(): {'POWER': 0, 'VOLTAGE': 0, 'CURRENT': 0}}
        self._firefly_channelstates = {1: {}, 2: {}}
        #self.sync_power_readings()
        self.sync_firefly_readings()

        # Define ParameterTree Sub-dictionaries
        firefly_tree_1 = self._gen_FireFly_Tree(1) if self._firefly_1 is not None else {}
        firefly_tree_2 = self._gen_FireFly_Tree(2) if self._firefly_2 is not None else {}
        rail_monitor_tree = self._gen_RailMonitor_Tree(
                self._pac1921_u3.get_name(), self._pac1921_u2.get_name(), self._pac1921_u1.get_name(),
                self._rail_monitor_mode,
                self.get_power_supply_readings)

        logging.info(rail_monitor_tree)

        # Define the ParameterTree
        self._param_tree = ParameterTree({
            "PSU": rail_monitor_tree,
            "FIREFLY1": firefly_tree_1,
            "FIREFLY2": firefly_tree_2,
            "TEMPERATURES":{
                "ZYNQ": {
                    "PS":(lambda: self.get_zynq_ams_temp('0_ps'), None, {"description":"Zynq system PS Temperature", "units":"C"}),
                    "REMOTE":(lambda: self.get_zynq_ams_temp('1_remote'), None, {"description":"Zynq system Remote Temperature", "units":"C"}),
                    "PL":(lambda: self.get_zynq_ams_temp('2_pl'), None, {"description":"Zynq system PL Temperature", "units":"C"}),
                },
                "AMBIENT":(self.get_ambient_temperature, None, {"description":"Board ambient temperature from BME280", "units":"C"}),
                "PT100":(self.get_pt100_temperature, None, {"description":"PT100 temperature", "units":"C"}),
                "ASIC_TEMP1":(self.get_asic_temp1_temperature, None, {"description":"ASIC internal TEMP1", "units":"C"}),
                "ASIC_TEMP2":(self.get_asic_temp2_temperature, None, {"description":"ASIC internal TEMP2", "units":"C"})
            },
            "VCAL": (self.get_vcal_in, self.set_vcal_in, {"description":"Analogue VCAL_IN", "units":"V"}),
            "SYNC": (lambda: 0, self.send_sync, {"description":"Write to send sync to ASIC. Ignore read"}),
            "SYNC_SEL_AUX": (self.get_sync_sel_aux, self.set_sync_sel_aux, {"description":"Set true to get sync signal externally"}),
            "ASIC_RST":(self.get_asic_rst, self.set_asic_rst, {"description":"Set true to enter ASIC reset"}),
            #"VREG_EN":(self.get_vreg_en, self.set_vreg_en, {"description":"Set true to enable on-board power supplies"})
            "VREG_CYCLE":(None, self.vreg_power_cycle_init, {"description":"Set to power cycle the VREG_EN and re-init devices"}),
            "CLKGEN":{
                "CONFIG_AVAIL":(self.get_clk_config_avail, None, {"description":"Available SI5344 config files"}),
                "CONFIG_SELECT":(self.get_clk_config, self.set_clk_config, {"description":"Currently selected SI5344 config"}),
                "CKTDC_STEP":(None, lambda dir: self.step_clk(0, dir), {"description": "Step frequency of TDC clock up or down"}),
                "CKSER_STEP":(None, lambda dir: self.step_clk(1, dir), {"description": "Step frequency of SER clock up or down"}),
                "CK200_STEP":(None, lambda dir: self.step_clk(2, dir), {"description": "Step frequency of 200 clock up or down"}),
                "CKDBG_STEP":(None, lambda dir: self.step_clk(3, dir), {"description": "Step frequency of the debug header clock up or down"}),
            }
        })
