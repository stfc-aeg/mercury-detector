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
'paged_register_test',
'shift_register_test',
'lower_serialiser_bias',
'test_12bit_output',
'calibration_set_firstpixel',
'vcal_noise_test',
'read_all_sector_gradient',
'all_sector_cal_capture']

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

    readback = asic.burst_read(start_register, num_bytes)[1:]

    print("Read {} bytes from address {} as {}".format(num_bytes, hex(start_register), [hex(x) for x in readback]))

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

def test_12bit_output():
    print([hex(x) for x in convert_8bit_12bit([0xaa,0xbb,0xcc])])

def asic_reset():
    asic = get_context('asic')
    asic.reset()
    print("ASIC reset")

def set_global_mode():
    mercury_carrier = get_context('carrier')
    asic = get_context('asic')

    # Use internal sync
    asic.set_sync_source_aux(False)
    # asic.set_sync_source_aux(True)

    print("Sync inactive")
    asic.set_sync(False)
    print("ASIC reset")
    asic.reset()

    asic.write_register(0x01, 0x7F)

    asic.write_register(0x02, 0x63)

    print("Sync active")
    asic.set_sync(True)

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

    # _spi_write_reg(36, 0x04)
    # _spi_write_reg(37, 0x04)
    # _spi_write_reg(38, 0x04)
    # _spi_write_reg(39, 0x04)
    # _spi_write_reg(40, 0x04)
    # _spi_write_reg(41, 0x04)
    # _spi_write_reg(42, 0x04)
    # _spi_write_reg(43, 0x04)
    # _spi_write_reg(44, 0x04)
    # _spi_write_reg(45, 0x04)

    print("Set global mode complete")

def sequence_2():
    mercury_carrier = get_context('carrier')
    asic = get_context('asic')
    mercury_carrier._gpiod_sync.set_value(0)

    asic.reset()
    # time.sleep(1)

    # asic.write_register(0x03, 0x08)

    print("Setting to local control")

    asic.set_register_bit(0x03, 0b00001000)
    asic.set_register_bit(0x03, 0b00000001)
    asic.set_register_bit(0x03, 0b00000100)
    print("Register 3: {}".format(hex(asic.read_register(0x03)[1])))

    for register in range(36, 46):
        print("Setting register {} to 44".format(register))
        time.sleep(10)
        asic.write_register(register, 44)

    # asic.write_register(36, 0x04)
    # asic.write_register(37, 0x04)
    # asic.write_register(38, 0x04)
    # asic.write_register(39, 0x04)
    # asic.write_register(40, 0x04)
    # asic.write_register(41, 0x04)
    # asic.write_register(42, 0x04)
    # asic.write_register(43, 0x04)
    # asic.write_register(44, 0x04)
    # asic.write_register(45, 0x04)

def change_to_external_bias():
    mercury_carrier = get_context('carrier')
    asic = get_context('asic')

    # asic.reset()

    time.sleep(1)

    asic.write_register(130, 0x00)

    print("Selected external ibias resistor")

def reset_safe_time():
    asic = get_context('asic')

    print("Testing SPI W/R for stable post-reset delay")

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

def read_test_pattern(sector=0, num_samples=1, store=False, printout=True):
    asic = get_context('asic')
    # Run global enable first

    readout_samples = []
    time_now = time.gmtime()
    filename = 'read-tests/' + '-'.join( [str(x) for x in [time_now.tm_year, time_now.tm_mon, time_now.tm_mday, time_now.tm_hour, time_now.tm_min, time_now.tm_sec]]) + '.csv'

    if not store:
        filename = '/dev/null'

    with open(filename, 'w') as f:

        for sample_num in range(0, num_samples):
            if printout:
                print("Begin read test shift register sector {}, sample {}".format(sector, sample_num))

            # Set test register read mode with trigger 0
            asic.write_register(0x07, 0x02 | (sector<<2))

            # Keep test register read mode with trigger 1
            asic.write_register(0x07, 0x82 | (sector<<2))
            time.sleep(0.001)

            # Put test shift register into shift mode
            asic.write_register(0x07, 0x81 | (sector<<2))

            # Read the test shift register
            readout = asic.burst_read(127, 480)
            
            # print("Test pattern: {}".format(readout))
            readout_12bit = convert_8bit_12bit(readout[1:])
            readout_samples.append(readout_12bit)
            if printout:
                print("Test pattern 12bit: {}".format(convert_8bit_12bit(readout[1:])))

            f.write(','.join([str(x) for x in readout_12bit]))
            f.write('\n')

    if printout:
        print("Write out to {} complete".format(filename))

    return readout_samples

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

def lower_serialiser_bias():
    asic = get_context('asic')

    print("Lowering serialiser biases")

    for register in range(131, 141):
        print("Setting register {} to 00".format(register))
        time.sleep(10)
        asic.write_register(register, 0)

def calibration_set_firstpixel(pattern=0):
    asic = get_context('asic')

    calibration_y = [0]*10
    calibration_x = [0]*10

    if pattern == 0:
        calibration_y [9] = 0b00000010  # Set LSB
        calibration_x [0] = 0b01000000  # Set MSB
    elif pattern == 1:
        calibration_y [9] = 0b00000001  # Set LSB
        calibration_x [0] = 0b10000000  # Set MSB
    elif pattern == 2:
        calibration_y [9] = 0b00000011  # Set LSB
        calibration_x [0] = 0b11000000  # Set MSB


    calibration_pattern = calibration_y + calibration_x
    print("Calibrating with pattern {}: {}".format(pattern, calibration_pattern))

    # Burst write to the calibration register
    asic.burst_write(126, calibration_pattern)

def vcal_noise_test(local_vcal=False, sector_samples=50, all_sectors=False):
    mercury_carrier = get_context('carrier')

    if local_vcal:
        print("Enable TDC local vcal mode")
        tdc_enable_local_vcal()
        title = 'vcal_noise'
    else:
        title = 'calibration_noise'

    if all_sectors:
        sector_array = range(0,20)
    else:
        sector_array = [0, 9, 19]

    time_now = time.gmtime()
    filename = "read-tests/" + title + "_{:04d}{:02d}{:02d}_{:02d}{:02d}".format(time_now.tm_year, time_now.tm_mon, time_now.tm_mday, time_now.tm_hour, time_now.tm_min, time_now.tm_sec) + '.csv'
    print("Will write to {}".format(filename))
    time.sleep(3)

    with open(filename, 'w') as file:
        for vcal_setting in [0.2, 0.5, 1.0]:
            # Set the new VCAL voltage
            mercury_carrier.set_vcal_in(vcal_setting)

            # Read out the results from select sectors
            for sector in sector_array:
                print("Begin reading samples for sector {} with VCAL: {}".format(sector, vcal_setting))

                # Sample the sector 50 times
                samples_out = read_test_pattern(sector=sector, num_samples=sector_samples, store=False, printout=False)

                # Write a line for each sample, with sample number, sector and vcal setting
                for i in range(0,len(samples_out)):
                    sample = samples_out[i]
                    first_columns = [vcal_setting, sector, i]
                    file.write(','.join([str(x) for x in (first_columns + sample)]))
                    file.write('\n')

    print("VCAL samples gathered and stored in {}".format(filename))

def read_all_sector_gradient(SAMPLE_NUM=50):
    mercury_carrier = get_context('carrier')

    # Enable VCAL TDC Input
    # tdc_enable_local_vcal()

    # Set VCAL to 0.8v
    mercury_carrier.set_vcal_in(0.8)

    title = 'all-sector-gradient'

    time_now = time.gmtime()
    filename = "read-tests/" + title + "_{:04d}{:02d}{:02d}_{:02d}{:02d}".format(time_now.tm_year, time_now.tm_mon, time_now.tm_mday, time_now.tm_hour, time_now.tm_min, time_now.tm_sec) + '.csv'
    print("Will write to {}".format(filename))
    time.sleep(3)

    with open(filename, 'w') as file:
        for sector_number in range(0,20):
            print("Begin reading samples for sector {} with VCAL: {}".format(sector_number, 0.8))

            # Sample the sector 50 times
            samples_out = read_test_pattern(sector=sector_number, num_samples=SAMPLE_NUM, store=False, printout=False)

            # Write a line for each sample, with sample number, sector and vcal setting
            for i in range(0,len(samples_out)):
                sample = samples_out[i]
                first_columns = [0.8, sector_number, i]
                file.write(','.join([str(x) for x in (first_columns + sample)]))
                file.write('\n')

def all_sector_cal_capture(vcal_setting=0.8, acceptable_threshold=1000):
    # Wait for 'valid' calibration readouts (only the 'high' version)
    # for each sector before recording a single record for each sector,
    # SIMULATING a full single capture of one calibration frame.
    mercury_carrier = get_context('carrier')

    # Enable VCAL TDC Input
    # tdc_enable_local_vcal()

    # Set VCAL
    mercury_carrier.set_vcal_in(vcal_setting)

    sector_tries = 100

    title = 'all-sector-cal-capture'

    time_now = time.gmtime()
    filename = "read-tests/" + title + "_{:04d}{:02d}{:02d}_{:02d}{:02d}".format(time_now.tm_year, time_now.tm_mon, time_now.tm_mday, time_now.tm_hour, time_now.tm_min, time_now.tm_sec) + '.csv'
    print("Will write to {}".format(filename))
    time.sleep(3)

    with open(filename, 'w') as file:
        for sector_number in range(0,20):
            print("Begin reading samples for sector {} with VCAL: {}".format(sector_number, vcal_setting))

            valid_sample_found = False

            for sector_try_num in range(sector_tries):
                # Sample the sector 1 time
                samples_out = read_test_pattern(sector=sector_number, num_samples=1, store=False, printout=False)

                # Determine if sector is valid
                if any([sample >= acceptable_threshold for sample in samples_out[0]]):
                    # Valid sample, store
                    first_columns = [vcal_setting, sector_number, sector_try_num]

                    # write
                    print("Found a valid sample read for sector {} on try {}".format(sector_number, sector_try_num))
                    file.write(','.join([str(x) for x in (first_columns + samples_out[0])]))
                    file.write('\n')
                    valid_sample_found = True
                    break
                
                time.sleep(0.002)
            
            if not valid_sample_found:
                print("Failed to find a sample set for sector {}, filling with 0".format(sector_number))
                sample_null = [0]*320
                first_columns = [vcal_setting, sector_number, 100]

                file.write(','.join([str(x) for x in (first_columns + sample_null)]))
                file.write('\n')

    print("Wrote to {}".format(filename))