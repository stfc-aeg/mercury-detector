import time
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

        self.page = 1

        self.gpio_nrst = gpio_nrst
        self.gpio_sync_sel = gpio_sync_sel
        self.gpio_sync = gpio_sync

        # Set up store for local serialiser configs
        self._serialiser_block_configs = []
        for i in range(1, 11):
            new_serialiser_block = SerialiserBlockConfig()
            self._serialiser_block_configs.append(new_serialiser_block)

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

    def get_enabled(self):
        return True if self.gpio_nrst.get_value() == 0 else False

    def disable(self):
        self.gpio_nrst.set_value(0)

    def set_sync(self, is_en):
        # pin_state = 0 if (is_en) else 1         # High is GPIO 0
        pin_state = 1 if (is_en) else 0         # High is GPIO 1
        self.gpio_sync.set_value(pin_state)

    def get_sync(self):
        return True if self.gpio_sync.get_value() == 0 else False

    def set_sync_source_aux(self, is_aux):
        pin_state = 0 if (is_aux) else 1
        self.gpio_sync_sel.set_value(pin_state)

    def get_set_sync_aux(self):
        return True if self.gpio_sync_sel.get_value() == 0 else False

    def reset(self):
        print("Resetting ASIC...")
        self.disable()
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
        ser_index = serialiser_block_num - 1    # Datasheet numbering starts at 1
        self._serialiser_block_configs[ser_index].patternControl = pattern
        if not holdoff:
            self._write_serialiser_config(serialiser_block_num)


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
        self.dll_phase_config = (combined_fields & (0b1 << 33)) >> 33

    def pack(self):
        # Pack config items into combined fields, without overwriting any
        # currently unsupported fields

        try:
            # Fill integer representation using current local register copy
            combined_fields = int.from_bytes(self._local_state_bytes, byteorder='little')

            # Mask off bits where supported fields exist (manually)
            #               |7     |0   |15    |8   |23    |16  |31    |24  |39    |32  |47    |40
            mask_bytes = [0b11111111, 0b11111111, 0b11111111, 0b11001111, 0b00111111, 0b10111010]
            combined_fields &= int.from_bytes(bytearray(mask_bytes), byteorder='little')

            # Overwrite supported fields
            combined_fields |= (self.enable_ccp & 0b1) << 46
            combined_fields |= (self.patternControl & 0b111) << 38
            combined_fields |= (self.bypassScramble & 0b1) << 42
            combined_fields |= (self.cml_en & 0b11) << 28
            combined_fields |= (self.dll_phase_config & 0b1) << 33

        except AttributeError as e:
            raise AttributeError("Invalid pack; config has not been read: {} (structure: {})".format(e, self.__repr__()))

        # Repack into 6-byte little-endian config register set
        bytes_out = int.to_bytes(combined_fields, byteorder='little', length=6)

        return bytes_out
