import time


# asic_spi.py
provides = ['spi_read_reg',
'spi_write_reg',
'spi_read_burst',
'set_global_mode',
'sequence_2',
'change_to_external_bias', 
'reset_safe_time',
'asic_reset',
'read_test_pattern',
'write_test_pattern',
'write_test_pattern2']

REGISTER_WRITE_TRANSACTION = 0X00
REGISTER_READ_TRANSACTION = 0X80
REGISTER_ADDRESS_MASK = 0b01111111

ASIC_CURRENT_PAGE = 0   # Assume page 0 on reset

def spi_set_page(page=0):
    mercury_carrier = get_context('carrier')

    # Do not interact if page is already correct
    #if ASIC_CURRENT_PAGE != page:
    # Read
    command = 0x00 | REGISTER_READ_TRANSACTION
    transfer_buffer = [command, 0x00]
    config_value = mercury_carrier.asic_spidev.transfer(transfer_buffer)[1]

    # Modify
    page_set_value = (config_value & 0b11111110) | (page & 0b1)

    # Write
    command = 0x00 | REGISTER_WRITE_TRANSACTION
    transfer_buffer = [command, page_set_value]
    mercury_carrier.asic_spidev.transfer(transfer_buffer)

    ASIC_CURRENT_PAGE = page
    print("Page changed to {}".format(page))


def spi_read_reg(register="0"):
    register = int(str(register), 0)
    _spi_read_reg(register)

def _spi_read_reg(register=0):
    mercury_carrier = get_context('carrier')

    command = (register & REGISTER_ADDRESS_MASK) | REGISTER_READ_TRANSACTION
    # spi_set_page(page)

    transfer_buffer = [command]
    transfer_buffer.append(0x00)
    
    readback = mercury_carrier.asic_spidev.transfer(transfer_buffer)

    print("Read {} bytes from address {} as {}".format(1, hex(register), [hex(x) for x in readback]))

    return readback

def spi_write_reg(register="0", value="0"):
    register = int(str(register), 0)
    value = int(str(value), 0)
    _spi_write_reg(register, value)

def _spi_write_reg(register=0, value=0):
    mercury_carrier = get_context('carrier')
    asic = get_context('asic')

    command = (register & REGISTER_ADDRESS_MASK) | REGISTER_WRITE_TRANSACTION
    # spi_set_page(page)

    transfer_buffer = [command]
    transfer_buffer.append(value)
    
    readback = mercury_carrier.asic_spidev.transfer(transfer_buffer)
    # readback = asic.transfer(transfer_buffer)

    print("Wrote {} bytes starting at address {}: {}".format(1, hex(register), hex(value)))

def spi_read_burst(start_register="0", num_bytes=1):
    start_register = int(str(start_register), 0)
    _spi_read_burst(start_register, num_bytes)

def _spi_read_burst(start_register=0, num_bytes=1):
    mercury_carrier = get_context('carrier')
    start_register = int(str(start_register), 0)

    command = (start_register & REGISTER_ADDRESS_MASK) | REGISTER_READ_TRANSACTION
    # spi_set_page(page)

    transfer_buffer = [command]
    for i in range(0, num_bytes):
        transfer_buffer.append(0x00)
    
    readback = mercury_carrier.asic_spidev.transfer(transfer_buffer)

    print("Read {} bytes from address {} as {}".format(num_bytes, hex(start_register), [hex(x) for x in readback]))

    return readback

def _spi_write_burst(start_register, num_bytes, values):
    mercury_carrier = get_context('carrier')
    start_register = int(str(start_register), 0)

    command = (start_register & REGISTER_ADDRESS_MASK) | REGISTER_WRITE_TRANSACTION
    # spi_set_page(page)

    transfer_buffer = [command]
    for i in range(0, num_bytes):
        transfer_buffer.append(values[i])
    
    mercury_carrier.asic_spidev.transfer(transfer_buffer)

    print("Wrote {} bytes to address {}".format(num_bytes, hex(start_register)))

def asic_reset():
    mercury_carrier = get_context('carrier')
    mercury_carrier.set_asic_rst(True)
    time.sleep(0.1)
    mercury_carrier.set_asic_rst(False)
    time.sleep(0.1)
    print("ASIC reset")

def set_global_mode():
    mercury_carrier = get_context('carrier')
    # Use internal sync
    mercury_carrier.set_sync_sel_aux(False)

    mercury_carrier._gpiod_sync.set_value(0)

    asic_reset()
    time.sleep(1.0)

    _spi_write_reg(0x01, 0x7F)

    _spi_write_reg(0x02, 0x63)

    mercury_carrier._gpiod_sync.set_value(1)

    _spi_write_reg(0x03, 0x08)

    _spi_write_reg(0x03, 0x09)

    _spi_write_reg(0x03, 0x0D)

    _spi_write_reg(0x03, 0x0F)

    _spi_write_reg(0x03, 0x1F)

    _spi_write_reg(0x03, 0x3F)

    _spi_write_reg(0x04, 0x01)

    _spi_write_reg(0x04, 0x03)

    _spi_write_reg(0x03, 0x7F)

    _spi_write_reg(0x00, 0x54)

    _spi_write_reg(36, 0x04)
    _spi_write_reg(37, 0x04)
    _spi_write_reg(38, 0x04)
    _spi_write_reg(39, 0x04)
    _spi_write_reg(40, 0x04)
    _spi_write_reg(41, 0x04)
    _spi_write_reg(42, 0x04)
    _spi_write_reg(43, 0x04)
    _spi_write_reg(44, 0x04)
    _spi_write_reg(45, 0x04)

def sequence_2():
    mercury_carrier = get_context('carrier')
    mercury_carrier._gpiod_sync.set_value(0)

    # asic_reset()
    # time.sleep(1)

    _spi_write_reg(0x03, 0x08)
    _spi_write_reg(36, 0x04)
    _spi_write_reg(37, 0x04)
    _spi_write_reg(38, 0x04)
    _spi_write_reg(39, 0x04)
    _spi_write_reg(40, 0x04)
    _spi_write_reg(41, 0x04)
    _spi_write_reg(42, 0x04)
    _spi_write_reg(43, 0x04)
    _spi_write_reg(44, 0x04)
    _spi_write_reg(45, 0x04)

def change_to_external_bias():
    mercury_carrier = get_context('carrier')

    asic_reset()
    time.sleep(1)

    _spi_write_reg(0x00, 0xD0)
    _spi_write_reg(0x00, 0xD1)  # Select page 2
    _spi_write_reg(0x02, 0x00)  # Register 130

def reset_safe_time():
    for delay_time in [x * 0.001 for x in range(1, 20)]:
        asic_reset()
        time.sleep(delay_time)
        _spi_write_reg(0x00, 0xD0)
        readback = _spi_read_reg(0x00)[1]
        if readback == 0xD0:
            print("RW Success, delay time {}".format(delay_time))
            return

    print("No stable time found")

def read_test_pattern():
    # Run global enable first

    _spi_read_reg(0x00)

    _spi_write_reg(0x07, 0x02)
    _spi_write_reg(0x07, 0x82)
    time.sleep(0.001)

    # Put test shift register into shift mode
    _spi_write_reg(0x07, 0x81)

    # Read the test shift register
    _spi_read_burst(127, 480)

def write_test_pattern():
    _spi_write_reg(0x07, 0x01)

    values_out = [x for x in range(0, 480)]

    _spi_write_burst(127, 480, values_out)

    # Test reg to write mode and select image sector 0
    _spi_write_reg(0x07, 0x03)


def write_test_pattern2():
    _spi_write_reg(0x07, 0x01)

    values_out = [0xFF for x in range(0, 480)]

    _spi_write_burst(127, 480, values_out)

    # Test reg to write mode and select image sector 0
    _spi_write_reg(0x07, 0x03)