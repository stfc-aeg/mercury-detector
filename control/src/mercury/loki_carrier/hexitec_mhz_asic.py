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
        self._current_page = None

    def self._set_page(self, page):
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
            self.spi._device.transfer(transfer_buffer)

            self.page = page

    def _read_register(self, address, length=1):
        # Direct ASIC function for reading from a register address, without caching (which
        # will be handled by the register controller). Result is a list of values. Should
        # support burst read.

        if not self._interface_enabled:
            raise ASICInterfaceDisabledError('Cannot read from ASIC')

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

        readback = self.spi.transfer(transfer_buffer)

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
        transfer_buffer.append(value)

        self._device.spi.transfer(transfer_buffer)

        self._logger.debug("Register {} written with {}".format(address, value))

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
        con.add_field('GL_TDC_EN', 'Global / Local TDC Oscillator enable', 3, 2, 1, is_volatile=False)
        con.add_field('GL_SerPLL_EN', 'Global / Local Serialiser PLL enable', 3, 1, 1, is_volatile=False)
        con.add_field('GL_TDC_EN', 'Global / Local TDC PLL enable', 3, 0, 1, is_volatile=False)

        self._REGISTER_NAMES[4] = 'GL_EN2'
        con.add_field('GL_VCALsel_EN', 'Global / Local VCAL enable', 4, 6, 1, is_volatile=False)
        con.add_field('GL_SerMode21_EN', 'Global / Local Serialiser 2 Mode bit 1', 4, 5, 1, is_volatile=False)
        con.add_field('GL_SerMode20_EN', 'Global / Local Serialiser 2 Mode bit 0', 4, 4, 1, is_volatile=False)
        con.add_field('GL_SerMode11_EN', 'Global / Local Serialiser 1 Mode bit 1', 4, 3, 1, is_volatile=False)
        con.add_field('GL_SerMode10_EN', 'Global / Local Serialiser 1 Mode bit 0', 4, 2, 1, is_volatile=False)
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
                'GL_DigSigEn_SEL{}'format(segment),
                'Local Digital Signal Enable (segment {})'.format(segment),
                addr, 7, 1, is_volatile=False)
            )
            con.add_field(
                'GL_AnaSigEn_SEL{}'format(segment),
                'Local Analogue Signal Enable (segment {})'.format(segment),
                addr, 6, 1, is_volatile=False)
            )
            con.add_field(
                'GL_TDCOscEn_SEL{}'format(segment),
                'Local Serialiser TDC Oscillator Enable (segment {})'.format(segment),
                addr, 5, 1, is_volatile=False)
            )
            con.add_field(
                'GL_SerPLLEn_SEL{}'format(segment),
                'Local Serialiser PLL Enable (segment {})'.format(segment),
                addr, 4, 1, is_volatile=False)
            )
            con.add_field(
                'GL_TDCPLLEn_SEL{}'format(segment),
                'Local TDC PLL Enable (segment {})'.format(segment),
                addr, 3, 1, is_volatile=False)
            )
            con.add_field(
                'GL_AnaEn_SEL{}'format(segment),
                'Local Pixel Bias Enable (segment {})'.format(segment),
                addr, 2, 1, is_volatile=False)
            )
            con.add_field(
                'GL_ROE_SEL{}'format(segment),
                'Local Readout Enable (segment {})'.format(segment),
                addr, 1, 1, is_volatile=False)
            )
            con.add_field(
                'GL_SerDigRstB_SEL{}'format(segment),
                'Local VCAL Select (segment {})'.format(segment),
                addr, 0, 1, is_volatile=False)
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
                7, 8, is_volatile=False
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
            patterncon_high = Field(con, 'PatternControl_ms', '', base_addr+5, 0, 1, is_volatile=False)
            patterncon_low = Field(con, 'PatternControl_ls', '', base_addr+4, 7, 2, is_volatile=False)
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
                'Ser{}_CMLEn'.format(serialiser_number),
                'CML En for Serialiser {}'.format(serialiser_number),
                base_addr+3, 5, 2, is_volatile=False
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

