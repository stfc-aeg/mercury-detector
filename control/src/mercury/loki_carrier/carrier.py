from loki.adapter import LokiCarrier_1v0, DeviceHandler
from mercury.loki_carrier.hexitec_mhz_asic import HEXITEC_MHz
from odin_devices.ad5593r import AD5593R
from odin_devices.ad7998 import AD7998
from odin_devices.mic284 import MIC284
from odin_devices.ltc2986 import LTC2986
from odin_devices.i2c_device import I2CDevice
from odin_devices.firefly import FireFly
import logging
import time
from enum import IntEnum, unique


# Holds information mapping ASIC channels onto different devices, for example, fireflies, retimers etc.
class ChannelInfo(object):
    def __init__(self, name, firefly_dev, firefly_ch_num, firefly_ch_bitfield):
        self.name = name
        self.firefly_dev = firefly_dev
        self.firefly_ch_num = firefly_ch_num
        self.firefly_ch_bitfield = firefly_ch_bitfield


class LokiCarrier_HMHz (LokiCarrier_1v0):

    _variant = 'LOKI 1v0 HEXITEC-MHz'

    # States the enable state machine will step through, in 'normal' order.
    @unique
    class ENABLE_STATE (IntEnum):
        PRE_INIT = 0
        LOKI_INIT = 1
        LOKI_DONE = 2
        PWR_INIT = 3
        PWR_DONE = 4
        COB_INIT = 5
        COB_DONE = 6
        ASIC_INIT = 7
        ASIC_DONE = 8

    def __init__(self, **kwargs):
        self._logger = logging.getLogger('HEXITEC-MHz Carrier')


        #TODO update this for HMHZ
        self._default_clock_config = 'ZL30266_LOKI_Nosync_500MHz_218MHz.mfg'

        # If this is set false, ASIC init will just set up SPI
        kwargs.setdefault('fast_data_enabled', True)
        self._fast_data_enabled = kwargs.get('fast_data_enabled')

        # Override parent pin settings

        # Add mhz-specific pins (Application/ASIC enable are already default LOKI
        # control pins, so these are additional IO only. Settings may be overridden
        # in the config file.
        kwargs.setdefault('pin_config_id_sync', 'EMIO18 LVDS')
        kwargs.setdefault('pin_config_active_low_sync', False)
        kwargs.setdefault('pin_config_is_input_sync', False)
        kwargs.setdefault('pin_config_default_value_sync', 0)     # Active high so low by default

        # Delay here should mean that if the ASIC was previously in use, the SYNC low will allow it to complete
        # the last frame before the firefly and ASIC are disabled.
        time.sleep(0.1)

        kwargs.setdefault('pin_config_id_diff01', 'EMIO19 LVDS')
        kwargs.setdefault('pin_config_active_low_diff01', False)
        kwargs.setdefault('pin_config_is_input_diff01', False)
        kwargs.setdefault('pin_config_default_value_diff01', 0)     # Active high so low by default

        kwargs.setdefault('pin_config_id_diff02', 'EMIO20 LVDS')
        kwargs.setdefault('pin_config_active_low_diff02', False)
        kwargs.setdefault('pin_config_is_input_diff02', False)
        kwargs.setdefault('pin_config_default_value_diff02', 0)     # Active high so low by default

        # This is actually the FF_RESET# pin
        kwargs.setdefault('pin_config_id_firefly_en', 'EMIO22')
        kwargs.setdefault('pin_config_active_low_firefly_en', False)
        kwargs.setdefault('pin_config_is_input_firefly_en', False)
        kwargs.setdefault('pin_config_default_value_firefly_en', 0)     # Active high so disabled by default

        kwargs.setdefault('pin_config_id_firefly_sel1', 'EMIO29')
        kwargs.setdefault('pin_config_active_low_firefly_sel1', False)
        kwargs.setdefault('pin_config_is_input_firefly_sel1', False)
        kwargs.setdefault('pin_config_default_value_firefly_sel1', 0)     # Active high so disabled by default

        kwargs.setdefault('pin_config_id_firefly_sel2', 'EMIO30')
        kwargs.setdefault('pin_config_active_low_firefly_sel2', False)
        kwargs.setdefault('pin_config_is_input_firefly_sel2', False)
        kwargs.setdefault('pin_config_default_value_firefly_sel2', 0)     # Active high so disabled by default

        kwargs.setdefault('pin_config_id_firefly_int1', 'EMIO24')
        kwargs.setdefault('pin_config_active_low_firefly_int1', False)
        kwargs.setdefault('pin_config_is_input_firefly_int1', True)

        kwargs.setdefault('pin_config_id_firefly_int2', 'EMIO23')
        kwargs.setdefault('pin_config_active_low_firefly_int2', False)
        kwargs.setdefault('pin_config_is_input_firefly_int2', True)

        # LOKI control pin CTRL1 being used for High Voltage Enable
        kwargs.setdefault('pin_config_id_hven', 'CTRL1')
        kwargs.setdefault('pin_config_active_low_hven', False)
        kwargs.setdefault('pin_config_is_input_hven', False)
        kwargs.setdefault('pin_config_default_value_hven', 0)     # Active high so disabled by default

        kwargs.setdefault('pin_config_id_peltier_en', 'EMIO21')
        kwargs.setdefault('pin_config_active_low_peltier_en', False)    # Active low SHDN, so active high en
        kwargs.setdefault('pin_config_is_input_peltier_en', False)
        kwargs.setdefault('pin_config_default_value_peltier_en', 0)     # Active high so disabled by default

        kwargs.setdefault('pin_config_id_pgood', 'EMIO25')
        kwargs.setdefault('pin_config_active_low_pgood', False)
        kwargs.setdefault('pin_config_is_input_pgood', True)

        # MIC284 critical pin
        kwargs.setdefault('pin_config_id_tcrit', 'EMIO26')
        kwargs.setdefault('pin_config_active_low_tcrit', True)
        kwargs.setdefault('pin_config_is_input_tcrit', True)

        # MIC284 interrupt pin
        kwargs.setdefault('pin_config_id_tint', 'EMIO27')
        kwargs.setdefault('pin_config_active_low_tint', True)
        kwargs.setdefault('pin_config_is_input_tint', True)

        #TODO add TRIP_CLK and TRIP_BUF, but I'm not sure of their direction yet

        # per_en (Periphernal Enable) being used for regulator enable signal REG_EN, aka ASIC_EN. Do not confuse with ASIC reset.
        kwargs.update({'pin_config_active_low_per_en': False})      # Is active low reset, therefore active high enable for ASIC_EN
        kwargs.update({'pin_config_default_value_per_en': False})      # Disabled by default

        kwargs.update({'pin_config_active_low_app_en': False})      # This will force the ASIC into reset

        # Set clock generator base configuration directory, can be overridden
        kwargs.setdefault('clkgen_base_dir', './clkgen/')

        # Get config for MIC284
        self._mic284 = DeviceHandler(device_type_name='MIC284')
        self._mic284.i2c_address = 0x48
        self._mic284.i2c_bus = self._application_interfaces_i2c['APP_PWR']

        # Get config for AD7998 ADC
        self._ad7998= DeviceHandler(device_type_name='AD7998')
        self._ad7998.i2c_address = 0x20
        self._ad7998.i2c_bus = self._application_interfaces_i2c['APP_PWR']

        # Get the limit for the DAC, other functionality provided by base adapter.
        kwargs.setdefault('vcal_in_limit', 1.8)     # 1.8v is max safe voltage to HEXITEC-MHz ASIC.
        kwargs.setdefault('vcal_in_default', 1.5)   # VCAL setting that will be set on startup.
        self._vcal_in_limit = kwargs.get('vcal_in_limit')
        self._vcal_in_default = kwargs.get('vcal_in_default')

        # Store information about the ADC channels
        # <multiple> will multiply the calculated pin input voltage in case a divider has been used.
        # <name>: (<dac channel>, <multiple>)
        self._ad7998._channel_mapping = {
            'VDDA':         (1, 1),
            'VDDD':         (2, 1),
            'HV_MON':       (3, 1),
            'TRIP_REG_T':   (4, 1),
            'TRIP_REG_AI':  (5, 1),
            'TRIP_REG_DI':  (6, 1),
            'T_CRIT':       (7, 1),
        }

        self._ad7998._trip_nice_names = {
            'TRIP_REG_T':   'Regulator Temperature',
            'TRIP_REG_AI':  'Analog Regulator Current',
            'TRIP_REG_DI':  'Digital Regulator Current',
            'T_CRIT':       'ASIC Temperature',
        }

        # Add more sensors to environment system for MIC
        self._env_sensor_info.extend([
            ('POWER_BOARD', 'temperature', {"description": "Power Board MIC284 internal temperature", "units": "C"}),
            ('ASIC', 'temperature', {"description": "ASIC via MIC84 external reading", "units": "C"}),
            ('DIODE', 'temperature', {"description": "ASIC internal temperature diode via LTC2986", "units": "C"}),
            ('FIREFLY00to09', 'temperature', {"description": "FireFly channels 0-9 temperature", "units": "C"}),
            ('FIREFLY10to19', 'temperature', {"description": "FireFly channels 10-19 temperature", "units": "C"}),
        ])

        # Get config for FireFly
        self._firefly_00to09 = DeviceHandler(device_type_name='FireFly')
        self._firefly_00to09.name = '00to09'
        self._firefly_00to09.select_pin_friendlyname = 'ff_sel_00to09'
        self._firefly_00to09.int_pin_friendlyname = 'ff_int_00to09'
        self._firefly_00to09.i2c_bus = self._application_interfaces_i2c['APP_PWR']
        self._firefly_10to19 = DeviceHandler(device_type_name='FireFly')
        self._firefly_10to19.name = '10to19'
        self._firefly_10to19.select_pin_friendlyname = 'ff_sel_10to19'
        self._firefly_10to19.int_pin_friendlyname = 'ff_int_10to19'
        self._firefly_10to19.i2c_bus = self._application_interfaces_i2c['APP_PWR']
        self._fireflies = [self._firefly_00to09, self._firefly_10to19]

        # Holds channel mapping information, relating named external channels to other parts of the system
        self._merc_channels = {}
        self._merc_channels['0'] = ChannelInfo(
            name='0',
            firefly_dev = self._firefly_00to09,
            firefly_ch_num = 2,
            firefly_ch_bitfield = FireFly.CHANNEL_02, #B14,15
        )
        self._merc_channels['1'] = ChannelInfo(
            name='1',
            firefly_dev = self._firefly_00to09,
            firefly_ch_num = 3,
            firefly_ch_bitfield = FireFly.CHANNEL_03, #A14,15
        )
        self._merc_channels['2'] = ChannelInfo(
            name='2',
            firefly_dev = self._firefly_00to09,
            firefly_ch_num = 4,
            firefly_ch_bitfield = FireFly.CHANNEL_04, #B11,12
        )
        self._merc_channels['3'] = ChannelInfo(
            name='3',
            firefly_dev = self._firefly_00to09,
            firefly_ch_num = 5,
            firefly_ch_bitfield = FireFly.CHANNEL_05, #A11,12
        )
        self._merc_channels['4'] = ChannelInfo(
            name='4',
            firefly_dev = self._firefly_00to09,
            firefly_ch_num = 6,
            firefly_ch_bitfield = FireFly.CHANNEL_06, #B8,9
        )
        self._merc_channels['5'] = ChannelInfo(
            name='5',
            firefly_dev = self._firefly_00to09,
            firefly_ch_num = 7,
            firefly_ch_bitfield = FireFly.CHANNEL_07, #A8,9
        )
        self._merc_channels['6'] = ChannelInfo(
            name='6',
            firefly_dev = self._firefly_00to09,
            firefly_ch_num = 8,
            firefly_ch_bitfield = FireFly.CHANNEL_08, #B14,15
        )
        self._merc_channels['7'] = ChannelInfo(
            name='7',
            firefly_dev = self._firefly_00to09,
            firefly_ch_num = 9,
            firefly_ch_bitfield = FireFly.CHANNEL_09, #A5,6
        )
        self._merc_channels['8'] = ChannelInfo(
            name='8',
            firefly_dev = self._firefly_00to09,
            firefly_ch_num = 10,
            firefly_ch_bitfield = FireFly.CHANNEL_10, #B2,3
        )
        self._merc_channels['9'] = ChannelInfo(
            name='9',
            firefly_dev = self._firefly_00to09,
            firefly_ch_num = 11,
            firefly_ch_bitfield = FireFly.CHANNEL_11, #A2,3
        )

        self._merc_channels['10'] = ChannelInfo(
            name='0',
            firefly_dev = self._firefly_10to19,
            firefly_ch_num = 2,
            firefly_ch_bitfield = FireFly.CHANNEL_02, #B14,15
        )
        self._merc_channels['11'] = ChannelInfo(
            name='1',
            firefly_dev = self._firefly_10to19,
            firefly_ch_num = 3,
            firefly_ch_bitfield = FireFly.CHANNEL_03, #A14,15
        )
        self._merc_channels['12'] = ChannelInfo(
            name='2',
            firefly_dev = self._firefly_10to19,
            firefly_ch_num = 4,
            firefly_ch_bitfield = FireFly.CHANNEL_04, #B11,12
        )
        self._merc_channels['13'] = ChannelInfo(
            name='3',
            firefly_dev = self._firefly_10to19,
            firefly_ch_num = 5,
            firefly_ch_bitfield = FireFly.CHANNEL_05, #A11,12
        )
        self._merc_channels['14'] = ChannelInfo(
            name='4',
            firefly_dev = self._firefly_10to19,
            firefly_ch_num = 6,
            firefly_ch_bitfield = FireFly.CHANNEL_06, #B8,9
        )
        self._merc_channels['15'] = ChannelInfo(
            name='5',
            firefly_dev = self._firefly_10to19,
            firefly_ch_num = 7,
            firefly_ch_bitfield = FireFly.CHANNEL_07, #A8,9
        )
        self._merc_channels['16'] = ChannelInfo(
            name='6',
            firefly_dev = self._firefly_10to19,
            firefly_ch_num = 8,
            firefly_ch_bitfield = FireFly.CHANNEL_08, #B14,15
        )
        self._merc_channels['17'] = ChannelInfo(
            name='7',
            firefly_dev = self._firefly_10to19,
            firefly_ch_num = 9,
            firefly_ch_bitfield = FireFly.CHANNEL_09, #A5,6
        )
        self._merc_channels['18'] = ChannelInfo(
            name='8',
            firefly_dev = self._firefly_10to19,
            firefly_ch_num = 10,
            firefly_ch_bitfield = FireFly.CHANNEL_10, #B2,3
        )
        self._merc_channels['19'] = ChannelInfo(
            name='9',
            firefly_dev = self._firefly_10to19,
            firefly_ch_num = 11,
            firefly_ch_bitfield = FireFly.CHANNEL_11, #A2,3
        )

        # Create an ASIC
        regmap_override_filenames = kwargs.get('regmap_override_filenames', None)
        if regmap_override_filenames is None:
            regmap_override_filenames_list = []
        else:
            regmap_override_filenames_list = [x.strip() for x in regmap_override_filenames.split(',')]

        # Store as an 'allowed' value, since it must still be disabled while the ASIC is disabled, so that reads are not served from the cache. Takes effect on init / re-init of the ASIC.
        self._asic_register_cache_allowed  = bool(kwargs.get('asic_register_cache_allowed', False))

        self._asic = HEXITEC_MHz(
            bus=kwargs.get('asic_bus', 2),
            device=kwargs.get('asic_device', 0),
            hz=20000,   #TODO make this an external setting again
            regmap_override_filenames=regmap_override_filenames_list,
            register_cache_enabled=False)   # Disabled until the ASIC is enabled

        self._logger.info('ASIC instance creation complete')

        # Init state machine
        self._ENABLE_STATE_CURRENT = self.ENABLE_STATE.PRE_INIT # The state the system is currently in
        self._ENABLE_STATE_NEXT = self.ENABLE_STATE.PRE_INIT    # The state the system will move to next
        self._ENABLE_STATE_TARGET = self.ENABLE_STATE.PRE_INIT # The state the system is aiming to get to
        self._ENABLE_STATE_LAST_IDLE = None                     # The last state passed through considered 'idle' (safe to return to)
        self._ENABLE_STATE_INERR = False                        # True if the system encountered an error at last state change
        self._ENABLE_STATE_ERRMSG = None                        # Message if an error was encountered

        # Final indicators of system readiness
        self._STATE_ASIC_INITIALISED = False
        self._STATE_ASIC_FASTDATA_INITIALISED = False

        super(LokiCarrier_HMHz, self).__init__(**kwargs)

        # Get config for LTC2986 (mostly done in base class), done after superclass init for this reason
        self._ltc2986.hmhz_diode_channel = 6

        # Register a callback for when the application enable state changes, since the API for this is
        # provided by the base class and we need to set state variables related to it.
        self.register_change_callback('application_enable', self._onChange_app_en)

        self._logger.info('LOKI super init complete')

        # Set the default state target based on what boards we think are present (unless it is overridden)
        if kwargs.get('enable_state_target_override', False):
            target_state = self.ENABLE_STATE[kwargs.get('enable_state_target_override', None)]
            self._logger.info('Enable state target has been overridden to {}'.format(target_state.name))
            self._ENABLE_STATE_TARGET = target_state
        elif self.get_pin_value('app_present'):
            # If application is present (COB), the power board must be too
            self._logger.info('Backplane and COB detected, will init all devices')
            self._ENABLE_STATE_TARGET = self.ENABLE_STATE.COB_DONE          # Init everything short of the ASIC
        elif self.get_pin_value('bkpln_present'):
            self._logger.info('Backplane only detected, will not attempt to init COB')
            self._ENABLE_STATE_TARGET = self.ENABLE_STATE.PWR_DONE          # Init just the power board
        else:
            self._logger.info('Neither backplane nor COB detected, will only init LOKI devices')
            self._ENABLE_STATE_TARGET = self.ENABLE_STATE.LOKI_DONE         # Init just the devces on the LOKI carrier

    def cleanup(self):
        # The cleanup function is called by odin-control on exit, for example if reloaded in debug mode
        # by a file edit.

        # This will terminate all threads, after setting main enable to false. This should also set SYNC
        # low first, ensuring that the ASIC completes its last packet before going down.
        self._exit_nicely()

    def _start_io_loops(self, options):
        # override IO loop start to add loops for this adapter
        super(LokiCarrier_HMHz, self)._start_io_loops(options)

        self.add_thread('enable_state_machine', self._mhz_enable_state_machine_loop)
        self.watchdog_add_thread('enable_state_machine', 10, lambda: logging.error('!!!! Enable State Machine Loop watchdog triggered !!!!'))

        self.add_thread('adc_update', self._mhz_adc_update_loop, update_period_s=5)
        self.watchdog_add_thread('adc_update', 10, lambda: logging.error('!!!! ADC Loop watchdog triggered !!!!'))

        self.add_thread('firefly_channel_loop', self._mhz_firefly_channel_loop)
        self.watchdog_add_thread('firefly_channel_loop', 10, lambda: logging.error('!!!! Firefly Loop watchdog triggered !!!!'))


    def _exit_nicely(self):
        # This wil be registered after the parent, therefore executed before automatic thread termination in LOKI
        # Therefore there is the chance to terminate 'nicely' before the threads are forced down.

        # Enter the LOKI_DONE state, which will disconnect external devices
        self._logger.critical('Trying to nicely grab HMHz mutexes')
        exit_target_state = 'LOKI_DONE'     # Will move to this state before exiting to disable system components.
        self.set_enable_state(exit_target_state)

        # Wait for up to 20s for the main enable to work properly
        timeout = 20
        while not self.get_enable_state() != exit_target_state:
            time.sleep(1)
            timeout -= 1
            self._logger.critical('\ttimeout: {}'.format(timeout))
            if timeout <= 0:
                break

        if self.get_enable_state() == exit_target_state:
            self._logger.critical('\tgot mutexes OK')
        else:
            self._logger.critical('\tgave up on getting mutexes, threads will have to be killed messily')

        # If main enable has succeeded of we've given up waiting, perform critical exit operations
        self._logger.critical('Performing final cleanup operations for HEXITEC-MHz')

        # Disable both fireflies
        self.set_pin_value('firefly_en', False)

        # Disable regulators
        self.set_pin_value('per_en', False)

        # Disable HV
        self.set_pin_value('hven', False)

        self._logger.critical('HEXITEC-MHz Cleanup done')

    def _mhz_enable_state_machine_loop(self):
        # Controls the main state progression of the system. Enables for individual devices are handled
        # by mutexes (locks). To effectively 'disable' a device, its mutex is grabbed to prevent any other
        # thread from attempting to use it. Once re-enabled, devices will be assumed to be in unknown state
        # and will be re-configured (since this could represent a new board being swapped in).

        # Generally, all devices handled have a 'config' and 'setup' stage. The former refers to instantiating
        # the device and performing everything that can be done once contact with it is established. This also
        # allows for early detection of device errors before attempting to move on. The latter 'setup' is
        # generally for configuring the device for the needs of the application.

        # This is structured as a traditional automatic state machine, except with a 'target' state that will
        # stop progression if reached.

        # These states do not preform any processes, and are safe to return to and 'sit' in while waiting
        # for further input. The last of these progressed through will be returned to in event of error.
        IDLE_STATES = [
            self.ENABLE_STATE.PRE_INIT,
            self.ENABLE_STATE.LOKI_DONE,
            self.ENABLE_STATE.PWR_DONE,
            self.ENABLE_STATE.COB_DONE,
            self.ENABLE_STATE.ASIC_DONE,
        ]

        def handle_state_error(msg):
            # Report the error
            full_message = 'error processing enable state {}: {}'.format(self._ENABLE_STATE_CURRENT.name, msg)
            self._logger.error(full_message)
            self._ENABLE_STATE_INERR = True
            self._ENABLE_STATE_ERRMSG = full_message

            # Set the current target to latest 'idle' state to prevent further advancement until
            # the user requests it.
            self._ENABLE_STATE_TARGET = self._ENABLE_STATE_LAST_IDLE

            # Force the current state to the latest 'idle' state to prevent further advancement until
            # the user requests it.
            self._ENABLE_STATE_CURRENT = self._ENABLE_STATE_LAST_IDLE
            
            self._logger.error('Moving back to last idle state ({}) until user advances it...'.format(self._ENABLE_STATE_LAST_IDLE.name))

        def clear_error():
            self._ENABLE_STATE_INERR = False
            self._ENABLE_STATE_ERRMSG = None

        def lock_devices(device_list):
            # Lock a set of devices from other tasks using it by grabbing the mutex.
            self._logger.info('State machine locking devices: {}'.format(device_list))
            for dev in device_list:
                result = dev.lock.acquire(blocking=True, timeout=5)
                if not result:
                    self._logger.error('Enable Control State Machine failed to get lock for device {}, there is something critically wrong.'.format(dev))
                    raise Exception('Enable Control State Machine failed to get lock for device {}, there is something critically wrong.'.format(dev))
                dev.initialised = False     # Force device re-init on ENABLE, and make sure things don't use it.
                self._logger.debug('Acquired {} (result {})'.format(dev, result))
            self._logger.info('State machine locking complete')

        def full_unlock(device):
            # With this structure and when using recursive (counting) locks, the devices can become
            # over-locked. Calling this on a device will remove all recursive locks this thread has
            # on it.
            lockcount = 0
            while True:
                try:
                    device.lock.release()
                    lockcount += 1
                except RuntimeError:
                    self._logger.debug('Released {} locks for device {}'.format(lockcount, device))
                    return

        while not self.TERMINATE_THREADS:
            self.watchdog_kick()

            # Handle current state
            if self._ENABLE_STATE_CURRENT == self.ENABLE_STATE.PRE_INIT:
                # This is just the state that the system starts up in
                try:
                    # Note: this state is entered immediately after the IO loops are started, and devices
                    # have note necessarily been created, so do nothing until advance is forced by setting
                    # the target at the end of __init__.

                    # Set the next step, will be advanced depending on target
                    self._ENABLE_STATE_NEXT = self.ENABLE_STATE(self._ENABLE_STATE_CURRENT + 1)
                except Exception as e:
                    handle_state_error(e)
                    continue

            elif self._ENABLE_STATE_CURRENT == self.ENABLE_STATE.LOKI_INIT:
                # Set up devices on the LOKI carrier for the application
                try:
                    #TODO Set the IO lines so that all resets are active. Ultimate safe state. Grab all mutexes.

                    # Grab all of the devices
                    lock_devices([
                        self._mic284,
                        self._ad7998,
                        self._firefly_00to09,
                        self._firefly_10to19
                    ])

                    # Disable FireFlies
                    self.set_pin_value('firefly_en', False)

                    # Disable the LTC diode sensor
                    self._ltc2986.diode_setup_done = False

                    # Perform init of devices on LOKI board
                    self._setup_clocks()
                    self._setup_vcal_in()

                    # Although the LTC is present on the LOKI carrier, it is not set up until it is known that an
                    # ASIC is present, since it measures temperature through the on-die diode.

                    # Set the next step, will be advanced depending on target
                    self._ENABLE_STATE_NEXT = self.ENABLE_STATE(self._ENABLE_STATE_CURRENT + 1)
                except Exception as e:
                    handle_state_error(e)
                    continue

            elif self._ENABLE_STATE_CURRENT == self.ENABLE_STATE.LOKI_DONE:
                try:
                    #TODO Set control lines, mutexes to disable anything on COB and power board

                    # Set the next step, will be advanced depending on target
                    self._ENABLE_STATE_NEXT = self.ENABLE_STATE(self._ENABLE_STATE_CURRENT + 1)
                except Exception as e:
                    handle_state_error(e)
                    continue

            elif self._ENABLE_STATE_CURRENT == self.ENABLE_STATE.PWR_INIT:
                # Check power board is present, and initialise devices on it and release mutexes.
                try:
                    # Check the power board has been detected
                    if not self.get_pin_value('bkpln_present'):
                        raise Exception('Backplane not present')

                    # Ensure that devices on the COB are locked
                    lock_devices([
                        self._firefly_00to09,
                        self._firefly_10to19,
                        self._mic284,           # Lock prior to release in this stage
                        self._ad7998,           # Lock prior to release in this stage
                    ])

                    # Disable FireFlies
                    self.set_pin_value('firefly_en', False)

                    # Disable the LTC diode sensor
                    self._ltc2986.diode_setup_done = False

                    # Init the MIC temperature sensor and release its mutex if successful
                    self._config_mic284()
                    if self._mic284.initialised:
                        full_unlock(self._mic284)

                    # Init the AD7998 ADC
                    self._config_ad7998()
                    if self._ad7998.initialised:
                        full_unlock(self._ad7998)

                    #TODO Init the Digial Potentiometers (see below)

                    #TODO Init the HV system

                    # Set the next step, will be advanced depending on target
                    self._ENABLE_STATE_NEXT = self.ENABLE_STATE(self._ENABLE_STATE_CURRENT + 1)
                except Exception as e:
                    handle_state_error(e)
                    continue

            elif self._ENABLE_STATE_CURRENT == self.ENABLE_STATE.PWR_DONE:
                try:
                    #TODO Set control lines, mutexes to disable anything on COB

                    # Set the next step, will be advanced depending on target
                    self._ENABLE_STATE_NEXT = self.ENABLE_STATE(self._ENABLE_STATE_CURRENT + 1)
                except Exception as e:
                    handle_state_error(e)
                    continue

            elif self._ENABLE_STATE_CURRENT == self.ENABLE_STATE.COB_INIT:
                try:
                    #TODO Init devices on the COB and release mutexes, except the ASIC

                    # Check the COB has been detected
                    if not self.get_pin_value('app_present'):
                        raise Exception('COB not present')

                    lock_devices([
                        self._firefly_00to09,       # Lock prior to release in this stage
                        self._firefly_10to19,       # Lock prior to release in this stage
                    ])

                    # Config fireflies, disable all output channels by default to prevent overheat
                    # This will be tried no matter if fast data is enabled or not, since we must
                    # still disable the channels to prevent overheat, if transceivers are present.
                    self._config_fireflies()
                    if self._firefly_00to09.initialised:
                        full_unlock(self._firefly_00to09)
                    if self._firefly_10to19.initialised:
                        full_unlock(self._firefly_10to19)

                    # Set up the LTC2986 to monitor the ASIC diode
                    self._setup_ltc2986()

                    # Set the next step, will be advanced depending on target
                    self._ENABLE_STATE_NEXT = self.ENABLE_STATE(self._ENABLE_STATE_CURRENT + 1)
                except Exception as e:
                    handle_state_error(e)
                    continue

            elif self._ENABLE_STATE_CURRENT == self.ENABLE_STATE.COB_DONE:
                try:
                    #TODO Set the ASIC into reset, grab its mutex.

                    # Set the next step, will be advanced depending on target
                    self._ENABLE_STATE_NEXT = self.ENABLE_STATE(self._ENABLE_STATE_CURRENT + 1)
                except Exception as e:
                    handle_state_error(e)
                    continue

            elif self._ENABLE_STATE_CURRENT == self.ENABLE_STATE.ASIC_INIT:
                try:
                    # Initialise the ASIC, either SPI only (if requested) or full functionality.
                    if self._fast_data_enabled:
                        if self._firefly_00to09.initialised and self._firefly_00to09.initialised:
                            # Enable the firefly channels for the ASIC outputs
                            self._setup_fireflies()
                        else:
                            raise Exception('At least one firefly was not initialised while fast data is enabled, cannot switch on optical channels')

                    self._initialise_asic(fast_data_enabled=self._fast_data_enabled)

                    # Set the next step, will be advanced depending on target
                    self._ENABLE_STATE_NEXT = self.ENABLE_STATE(self._ENABLE_STATE_CURRENT + 1)
                except Exception as e:
                    handle_state_error(e)
                    continue

            elif self._ENABLE_STATE_CURRENT == self.ENABLE_STATE.ASIC_DONE:
                try:
                    # System is ready! Release the ASIC mutex.

                    self._ENABLE_STATE_NEXT = self._ENABLE_STATE_CURRENT
                except Exception as e:
                    handle_state_error(e)
                    continue

            # If the last current state processed was considered 'idle' (safe to return to),
            # store it.
            if self._ENABLE_STATE_CURRENT in IDLE_STATES:
                self._ENABLE_STATE_LAST_IDLE = self._ENABLE_STATE_CURRENT

            # Set the next loop current state
            if self._ENABLE_STATE_CURRENT < self._ENABLE_STATE_TARGET:
                # The state requires progressing normally, set current state to next state for next loop
                self._logger.info('STATE CHANGE {} -> {}'.format(self._ENABLE_STATE_CURRENT.name, self._ENABLE_STATE_NEXT.name))
                self._ENABLE_STATE_CURRENT = self._ENABLE_STATE_NEXT
                clear_error()
            elif self._ENABLE_STATE_CURRENT > self._ENABLE_STATE_TARGET:
                # The requested state is before the current one, move to it directly assuming that the
                # user knows what they are doing.
                self._logger.info('STATE CHANGE {} -> {}'.format(self._ENABLE_STATE_CURRENT.name, self._ENABLE_STATE_TARGET.name))
                self._ENABLE_STATE_CURRENT = self._ENABLE_STATE_TARGET
                clear_error()
            else:
                # The state is as required, do not progress (ignore next state for now)
                self._logger.debug('STATE AT TARGET({}), not progressing state machine'.format(self._ENABLE_STATE_TARGET.name))
                time.sleep(1)

    def get_enable_state_error(self):
        if self._ENABLE_STATE_INERR:
            return self._ENABLE_STATE_ERRMSG
        else:
            return None

    def get_enable_state(self):
        return self._ENABLE_STATE_CURRENT.name

    def _set_enable_state_target(self, target_state):
        # State machine will move to this target state directly if it is an earlier state,
        # or will proceed as normal until this state if it is a later state.
        self._ENABLE_STATE_TARGET = self.ENABLE_STATE(target_state)

    def _set_enable_state_target_via(self, target_state, via_state):
        # State machine will proceed to a first target state, and once reached, will move
        # to a second target state. Often used to jump back through the state machine to a
        # different target while wanting to repeat previous init steps.
        self._ENABLE_STATE_TARGET = self.ENABLE_STATE(via_state)
        while (self._ENABLE_STATE_CURRENT != self.ENABLE_STATE(via_state)):
            #TODO time this out
            pass
        self._ENABLE_STATE_TARGET = self.ENABLE_STATE(target_state)

    def set_enable_state(self, state_name):
        # Request a state is moved to by name. This is meant to be used externally in sequences or from
        # the parameter tree, and as such has fewer valid states. The done states will be moved to via
        # initialisation states as required.

        if state_name == self.ENABLE_STATE.LOKI_DONE.name:
            # Init LOKI devices, or re-init
            self._set_enable_state_target_via(
                self.ENABLE_STATE.LOKI_DONE,
                self.ENABLE_STATE.LOKI_INIT
            )
        elif state_name == self.ENABLE_STATE.PWR_DONE.name:
            # Init power board devices, or re-init.
            self._set_enable_state_target_via(
                self.ENABLE_STATE.PWR_DONE,
                self.ENABLE_STATE.PWR_INIT
            )
        elif state_name == self.ENABLE_STATE.COB_DONE.name:
            # Init COB devices, or re-init.
            self._set_enable_state_target_via(
                self.ENABLE_STATE.COB_DONE,
                self.ENABLE_STATE.COB_INIT
            )
        elif state_name == self.ENABLE_STATE.ASIC_DONE.name:
            # Init ASIC, or re-init.
            self._set_enable_state_target_via(
                self.ENABLE_STATE.ASIC_DONE,
                self.ENABLE_STATE.ASIC_INIT
            )
        else:
            self._logger.error('Invalid state requested: {}'.format(state_name))

    def _initialise_asic(self, fast_data_enabled):
        # The general process for setting up the HEXITEC-MHz ASIC, assuming that it has
        # now been powered, and all other system components have been configured. At this
        # stage, FireFlies should still be disabled. This function will by default set up
        # the system for full functionality (SPI and fast data readout), but if supplied
        # with fast_data_enabled=False, will not set up the serialisers or enable the FireFlies.

        # Any errors will be caught externally, but in addition, this function will disable
        # the firefly channels.

        try:
            # Enter Global mode - and reset the ASIC
            try:
                self.enter_global_mode()
            except Exception as e:
                raise Exception('Failed while entering global mode: {}'.format(e))

            # Set Diamond Default Registers
            try:
                self._asic.Set_DiamondDefault_Registers()
            except Exception as e:
                raise Exception('Failed while setting DIAMOND defaults: {}'.format(e))

            if fast_data_enabled:
                # Reset the serialisers
                logging.info("\tResetting Serialisers...")
                time.sleep(0.5)
                self._asic.ser_enter_reset()
                time.sleep(0.5)
                self._asic.ser_exit_reset()

                # Enter Bonding mode
                logging.info("\tEntering Bonding Mode...")
                time.sleep(0.5)
                self._asic.enter_bonding_mode()

                # Enter Data mode
                logging.info("\tEntering Data Mode...")
                time.sleep(0.5)
                self._asic.enter_data_mode()

                logging.info("Device is now outputting fast data")
                self._STATE_ASIC_FASTDATA_INITIALISED = True

            logging.info('ASIC initialisation complete')
            self._STATE_ASIC_FASTDATA_INITIALISED = True

        except Exception as e:
            fullmsg = 'Failed to init ASIC properly, disabling FireFlies: {e}'.format(e)
            self._logger.error(fullmsg)
            if fast_data_enabled:
                self.mhz_firefly_set_all_enabled(False)

            # Raise the error higher for the calling thread to handle raise Exception(fullmsg) def enter_global_mode(self): Complete the process defined in the ASIC manual for entering global mode. This is part of the carrier due to the requirement to synchronise parts of the process with the external SYNC signal, which is not under the control of the ASIC.  The ASIC is assumed to have been reset prior to this.  
        # Set the sync line low before reset
        self.set_sync(False)

        # Reset the ASIC
        self.reset_cycle_asic()

        # Enable global control of readout, digital signals, analogue signals,
        # analogue bias enable, TDC oscillator enable, serialiser PLL enable,
        # TDC PLL enable, VCAL select, serialiser mode, serialiser analogue/
        # digital reset.
        self.write_field('GL_ROE_CONT', 0b1)
        self.write_field('GL_DigSig_CONT', 0b1)
        self.write_field('GL_AnaSig_CONT', 0b1)
        self.write_field('GL_AnaBias_CONT', 0b1)
        self.write_field('GL_TDCOsc_CONT', 0b1)
        self.write_field('GL_SerPLL_CONT', 0b1)
        self.write_field('GL_TDCPLL_CONT', 0b1)
        self.write_field('GL_VCALsel_CONT', 0b1)
        self.write_field('GL_SerMode_CONT', 0b1)
        self.write_field('GL_SerAnaRstB_CONT', 0b1)
        self.write_field('GL_SerDigRstB_CONT', 0b1)

        # Set the sync active
        self.set_sync(True)

        # Enter further settings post sync raise
        self.write_field('GL_AnaBias_EN', 0b1)  # Enable pixel bias
        self.write_field('GL_TDCPLL_EN', 0b1)   # Enable TDC PLLs
        self.write_field('GL_TDCOsc_EN', 0b1)   # Enable TDC oscillators
        self.write_field('GL_SerPLL_EN', 0b1)   # Enable Serialiser PLLs
        self.write_field('GL_AnaSig_EN', 0b1)   # Enable pixel analogue signals
        self.write_field('GL_DigSig_EN', 0b1)   # Enable pixel digital signals

        time.sleep(0.1) #TEMP suggested by Lawrence

        # Set serialisers configuration blocks to default working mode
        self._asic._init_serialisers()

        # Remove serialiser digital and analogue reset
        self.write_field('GL_SerAnaRstB_EN', 0b1)   # Remove analogue reset
        time.sleep(0.1) #TEMP suggested by Lawrence
        self.write_field('GL_SerDigRstB_EN', 0b1)   # Remove analogue reset

        # Enable readout
        self.write_field('GL_ROE_EN', 0b1)

        self._logger.info("Global mode configured")

        # RE-INIT SERIALISERS (Serialisers will not function without additional reset. Reason unknown.)
        time.sleep(0.5)
        self.write_field('GL_SerAnaRstB_EN', 0b0)
        self.write_field('GL_SerDigRstB_EN', 0b0)
        time.sleep(0.5)
        self.write_field('GL_SerDigRstB_EN', 0b1)
        self.write_field('GL_SerAnaRstB_EN', 0b1)
        self._logger.info("Serialiser encoding state force reset")

    def _setup_ltc2986(self):
        # Enable the sensor channel for the on-ASIC diode temperature sensor.

        # Since the LTC is already configured by the base class, getting the device should be done
        # through the provided accessor:
        ltc_dev = self.ltc_get_device()

        with ltc_dev.acquire(blocking=True, timeout=1) as rslt:
            if not rslt:
                if ltc_dev.initialised:
                    raise Exception('Failed to get LTC lock while setting up ASIC Diode channel')

            ltc_dev.device.add_diode_channel(
                endedness=LTC2986.Diode_Endedness.DIFFERENTIAL,
                conversion_cycles=LTC2986.Diode_Conversion_Cycles.CYCLES_2,
                average_en=LTC2986.Diode_Running_Average_En.OFF,
                excitation_current=LTC2986.Diode_Excitation_Current.CUR_80UA_320UA_640UA,
                diode_non_ideality=1.0,
                channel_num=self._ltc2986.hmhz_diode_channel,
            )

            self._ltc2986.diode_setup_done = True
            self._logger.info('Added channel for ASIC diode to LTC2986')

    def _mhz_get_asic_diode_direct(self):
        if self._ltc2986.initialised and self._ltc2986.diode_setup_done:
            return self.ltc_read_channel_direct(self._ltc2986.hmhz_diode_channel)
        else:
            return None

    def reset_cycle_asic(self):
        logging.warning('Resetting ASIC...')
        self.set_sync(False)
        time.sleep(0.1)
        self.set_app_enabled(False)

        time.sleep(0.1)

        self.set_app_enabled(True)
        time.sleep(0.1)
        logging.debug('ASIC reset complete')

    def _onChange_app_en(self, state):
        if state:
            # ASIC is enabled, so start caching successful writes
            self._asic.enable_interface()
            self._set_asic_register_cache_enabled(True)

        else:
            # ASIC is disabled, so disable caching write values
            self._set_asic_register_cache_enabled(False)
            self._asic.disable_interface()
            self._STATE_ASIC_INITIALISED = False
            self._STATE_ASIC_FASTDATA_INITIALISED = False

    def set_asic_register_cache_allowed(self, value):
        # Set the allowed value directly, will only take place on
        self._asic_register_cache_allowed = value

    def _get_asic_register_cache_enabled(self):
        # Get if the ASIC cache is currently active.         pass
        return self._asic.get_cache_enabled()

    def _set_asic_register_cache_enabled(self, value):
        # Set the asic cache enabled, but only if it's been allowed in the config
        # Dangerous without knowledge of current enable state.

        if value:
            if self._asic_register_cache_allowed:
                self._asic.enable_cache()
            else:
                # Cache has not been explicity allowed
                self._logger.warning('ASIC cache enable requested, but has not been allowed in config, so ignoring...')
        else:
            self._asic.disable_cache()

    def _setup_clocks(self):
        #TODO create a real clock config
        pass
        #self.clkgen_set_config(self._default_clock_config)

    def _config_mic284(self):
        try:
            self._mic284.initialised = False
            self._mic284.error = False
            self._mic284.error_message = False

            self._mic284.device = MIC284(
                address=self._mic284.i2c_address,
                busnum=self._mic284.i2c_bus,
            )

            time.sleep(0.5)
            self._logger.info('Test read of MIC284 internal temperature: {}'.format(
                self._mic284.device.read_temperature_internal()
            ))
            self._logger.info('Test read of MIC284 external temperature: {}'.format(
                self._mic284.device.read_temperature_external()
            ))

            self._mic284.initialised = True

            self._logger.info('MIC284 {} initialised successfuly'.format(self._mic284))

        except Exception as e:
            self._mic284.critical_error('Failed to init MIC284 {}: {}'.format(self._mic284, e))

    def _get_mic284_internal_direct(self):
        with self._mic284.acquire(blocking=True, timeout=1) as rslt:
            if not rslt:
                if self._mic284.initialised:
                    raise Exception('Could not acquire lock for mic284, timed out')
                return None

            return self._mic284.device.read_temperature_internal()

    def _get_mic284_external_direct(self):
        with self._mic284.acquire(blocking=True, timeout=1) as rslt:
            if not rslt:
                if self._mic284.initialised:
                    raise Exception('Could not acquire lock for mic284, timed out')
                return None

            return self._mic284.device.read_temperature_external()

    def _env_get_sensor(self, name, sensor_type):
        # This will return the raw value, cached by the LokiCarrierEnvmonitor class automatically

        # This extension will handle results for LTC2986 and any on-asic-carrier temps, must also
        # call parent to handle LOKI's own sensors.

        try:
            return super(LokiCarrier_HMHz, self)._env_get_sensor(name, sensor_type)
        except NotImplementedError:

            # If sensor is not found in main adapter, try sensors from this implementation
            if name == 'POWER_BOARD':
                if sensor_type == 'temperature':
                    return self._get_mic284_internal_direct()
                else:
                    raise
            elif name == 'ASIC':
                if sensor_type == 'temperature':
                    return self._get_mic284_external_direct()
                else:
                    raise
            elif name == 'DIODE':
                if sensor_type == 'temperature':
                    return self._mhz_get_asic_diode_direct()
                else:
                    raise
            elif name == 'FIREFLY00to09':
                if sensor_type == 'temperature':
                    # This is actually a cached value already, but no matter
                    return self._mhz_firefly_get_temperature_direct('00to09')
                else:
                    raise
            elif name == 'FIREFLY10to19':
                if sensor_type == 'temperature':
                    # This is actually a cached value already, but no matter
                    return self._mhz_firefly_get_temperature_direct('10to19')
                else:
                    raise
            else:
                raise

    def _config_ad7998(self):
        # Initialise the ADC device if possible
        try:
            self._ad7998.initialised = False
            self._ad7998.error = False
            self._ad7998.error_message = False

            self._ad7998.reference_voltage = 2.5

            self._ad7998.device = AD7998(
                address=self._ad7998.i2c_address,
                busnum=self._ad7998.i2c_bus,
            )

            time.sleep(0.5)
            self._logger.info('Test read AD7998 ADC inputs:')
            for i in range(1, 8):
                self._logger.info('\tchannel {}: \traw: {}\tscaled: {}'.format(
                    i, self._ad7998.device.read_input_raw(i) & 0xFFF, self._ad7998.device.read_input_scaled(i) * self._ad7998.reference_voltage
                ))

            self._ad7998._reading_cache = {}

            self._logger.info('AD7998 {} initialised successfuly'.format(self._ad7998))
            self._ad7998.initialised = True

        except Exception as e:
            self._ad7998.critical_error('Failed to init MIC284 {}: {}'.format(self._ad7998, e))

    def _mhz_adc_read_chan_num_direct(self, channel_number):
        with self._ad7998.acquire(blocking=True, timeout=1) as rslt:
            if not rslt:
                if self._ad7998.initialised:
                    raise Exception('Failed to get ADC input {} from AD7998, mutex timed out'.format(channel_number))
                return None

            # Proportional input is float between 0-1.
            input_proportional = self._ad7998.device.read_input_scaled(channel_number)

            # To convert to voltage, use known reference
            input_volts = input_proportional * self._ad7998.reference_voltage

            return input_volts

    def _mhz_adc_read_chan_direct(self, channel_name):
        if not self._ad7998.initialised:
            return None

        (dac_chan, input_multiplier) = self._ad7998._channel_mapping.get(channel_name, (None, None))
        if dac_chan is None:
            raise Exception('ADC channel {} does not exist'.format(channel_name))

        return (self._mhz_adc_read_chan_num_direct(dac_chan) * input_multiplier)

    def _setup_vcal_in(self):
        # Initial setup for vcal, using default value.

        if not self._max5306.initialised:
            raise Exception('Could not setup DAC for VCAL, DAC was not initialised')

        self.set_vcal_in(self._vcal_in_default)

    def set_vcal_in(self, value):
        # Use the DAC functionality provided by the generic carrier to set VCAL on DAC
        # DAC output 0 (SEAF:B50).

        # Check that we are in range for HEXITEC-MHz (nothing greater than 1.2)
        if value >= self._vcal_in_limit:
            raise Exception('VCAL cannot be set to {}v; it exceeds the limit {}v. To change the limit, set "vcal_in_limit" in the config file.'.format(
                value, self._vcal_in_limit))
        else:
            self.dac_set_output(0, value)   # Output number is LOKI count, not MAX5306 count

    def get_vcal_in(self):
        # Return the last setting of the VCAL in signal using base adapter function for DAC
        # channel 0. This is already cached, so can be returned directly.
        return self.dac_get_output(0)       # Output number is LOKI count, not MAX5306 count

    def mhz_adc_get_channel_names(self):
        return list(self._ad7998._channel_mapping.keys())

    def _mhz_adc_update_loop(self, update_period_s=5):
        while not self.TERMINATE_THREADS:
            self.watchdog_kick()

            # Don't bother doing anything until / if the ADC is init.
            if not self._ad7998.initialised:
                time.sleep(1)
                continue

            for channel_name in self.mhz_adc_get_channel_names():
                # Protect the cache and device with mutex while reading
                with self._ad7998.acquire(blocking=True, timeout=1) as rslt:
                    if not rslt:
                        if self._ad7998.initialised:
                            raise Exception('Failed to get ADC mutex while syncing cache for input {}, mutex timed out'.format(channel_name))
                        return None

                    # Read channel, this is mutex protected already, but RLock can have more than one entry
                    direct_reading = self._mhz_adc_read_chan_direct(channel_name)

                    # Update the cache
                    self._ad7998._reading_cache.update({channel_name: direct_reading})

            time.sleep(update_period_s)

    def _mhz_adc_clear_reading_cache(self):
        with self._ad7998.acquire(blocking=True, timeout=1) as rslt:
            if not rslt:
                if self._ad7998.initialised:
                    raise Exception('Failed to get access AD7998 reading cache while clearing it, mutex timed out')
                return None

            self._ad7998._reading_cache = {}

    def mhz_adc_read_chan(self, channel_name):
        with self._ad7998.acquire(blocking=True, timeout=1) as rslt:
            if not rslt:
                if self._ad7998.initialised:
                    raise Exception('Failed to get access AD7998 reading cache while reading {}, mutex timed out'.format(channel_name))
                return None

            return self._ad7998._reading_cache.get(channel_name, None)

    def mhz_adc_read_VDDA_current_A(self):
        #TODO
        pass

    def mhz_adc_read_VDDD_current_A(self):
        #TODO
        pass

    def mhz_adc_read_HV_voltage_V(self):
        # The HV_MONITOR_OUT voltage is 0 to +5v. I am assuming that this is simply proportional
        # to the actual output HV voltage, over range 0 to -1500V for C1152-01.
        adc_in_voltage = self.mhz_adc_read_chan('HV_MON')
        if adc_in_voltage is None:
            return None
        else:
            return (-1500) * (adc_in_voltage / 5.0)

    def mhz_adc_read_trips(self):
        # All four trip signals TRIP_<1:3> come from 74LS279. This device is a set of latches,
        # therefore the output is actually digital and should be converted. Minimum Voh is 2.7v.

        #TODO consider whether these should actually be related to the names on the inputs of the 74LS279 device.

        def dig_convert(in_analog):
            if in_analog is None:
                return None
            else:
                return True if in_analog >= 2.7 else False

        output_dict = {}

        for trip_name in self._ad7998._trip_nice_names.keys():
            output_dict.update({
                trip_name: {
                    'Tripped': dig_convert(self.mhz_adc_read_chan(trip_name)),
                    'Description': self._ad7998._trip_nice_names[trip_name],
                }
            })

        return output_dict

    def _mhz_hv_set_potentiometer(self, value):
        #TODO
        pass

    def mhz_hv_set_enable(self, value):
        # External HV enable / disable
        #TODO
        pass

    def _mhz_hv_enable(self):
        # Directly enable the HV
        self.set_pin_value('hven', 1)

    def _mhz_hv_disable(self):
        # Directly disable the HV
        self.set_pin_value('hven', 0)

    def _config_fireflies(self):

        # Enable the devices (reset line)
        self.set_pin_value('firefly_en', 1)
        time.sleep(1)

        for current_ff in self._fireflies:
            try:
                current_ff.initialised = False
                current_ff.error = False
                current_ff.error_message = False

                #TODO because the driver is currently not very smart, it does not set the bus used, and
                # relies on the default setting. Therefore set the I2CDevice default bus and hope it doesn't
                # mess anything else up (it shouldn't if other buses are set manually).
                self._logger.warning('Setting default I2C bus number due to lack of functionality in firefly driver. This could cause issues with other drivers')
                I2CDevice._default_i2c_bus = current_ff.i2c_bus

                # If the device is present, it should auto-detect the type etc.
                current_ff.device = FireFly(
                    base_address=current_ff.i2c_address,
                    select_line=self.get_pin(current_ff.select_pin_friendlyname),
                )

                # Disable all firefly channels by default
                self._logger.info('Disabling all FireFly channels by default')
                current_ff.device.disable_tx_channels(FireFly.CHANNEL_ALL)

                # Setup sync caches
                #TODO update for HMHZ?
                current_ff._cached_channels_disabled = 0

                # Store the part number, vendor number, and OUI for later use
                self._logger.info('Storing FireFly PN, VN, OUI')
                current_ff.info_pn, current_ff.info_vn, current_ff.info_oui = current_ff.device.get_device_info()

                self._logger.info('Firefly current temperature {}C'.format(current_ff.device.get_temperature()))

                current_ff.initialised = True

                self._logger.debug('FireFly {} initialised successfuly'.format(current_ff))

            except Exception as e:
                current_ff.critical_error('Failed to init FireFly {}: {}'.format(current_ff.name, e))
                self._logger.critical('Will disable firefly via reset line')
                self.set_pin_value('firefly_en', 0)

    def _setup_fireflies(self):
        # Set up firefly for normal babyD usage, where all channels required are enabled

        for current_ff in self._fireflies:
            with current_ff.acquire(blocking=True, timeout=1) as rslt:
                if not rslt:
                    if current_ff.initialised:
                        self._logger.error('Failed to get FireFly lock while setting up base channel states, timed out')
                    return None

                self.mhz_firefly_set_channel_enabled('Z1', True)
                self.mhz_firefly_set_channel_enabled('Z2', True)

    def _mhz_firefly_channel_loop(self):
        while not self.TERMINATE_THREADS:
            self.watchdog_kick()
            time.sleep(0.2)
            for current_ff in self._fireflies:
                try:
                    # Try and grab the mutex to update channel status
                    with current_ff.acquire(blocking=True, timeout=1) as rslt:
                        if not rslt:
                            if current_ff.initialised:
                                self._logger.debug('Failed to get FireFly lock while updating channel states')
                        else:
                            current_ff._cached_channels_disabled = current_ff.device.get_disabled_tx_channels_field()
                except Exception as e:
                    logging.error('Error in FireFly channel sync loop: {}'.format(e))

    def mhz_firefly_get_device_names(self):
        return [dev.name for dev in  self._fireflies]

    def _mhz_firefly_get_device_from_name(self, name):
        for device in self._fireflies:
            if device.name == name:
                return device
        raise Exception('No such firefly device name {}. Available names: {}'.format(name, self.mhz_firefly_get_device_names()))

    def _mhz_firefly_get_temperature_direct(self, ff_dev_name):
        # Protect cache access and interaction with the I2C device with mutex
        current_ff = self._mhz_firefly_get_device_from_name(ff_dev_name)
        with current_ff.acquire(blocking=True, timeout=1) as rslt:
            if not rslt:
                if current_ff.initialised:
                    self._logger.error('Failed to get FireFly lock while returning temperature, timed out')
                return None

            return current_ff.device.get_temperature()

    def mhz_firefly_get_partnumber(self, ff_dev_name):
        # Protect cache access and interaction with the I2C device with mutex
        current_ff = self._mhz_firefly_get_device_from_name(ff_dev_name)
        with current_ff.acquire(blocking=True, timeout=1) as rslt:
            if not rslt:
                if current_ff.initialised:
                    self._logger.error('Failed to get FireFly lock while returning temperature, timed out')
                return None

            return current_ff.info_pn

    def mhz_firefly_get_vendornumber(self, ff_dev_name):
        # Protect cache access and interaction with the I2C device with mutex
        current_ff = self._mhz_firefly_get_device_from_name(ff_dev_name)
        with current_ff.acquire(blocking=True, timeout=1) as rslt:
            if not rslt:
                if current_ff.initialised:
                    self._logger.error('Failed to get FireFly lock while returning temperature, timed out')
                return None

            return current_ff.info_vn

    def mhz_firefly_get_oui(self, ff_dev_name):
        # Protect cache access and interaction with the I2C device with mutex
        current_ff = self._mhz_firefly_get_device_from_name(ff_dev_name)
        with current_ff.acquire(blocking=True, timeout=1) as rslt:
            if not rslt:
                if current_ff.initialised:
                    self._logger.error('Failed to get FireFly lock while returning temperature, timed out')
                return None

            return current_ff.info_oui

    def mhz_get_channel_names(self):
        # Returns a list of BabyD channel names used logically within the control system for various
        # settings across devices (firefly, retimer etc...)
        return list(self._merc_channels.keys())

    def mhz_firefly_set_channel_enabled(self, channel_name, en=True):
        # Set enable state for a specific channel name, as defined by the application.
        # If channel_name is supplied as 'All', will operate on all channels (used for BabyD)
        channel = self._merc_channels.get(channel_name, None)
        if channel is None:
            return
        else:
            channel_bitfield = channel.firefly_ch_bitfield

        # Use the firefly stored for this ASIC channel
        with channel.firefly_dev.acquire(blocking=True, timeout=1) as rslt:
            if not rslt:
                if channel.firefly_dev.initialised:
                    self._logger.error('Failed to get FireFly lock while returning channel states')

            channel.firefly_dev.device.enable_tx_channels(channel_bitfield)
            self._logger.info('Firefly: {}abled channel {}'.format('en' if en else 'dis', channel_name))

    def mhz_firefly_get_channel_enabled(self, channel_name):
        # Get the current enable state for a channel name, where name is application-specific.
        # Get the current enable state for a channel name, as defined by the application.
        # If the channel_name is supplied as 'All', will return true if all used channels are enabled, false otherwise.
        channel = self._merc_channels.get(channel_name, None)
        if channel is None:
            return None
        else:
            channel_bitfield = channel.firefly_ch_bitfield

        with channel.firefly_dev.acquire(blocking=True, timeout=1) as rslt:
            if not rslt:
                if channel.firefly_dev.initialised:
                    self._logger.error('Failed to get FireFly lock while returning channel states')
                return None

            return not bool((channel.firefly_dev._cached_channels_disabled & channel_bitfield) == channel_bitfield)

    def mhz_firefly_set_all_enabled(self, enabled=True):
        for current_ff in self._fireflies:

            with current_ff.acquire(blocking=True, timeout=1) as rslt:
                if not rslt:
                    if current_ff.initialised:
                        self._logger.error('Failed to get FireFly lock while setting all states')
                if enabled:
                    current_ff.device.enable_tx_channels(FireFly.CHANNEL_ALL)
                else:
                    current_ff.device.disable_tx_channels(FireFly.CHANNEL_ALL)

    def get_sync(self):
        # Cached by handler, safe to directly request
        return bool(self.get_pin_value('sync'))

    def set_sync(self, value):
        self.set_pin_value('sync', bool(value))
        self._logger.info('SYNC {}'.format('high' if value else 'low'))

    def _gen_app_paramtree(self):
        # Override parameter tree generation to add application-specific tree

        self._logger.debug('Creating BabyD-specific ParameterTree')
        self.hmhzpt = {
            'info': {
                'asic_cache_hitrate': (lambda: self._asic.get_cache_hitrate(), None),
                'asic_cache_allowed': (lambda: self._asic_register_cache_allowed, self.set_asic_register_cache_allowed),
                'asic_cache_enabled': (self._get_asic_register_cache_enabled, None),
            },
            'system_state': {
                'SYNC': (self.get_sync, self.set_sync),
                'ASIC_EN': (self.get_app_enabled, self.set_app_enabled),
                'REGS_EN': (self.get_peripherals_enabled, None),
                'ENABLE_STATE': (self.get_enable_state, self.set_enable_state),
                'ENABLE_STATE_ERROR': (self.get_enable_state_error, None),
                'ASIC_INIT': (lambda: self._STATE_ASIC_INITIALISED, None),
                'ASIC_FASTDATA_INIT': (lambda: self._STATE_ASIC_FASTDATA_INITIALISED, None),
                'DEVICES': {
                    'FIREFLY': {
                        '00to09': (lambda: 'error' if self._firefly_00to09.error else ('initialised' if self._firefly_00to09.initialised else 'unconfigured'), None),
                        '10to19': (lambda: 'error' if self._firefly_10to19.error else ('initialised' if self._firefly_10to19.initialised else 'unconfigured'), None),
                    },
                    'MIC284': (lambda: 'error' if self._mic284.error else ('initialised' if self._mic284.initialised else 'unconfigured'), None),
                    'AD7998': (lambda: 'error' if self._ad7998.error else ('initialised' if self._ad7998.initialised else 'unconfigured'), None),
                    'LTC2986': (lambda: 'error' if self.ltc_get_device().error else ('initialised' if self.ltc_get_device().initialised else 'unconfigured'), None),
                },
            },
            'asic_settings': {
                'integration_time': (self._asic.get_integration_time, self._asic.set_integration_time),
                'frame_length': (self._asic.get_frame_length, self._asic.set_frame_length),
                'feedback_capacitance': (self._asic.get_feedback_capacitance, self._asic.set_feedback_capacitance),#TODO
                'serialiser_all_mode': (self._asic.get_global_serialiser_mode, self._asic.set_global_serialiser_mode),
                'serialiser_all_pattern': (self._asic.get_all_serialiser_pattern, self._asic.set_all_serialiser_pattern),
                'serialiser_all_scrambleen': (self._asic.get_all_serialiser_bit_scramble, self._asic.set_all_serialiser_bit_scramble),
                'segment_readout': {
                    'TRIGGER': (None, None),#TODO
                    'SEGMENT_DATA': (None, None),#TODO
                },
                #'calibration_pattern': {
                    #"ENABLE":(self.get_asic_cal_pattern_en, self.set_asic_cal_pattern_en, {"description":"Enable ASIC calibration pattern injection"}),#TODO
                    #"PATTERN":(None, self.set_asic_cal_pattern, {"description":"Selection of pattern type: default or highlight"}),#TODO
                    #"HIGHLIGHT_DIVISION":(lambda: self._asic_cal_highlight_div, lambda division: self.cfg_asic_highlight(division=division), {"description":"Division chosen for 4x4 grid highlighting via calibration pattern"}),#TODO
                    #"HIGHLIGHT_SECTOR":(lambda: self._asic_cal_highlight_sec, lambda sector: self.cfg_asic_highlight(sector=sector), {"description":"Sector chosen for 4x4 grid highlighting via calibration pattern"}),#TODO
                    #"HIGHLIGHT_ROW":(lambda: self._asic_cal_highlight_row, lambda row: self.cfg_asic_highlight(row=row), {"description":"Row chosen for 1x1 pixel highlighting via calibration pattern"}),#TODO
                    #"HIGHLIGHT_COLUMN":(lambda: self._asic_cal_highlight_col, lambda column: self.cfg_asic_highlight(column=column), {"description":"Column chosen for 1x1 pixel highlighting via calibration pattern"}),#TODO
                #},
                #'fast_data_setup': {
                #    #TODO
                #}
            },
            'monitoring': {
                'TRIPS': (self.mhz_adc_read_trips, None),
                'HV': (self.mhz_adc_read_HV_voltage_V, None),
                'VDDD_I': (self.mhz_adc_read_VDDD_current_A, None),
                'VDDA_I': (self.mhz_adc_read_VDDA_current_A, None),
            },
            'firefly': {
                '00to09': self._gen_firefly_paramtree('00to09'),
                '10to19': self._gen_firefly_paramtree('10to19'),
                'CHANNELS': self._gen_firefly_paramtree_channels(),
            },
            'vcal': (self.get_vcal_in, self.set_vcal_in),
        }

        self._logger.debug('HEXITEC-MHz ParameterTree dict:{}'.format(self.hmhzpt))

        return self.hmhzpt

    def _gen_firefly_paramtree(self, ff_dev_name):
        treedict = {
            # Temperature is now cached by the LOKI sensor manager, and is already in the parameter tree. This is a clone entry.
            "TEMPERATURE": (lambda: self.env_get_sensor_cached('FIREFLY{}'.format(ff_dev_name), 'temperature'), None, {"description": "FireFly Temperature", "units": "C"}),
            "PARTNUMBER": (lambda: self.mhz_firefly_get_partnumber(ff_dev_name), None, {"description": "FireFly Part Number"}),
            "VENDORID": (lambda: self.mhz_firefly_get_vendornumber(ff_dev_name), None, {"description": "FireFly Vendor ID"}),
            "OUI": (lambda: self.mhz_firefly_get_oui(ff_dev_name), None, {"description": "FireFly OUI"}),
        }

        return treedict

    def _gen_firefly_paramtree_channels(self):
        treedict = {}

        for channel_name in self._merc_channels.keys():
            channel = self._merc_channels.get(channel_name)

            # ALL is a special case, and has a more detailed description
            if channel_name == 'ALL':
                desc = 'All channel enable/disable. Value reads true if all channels are enabled and false if any channel is disabled.'
            else:
                desc = "Channel {} enable (firefly {} channel {})".format(channel_name, channel.firefly_dev, channel.firefly_ch_num)

            treedict[channel_name] = {
                "Enabled": (
                    (lambda ch_name_internal: lambda: self.mhz_firefly_get_channel_enabled(ch_name_internal))(channel_name),
                    (lambda ch_name_internal: lambda en: self.mhz_firefly_set_channel_enabled(ch_name_internal, en))(channel_name),
                    {"description": desc}
                )
            }

        return treedict
