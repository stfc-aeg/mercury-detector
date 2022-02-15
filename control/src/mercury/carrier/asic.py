import time
import logging
from odin_devices.spi_device import SPIDevice

REGISTER_WRITE_TRANSACTION = 0X00
REGISTER_READ_TRANSACTION = 0X80
REGISTER_ADDRESS_MASK = 0b01111111

class Asic():

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

    def enable(self):
        self.gpio_nrst.set_value(1)
        self.reset_page()    # Page is now default value

        # Read into local copies of serialiser config
        for i in range(0, 11):
            self._read_serialiser_config(i)

        self._logger.info('ASIC enabled')

    def get_enabled(self):
        return True if self.gpio_nrst.get_value() == 0 else False

    def disable(self):
        self.gpio_nrst.set_value(0)
        self._logger.info('ASIC disabled')

    def set_sync(self, is_en):
        pin_state = 1 if (is_en) else 0         # High is GPIO 1
        self.gpio_sync.set_value(pin_state)
        self._logger.info('ASIC SYNC set: {}'.format(is_en))

    def get_sync(self):
        return True if self.gpio_sync.get_value() == 0 else False

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
        print("ASIC reset complete")

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