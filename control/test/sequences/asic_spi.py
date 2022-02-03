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
'write_test_pattern2',
'tdc_enable_local_vcal',
'read_test_pattern_edit',
'paged_register_test',
'shift_register_test']

REGISTER_WRITE_TRANSACTION = 0X00
REGISTER_READ_TRANSACTION = 0X80
REGISTER_ADDRESS_MASK = 0b01111111

ASIC_CURRENT_PAGE = 0   # Assume page 0 on reset

def spi_read_reg(register="0"):
    asic = get_context('asic')

    # Sanitise input
    register = int(str(register), 0)

    readback = asic.read_register(register)

    print("Read {} bytes from address {} as {}".format(1, hex(register), [hex(x) for x in readback]))

def spi_write_reg(register="0", value="0"):
    asic = get_context('asic')

    # Sanitise input
    register = int(str(register), 0)
    value = int(str(value), 0)

    asic.write_register(register, value)

    print("Wrote {} bytes starting at address {}: {}".format(1, hex(register), hex(value)))

def spi_read_burst(start_register="0", num_bytes=1):
    asic = get_context('asic')
    
    # Sanitise input
    start_register = int(str(start_register), 0)

    readback = asic.burst_read(start_register, num_bytes)

    print("Read {} bytes from address {} as {}".format(num_bytes, hex(start_register), [hex(x) for x in readback]))

def asic_reset():
    asic = get_context('asic')
    asic.reset()
    print("ASIC reset")

def set_global_mode():
    mercury_carrier = get_context('carrier')
    asic = get_context('asic')

    # Use internal sync
    mercury_carrier.set_sync_sel_aux(False)

    mercury_carrier._gpiod_sync.set_value(1)

    asic.reset()

    asic.write_register(0x01, 0x7F)

    asic.write_register(0x02, 0x63)

    mercury_carrier._gpiod_sync.set_value(0)

    asic.write_register(0x03, 0x08)

    asic.write_register(0x03, 0x09)

    asic.write_register(0x03, 0x0D)

    asic.write_register(0x03, 0x0F)

    asic.write_register(0x03, 0x1F)

    asic.write_register(0x03, 0x3F)

    asic.write_register(0x04, 0x01)

    asic.write_register(0x04, 0x03)

    asic.write_register(0x03, 0x7F)

    asic.write_register(0x00, 0x54)

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
    asic = get_context('asic')
    mercury_carrier._gpiod_sync.set_value(0)

    # asic_reset()
    # time.sleep(1)

    asic.write_register(0x03, 0x08)
    asic.write_register(36, 0x04)
    asic.write_register(37, 0x04)
    asic.write_register(38, 0x04)
    asic.write_register(39, 0x04)
    asic.write_register(40, 0x04)
    asic.write_register(41, 0x04)
    asic.write_register(42, 0x04)
    asic.write_register(43, 0x04)
    asic.write_register(44, 0x04)
    asic.write_register(45, 0x04)

def change_to_external_bias():
    mercury_carrier = get_context('carrier')
    asic = get_context('asic')

    asic.reset()

    time.sleep(1)

    asic.write_register(0x00, 0xD0)
    asic.write_register(0x00, 0xD1)  # Select page 2
    asic.write_register(0x02, 0x00)  # Register 130

def reset_safe_time():
    asic = get_context('asic')

    for delay_time in [x * 0.001 for x in range(1, 20)]:
        asic.disable()
        time.sleep(0.1)     # Hold in reset
        asic.enable()

        time.sleep(delay_time)
        
        asic.write_register(0x00, 0xD0)
        readback = asic.read_register(0x00)[1]

        if readback == 0xD0:
            print("RW Success, delay time {}".format(delay_time))
            return

    print("No stable time found")

def paged_register_test():
    asic = get_context('asic')

    asic.reset()
    
    # Read default values for same register in page 1 and 2
    for test_reg, default_value in [(0x02, 0x00), (130, 0xF0)]:
        register_contents = asic.read_register(test_reg)[1]
        if(register_contents != default_value):
            raise Exception('Register {} read incorrectly')
    
    # Write 0b11000000 to register 130
    asic.write_register(130, 0b11000000)

    # Check that register 2 still reads 0x00
    if(asic.read_register(0x02)[1] != 0x00):
        raise Exception('Register 2 overwritten by write to 130')

    print("Page register read test successful")

def shift_register_test():
    asic = get_context('asic')

    asic.reset()

    # Check the default value is found in the calibration shift reg
    # initial_values = asic.burst_read(126, 20)
    initial_values = asic.burst_read(126, 20)
    if (initial_values[1+0] != 0x55 or initial_values[1+10] != 0xAA):
        raise Exception('Initial values did not match expectation: ', initial_values)

    # Write to the calibration shift register
    test_values = range(0,20)
    # asic.burst_write(126, test_values)
    asic.burst_write(126, test_values)

    # Check that the values read back match those written
    # test_values_out = asic.burst_read(126, 20)
    test_values_out = asic.burst_read(126, 20)
    if test_values_out[1:] != list(test_values):
        raise Exception('Calibration shift register write/read failed: ', test_values_out[1:], list(test_values))

    print("Shift register test successful")

def read_test_pattern(sector=0):
    asic = get_context('asic')
    # Run global enable first

    # _spi_read_reg(0x00)

    # Set test register read mode with trigger 0
    asic.write_register(0x07, 0x02 | (sector<<2))

    # Keep test register read mode with trigger 1
    asic.write_register(0x07, 0x82 | (sector<<2))
    time.sleep(0.001)

    # Put test shift register into shift mode
    asic.write_register(0x07, 0x81 | (sector<<2))

    # Read the test shift register
    readout = asic.burst_read(127, 480)
    
    print("Test pattern: {}".format(readout))

def read_test_pattern_edit(sector=0):
    asic = get_context('asic')
    # Run global enable first

    # _spi_read_reg(0x00)

    # Set test register read mode with trigger 0
    asic.write_register(0x07, 0x02 | (sector<<2))

    # Keep test register read mode with trigger 1
    asic.write_register(0x07, 0x82 | (sector<<2))

    # Set trigger 0
    asic.write_register(0x07, 0x02 | (sector<<2))

    time.sleep(0.001)

    # Put test shift register into shift mode
    asic.write_register(0x07, 0x01 | (sector<<2))

    # Read the test shift register
    readout = asic.burst_read(127, 480)

    print("Test pattern: {}".format(readout))

def write_test_pattern(sector=0):
    asic = get_context('asic')

    # Set to shift mode with trigger 0
    asic.write_register(0x07, 0x01 | (sector<<2))

    values_out = [x for x in range(0, 480)]

    # Burst write to shift register
    asic.burst_write(127, values_out)

    # Test reg to write mode and select image sector 0
    asic.write_register(0x07, 0x03 | (sector<<2))


def write_test_pattern2(sector=0):
    asic = get_context('asic')

    asic.write_register(0x07, 0x01 | (sector<<2))

    values_out = [0xFF for x in range(0, 480)]

    asic.burst_write(127, values_out)

    # Test reg to write mode and select image sector 0
    asic.write_register(0x07, 0x03 | (sector<<2))


def tdc_enable_local_vcal():
    asic = get_context('asic')

    asic.set_register_bit(0x04, 0b1 << 6)   # Set bit 6

    print("TDC local VCAL enabled")