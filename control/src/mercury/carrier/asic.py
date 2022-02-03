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

        command = start_register | REGISTER_READ_TRANSACTION

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

    def get_enabled(self):
        return True if self.gpio_nrst.get_value() == 0 else False

    def disable(self):
        self.gpio_nrst.set_value(0)

    def set_sync(self, value):
        self.gpio_sync.set_value(value)

    def get_sync(self):
        return self.gpio_sync.get_value()

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
