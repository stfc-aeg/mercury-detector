import time
import logging
from odin_devices.spi_device import SPIDevice

REGISTER_WRITE_TRANSACTION = 0X00
REGISTER_READ_TRANSACTION = 0X80
REGISTER_ADDRESS_MASK = 0b01111111

class Asic():

    # Maps MERCURY logical channel to (serialiser block, driver number)
    _block_drv_channel_map = {  0   :   (1, 2),
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

    def __init__(self, gpio_nrst, gpio_sync_sel, gpio_sync, bus=2, device=0, hz=2000000):

        # super(Asic, self).__init__(bus, device, hz)
        self.spi = SPIDevice(bus=bus, device=device, hz=hz)
        self.spi.set_mode(0)
        self.spi.set_cs_active_high(False)

        self._logger = logging.getLogger('ASIC')

        self.page = 1

        self.gpio_nrst = gpio_nrst
        self.gpio_sync_sel = gpio_sync_sel
        self.gpio_sync = gpio_sync

        # Set up store for local serialiser configs
        self._serialiser_block_configs = []
        for i in range(1, 11):
            new_serialiser_block = SerialiserBlockConfig()
            self._serialiser_block_configs.append(new_serialiser_block)
        self._logger.info("ASIC init complete")

    """ SPI Register Access Functions """
    def reset_page(self):
        self.page = 1

    def set_page(self, page):
        page_bit = {1: 0b0, 2: 0b1}[page]

        if self.page != page:
            # Read
            command = 0x00 | REGISTER_READ_TRANSACTION
            transfer_buffer = [command, 0x00]
            config_value = self.spi.transfer(transfer_buffer)[1]

            # Modify
            page_set_value = (config_value & 0b11111110) | (page_bit & 0b1)

            # Write
            command = 0x00 | REGISTER_WRITE_TRANSACTION
            transfer_buffer = [command, page_set_value]
            self.spi.transfer(transfer_buffer)

            self.page = page

    def read_register(self, address):

        if (address > 127):     # Page 2
            self.set_page(2)
        else:                   # Page 1
            self.set_page(1)
        address = address & REGISTER_ADDRESS_MASK

        command = address | REGISTER_READ_TRANSACTION

        transfer_buffer = [command]
        transfer_buffer.append(0x00)

        readback = self.spi.transfer(transfer_buffer)

        self._logger.debug("Register {} read as {}".format(address, readback))

        return readback
    
    def write_register(self, address, value):

        if (address > 127):     # Page 2
            self.set_page(2)
        else:                   # Page 1
            self.set_page(1)
        address = address & REGISTER_ADDRESS_MASK

        command = address | REGISTER_WRITE_TRANSACTION

        transfer_buffer = [command]
        transfer_buffer.append(value)

        self.spi.transfer(transfer_buffer)

        self._logger.debug("Register {} written with {}".format(address, value))

    def burst_read(self, start_register, num_bytes):

        if (start_register > 127):  # Page 2
            self.set_page(2)
        else:                       # Page 1
            self.set_page(1)
        start_register = start_register & REGISTER_ADDRESS_MASK

        command = start_register | REGISTER_READ_TRANSACTION

        transfer_buffer = [command]
        for i in range(0, num_bytes):
            transfer_buffer.append(0x00)

        readback = self.spi.transfer(transfer_buffer)

        return readback

    def burst_write(self, start_register, values):

        if (start_register > 127):  # Page 2
            self.set_page(2)
        else:                       # Page 1
            self.set_page(1)
        start_register = start_register & REGISTER_ADDRESS_MASK

        command = start_register | REGISTER_WRITE_TRANSACTION

        transfer_buffer = [command]
        for i in range(0, len(values)):
            transfer_buffer.append(values[i])

        self.spi.transfer(transfer_buffer)

    def set_register_bit(self, register, bit):
        original = self.read_register(register)[1]
        self.write_register(register, original | bit)

    def clear_register_bit(self, register, bit):
        original = self.read_register(register)[1]
        self.write_register(register, original & (~bit))

    @staticmethod
    def convert_8bit_12bit(values_8bit):
        val1 = 0
        val2 = 0
        val_index = 0
        output_array = []

        for i in range(len(values_8bit)):
            if val_index == 0:      # First byte
                val1 = values_8bit[i]
            elif val_index == 1:    # Second byte
                val2 = values_8bit[i]
            else:                   # Third byte
                val3 = values_8bit[i]

                output_12bit_1 = (val1 << 4) + ((val2 & 0xF0) >> 4)
                output_12bit_2 = ((val2 & 0x0F) << 8) + val3
                output_array.append(output_12bit_1)
                output_array.append(output_12bit_2)

            if val_index == 2:
                val_index = 0
            else:
                val_index += 1

        return output_array

    """ Pin and power control """
    def enable(self):
        self.gpio_nrst.set_value(1)
        self.reset_page()    # Page is now default value

        # Read into local copies of serialiser config
        for i in range(0, 11):
            self._read_serialiser_config(i)

        self._logger.info('ASIC enabled')

    def get_enabled(self):
        return True if self.gpio_nrst.get_value() == 1 else False

    def disable(self):
        self.gpio_nrst.set_value(0)
        self._logger.info('ASIC disabled')

    def set_sync(self, is_en):
        pin_state = 1 if (is_en) else 0         # High is GPIO 1
        self.gpio_sync.set_value(pin_state)
        self._logger.info('ASIC SYNC set: {}'.format(is_en))

    def get_sync(self):
        enabled = True if self.gpio_sync.get_value() == 1 else False
        return enabled

    def set_sync_source_aux(self, is_aux):
        pin_state = 0 if (is_aux) else 1
        self.gpio_sync_sel.set_value(pin_state)
        source = 'aux' if is_aux else 'zynq'
        self._logger.info('ASIC SYNC configured to come from {}'.format(source))

    def get_sync_source_aux(self):
        return True if self.gpio_sync_sel.get_value() == 0 else False

    def reset(self):
        # Reset the ASIC using the nRST and SYNC control lines
        self._logger.warning("Resetting ASIC...")
        self.disable()          # nReset low
        self.set_sync(False)    # Sync also low
        time.sleep(0.1)

        self.enable()
        self.reset_page()   # Page is now default value
        time.sleep(0.1)     # Allow ASIC time to come out of reset
        self._logger.debug("ASIC reset complete")

    """ Device function control """
    def enter_global_mode(self):
        # Ensure that the sync is under zynq control
        self.set_sync_source_aux(False)

        # Set the sync line low before reset
        self.set_sync(False)

        # Reset the ASIC
        self.reset()

        # Enable global control of readout, digital signals, analogue signals,
        # analogue bias enable, TDC oscillator enable, serialiser PLL enable,
        # TDC PLL enable, VCAL select, serialiser mode, serialiser analogue/
        # digital reset.
        self.write_register(0x01, 0x7F)
        self.write_register(0x02, 0x63)

        # Set the sync active
        self.set_sync(True)

        # Enter further settings post sync raise
        self.write_register(0x03, 0x08)     # Enable pixel bias
        self.write_register(0x03, 0x09)     # Enable TDC PLLs
        self.write_register(0x03, 0x0D)     # Enable TDC oscillators
        self.write_register(0x03, 0x0F)     # Enable Serialiser PLLs
        self.write_register(0x03, 0x1F)     # Enable pixel analogue signals
        self.write_register(0x03, 0x3F)     # Enable pixel digital signals

        # Remove serialiser digital and analogue reset
        self.write_register(0x04, 0x01)
        self.write_register(0x04, 0x03)

        # Enable readout
        self.write_register(0x03, 0x7F)

        # Enable calibrate
        self.write_register(0x00, 0x54)

        self._logger.info("Global mode configured")

    def read_test_pattern(self, sector):
        # Read out a test pattern from a specificed sector using the 480
        # byte test shift register (320 12-bit pixels). The result is
        # returned as an array of 320 12-bit pixel values.

        # Set test register read mode with trigger 0
        self.write_register(0x07, 0x02 | (sector<<2))

        # Keep test register read mode with trigger 1
        self.write_register(0x07, 0x82 | (sector<<2))
        time.sleep(0.001)

        # Put test shift register into shift mode
        self.write_register(0x07, 0x81 | (sector<<2))

        # Read the test shift register
        readout = self.burst_read(127, 480)

        # Convert to 12-bit data and remove first byte (not part of read)        
        readout_12bit = Asic.convert_8bit_12bit(readout[1:])

        return readout_12bit

    def set_tdc_local_vcal(self, local_vcal_en=True):
        # Enable to use VCAL as the direct comparator input rather than the
        # default.
        bitval = {True: 0b1, False: 0b0}[local_vcal_en]
        self.set_register_bit(0x04, bitval << 6)

    def set_all_ramp_bias(self, bias):
        # Set the ramp bias value for all 40 ramps in the ASIC.
        if not bias in range(0, 16):     # 4-bit field
            raise ValueError("bias must be in range 0-15")

        for register in range(46, 66):
            self.write_register(register, (bias << 4) | bias)   # Set for both nibbles

        self._logger.info("Set ramp bias for all 40 ASIC ramps to {}".format(bias))

    """ Serialiser Functions """
    def get_serialiserblk_from_channel(channel):
        block_num, driver_num = self._block_drv_channel_map[channel]
        serialiser = self._serialiser_block_configs[block_num]

        self._logger.debug('Channel {} decoded to serialiser {} driver {}'.format(
            channel, block_num, driver_num))

        return (serialiser, block_num, driver_num)

    def _write_serialiser_config(self, serialiser_block_num):
        ser_index = serialiser_block_num - 1    # Datasheet numbering starts at 1
        base_address = 66 + (ser_index) * 6

        # Pack the structure values into the local array and export
        config_block = self._serialiser_block_configs[ser_index].pack()

        # Write to the ASIC
        self.burst_write(base_address, config_block)

        # Assume the write succeeded and re-import the config bytes
        self._serialiser_block_configs[ser_index].unpack(config_block)

    def _read_serialiser_config(self, serialiser_block_num):
        ser_index = serialiser_block_num - 1    # Datasheet numbering starts at 1
        base_address = 66 + (ser_index) * 6

        config_block = self.burst_read(base_address, 6)[1:]

        self._serialiser_block_configs[ser_index].unpack(config_block)

    def set_serialiser_patternControl(self, serialiser_block_num, pattern, holdoff=False):
        # LEGACY, DO NOT USE
        ser_index = serialiser_block_num - 1    # Datasheet numbering starts at 1
        self._serialiser_block_configs[ser_index].patternControl = pattern

        if not holdoff:
            self._write_serialiser_config(serialiser_block_num)

    def set_ser_enable_CML_drivers(self, enable, holdoff=False):
        # Sets the CML driver enable for all channels

        for serialiser_number in range(1,11):
            serialiser = self._serialiser_block_configs[serialiser_number-1]
            serialiser.set_cml_driver_enable(1, enable)
            serialiser.set_cml_driver_enable(2, enable)
            if not holdoff:
                self._write_serialiser_config(serialiser_number)

    def set_channel_serialiser_pattern(self, channel, pattern, holdoff=False):
        # Selectively set the output pattern for the serialiser associated with 
        # a channel. Note that this will affect the other channel on the same
        # control block

        if not pattern in range(0, 8):
            return ValueError('Pattern setting must be 0-7')

        serialiser_block, ser_num, drv_num = self.get_serialiserblk_from_channel(channel)

        serialiser_block.patternControl = pattern

        if not holdoff:
            self._write_serialiser_config(ser_num)

        self._logger.info('Serialiser for channel {} pattern set to {}'.format(channel, pattern))

    def set_channel_serialiser_cml_en(self, channel, enable):
        # Selectively enable or disable CML drivers enable for a given channel

        serialiser_block, ser_num, drv_num = self.get_serialiserblk_from_channel(channel)

        serialiser_block.set_cml_driver_enable(enable)

        # Force write to ASIC (no holdoff available)
        self._write_serialiser_config(ser_num)

        self._logger.info('Serialiser for channel {} CML logic enabled: {}'.format(channel, enable))

    def get_channel_serialiser_cml_en(self, channel):
        serialiser_block, ser_num, drv_num = self.get_serialiserblk_from_channel(channel)
        return serialiser_block.get_cml_driver_enable()

    def set_all_serialiser_DLL_Config(self, DLL_Config):
        if not DLL_Config in range(0, 8):
            raise ValueError('DLL Config value must be in range 0-7')

        self._logger.info("Setting dll config to {}".format(DLL_Config))
        for ser_index, ser_block in enumerate(self._serialiser_block_configs):
            ser_block.dll_config = DLL_Config
            self._write_serialiser_config(ser_index+1)

    def set_all_serialiser_DLL_phase_invert(self, DLL_Phase_Config=True):
        # True means inverted phase from nominal
        bit_value = {True: 0b0, False: 0b1}[DLL_Phase_Config]

        self._logger.info("Setting dll phase config to {}".format(bit_value))
        for ser_index, ser_block in enumerate(self._serialiser_block_configs):
            ser_block.dll_phase_config = bit_value
            self._write_serialiser_config(ser_index+1)


class SerialiserBlockConfig():

    def __init__(self):
        # Simply do not return valid data if read before unpack()
        # self.data_invalid = True
        
        self._local_state_bytes = bytearray(6)

    def __repr__(self):
        outstr= ""
        try:
            outstr += "Enable CCP: {}".format(bool(self.enable_ccp))
            outstr += ", Pattern Control: {}".format(self.patternControl)
            outstr += ", Bypass Scramble: {}".format(bool(self.bypassScramble))
            outstr += ", CML EN: {}".format(bool(self.cml_en))
        except AttributeError as e:
            outstr = "No read (failed on with {})".format(e)

        return outstr

    def unpack(self, bytes_in):
        # Unpack the 6-byte field supplied as read out into config items
        bytes_in = bytearray(bytes_in)
        self._local_state_bytes = bytes_in

        # Reverse byte order so that fields spanning bytes are aligned, and
        # pack into a single value for easier slicing
        combined_fields = int.from_bytes(bytes_in, byteorder='little')

        # Slice config items
        self.enable_ccp = (combined_fields & (0b1 << 46)) >> 46
        self.patternControl = (combined_fields & (0b111 << 38)) >> 38
        self.bypassScramble = (combined_fields & (0b1 << 42)) >> 42
        self.cml_en = (combined_fields & (0b11 << 28)) >> 28
        self.dll_config = (combined_fields & (0b111 << 30)) >> 30
        self.dll_phase_config = (combined_fields & (0b1 << 33)) >> 33

    def pack(self):
        # Pack config items into combined fields, without overwriting any
        # currently unsupported fields

        try:
            # Fill integer representation using current local register copy
            combined_fields = int.from_bytes(self._local_state_bytes, byteorder='little')

            # Mask off bits where supported fields exist (manually)
            #               |7     |0   |15    |8   |23    |16  |31    |24  |39    |32  |47    |40
            mask_bytes = [0b11111111, 0b11111111, 0b11111111, 0b00001111, 0b00111100, 0b10111010]
            combined_fields &= int.from_bytes(bytearray(mask_bytes), byteorder='little')

            # Overwrite supported fields
            combined_fields |= (self.enable_ccp & 0b1) << 46
            combined_fields |= (self.patternControl & 0b111) << 38
            combined_fields |= (self.bypassScramble & 0b1) << 42
            combined_fields |= (self.cml_en & 0b11) << 28
            combined_fields |= (self.dll_config & 0b111) << 30
            combined_fields |= (self.dll_phase_config & 0b1) << 33

        except AttributeError as e:
            raise AttributeError("Invalid pack; config has not been read: {} (structure: {})".format(e, self.__repr__()))

        # Repack into 6-byte little-endian config register set
        bytes_out = int.to_bytes(combined_fields, byteorder='little', length=6)

        return bytes_out

    def set_cml_driver_enable(self, driver, enabled):
        bitmask =   {1: 0b10, 2: 0b01}[driver]
        bitval =    ({1: 0b01, 2:0b10}[driver]) if enabled else 0

        old_cmlen = self.cml_en
        self.cml_en = (self.cml_en & bitmask) | bitval

    def get_cml_driver_enable(self, driver):
        bitmask =   {1: 0b01, 2:0b10}[driver]
        return (bitmask & self.cml_en) > 0