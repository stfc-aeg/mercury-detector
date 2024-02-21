from odin_devices.spi_device import SPIDevice
from loki.register_controller import RegisterController

import logging
logging.basicConfig()
logging.root.setLevel(logging.INFO)

REGISTER_WRITE_TRANSACTION = 0X00
REGISTER_READ_TRANSACTION = 0X80
REGISTER_ADDRESS_MASK = 0b01111111

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
    _serialiser_mode_names = {
        "init": 0b00,
        "bonding": 0b01,
        "data": 0b11
    }

    def __init__(self, bus, device, hz, regmap_override_filenames: list, register_cache_enabled):
        self._logger = logging.getLogger('ASIC')

        # Setup up SPI Device
        self._device = SPIDevice(bus=bus, device=device, hz=hz)
        self._device.spi.mode = 0   # HEXITEC-MHz uses mode 0
        self._device.set_cs_active_high(False)

        # Set up register controller to interact over SPI with defined fields
        if register_cache_enabled:
            self._logger.warning('Register caching was enabled for the ASIC, ensure that definitions for volatile registers are correct, or readback data may be false...')
        self.setup_fields(regmap_override_filenames, register_cache_enabled)

        self._interface_enabled = False

        # The register map is paged. Second page for higher addresses.
        self._current_page = None

        self._logger.info('HEXITEC-MHz ASIC init complete')

    def _set_page(self, page):
        # Set the page pit in the control register (0), which is the same no matter which
        # page you are on. Don't bother to change the page if it is already correct, as
        # this will add pointless transactions. Note that pages are 0 and 1, not 1 and 2
        # as sometimes indicated in documentation.

        if self._current_page != page:
            # Because this function is called by the register controller below the caching
            # layer, it must perform the read-modify-write itself.

            # Read
            command = 0x00 | REGISTER_READ_TRANSACTION
            transfer_buffer = [command, 0x00]
            config_value = self._device.spi.transfer(transfer_buffer)[1]

            # Modify
            page_set_value = (config_value & 0b11111110) | (page_bit & 0b1)

            # Write
            command = 0x00 | REGISTER_WRITE_TRANSACTION
            transfer_buffer = [command, page_set_value]
            self._device.spi.transfer(transfer_buffer)

            self.page = page

    def _read_register(self, address, length=1):
        # Direct ASIC function for reading from a register address, without caching (which
        # will be handled by the register controller). Result is a list of values. Should
        # support burst read.

        if not self._interface_enabled:
            raise ASICInterfaceDisabledError('Cannot read from ASIC when disabled')

        # Set the register page
        if (address == 0):      # CONFIG appears on both pages
            pass
        elif (address > 127):   # Second page
            self._set_page(1)
        else:                   # First page
            self._set_page(0)
        address = address & REGISTER_ADDRESS_MASK

        command = address | REGISTER_READ_TRANSACTION

        transfer_buffer = [command]
        transfer_buffer.append(0x00)

        readback = self._device.spi.transfer(transfer_buffer)

        if readback is None:
            raise ASICIOError('Failed to read {} bytes, SPI error'.format(length))
        elif len(readback) != length:
            raise ASICIOError('Got incorrect number of bytes back. Expected {}, got {}'.format(length, len(readback)))

        self._logger.debug("Register {} read as {}".format(address, readback))

    def read_register(self, address, length=1):
        # Read a register through the register controller, therefore cache already handled
        # internally. Address can be either a number (typical) or a string name, since this
        # ASIC has a register name table.

        # If the address was supplied as a name, get the actual address of it
        if type(address) == str:
            address = self.register_name_to_address(address)

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

        if not self._interface_enabled:
            raise ASICInterfaceDisabledError('Cannot write to ASIC when disabled')

        # Set the register page
        if (address == 0):      # CONFIG appears on both pages
            pass
        elif (address > 127):   # Second page
            self._set_page(1)
        else:                   # First page
            self._set_page(0)

        address = address & REGISTER_ADDRESS_MASK

        command = address | REGISTER_WRITE_TRANSACTION

        transfer_buffer = [command]
        transfer_buffer.append(data)

        self._device.spi.transfer(transfer_buffer)

        self._logger.debug("Register {} written with {}".format(address, data))

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

        # If the address was supplied as a name, get the actual address of it
        if type(address) == str:
            address = self.register_name_to_address(address)

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

    def register_name_to_address(self, name):
        return list(self._REGISTER_NAMES.values()).index(name)

    def register_address_to_name(self, address):
        return self._REGISTER_NAMES.get(address, None)

    def setup_fields(self, regmap_file_list: list, register_cache_enabled):
        # Create the register controller to handle field and register access
        self._register_controller = RegisterController(
            func_readreg=lambda address, length: self._read_register(address, length),
            func_writereg=lambda address, values: self._write_register(address, values),
            word_width_bits=8,
            cache_enabled=register_cache_enabled,
        )

        self._REGISTER_NAMES = {}

        # Create default field mappings
        con = self._register_controller

        self._REGISTER_NAMES[0] = 'CONFIG'
        con.add_field('ExtBiasSel', 'Select External Bias Current, 0 = use bandgap', 0, 7, 1, is_volatile=False)
        con.add_field('Range', 'Negative Range, 0 = -20keV, 1 = -10keV', 0, 6, 1, is_volatile=False)
        con.add_field('Ipre', 'Preamp current, 0 = normal, 1 = high', 0, 5, 1, is_volatile=False)
        con.add_field('14fF', 'Select 14fF feedback capacitor', 0, 4, 1, is_volatile=False)
        con.add_field('7fF', 'Select 7fF feedback capacitor', 0, 3, 1, is_volatile=False)
        con.add_field('CalEn', 'Enable the test pulse', 0, 2, 1, is_volatile=False)
        # unused bit
        con.add_field('Page', 'Select the current register page', 0, 0, 1, is_volatile=True)        # Considered volatile because the page is changed at a lower level than the caching layer to access different registers.
        #TODO make this non-volatile once the mutexes are properly sorted for the register handler

        self._REGISTER_NAMES[1] = 'GL_CONT1'
        con.add_field('GL_ROE_CONT', 'Global / Local readout control', 1, 6, 1, is_volatile=False)
        con.add_field('GL_DigSig_CONT', 'Global / Local digital signals control', 1, 5, 1, is_volatile=False)
        con.add_field('GL_AnaSig_CONT', 'Global / Local analog signals control', 1, 4, 1, is_volatile=False)
        con.add_field('GL_AnaBias_CONT', 'Global / Local analog bias control', 1, 3, 1, is_volatile=False)
        con.add_field('GL_TDCOsc_CONT', 'Global / Local TDC Oscillator control', 1, 2, 1, is_volatile=False)
        con.add_field('GL_SerPLL_CONT', 'Global / Local Serialiser PLL control', 1, 1, 1, is_volatile=False)
        con.add_field('GL_TDCPLL_CONT', 'Global / Local TDC PLL control', 1, 0, 1, is_volatile=False)

        self._REGISTER_NAMES[2] = 'GL_CONT2'
        con.add_field('GL_VCALsel_CONT', 'Global / Local VCAL Control', 2, 6, 1, is_volatile=False)
        con.add_field('GL_SerMode_CONT', 'Global / Local serialiser mode Control', 2, 5, 1, is_volatile=False)
        con.add_field('GL_SerAnaRstB_CONT', 'Global / Local serialiser analogue reset Control', 2, 1, 1, is_volatile=False)
        con.add_field('GL_SerDigRstB_CONT', 'Global / Local serialiser digital reset Control', 2, 0, 1, is_volatile=False)

        self._REGISTER_NAMES[3] = 'GL_EN1'
        con.add_field('GL_ROE_EN', 'Global / Local readout enable', 3, 6, 1, is_volatile=False)
        con.add_field('GL_DigSig_EN', 'Global / Local digital signals enable', 3, 5, 1, is_volatile=False)
        con.add_field('GL_AnaSig_EN', 'Global / Local analog signals enable', 3, 4, 1, is_volatile=False)
        con.add_field('GL_AnaBias_EN', 'Global / Local analog bias enable', 3, 3, 1, is_volatile=False)
        con.add_field('GL_TDCOsc_EN', 'Global / Local TDC Oscillator enable', 3, 2, 1, is_volatile=False)
        con.add_field('GL_SerPLL_EN', 'Global / Local Serialiser PLL enable', 3, 1, 1, is_volatile=False)
        con.add_field('GL_TDCPLL_EN', 'Global / Local TDC PLL enable', 3, 0, 1, is_volatile=False)

        self._REGISTER_NAMES[4] = 'GL_EN2'
        con.add_field('GL_VCALsel_EN', 'Global / Local VCAL enable', 4, 6, 1, is_volatile=False)
        con.add_field('GL_SerMode2_EN', 'Global / Local Serialiser 2 Mode bits', 4, 5, 2, is_volatile=False)
        con.add_field('GL_SerMode1_EN', 'Global / Local Serialiser 1 Mode bits', 4, 3, 2, is_volatile=False)
        con.add_field('GL_SerAnaRstB_EN', 'Global / Local Serialiser Analogue Reset Control', 4, 1, 1, is_volatile=False)
        con.add_field('GL_SerDigRstB_EN', 'Global / Local Serialiser Digital Reset Control', 4, 0, 1, is_volatile=False)

        self._REGISTER_NAMES[5] = 'FrmLength'
        con.add_field('FrmLength', 'Frame Length', 5, 7, 8, is_volatile=False)

        self._REGISTER_NAMES[6] = 'IntTime'
        con.add_field('IntTime', 'Integration Time', 6, 7, 8, is_volatile=False)

        self._REGISTER_NAMES[7] = 'TESTSR'
        con.add_field('TS_TRIG', 'Test Shift Register Trigger', 7, 7, 1, is_volatile=False)
        con.add_field('TS_SECT', 'Test Shift Register Image Sector Number 0-19', 7, 6, 5, is_volatile=False)
        con.add_field('TS_MODE', 'Test Shift Register Mode: 00 IDLE, 01 Shift, 10 Read, 11 Write', 7, 1, 2, is_volatile=False)

        self._REGISTER_NAMES[8] = 'SER_PLL_BIAS'
        con.add_field('SerPLLBias_ChargePump', 'Serialiser PLL Charge Pump Bias', 8, 7, 4, is_volatile=False)
        con.add_field('SerPLLBias_Regulator', 'Serialiser PLL Regulator Bias', 8, 3, 4, is_volatile=False)

        self._REGISTER_NAMES[9] = 'TDC_PLL_BIAS'
        con.add_field('TDCPLLBias_ChargePump', 'TDC PLL Charge Pump Bias', 9, 7, 4, is_volatile=False)
        con.add_field('TDCPLLBias_Regulator', 'TDC PLL Regulator Bias', 9, 3, 4, is_volatile=False)

        # The timing registers are all non-volatile, single byte registers
        for (addr, name, desc) in [
            (10,    'DATA_SHIFT',       'Load Read Out Data'),
            (11,    'PRE_RST_ON',       'Reset preamplifier on'),
            (12,    'PRE_RST_OFF',      'Reset preamplifier off'),
            (13,    'CDS_RST_ON',       'Reset CDS on'),
            (14,    'CDS_RST_OFF',      'Reset CDS off'),
            (15,    'CDS_COUNTER_ON',   'CDS Sample on'),
            (16,    'CDS_COUNTER_OFF',  'CDS Sample off'),
            (17,    'SAMPLE_H_ON',      'Sample & Hold on'),
            (18,    'SAMPLE_H_OFF',     'Sample & Hold off'),
            (19,    'RAMP_EN_ON',       'Ramp Enable on'),
            (20,    'RAMP_EN_OFF',      'Ramp Enable off'),
            (21,    'TDC_OUT_ENB_ON',   'TDC Output Enable on'),
            (22,    'TDC_OUT_ENB_OFF',  'TDC Output Enable off'),
            (23,    'TDC_CND_RST_ON',   'TDC Counter Reset on'),
            (24,    'TDC_CND_RST_OFF',  'TDC Counter Reset off'),
            (25,    'CAL_TOGGLE',       'Calibration Pulse Toggle'),
        ]:
            self._REGISTER_NAMES[addr] = name
            con.add_field(name, desc, addr, 7, 8, is_volatile=False)

        self._REGISTER_NAMES[11] = 'PRE_RST_ON'
        con.add_field(self.register_address_to_name(11), 'Reset preamplifier on', 11, 7, 8, is_volatile=False)

        # Segment Serialiser Select is a collection of 6 fields over 1 register, but there
        # is one for each of the 10 segments. These will just be created as differently named
        # fields. Segments are named 1-10.
        for segment in range(1, 11):
            addr = (26 + segment) - 1   # -1 for first segment being 1
            self._REGISTER_NAMES[addr] = 'GL_SER_SEL{}'.format(segment)

            # For each register, add the local serialiser mode / reset signals as combined
            # bit pairs.
            con.add_field(
                'GL_SerMode2_SEL{}'.format(segment),
                'Local Serialiser 2 mode (segment {})'.format(segment),
                addr, 5, 2, is_volatile=False
            )
            con.add_field(
                'GL_SerMode1_SEL{}'.format(segment),
                'Local Serialiser 1 mode (segment {})'.format(segment),
                addr, 3, 2, is_volatile=False
            )
            con.add_field(
                'GL_SerAnaRstB_SEL{}'.format(segment),
                'Local Serialiser Analogue Reset (segment {})'.format(segment),
                addr, 1, 1, is_volatile=False
            )
            con.add_field(
                'GL_SerDigRstB_SEL{}'.format(segment),
                'Local Serialiser Digital Reset (segment {})'.format(segment),
                addr, 0, 1, is_volatile=False
            )

        # Similar to above, Segment Signal Select is a collection of fields over 1 register,
        # one for each of the 10 segments. They are then separated into serialiser 1 and 2,
        # for left and right.
        for segment in range(1, 11):
            addr = (36 + segment) -1    # -1 for first segment being 1
            self._REGISTER_NAMES[addr] = 'GL_SEL{}'.format(segment)

            # For each resister, add the local serialiser signal select signals
            con.add_field(
                'GL_DigSigEn_SEL{}'.format(segment),
                'Local Digital Signal Enable (segment {})'.format(segment),
                addr, 7, 1, is_volatile=False
            )
            con.add_field(
                'GL_AnaSigEn_SEL{}'.format(segment),
                'Local Analogue Signal Enable (segment {})'.format(segment),
                addr, 6, 1, is_volatile=False
            )
            con.add_field(
                'GL_TDCOscEn_SEL{}'.format(segment),
                'Local Serialiser TDC Oscillator Enable (segment {})'.format(segment),
                addr, 5, 1, is_volatile=False
            )
            con.add_field(
                'GL_SerPLLEn_SEL{}'.format(segment),
                'Local Serialiser PLL Enable (segment {})'.format(segment),
                addr, 4, 1, is_volatile=False
            )
            con.add_field(
                'GL_TDCPLLEn_SEL{}'.format(segment),
                'Local TDC PLL Enable (segment {})'.format(segment),
                addr, 3, 1, is_volatile=False
            )
            con.add_field(
                'GL_AnaEn_SEL{}'.format(segment),
                'Local Pixel Bias Enable (segment {})'.format(segment),
                addr, 2, 1, is_volatile=False
            )
            con.add_field(
                'GL_ROE_SEL{}'.format(segment),
                'Local Readout Enable (segment {})'.format(segment),
                addr, 1, 1, is_volatile=False
            )
            con.add_field(
                'GL_SerDigRstB_SEL{}'.format(segment),
                'Local VCAL Select (segment {})'.format(segment),
                addr, 0, 1, is_volatile=False
            )

        # Add a Ramp control register for each of 20 columns.
        # There are 10 segments, each of which has 8 pixels. Each segment has two control
        # registers for ramp controllers, each of which is responsible for two ramp generators.
        # Each ramp generator is responsible for two pixels.
        for ramp_generator_number in range(1, 21):
            addr = (46 + ramp_generator_number) -1
            self._REGISTER_NAMES[addr] = 'RAMPControl{}'.format(ramp_generator_number)

            # Each 8-bit register represents a pair of two ramp generators, each of which
            # operates on two pixels. There are two control registers (4 generators) per
            # segment.

            segment_num = int((ramp_generator_number + 1) / 2)

            con.add_field(
                'RAMPControl{}'.format(ramp_generator_number),
                'RAMP Bias Control {} (Segment {}, generators {})'.format(ramp_generator_number, segment_num, '1 and 2' if (ramp_generator_number % 2) else '3 and 4'),
                addr, 7, 8, is_volatile=False
            )

        # Add a serialiser control registers. These are in groups 10 of 6 registers, one for
        # each serialiser. Each of these segments is actually made up of 10 fields spread over
        # the registers, in reverse.

        for serialiser_number  in range(1, 11):
            base_addr = (66 + serialiser_number) -1

            # The register names match the manual, but do not relate to field organisation
            self._REGISTER_NAMES.update({
                base_addr: 'SerControl{}A'.format(serialiser_number),
                base_addr+1: 'SerControl{}B'.format(serialiser_number),
                base_addr+2: 'SerControl{}C'.format(serialiser_number),
                base_addr+3: 'SerControl{}D'.format(serialiser_number),
                base_addr+4: 'SerControl{}E'.format(serialiser_number),
                base_addr+5: 'SerControl{}F'.format(serialiser_number),
            })

            # The fields are organised spanning the 6 bytes, but some fields start in the LSBs
            # of register n, and finish in the MSBs of register n-1, meaning they will have to
            # be implemented as subfields joined together to form one logical field. For example.
            # the `PatternControl` 3-bit field has its first bit in register F:0, and then its
            # final 2 bits in register E:7-6.

            con.add_field(
                'Ser{}_EnableCCP'.format(serialiser_number),
                'Enable CCP'.format(serialiser_number),
                base_addr+5, 6, 1, is_volatile=False
            )
            con.add_field(
                'Ser{}_EnableCCPInitial'.format(serialiser_number),
                'Enable CCP Initial for Serialiser {}'.format(serialiser_number),
                base_addr+5, 5, 1, is_volatile=False
            )
            con.add_field(
                'Ser{}_LowPriorityCCP'.format(serialiser_number),
                'Low Priority CCP for Serialiser {}'.format(serialiser_number),
                base_addr+5, 4, 1, is_volatile=False
            )
            con.add_field(
                'Ser{}_EnableEndframe'.format(serialiser_number),
                'Enable Endframe for Serialiser {}'.format(serialiser_number),
                base_addr+5, 3, 1, is_volatile=False
            )
            con.add_field(
                'Ser{}_BypassScramble'.format(serialiser_number),
                'Bypass Scramble for Serialiser {}'.format(serialiser_number),
                base_addr+5, 2, 1, is_volatile=False
            )
            con.add_field(
                'Ser{}_StrictAlignmentFlagEn'.format(serialiser_number),
                'Strict Alignment Flag Enable for Serialiser {}'.format(serialiser_number),
                base_addr+5, 1, 1, is_volatile=False
            )

            # PatternControl spans two registers
            patterncon_high = con.add_field(
                'PatternControl_ms', '', base_addr+5, 0, 1, is_volatile=False
            )
            patterncon_low = con.add_field(
                'PatternControl_ls', '', base_addr+4, 7, 2, is_volatile=False
            )
            con.add_multifield(
                'Ser{}_PatternControl'.format(serialiser_number),
                'Pattern Control for Serialiser {}'.format(serialiser_number),
                [patterncon_high, patterncon_low]
            )

            con.add_field(
                'Ser{}_CCPCount'.format(serialiser_number),
                'CCP Count for Serialiser {}'.format(serialiser_number),
                base_addr+4, 5, 2, is_volatile=False
            )
            con.add_field(
                'Ser{}_DLLPhaseConfig'.format(serialiser_number),
                'DLL Phase Config for Serialiser {}'.format(serialiser_number),
                base_addr+4, 1, 1, is_volatile=False
            )

            # DLLConfig spans two registers
            dllconfig_high = con.add_field(
                'Ser{}_DLLConfig_ms'.format(serialiser_number), '', base_addr+4, 0, 1, is_volatile=False
            )
            dllconfig_low = con.add_field(
                'Ser{}_DLLConfig_ls'.format(serialiser_number), '', base_addr+3, 7, 2, is_volatile=False
            )
            con.add_multifield(
                'Ser{}_DLLConfig'.format(serialiser_number),
                'DLL Config for Serialiser {}'.format(serialiser_number),
                [dllconfig_high, dllconfig_low]
            )

            con.add_field(
                'Ser{}_CMLEn1'.format(serialiser_number),
                'CML En Driver 1 for Serialiser {}'.format(serialiser_number),
                base_addr+3, 5, 1, is_volatile=False
            )
            con.add_field(
                'Ser{}_CMLEn2'.format(serialiser_number),
                'CML En Driver 2 for Serialiser {}'.format(serialiser_number),
                base_addr+3, 4, 1, is_volatile=False
            )
            con.add_field(
                'Ser{}_Pre2Tweak'.format(serialiser_number),
                'Pre2 Tweak for Serialiser {}'.format(serialiser_number),
                base_addr+3, 3, 4, is_volatile=False
            )
            con.add_field(
                'Ser{}_Pre1Tweak'.format(serialiser_number),
                'Pre1 Tweak for Serialiser {}'.format(serialiser_number),
                base_addr+2, 7, 4, is_volatile=False
            )
            con.add_field(
                'Ser{}_CMLBuffTweak'.format(serialiser_number),
                'CML Buffer Tweak for Serialiser {}'.format(serialiser_number),
                base_addr+2, 3, 4, is_volatile=False
            )
            con.add_field(
                'Ser{}_CMLTweak'.format(serialiser_number),
                'CML Tweak for Serialiser {}'.format(serialiser_number),
                base_addr+1, 7, 4, is_volatile=False
            )
            con.add_field(
                'Ser{}_DLLTweak'.format(serialiser_number),
                'DLL Tweak for Serialiser {}'.format(serialiser_number),
                base_addr+1, 3, 4, is_volatile=False
            )
            con.add_field(
                'Ser{}_SerClkTweak'.format(serialiser_number),
                'Serialiser Clock Tweak for Serialiser {}'.format(serialiser_number),
                base_addr+0, 7, 4, is_volatile=False
            )
            con.add_field(
                'Ser{}_SerTweak'.format(serialiser_number),
                'Serialiser Tweak for Serialiser {}'.format(serialiser_number),
                base_addr+0, 3, 4, is_volatile=False
            )

        # Calibration shift register is actually 20-byte depth, at one address
        con.add_field('SRCal', 'Test Pattern shift register, 20 bytes', 126, 7, 20*8, is_volatile=True)

        # Test pattern shift register is actually 20-byte depth, at one address
        con.add_field('SRTest', 'Test Pattern shift register, 20 bytes', 127, 7, 20*8, is_volatile=True)

        # Page 2 registers, paging handled automatically
        ################################################

        self._REGISTER_NAMES[131] = 'ChipBias'
        con.add_field('ChipBias', 'Global Chip Bias', 130, 7, 8, is_volatile=False)

        for segment in range(1, 11):
            addr = (131 + segment) -1    # -1 for first segment being 1
            self._REGISTER_NAMES[addr] = 'SerBias{}'.format(segment)

            con.add_field(
                'SerBias{}'.format(segment),
                'Serialiser Bias Setting, Segment {}'.format(segment),
                addr, 7, 8, is_volatile=False
            )

        # Read-only registers
        #####################
        #TODO Add the rest of the ASIC fields

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
        failed = self._register_controller.stats_failed()

        return (
            {
                'hitrate': (cache / (cache + direct)) if ((cache + direct) > 0) else 0,
                'hits': cache,
                'misses': direct,
                'failed': failed,
            }
        )

    def read_test_pattern(self, sector):
        # Read out a test pattern from a specificed sector using the 480
        # byte test shift register (320 12-bit pixels). The result is
        # returned as an array of 320 12-bit pixel values.

        # Set the sector
        self.write_field('TS_SECT', sector)

        # Set test register read mode with trigger 0
        self.write_field('TS_TRIG', 0)
        self.write_field('TS_MODE', 0b10)

        # Keep test register read mode with trigger 1
        self.write_field('TS_TRIG', 1)

        # Put test shift register into shift mode
        self.write_field('TS_MODE', 0b01)

        # Read the test shift register
        #readout = self.burst_read(127, 480)
        readout = self.read_field('SRTest')

        # Convert to 12-bit data and remove first byte (not part of read)        
        readout_12bit = Asic.convert_8bit_12bit(readout[1:])

        return readout_12bit

    def write_test_pattern(self, pattern_data_12bit, sector):
        # Write a test pattern to the test shift register for a single sector.
        # The input is taken as an array of 360 12-bit pixel values, written in 4x4
        # grids from left to right. Each grid is supplied with values starting at
        # the bottom left pixel, moving horizontally then up one row (see the ASIC
        # manual Test Shfit Reigster Data Order (v1.3 section 5.7.2).

        # Prepare the 8-bit data
        pattern_data_8bit = Asic.convert_12bit_8bit(pattern_data_12bit)

        # Set the test register to shift mode with no trigger
        self.write_field('TS_SECT', sector)
        self.write_field('TS_TRIG', 0)
        self.write_field('TS_MODE', 0b01)

        # Burst write register 127 with the 8-bit data
        #self.burst_write(pattern_data_8bit, 480)
        self.write_field('SRTest', pattern_data_8bit)

        # Set the test register to write mode
        self.write_field('TS_MODE', 0b11)

    def test_pattern_identify_sector_division(self, sector):
        # Send data to a given sector that will identify individual 4x4 grids with
        # set pattern. Each pixel in the 4x4 grid will have the same value, which is
        # incremented counting the grids from left to right and then top to bottom.
        # Grid numbering will start at 1 to ensure there is something to receive.
        # (i.e. the second grid in the third sector will contain pixel values 43)

        sector_offset = (sector * 20) + 1 # Sector numbering starts at 0, first value 1

        # Generate the 4x4 grid 12-bit values
        pattern_12bit = []
        for grid_id in range(sector_offset, sector_offset+20):
            grid_values = [grid_id] * 20
            pattern_12bit.extend(grid_values)

        # Submit the test pattern
        self.write_test_pattern(pattern_12bit, sector)

    def enable_calibration_test_pattern(self, enable=True):
        self.write_field('CalEn', 1 if enable else 0)
        self._logger.info(("Enabled" if enable else "Disabled") + " calibration pattern mode")

    def get_calibration_test_pattern_enabled(self, direct=True):
        return self.read_field('CalEn')

    def set_calibration_test_pattern(self, row_bytes, column_bytes):
        # Submit a calibration test pattern, which consists of two arrays (one for
        # row and the other for columns). Each array contains binary pixel values.
        # The row and column patterns are ANDed toghether, so only pixels that have
        # a high value in both row and column will be high. The ASIC cycles through
        # 4 patterns (rising, falling, and 2 blanks) using this base pattern.
        #
        # Bytes are MSB-first, but the rows are loaded in reverse from 79 to 0 (i.e.
        # to set only the first pixel, the last row byte would be 0b00000001 and the
        # first column byte would be 0b10000000.

        self._logger.debug('Writing calibration test pattern {}'.format(
            [hex(x) for x in (row_bytes + column_bytes)]))

        #self.burst_write(126, row_bytes + column_bytes)
        self.write_field('SRCal', row_bytes + column_bytes)

    def set_calibration_test_pattern_bits(self, row_bits, column_bits):
        # Constructs a calibration pattern using arrays of bits for rows and columns.
        # Ordering is from pixel count 0 to 79 for each.

        # Reverse the row array, since it is loaded from pixel 79 to 0.
        row_bits_reversed = reversed(row_bits)

        # Convert bits to byte array, MSB First
        row_bytes = [sum([byte[b] << (7- b) for b in range(7,-1,-1)])
                for byte in zip(*(iter(row_bits_reversed),) * 8)]
        column_bytes = [sum([byte[b] << (7- b) for b in range(7,-1,-1)])
                for byte in zip(*(iter(column_bits),) * 8)]

        self.set_calibration_test_pattern(row_bytes=row_bytes, column_bytes=column_bytes)

    def cal_pattern_highlight_sector_division(self, sector, division):
        # Use the calibration test pattern to (within a single sector) zero all pixels
        # except those in a certain division and sector, which will be filled with all
        # high bits. There is one bit per pixel in the calibration pattern.

        row_bits = []
        column_bits = []

        sector = int(sector)
        division = int(division)

        # Only rows with pixels in the correct sector will be highlighted
        for row_id in range(0, 80):
            sector_id = int(row_id / 4)
            if sector_id == sector:
                row_bits.append(1)
            else:
                self._logger.debug('{}: did not accept sector id {} from row {} to match sector {}'.format(
                    sector_id == sector, sector_id, row_id, sector))
                row_bits.append(0)

        # Only columns with pixels in the correct division will be highlighted
        for column_id in range(0, 80):
            division_id = int(column_id / 4)
            if division_id == division:
                column_bits.append(1)
            else:
                column_bits.append(0)

        self._logger.info("Generated calibration test pattern to highlight sector {}, division {}".format(sector, division))
        self._logger.debug("In bit form:\n\trows: {}\n\tcolumns:{}".format(row_bits, column_bits))

        # Submit the test pattern and enable it
        self.set_calibration_test_pattern_bits(row_bits=row_bits, column_bits=column_bits)
        self.enable_calibration_test_pattern(True)

    def cal_pattern_highlight_pixel(self, column, row):
        # Use the calibration tesst pattern to zero all pixels except one defined pixel
        # location, which will be high. The exact output of this is defined by the ASIC
        # calibration pattern cycle. 1/4 frames will be the highest contrast.

        row_bits = [0] * row + [1] + [0] * (79-row)
        column_bits = [0] * column + [1] + [0] * (79-column)

        self._logger.info("Generated calibration test pattern to highlight pixel row {}, column {}".format(row, column))
        self._logger.debug("In bit form:\n\trows: {}\n\tcolumns:{}".format(row_bits, column_bits))

        # Submit the test pattern and enable it
        self.set_calibration_test_pattern_bits(row_bits=row_bits, column_bits=column_bits)
        self.enable_calibration_test_pattern(True)

    def cal_pattern_set_default(self):
        self.set_calibration_test_pattern(CAL_PATTERN_DEFAULT_BYTES['rows'],
                CAL_PATTERN_DEFAULT_BYTES['cols'])

        self._logger.info("Set calibration test pattern to default value")

    def set_tdc_local_vcal(self, local_vcal_en=True):
        self.write_field('GL_VCALsel_EN', 1 if local_vcal_en else 0)

    def set_all_ramp_bias(self, bias):
        # Set the ramp bias value for all 40 ramps in the ASIC
        if not bias in range(0,16):
            raise ValueError("Bias must be in range 0-15")

        for fieldname in ['RAMPControl{}'.format(x) for x in range(1,21)]:
            self.write_field(bias)

        self._logger.info("Set ramp bias for all 40 ASIC ramps to {}".format(bias))

    def set_integration_time(self, integration_time_frames):
        self.write_field('IntTime', integration_time_frames)

    def get_integration_time(self):
        self.read_field('IntTime')

    def set_frame_length(self, frame_length_clocks):
        self.write_field('FrmLength', integration_time_frames)

    def get_frame_length(self, direct=False):
        self.read_field('FrmLength')

    def set_feedback_capacitance(self, feedback_capacitance_fF):
        if not feedback_capacitance_fF in [0, 7, 14, 21]:
            raise ValueError("Capacitance must be 0, 7, 14 or 21 (fF)")

        self.write_field('7fF', 1 if feedback_capacitance_fF in [7, 21] else 0)
        self.write_field('14fF', 1 if feedback_capacitance_fF in [14, 21] else 0)

    def get_feedback_capacitance(self):
        total_ff = 0
        total_ff += 7 if self.read_field('7fF') else 0
        total_ff += 14 if self.read_field('14fF') else 0

    ##############################################################################
    # Serialiser Control                                                         #
    ##############################################################################
    # There are 20 serialisers in the ASIC, however, these are organised into 10 #
    # distinct control blocks, each of which has two associated serialisers. For #
    # most settings, these are shared between the pair. However, some settings,  #
    # such as CMLEn1/2 and Pre1/2_Tweak are differentiated by driver number.     #
    #                                                                            #
    # The access functions using 'channel' as an input are using this to mean an #
    # ASIC channel number. Many functions simply write to all serialisers, which #
    # means no channel is required. Some use 'serialiser_number', which is the   #
    # number of the control block, 1-10. Related registers have been named with  #
    # fields that start 'SerN_' where 'N' is the control block number.           #
    ##############################################################################

    # This map relates ASIC output channel numbers to a tuple of serialiser number
    # (aka control block number) 1-10, and the driver number 1 or 2.
    _block_drv_channel_map = {
        0   :   (1, 2),
        1   :   (1, 1),
        2   :   (2, 1),
        3   :   (2, 2),
        4   :   (3, 2),
        5   :   (3, 1),
        6   :   (4, 1),
        7   :   (4, 2),
        8   :   (5, 2),
        9   :   (5, 1),
        10  :   (6, 1),
        11  :   (6, 2),
        12  :   (7, 2),
        13  :   (7, 1),
        14  :   (8, 1),
        15  :   (8, 2),
        16  :   (9, 2),
        17  :   (9, 1),
        18  :   (10, 1),
        19  :   (10, 2),
    }

    def get_serialiserblk_from_channel(self, channel):
        # Get the serialiser control block number and driver number associated with
        # a given ASIC output channel.
        block_num, driver_num = self._block_drv_channel_map[channel]

        self._logger.debug('Channel {} decoded to serialiser control block {} driver {}'.format(
            channel, block_num, driver_num))

        return (block_num, driver_num)

    def _init_serialisers(self):
        # Configure serialiser control blocks so that they have settings that
        # have been determined during the tuning process. Ideally this should
        # be called after an ASIC reset.

        # Set optimal settings
        for serialiser_number in range(1,11):
            self.write_field('Ser{}_EnableCCP'.format(serialiser_number), 0b1)
            self.write_field('Ser{}_EnableCCPInitial'.format(serialiser_number), 0b1)
            self.write_field('Ser{}_LowPriorityCCP'.format(serialiser_number), 0b1)
            self.write_field('Ser{}_StrictAlignmentFlagEn'.format(serialiser_number), 0b1)
            self.write_field('Ser{}_PatternControl'.format(serialiser_number), 0b000)
            self.write_field('Ser{}_CCPCount'.format(serialiser_number), 0b000)
            self.write_field('Ser{}_BypassScramble'.format(serialiser_number), 0b0)
            self.write_field('Ser{}_CMLEn1'.format(serialiser_number), 0b0)
            self.write_field('Ser{}_CMLEn2'.format(serialiser_number), 0b0)
            self.write_field('Ser{}_DLLConfig'.format(serialiser_number), 0b000)
            self.write_field('Ser{}_DLLPhaseConfig'.format(serialiser_number), 0b0)

    def set_ser_enable_CML_drivers(self, enable):
        # Set the CML driver enable for all channels
        for serialiser_number in range(1,11):
            self._set_serialiser_driver_cml_en(serialiser_number, 1, enable)    # Driver 1
            self._set_serialiser_driver_cml_en(serialiser_number, 2, enable)    # Driver 2

    def set_all_serialiser_pattern(self, pattern):
        # Set the pattern control field for all serialisers
        for serialiser_number in range(1,11):
            self.write_field('Ser{}_PatternControl'.format(serialiser_number), pattern)

    def get_all_serialiser_pattern(self, direct=False):
        # Get the pattern control field for the first serialiser control block, assuming that
        # this will be the same for all blocks.
        return self.get_channel_serialiser_pattern(0)

    def set_all_serialiser_bit_scramble(self, scramble_en):
        # Set the bit scramble enable (Aurora) for all seriailisers. Note that the bit
        # disables the scrambler, hence logic inversion.
        scramble_bit = 0 if scramble_en else 1
        for serialiser_number in range(1,11):
            self.write_field('Ser{}_BypassScramble'.format(serialiser_number), scramble_bit)

    def get_all_serialiser_bit_scramble(self):
        # Will return True if ALL serialisers have the scramble enabled, and False if
        # ANY serialiser config has scrambling disabled.
        for serialiser_number in range(1,11):
            current_scramble_en = self.read_field('Ser{}_BypassScramble'.format(serialiser_number))
            if not current_scramble_en:
                return False

        return True

    def set_channel_serialiser_pattern(self, channel, pattern):
        # Selectively set the output pattern for the serialiser associated with an ASIC
        # output channel. Note that this will affect the other channel on the same control
        # block.

        serialiser_number, driver_number = self.get_serialiserblk_from_channel(channel)
        self.write_field('Ser{}_PatternControl'.format(serialiser_number), pattern)

    def get_channel_serialiser_pattern(self, channel):
        # Selectively get the output pattern for the serialiser associated with an ASIC
        # output channel.

        serialiser_number, driver_number = self.get_serialiserblk_from_channel(channel)
        self.read_field('Ser{}_PatternControl'.format(serialiser_number))

    def set_channel_serialiser_cml_en(self, channel, enable):
        # Set the serialiser CML enable state for the driver associated with an ASIC channel

        serialiser_number, driver_number = self.get_serialiserblk_from_channel(channel)
        self._set_serialiser_driver_cml_en(serialiser_number, driver_number, enable)

        self._logger.info('Serialiser for channel {} CML logic enabled: {}'.format(channel, enable))

    def get_channel_serialiser_cml_en(self, channel):
        # Get the serialiser CML enable state for the driver associated with an ASIC channel

        serialiser_number, driver_number = self.get_serialiserblk_from_channel(channel)
        return self._get_serialiser_driver_cml_en(serialiser_number, driver_number)

    def _set_serialiser_driver_cml_en(self, serialiser_number, driver, enable):
        # Set the CML enable for a given driver number (1 or 2) of a seriliser (1-10).
        self.write_field('Ser{}_CmlEn{}'.format(serialiser_number, driver), 1 if enable else 0)

    def _get_serialiser_driver_cml_en(self, serialiser_number, driver, enable):
        # Get the CML enable for a given driver number (1 or 2) of a seriliser (1-10).
        self.read_field('Ser{}_CmlEn{}'.format(serialiser_number, driver))

    def set_all_serialiser_DLL_Config(self, DLL_Config):
        if not DLL_Config in range(0, 8):
            raise ValueError('DLL Config value must be in range 0-7')

        self._logger.info("Setting dll config to {}".format(DLL_Config))

        for serialiser_number in range(1, 11):
            self.write_field('Ser{}_DLLConfig'.format(serialiser_number), DLL_Config)

    def set_all_serialiser_DLL_phase_invert(self, DLL_Phase_Config=True):
        # True means inverted phase from nominal
        bit_value = {True: 0b0, False: 0b1}[DLL_Phase_Config]

        self._logger.info("Setting dll phase config to {}".format(bit_value))

        for serialiser_number in range(1, 11):
            self.write_field('Ser{}_DLLPhaseConfig'.format(serialiser_number), bit_value)

    def set_global_serialiser_mode(self, mode):
        if isinstance(mode, int):       # Using bits
            mode_bits = mode & 0b11
        elif isinstance(mode, str):     # Using mode name
            mode_bits = self._serialiser_mode_names[mode]

        # Set serialiser global mode for both serialiser 1 and 2
        self.write_field('GL_SerMode2_EN', mode_bits)
        self.write_field('GL_SerMode1_EN', mode_bits)

    def get_global_serialiser_mode(self, bits_only=False, direct=False):
        # Return the currently set mode. If bits_only is True, will send
        # the bit encoding rather than the name.

        # Assume that modes are the same, and only read SERMode1xG
        mode = self.read_field('GL_SerMode1_EN')

        if bits_only:
            return mode
        else:
            for name, mode_bits in self._serialiser_mode_names.items():
                if mode_bits == mode:
                    return name

    def Set_DiamondDefault_Registers(self):
        #Set default negative range
        #self.set_register_bit(0,0b01000000)
        self.write_field('Range', 1)

        #14fF, 0000 slew rate
        self.set_all_ramp_bias(0b0000)

        #self.clear_register_bit(0,0b00000100)
        self.write_field('7Ff', 0)
        #self.clear_register_bit(0,0b00100000)
        self.write_field('Ipre', 0)

        #self.write_register(12,6)
        self.write_field('PRE_RST_OFF', 6)
        #self.write_register(14,20)
        self.write_field('CDS_RST_OFF', 20)
        #self.write_register(9,0b10001111)
        self.write_field('TDCPLLBias_ChargePump', 0b1000)
        self.write_field('TDCPLLBias_Regulator', 0b1111)
        #self.write_register(17,174)
        self.write_field('SAMPLE_H_ON', 174)
        #self.write_register(21,190)
        self.write_field('TDC_OUT_ENB_ON', 190)
        #self.write_register(18,197)
        self.write_field('SAMPLE_H_OFF', 197)

        self._logger.info("Finished setting registers")

    def ser_enter_reset(self):
        self.write_field('GL_SerAnaRstB_CONT', 0)
        self.write_field('GL_SerDigRstB_CONT', 0)
        self.write_field('GL_SerPLL_CONT', 0)

    def ser_exit_reset(self):
        self.write_field('GL_SerAnaRstB_CONT', 1)
        self.write_field('GL_SerDigRstB_CONT', 1)
        self.write_field('GL_SerPLL_CONT', 1)

    def enter_bonding_mode(self):
        self.set_global_serialiser_mode("bonding")

    def enter_data_mode(self):
        self.set_global_serialiser_mode("data")

# TODO also work out how to add serialiser stuff....

