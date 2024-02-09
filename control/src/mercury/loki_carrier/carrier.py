from loki.adapter import LokiCarrier_1v0, DeviceHandler
from mercury.loki_carrier.hexite_mhz_asic import HEXITEC_MHz
from odin_devices.ad5593r import AD5593R
from odin_devices.mic284 import MIC284
from odin_devices.i2c_device import I2CDevice
from odin_devices.firefly import FireFly
from .retimer import Retimer
import logging
import time

class LokiCarrier_HMHz (LokiCarrier_1v0):
    def __init__(self, **kwargs):
        self._logger = logging.getLogger('HEXITEC-MHz Carrier')

        #TODO update this for HMHZ
        self._default_clock_config = 'ZL30266_LOKI_Nosync_500MHz_218MHz.mfg'

        # Override parent pin settings
        #TODO update this for HMHZ

        # Add babyd-specific pins (Application/ASIC enable are already default LOKI
        # control pins, so these are additional IO only. Settings may be overridden
        # in the config file.
        kwargs.setdefault('pin_config_id_sync', 'EMIO18 LVDS')
        kwargs.setdefault('pin_config_active_low_sync', False)
        kwargs.setdefault('pin_config_is_input_sync', False)
        kwargs.setdefault('pin_config_default_value_sync', 0)     # Active high so low by default

        # Delay here should mean that if the ASIC was previously in use, the SYNC low will allow it to complete
        # the last frame before the firefly and ASIC are disabled.
        time.sleep(0.1)

        kwargs.setdefault('pin_config_id_firefly_en', 'EMIO29')
        kwargs.setdefault('pin_config_active_low_firefly_en', False)
        kwargs.setdefault('pin_config_is_input_firefly_en', False)
        kwargs.setdefault('pin_config_default_value_firefly_en', 0)     # Active high so disabled by default

        kwargs.update({'pin_config_active_low_app_en': False})      # This will force the ASIC into reset

        # Set clock generator base configuration directory, can be overridden
        kwargs.setdefault('clkgen_base_dir', './clkgen/')

        # Get config for MIC284
        #TODO update this for HMHZ
        self._mic284 = DeviceHandler(device_type_name='MIC284')
        self._mic284.i2c_address = 0x48
        self._mic284.i2c_bus = self._application_interfaces_i2c['APP_EXT']

        # Add more sensors to environment system for MIC
        #TODO update this for HMHZ
        self._env_sensor_info.extend([
            ('BD_MIC_IN', 'temperature', {"description": "MIC284 internal temperature", "units": "C"}),
            ('FIREFLY', 'temperature', {"description": "FireFly temperature", "units": "C"})
        ])

        # Get config for FireFly
        #TODO update this for HMHZ
        self._firefly = DeviceHandler(device_type_name='FireFly')
        self._firefly.i2c_address = 0x50    # There is a single firefly with no select line
        self._firefly.i2c_bus = self._application_interfaces_i2c['APP_EXT']

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

        super(LokiCarrier_HMHz, self).__init__(**kwargs)

        # Register a callback for when the application enable state changes, since the API for this is
        # provided by the base class and we need to set state variables related to it.
        self.register_change_callback('application_enable', self._onChange_app_en)

        self._logger.info('LOKI super init complete')

    def cleanup(self):
        # The cleanup function is called by odin-control on exit, for example if reloaded in debug mode
        # by a file edit.

        # This will terminate all threads, after setting main enable to false. This should also set SYNC
        # low first, ensuring that the ASIC completes its last packet before going down.
        self._exit_nicely()

    def _start_io_loops(self, options):
        # override IO loop start to add loops for this adapter
        super(LokiCarrier_HMHz, self)._start_io_loops(options)
        #TODO add HMHz threads here

    def _exit_nicely(self):
        # This wil be registered after the parent, therefore executed before automatic thread termination in LOKI
        # Therefore there is the chance to terminate 'nicely' before the threads are forced down.

        # Set the main enable low, which should in an ideal world grab all of the mutexes once ready.
        self._logger.critical('Trying to nicely grab HMHz mutexes')
        self.set_main_enable(False)

        # Wait for up to 20s for the main enable to work properly
        timeout = 20
        while not self.get_disconnect_safe():
            time.sleep(1)
            timeout -= 1
            self._logger.critical('\ttimeout: {}'.format(timeout))
            if timeout <= 0:
                break

        if self.get_disconnect_safe():
            self._logger.critical('\tgot mutexes OK')
        else:
            self._logger.critical('\tgave up on getting mutexes, threads will have to be killed messily')

        # If main enable has succeeded of we've given up waiting, perform critical exit operations
        self._logger.critical('Performing final cleanup operations for HEXITEC-MHz')
        #TODO add HMHz specifics here
        #TODO disable both fireflies
        #TODO disable power supplies
        #TODO disable HV?
        #TODO disable the ASIC

    def _config_ltc2986(self):
        # todo define any sensor readings required here
        pass

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
        self.clkgen_set_config(self._default_clock_config)

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
            self._logger.debug('Test read of MIC284 internal temperature: {}'.format(
                self._mic284.device.read_temperature_internal()
            ))

            self._mic284.initialised = True

            self._logger.debug('MIC284 {} initialised successfuly'.format(self._mic284))

        except Exception as e:
            self._mic284.critical_error('Failed to init MIC284 {}: {}'.format(self._mic284, e))

    def _get_mic284_internal_direct(self):
        with self._mic284.acquire(blocking=True, timeout=1) as rslt:
            if not rslt:
                raise Exception('Could not acquire lock for mic284, timed out')

            return self._mic284.device.read_temperature_internal()

    def _env_get_sensor(self, name, sensor_type):
        # This will return the raw value, cached by the LokiCarrierEnvmonitor class automatically

        # This extension will handle results for LTC2986 and any on-asic-carrier temps, must also
        # call parent to handle LOKI's own sensors.

        try:
            return super(LokiCarrier_BabyD, self)._env_get_sensor(name, sensor_type)
        except NotImplementedError:

            # If sensor is not found in main adapter, try sensors from BabyD implementation
            if name == 'BD_MIC_IN':
                if sensor_type == 'temperature':
                    return self._get_mic284_internal_direct()
                else:
                    raise
            elif name == 'FIREFLY':
                if sensor_type == 'temperature':
                    # This is actually a cached value already, but no matter
                    return self._bd_firefly_get_temperature_direct()
                else:
                    raise
            else:
                raise

    def _config_firefly(self):
        try:
            self._firefly.initialised = False
            self._firefly.error = False
            self._firefly.error_message = False

            #TODO because the driver is currently not very smart, it does not set the bus used, and
            # relies on the default setting. Therefore set the I2CDevice default bus and hope it doesn't
            # mess anything else up (it shouldn't if other buses are set manually).
            self._logger.warning('Setting default I2C bus number due to lack of functionality in firefly driver. This could cause issues with other drivers')
            I2CDevice._default_i2c_bus = self._firefly.i2c_bus

            # Enable the device
            self.set_pin_value('firefly_en', 1)
            time.sleep(1)

            # If the device is present, it should auto-detect the type etc.
            self._firefly.device = FireFly(
                base_address=self._firefly.i2c_address,
            )

            # Disable all firefly channels by default
            self._logger.info('Disabling all FireFly channels by default')
            self._firefly.device.disable_tx_channels(FireFly.CHANNEL_ALL)

            # Setup sync caches
            self._firefly._cached_channels_disabled = 0

            # Store the part number, vendor number, and OUI for later use
            self._logger.info('Storing FireFly PN, VN, OUI')
            self._firefly.info_pn, self._firefly.info_vn, self._firefly.info_oui = self._firefly.device.get_device_info()

            self._logger.info('Firefly current temperature {}C'.format(self._firefly.device.get_temperature()))

            self._firefly.initialised = True

            self._logger.debug('FireFly {} initialised successfuly'.format(self._firefly))

        except Exception as e:
            self._firefly.critical_error('Failed to init FireFly {}: {}'.format(self._firefly, e))
            self._logger.critical('Will disable firefly via reset line')
            self.set_pin_value('firefly_en', 0)

    def _setup_firefly(self):
        # Set up firefly for normal babyD usage, where all channels required are enabled
        with self._firefly.acquire(blocking=True, timeout=1) as rslt:
            if not rslt:
                if self._firefly.initialised:
                    self._logger.error('Failed to get FireFly lock while setting up base channel states, timed out')
                return None

            self.bd_firefly_set_channel_enabled('Z1', True)
            self.bd_firefly_set_channel_enabled('Z2', True)

    def _bd_firefly_channel_loop(self):
        while not self.TERMINATE_THREADS:
            time.sleep(0.2)
            try:
                # Try and grab the mutex to update channel status
                with self._firefly.acquire(blocking=True, timeout=1) as rslt:
                    if not rslt:
                        if self._firefly.initialised:
                            self._logger.debug('Failed to get FireFly lock while updating channel states')
                    else:
                        self._firefly._cached_channels_disabled = self._firefly.device.get_disabled_tx_channels_field()
            except Exception as e:
                logging.error('Error in FireFly channel sync loop: {}'.format(e))

    def _bd_firefly_get_temperature_direct(self):
        # Protect cache access and interaction with the I2C device with mutex
        with self._firefly.acquire(blocking=True, timeout=1) as rslt:
            if not rslt:
                if self._firefly.initialised:
                    self._logger.error('Failed to get FireFly lock while returning temperature, timed out')
                return None

            return self._firefly.device.get_temperature()

    def bd_firefly_get_partnumber(self):
        # Protect cache access and interaction with the I2C device with mutex
        with self._firefly.acquire(blocking=True, timeout=1) as rslt:
            if not rslt:
                if self._firefly.initialised:
                    self._logger.error('Failed to get FireFly lock while returning temperature, timed out')
                return None

            return self._firefly.info_pn

    def bd_firefly_get_vendornumber(self):
        # Protect cache access and interaction with the I2C device with mutex
        with self._firefly.acquire(blocking=True, timeout=1) as rslt:
            if not rslt:
                if self._firefly.initialised:
                    self._logger.error('Failed to get FireFly lock while returning temperature, timed out')
                return None

            return self._firefly.info_vn

    def bd_firefly_get_oui(self):
        # Protect cache access and interaction with the I2C device with mutex
        with self._firefly.acquire(blocking=True, timeout=1) as rslt:
            if not rslt:
                if self._firefly.initialised:
                    self._logger.error('Failed to get FireFly lock while returning temperature, timed out')
                return None

            return self._firefly.info_oui

    def bd_get_channel_names(self):
        # Returns a list of BabyD channel names used logically within the control system for various
        # settings across devices (firefly, retimer etc...)
        return list(self._bd_channels.keys())

    def bd_firefly_set_channel_enabled(self, channel_name, en=True):
        # Set enable state for a specific channel name, as defined by the application.
        # If channel_name is supplied as 'All', will operate on all channels (used for BabyD)
        channel = self._bd_channels.get(channel_name, None)
        if channel is None:
            return
        else:
            channel_bitfield = channel.firefly_ch_bitfield

        with self._firefly.acquire(blocking=True, timeout=1) as rslt:
            if not rslt:
                if self._firefly.initialised:
                    self._logger.error('Failed to get FireFly lock while returning channel states')

            self._firefly.device.enable_tx_channels(channel_bitfield)
            self._logger.info('Firefly: {}abled channel {}'.format('en' if en else 'dis', channel_name))

    def bd_firefly_get_channel_enabled(self, channel_name):
        # Get the current enable state for a channel name, where name is application-specific.
        # Get the current enable state for a channel name, as defined by the application.
        # If the channel_name is supplied as 'All', will return true if all used channels are enabled, false otherwise.
        channel = self._bd_channels.get(channel_name, None)
        if channel is None:
            return None
        else:
            channel_bitfield = channel.firefly_ch_bitfield

        with self._firefly.acquire(blocking=True, timeout=1) as rslt:
            if not rslt:
                if self._firefly.initialised:
                    self._logger.error('Failed to get FireFly lock while returning channel states')
                return None

            return not bool((self._firefly._cached_channels_disabled & channel_bitfield) == channel_bitfield)

    def get_sync(self):
        # Cached by handler, safe to directly request
        return bool(self.get_pin_value('sync'))

    def set_sync(self, value):
        self.set_pin_value('sync', bool(value))
        self._logger.info('SYNC {}'.format('high' if value else 'low'))

    def _gen_app_paramtree(self):
        # Override parameter tree generation to add application-specific tree

        self._logger.debug('Creating BabyD-specific ParameterTree')
        self.hmhz = {
            'info': {
                'asic_cache_hitrate': (lambda: self._asic.get_cache_hitrate(), None),
                'asic_cache_allowed': (lambda: self._asic_register_cache_allowed, self.set_asic_register_cache_allowed),
                'asic_cache_enabled': (self._get_asic_register_cache_enabled, None),
            },
            'system_state': {
                'SYNC': (self.get_sync, self.set_sync),
                'ASIC_EN': (self.get_app_enabled, self.set_app_enabled),
                'MAIN_EN': (self.get_main_enable, self.set_main_enable),
                'FIREFLY': (lambda: 'error' if self._firefly.error else ('initialised' if self._firefly.initialised else 'unconfigured'), None),
                'MIC284': (lambda: 'error' if self._mic284.error else ('initialised' if self._mic284.initialised else 'unconfigured'), None),
            },
            'firefly': self._gen_firefly_paramtree(),
            },
        }

        self._logger.debug('HEXITEC-MHz ParameterTree dict:{}'.format(self.hmhzpt))

        return self.hmhzpt

    def _gen_firefly_paramtree(self):
        channels_tree = self._gen_firefly_paramtree_channels()

        treedict = {
            # Temperature is now cached by the LOKI sensor manager, and is already in the parameter tree. This is a clone entry.
            "TEMPERATURE": (lambda: self.env_get_sensor_cached('FIREFLY', 'temperature'), None, {"description": "FireFly Temperature", "units": "C"}),
            "PARTNUMBER": (lambda: self.bd_firefly_get_partnumber(), None, {"description": "FireFly Part Number"}),
            "VENDORID": (lambda: self.bd_firefly_get_vendornumber(), None, {"description": "FireFly Vendor ID"}),
            "OUI": (lambda: self.bd_firefly_get_oui(), None, {"description": "FireFly OUI"}),
            "CHANNELS": channels_tree
        }

        return treedict

    def _gen_firefly_paramtree_channels(self):
        treedict = {}

        for channel_name in self._bd_channels.keys():
            channel = self._bd_channels.get(channel_name)

            # ALL is a special case, and has a more detailed description
            if channel_name == 'ALL':
                desc = 'All channel enable/disable. Value reads true if all channels are enabled and false if any channel is disabled.'
            else:
                desc = "Channel {} enable (firefly channel {})".format(channel_name, channel.firefly_ch_num)

            treedict[channel_name] = {
                "Enabled": (
                    (lambda ch_name_internal: lambda: self.bd_firefly_get_channel_enabled(ch_name_internal))(channel_name),
                    (lambda ch_name_internal: lambda en: self.bd_firefly_set_channel_enabled(ch_name_internal, en))(channel_name),
                    {"description": desc}
                )
            }

        return treedict
