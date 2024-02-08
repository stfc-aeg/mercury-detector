from odin_devices.spi_device import SPIDevice
from loki.register_controller import RegisterController

import logging
logging.basicConfig()
logging.root.setLevel(logging.INFO)


def convert_16b_8b(array_16b):
    array_out = []
    for word_16b in array_16b:
        array_out.append(word_16b >> 8)
        array_out.append(word_16b & 0xFF)
    return array_out


def convert_8b_16b(array_8b):
    array_out = []
    word_16b = 0
    for i in range(len(array_8b)):
        word_8b = array_8b[i]

        if i % 2 == 0:
            # Top byte
            word_16b = 0 | (word_8b << 8)
        else:
            # Bottom byte
            word_16b = word_16b | word_8b
            array_out.append(word_16b)

    return array_out


class ASICInterfaceDisabledError(Exception):
    def __init__(self, message):
        self.message = 'ASIC Interface Disabled, {}'.format(message)


class ASICIOError(Exception):
    def __init__(self, message):
        self.message = 'ASIC IO Error: {}'.format(message)


class HEXITEC_MHz(object):
    def __init__(self, bus, device, regmap_override_filenames: list, register_cache_enabled):
        self._logger = logging.getLogger('ASIC')

        # Setup up SPI Device
        self._device = SPIDevice(bus=bus, device=device, hz=20000)
        self._device.spi.mode = 0   # HEXITEC-MHz uses mode 0

        # Set up register controller to interact over SPI with defined fields
        if register_cache_enabled:
            self._logger.warning('Register caching was enabled for the ASIC, ensure that definitions for volatile registers are correct, or readback data may be false...')
        self.setup_fields(regmap_override_filenames, register_cache_enabled)

        self._interface_enabled = False

        # The register map is paged. Second page for higher addresses.
        self._current_page = 1

    def _read_register(self, address, length=1):
        # Direct ASIC function for reading from a register address, without caching (which
        # will be handled by the register controller). Result is a list of values. Should
        # support burst read.

        if not self._interface_enabled:
            raise ASICInterfaceDisabledError('Cannot read from ASIC')

        # TODO read value(s), or throw an ASICIOError if there is some failure

    def read_register(self, address, length=1):
        try:
            return self._register_controller.read_register(address, length)
        except ASICInterfaceDisabledError as e:
            #TODO Actually handle the error properly once it's passed through the register controller
            self._logger.error('Failed to read from ASIC register')
            # raise Exception('Failed to read from ASIC register')
        except Exception as e:
            raise

    def _write_register(self, address, data, verify=False):
        # Write a value / series of values directly to the ASIC, ignoring caching (this is handled
        # by the register controller). Should handle burst writes.

        # TODO write to the ASIC, throw ASICIOError if failure

        # If verification has been requested, read back the same address range and compare
        if verify:
            verification_readback = self.read_register(address, len(data))
            if verification_readback != data:
                raise ASICIOError(
                    'Verification failed writing register {}: \n\twrite data: {}\n\treadback: {}'.format(
                        address,
                        [hex(x) for x in data],
                        [hex(x) for x in verification_readback]))
            self._logger.debug('Data write verified')

    def write_register(self, address, data, verify=False):
        # Write data through the register controller
        # Data can either be a single word, or list of words to burst write

        # Convert single byte to list format
        if type(data) is int:
            data = [data]

        try:
            self._register_controller.write_register(address, data)
        except ASICInterfaceDisabledError as e:
            #TODO Actually handle the error properly once it's passed through the register controller
            self._logger.error('Failed to write to ASIC register')
            # raise Exception('Failed to write to ASIC register')
        except Exception as e:
            raise

        if verify:
            # Read back value directly (bypassing cache) to check it landed
            verification_readback = self._register_controller.read_register(address, len(data), direct_read=True)
            if verification_readback != data:
                raise Exception(
                    'Verification failed writing register {}: \n\twrite data: {}\n\treadback: {}'.format(
                        address,
                        [hex(x) for x in data],
                        [hex(x) for x in verification_readback]))
            self._logger.debug('Data write verified')

    def setup_fields(self, regmap_file_list: list, register_cache_enabled):
        # Create the register controller to handle field and register access
        self._register_controller = RegisterController(
            func_readreg=lambda address, length: self._read_register(address, length),
            func_writereg=lambda address, values: self._write_register(address, values),
            word_width_bits=8,
            cache_enabled=register_cache_enabled,
        )

        # Create default field mappings
        con = self._register_controller
        con.add_field('ExtBiasSel', 'Select External Bias Current, 0 = use bandgap', 0, 7, 1, is_volatile=False)
        con.add_field('Range', 'Negative Range, 0 = -20keV, 1 = -10keV', 0, 6, 1, is_volatile=False)
        con.add_field('Ipre', 'Preamp current, 0 = normal, 1 = high', 0, 5, 1, is_volatile=False)
        con.add_field('14fF', 'Select 14fF feedback capacitor', 0, 4, 1, is_volatile=False)
        con.add_field('7fF', 'Select 7fF feedback capacitor', 0, 3, 1, is_volatile=False)
        con.add_field('CalEn', 'Enable the test pulse', 0, 2, 1, is_volatile=False)
        # unused bit
        con.add_field('Page', 'Select the current register page', 0, 0, 1, is_volatile=False)
        # Add the rest of the ASIC fields

    def read_field(self, fieldname):
        try:
            return self._register_controller.read_field(fieldname)
        except Exception as e:
            #TODO Actually handle the error properly once it's passed through the register controller
            self._logger.error('Failed to read from ASIC field: {}'.format(e))
            # raise Exception('Failed to read from ASIC field')
            return 0

    def write_field(self, fieldname, value):
        try:
            self._register_controller.write_field(fieldname, value)
        except Exception as e:
            #TODO Actually handle the error properly once it's passed through the register controller
            self._logger.error('Failed to write to ASIC field')
            # raise Exception('Failed to write to ASIC field')

    def clear_register_cache(self):
        # Should be called every time the ASIC is reset and the register cache is known
        # to be invalid.
        self._register_controller.clear_cache()
        self._logger.warning('Cleared ASIC register cache, cache state is {}'.format('enabled' if self._register_controller.cache_enabled() else 'disabled'))

    def get_cache_enabled(self):
        return self._register_controller.cache_enabled()

    def disable_cache(self):
        self._register_controller.disable_cache()

    def enable_cache(self):
        self._register_controller.enable_cache()

    def enable_interface(self):
        # Used to tell the ASIC that its state is currently unreadible, and therefore
        # it should not respond to read / write operations
        self._interface_enabled = True

    def disable_interface(self):
        # Used to tell the ASIC that its state is currently unreadible, and therefore
        # it should not respond to read / write operations
        self._interface_enabled = False

    def interface_enabled(self):
        return self._interface_enabled

    def get_cache_hitrate(self):
        # Return the proportion of read operations that hit the cache
        cache, direct = self._register_controller.stats_cached_direct()

        return (
            {
                'hitrate': (cache / (cache + direct)) if ((cache + direct) > 0) else 0,
                'hits': cache,
                'misses': direct,
            }
        )

    def read_test_pattern(self, sector):
        #TODO
        pass

    def write_test_pattern(self, pattern_data_12bit, sector):
        #TODO
        pass

    def test_pattern_identify_sector_division(self, sector):
        #TODO
        pass

    def enable_calibration_test_pattern(self, enable=True):
        #TODO
        pass

    def get_calibration_test_pattern_enabled(self, direct=True):
        #TODO
        pass

    def set_calibration_test_pattern(self, row_bytes, column_bytes):
        #TODO
        pass

    def set_calibration_test_pattern_bits(self, row_bits, column_bits):
        #TODO
        pass

    def cal_pattern_highlight_sector_division(self, sector, division):
        #TODO
        pass

    def cal_pattern_highlight_pixel(self, column, row):
        #TODO
        pass

    def cal_pattern_set_default(self):
        #TODO
        pass

    def set_tdc_local_vcal(self, local_vcal_en=True):
        #TODO
        pass

    def set_all_ramp_bias(self, bias):
        #TODO
        pass

    def set_integration_tion(self, integration_time_frames):
        #TODO
        pass

    def get_integration_time(self):
        #TODO
        pass

    def set_frame_length(self, frame_length_clocks):
        #TODO
        pass

    def get_frame_length(self, direct=False):
        #TODO
        pass

    def set_feedback_capacitance(self, feedback_capacitance_fF):
        #TODO
        pass

    def get_feedback_capacitance(self):
        #TODO
        pass

    def _init_serialisers(self):
        #TODO
        pass

    def set_ser_enable_CML_drivers(self, enable, holdoff=False):
        #TODO
        pass

    def set_all_serialiser_pattern(self, pattern):
        #TODO
        pass

    def get_all_serialiser_pattern(self, direct=False):
        #TODO
        pass

    def set_all_serialiser_bit_scramble(self, scrable_en):
        #TODO
        pass

    def set_channel_serialiser_pattern(self, channel, pattern, holdoff=False):
        #TODO
        pass

    def set_channel_serialiser_cml_en(self, channel, enable):
        #TODO
        pass

    def get_channel_serialiser_cml_en(self, channel):
        #TODO
        pass

    def set_all_serialiser_DLL_Config(self, DLL_Config):
        #TODO
        pass

    def set_all_serialiser_DLL_phase_invert(self, DLL_Phase_Config=True):
        #TODO
        pass

    def set_global_serialiser_mode(self, mode):
        #TODO
        pass

    def get_global_serialiser_mode(self, bits_only=False, direct=False):
        #TODO
        pass

    def Set_DiamondDefault_Registers(self):
        #TODO
        pass

    def ser_enter_reset(self):
        #TODO
        pass

    def ser_exit_reset(self):
        #TODO
        pass

    def enter_bonding_mode(self):
        #TODO
        pass

    def enter_data_mode(self):
        #TODO
        pass

# TODO also work out how to add serialiser stuff....

