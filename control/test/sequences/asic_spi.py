import time

# asic_spi.py
provides = ['spi_read_reg',
'spi_write_reg',
'spi_read_burst',
'set_global_mode',
# 'sequence_2',
'change_to_external_bias', 
'reset_safe_time',
'asic_reset',
'read_test_pattern',
'write_test_pattern',
'write_test_pattern2',
'tdc_enable_local_vcal',
# 'paged_register_test',
# 'shift_register_test',
'lower_serialiser_bias',
# 'test_12bit_output',
'calibration_set_firstpixel',
'vcal_noise_test',
'read_all_sector_gradient',
'all_sector_cal_capture',
'set_all_ram_bias',
'set_clock_config',
'test_meta_20220211_TDC_frequency',
'test_VCAL_large_range_20220225',
'test_VCAL_large_range_TDC_20220225',
'printdir',
'test_VCAL_capacitance_slewRate_20220303',
'test_VCAL_single_pixel_20220307','test_VCAL_bias_20220308',
'test_VCAL_recordLowCurrent_20220308',
'test_VCAL_capacitance_20220311',
'test_VCAL_14fF_slewRate_20220308',
'test_VCAL_14fF_Ipre_20220311',
'test_VCAL_14fF_TDC_20220311',
'test_VCAL_14fF_SinglePix_20220311',
'serialiser_global_change',
'test_VCAL_14fF_SinglePix_2patterns_range_globalBias_20220314']

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

    # Force ASIC to 'forget' cached values that now may not be valid
    asic._reset_local_states()
    for i in range(1, 11):
        asic._read_serialiser_config(i)

    print("Wrote {} bytes starting at address {}: {}".format(1, hex(register), hex(value)))

def spi_read_burst(start_register="0", num_bytes=1):
    asic = get_context('asic')
    
    # Sanitise input
    start_register = int(str(start_register), 0)

    readback = asic.burst_read(start_register, num_bytes)[1:]

    print("Read {} bytes from address {} as {}".format(num_bytes, hex(start_register), [hex(x) for x in readback]))

def test_12bit_output():
    asic = get_context('asic')
    print([hex(x) for x in asic.convert_8bit_12bit([0xaa,0xbb,0xcc])])

def asic_reset():
    asic = get_context('asic')
    asic.reset()
    print("ASIC reset")

def set_global_mode():
    asic = get_context('asic')
    asic.enter_global_mode()
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
            
            readout_12bit = asic.read_test_pattern(sector)
            readout_samples.append(readout_12bit)
            if printout:
                print("Test pattern 12bit: {}".format(readout_12bit))

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

def tdc_enable_local_vcal(local_vcal_en=True):
    asic = get_context('asic')
    asic.set_tdc_local_vcal(local_vcal_en)
    print("TDC local VCAL enabled: {}".format(local_vcal_en))

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
    elif pattern == 3:
        calibration_x[0] = 0b10000000
        calibration_y[0] = 0b10000000
    elif pattern ==4:
        calibration_x[9] = 0b00000001
        calibration_y[0] = 0b10000000
    elif pattern == 5:
        calibration_x[0] = 0b10000000
        calibration_y[9] = 0b00000001
    elif pattern == 6:
        calibration_x[9] = 0b00000001
        calibration_y[9] = 0b00000001
    elif pattern == 7:
        calibration_x[9] = 0b00000011
        calibration_y[9] = 0b00000001
    elif pattern == 8:
        calibration_x[9] = 0b00000011
        calibration_y[9] = 0b00000011
   


    calibration_pattern = calibration_y + calibration_x
    print("Calibrating with pattern {}: {}".format(pattern, calibration_pattern))

    # Burst write to the calibration register
    asic.burst_write(126, calibration_pattern)

def vcal_noise_test(local_vcal=False, sector_samples=50, all_sectors=False, vcal_values=[0.2, 0.5, 1.0]):
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
    filename = "read-tests/" + title + "_{:04d}{:02d}{:02d}_{:02d}{:02d}{:02d}".format(time_now.tm_year, time_now.tm_mon, time_now.tm_mday, time_now.tm_hour, time_now.tm_min, time_now.tm_sec, int((time.time() % 1) * 1000)) + '.csv'
    print("Will write to {}".format(filename))
    time.sleep(3)

    with open(filename, 'w') as file:
        for vcal_setting in vcal_values:
            # Set the new VCAL voltage
            mercury_carrier.set_vcal_in(vcal_setting)

            # Read out the results from select sectors
            for sector in sector_array:
                print("Begin reading samples for sector {} with VCAL: {}".format(sector, vcal_setting))
                time.sleep(0.5)

                # Sample the sector 50 times
                samples_out = read_test_pattern(sector=sector, num_samples=sector_samples, store=False, printout=False)

                # Write a line for each sample, with sample number, sector and vcal setting
                for i in range(0,len(samples_out)):
                    sample = samples_out[i]
                    first_columns = [vcal_setting, sector, i]
                    file.write(','.join([str(x) for x in (first_columns + sample)]))
                    file.write('\n')

    print("VCAL samples gathered and stored in {}".format(filename))

    return filename

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

def set_all_ram_bias(bias=0b1000):
    asic = get_context('asic')
    asic.set_all_ramp_bias(bias)
    print("Set all ramp bias to {}".format(bias))

def set_clock_config(config=205):
    carrier = get_context('carrier')

    if config == 205:
        carrier.set_clk_config('Si5344-RevD-merc0000-Registers2.txt')
    elif config in [210, 215, 220, 225]:
        carrier.set_clk_config('Si5344-RevD-merc0000-FastTDC-Registers-' + str(config) + 'M.txt')
    elif config == 243:
        carrier.set_clk_config('Si5344-RevD-merc0000-243MHz-Registers.txt')
    else:
        raise Exception("No matching config")
    carrier.set_clk_config(config)

def test_meta_20220211_TDC_frequency():
    # 20220211 Test to determine the effect of changing ramp bias
    asic = get_context('asic')

    timenow = time.localtime()
    print("Begin test {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    # Perform global mode before running this test, includes reset
    set_global_mode()

    # Set the feedback capacitence to 7fF
    asic.clear_register_bit(0, 0b00010000)
    asic.set_register_bit(  0, 0b00001000)

    # Create reference sample of slow slew ramping, limited sectors
    asic.set_all_ramp_bias(0b1000)        # Slow ramp slew (default)
    set_clock_config(205)           # Use default 205Mhz TDC clock
    test1 = vcal_noise_test(local_vcal=False,
                            sector_samples=1000,
                            all_sectors=False,
                            vcal_values=[0, 0.5, 1.0])
    timenow = time.localtime()
    print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    # Increase resolution and test decreased range
    asic.set_all_ramp_bias(0b1111)        # Fast ramp slew
    set_clock_config(205)           # Use default 205Mhz TDC clock
    test2 = vcal_noise_test(local_vcal=False,
                            sector_samples=1000,
                            all_sectors=False,
                            vcal_values=[0, 0.5, 1.0])
    timenow = time.localtime()    
    print("Test 2 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    # Increase measured resolution and look at high/low linearity
    asic.set_all_ramp_bias(0b1111)        # Fast ramp slew
    set_clock_config(225)           # Use 225Mhz TDC clock
    test3 = vcal_noise_test(local_vcal=False,
                            sector_samples=1000,
                            all_sectors=False,
                            vcal_values=[0.0, 0.1, 0.2, 0.3, 0.4,
                                         1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()
    print("Test 3 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    # Measure uniformity across array of noise, resolution, range & speed. All sectors.
    asic.set_all_ram_bias(0b1111)        # Fast ramp slew
    set_clock_config(225)           # Use 225Mhz TDC clock
    test4 = vcal_noise_test(local_vcal=False,
                            sector_samples=1000,
                            all_sectors=True,
                            vcal_values=[0, 0.5, 1.0])
    timenow = time.localtime()
    print("Test 4 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    # Check effect of CDS reset, with reset on full time, still at 225 and 0b1111. Only one VCAL necessary
    asic.set_all_ram_bias(0b1111)        # Fast ramp slew
    set_clock_config(225)           # Use 225Mhz TDC clock
    asic.write_register(13, 12)     # Set CDS reset on time
    asic.write_register(14, 0)     # Set CDS reset off time
    test5 = vcal_noise_test(local_vcal=False,
                            sector_samples=1000,
                            all_sectors=True,
                            vcal_values=[0, 0.5, 1.0])
    timenow = time.localtime()
    print("Test 5 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    print("!!! All tests complete:")
    print("\t1) Reference test stored in {}".format(test1))
    print("\t2) Resolution test stored in {}".format(test2))
    print("\t3) Linearity test stored in {}".format(test3))
    print("\t4) Uniformity test stored in {}".format(test4))
    print("\t5) CDS RST test stored in {}".format(test5))

def test_VCAL_large_range_20220225():
    #testing the effect of changing the negative range

    asic = get_context('asic')

    timenow = time.localtime()
    print("Begin test {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    # Perform global mode before running this test, includes reset
    set_global_mode()

    # Set the feedback capacitence to 7fF
    asic.clear_register_bit(0, 0b00010000)
    asic.set_register_bit(  0, 0b00001000)

    #Set default slew rate
    asic.set_all_ramp_bias(0b1000) # Slow ramp slew (default)
    set_clock_config(205)  # Use default 205 MHz TDC clock

    #Set default negative range
    asic.set_register_bit(0,0b01000000)

    # Create reference sample of -10keV range, limited sectors
    test1 = vcal_noise_test(local_vcal=False,
                            sector_samples=5000,
                            all_sectors=False,
                            vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()
    print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    # Set negative range to -20keV
    asic.clear_register_bit(0,0b01000000)              
    test2 = vcal_noise_test(local_vcal=False,
                            sector_samples=5000,
                            all_sectors=False,
                            vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()    
    print("Test 2 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))
    
    print("!!! All tests complete:")
    print("\t1) Reference test stored in {}".format(test1))
    print("\t2) Resolution test stored in {}".format(test2))

def test_VCAL_large_range_TDC_20220225():
    #testing the effect of changing the negative range

    asic = get_context('asic')

    timenow = time.localtime()
    print("Begin test {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    # Perform global mode before running this test, includes reset
    set_global_mode()

    # Set the feedback capacitence to 7fF
    asic.clear_register_bit(0, 0b00010000)
    asic.set_register_bit(  0, 0b00001000)

    #Set default slew rate
    asic.set_all_ramp_bias(0b1000) # Slow ramp slew (default)
    set_clock_config(205)  # Use default 205 MHz TDC clock

    #Set default negative range
    asic.set_register_bit(0,0b01000000)

    # Create reference sample of -10keV range, limited sectors
    test1 = vcal_noise_test(local_vcal=True,
                            sector_samples=1000,
                            all_sectors=False,
                            vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()
    print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    # Set negative range to -20keV
    asic.clear_register_bit(0,0b01000000)              
    test2 = vcal_noise_test(local_vcal=True,
                            sector_samples=1000,
                            all_sectors=False,
                            vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()    
    print("Test 2 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))
    
    print("!!! All tests complete:")
    print("\t1) Reference test stored in {}".format(test1))
    print("\t2) Resolution test stored in {}".format(test2))

def printdir():
    asic = get_context('asic')
    carrier = get_context('carrier')

    print(dir(asic))
    print(dir(carrier))

def test_VCAL_capacitance_slewRate_20220303():
    #testing the effect of changing the negative range

    asic = get_context('asic')

    timenow = time.localtime()
    print("Begin test {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    # Perform global mode before running this test, includes reset
    set_global_mode()

    # Set the feedback capacitence to 7fF
    asic.clear_register_bit(0, 0b00010000)
    asic.set_register_bit(  0, 0b00001000)

    #Set default slew rate
    asic.set_all_ramp_bias(0b1000) # Slow ramp slew (default)
    set_clock_config(205)  # Use default 205 MHz TDC clock

    #Set default negative range
    asic.set_register_bit(0,0b01000000)

    # Create reference sample of 7fF, 1000 slew rate
    test1 = vcal_noise_test(local_vcal=False,
                            sector_samples=5000,
                            all_sectors=False,
                            vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()
    print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    #7fF, 0000 slew rate
    asic.set_all_ramp_bias(0b0000) #Slowest ramp slew       
    test2 = vcal_noise_test(local_vcal=False,
                            sector_samples=5000,
                            all_sectors=False,
                            vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()    
    print("Test 2 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))
    
    #7fF, 1111 slew rate
    asic.set_all_ramp_bias(0b1111) #fastest ramp slew
    test3 = vcal_noise_test(local_vcal=False,
                            sector_samples=5000,
                            all_sectors=False,
                            vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()    
    print("Test 3 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    #14fF, 1000 slew rate
    asic.set_all_ramp_bias(0b1000) #default slew rate
    #Setting 14fF capacitor
    asic.set_register_bit(0, 0b00010000)
    asic.clear_register_bit(  0, 0b00001000)
    test4 = vcal_noise_test(local_vcal=False,
                            sector_samples=5000,
                            all_sectors=False,
                            vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    print("Test 4 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    #21fF, 1000 slew rate
    asic.set_register_bit(  0, 0b00001000)
    test5 = vcal_noise_test(local_vcal=False,
                            sector_samples=5000,
                            all_sectors=False,
                            vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    print("Test 5 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))


    print("!!! All tests complete:")
    print("\t1) 7pF, 1000 slew rate test stored in {}".format(test1))
    print("\t2) 7pF, 0000 slew rate test stored in {}".format(test2))
    print("\t3) 7pF, 1111 slew rate test stored in {}".format(test3))
    print("\t4) 14pF, 1000 slew rate test stored in {}".format(test4))
    print("\t5) 21pF, 1000 slew rate test stored in {}".format(test5))

def test_VCAL_single_pixel_20220307():
    #testing the effect of changing the negative range

    asic = get_context('asic')

    timenow = time.localtime()
    print("Begin test {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    # Perform global mode before running this test, includes reset
    set_global_mode()

    # Set the feedback capacitence to 7fF
    asic.clear_register_bit(0, 0b00010000)
    asic.set_register_bit(  0, 0b00001000)

    #Set default slew rate
    asic.set_all_ramp_bias(0b1000) # Slow ramp slew (default)
    set_clock_config(205)  # Use default 205 MHz TDC clock

    #Set default negative range
    asic.set_register_bit(0,0b01000000)

    #setting pattern to be top left pixel
    calibration_set_firstpixel(pattern=3)
    # Create reference sample of -10keV range, limited sectors
    test1 = vcal_noise_test(local_vcal=False,
                            sector_samples=5000,
                            all_sectors=False,
                            vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()
    print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    #setting pattern to be top right pixel
    calibration_set_firstpixel(pattern=4)
    # Create reference sample of -10keV range, limited sectors
    test2 = vcal_noise_test(local_vcal=False,
                            sector_samples=5000,
                            all_sectors=False,
                            vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()
    print("Test 2 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    #setting pattern to be bottom left pixel
    calibration_set_firstpixel(pattern=5)
    # Create reference sample of -10keV range, limited sectors
    test3 = vcal_noise_test(local_vcal=False,
                            sector_samples=5000,
                            all_sectors=False,
                            vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()
    print("Test 3 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    #setting pattern to be bottom right pixel
    calibration_set_firstpixel(pattern=6)
    # Create reference sample of -10keV range, limited sectors
    test4 = vcal_noise_test(local_vcal=False,
                            sector_samples=5000,
                            all_sectors=False,
                            vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()
    print("Test 4 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))
    
    print("!!! All tests complete:")
    print("\t1) Top left test stored in {}".format(test1))
    print("\t2) Top right test stored in {}".format(test2))
    print("\t3) Bottom left test stored in {}".format(test3))
    print("\t4) Bottom right test stored in {}".format(test4))

def test_VCAL_bias_20220308():
    #testing the effect of changing the negative range

    asic = get_context('asic')

    timenow = time.localtime()
    print("Begin test {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    # Perform global mode before running this test, includes reset
    set_global_mode()

    # Set the feedback capacitence to 7fF
    asic.clear_register_bit(0, 0b00010000)
    asic.set_register_bit(  0, 0b00001000)

    #Set default slew rate
    asic.set_all_ramp_bias(0b1000) # Slow ramp slew (default)
    set_clock_config(205)  # Use default 205 MHz TDC clock

    #Set default negative range
    asic.set_register_bit(0,0b01000000)

    #setting pattern to be top left pixel
    #taking reference sample
    test1 = vcal_noise_test(local_vcal=False,
                            sector_samples=5000,
                            all_sectors=False,
                            vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()
    print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    #setting lowest current
    asic.write_register(130,0b00000000)
    # Create reference sample of -10keV range, limited sectors
    test2 = vcal_noise_test(local_vcal=False,
                            sector_samples=5000,
                            all_sectors=False,
                            vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()
    print("Test 2 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    #setting highest current
    asic.write_register(130,0b11111111)
    # Create reference sample of -10keV range, limited sectors
    test3 = vcal_noise_test(local_vcal=False,
                            sector_samples=5000,
                            all_sectors=False,
                            vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()
    print("Test 3 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    print("!!! All tests complete:")
    print("\t1) Default current test stored in {}".format(test1))
    print("\t2) Lowest current test stored in {}".format(test2))
    print("\t3) Highest current test stored in {}".format(test3))

def test_VCAL_recordLowCurrent_20220308():
    #testing the effect of changing the negative range

    asic = get_context('asic')

    timenow = time.localtime()
    print("Begin test {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    # Perform global mode before running this test, includes reset
    set_global_mode()

    # Set the feedback capacitence to 7fF
    asic.clear_register_bit(0, 0b00010000)
    asic.set_register_bit(  0, 0b00001000)

    #Set default slew rate
    asic.set_all_ramp_bias(0b1000) # Slow ramp slew (default)
    set_clock_config(205)  # Use default 205 MHz TDC clock

    #Set default negative range
    asic.set_register_bit(0,0b01000000)

    #setting lowest current
    asic.write_register(130,0b00000000)
    # Create reference sample of -10keV range, limited sectors
    test1 = vcal_noise_test(local_vcal=False,
                            sector_samples=500,
                            all_sectors=False,
                            vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()
    print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))


    print("!!! All tests complete:")
    print("\t1) Default current test stored in {}".format(test1))
    

def test_VCAL_capacitance_20220311():
    #testing the effect of changing the negative range

    asic = get_context('asic')

    timenow = time.localtime()
    print("Begin test {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    # Perform global mode before running this test, includes reset
    set_global_mode()

    #Set default slew rate
    asic.set_all_ramp_bias(0b1000) # Slow ramp slew (default)
    set_clock_config(205)  # Use default 205 MHz TDC clock

    #Set default negative range
    asic.set_register_bit(0,0b01000000)

    #14fF, 1000 slew rate
    #Setting 14fF capacitor
    asic.set_register_bit(0, 0b00010000)
    asic.clear_register_bit(  0, 0b00001000)
    test4 = vcal_noise_test(local_vcal=False,
                            sector_samples=5000,
                            all_sectors=False,
                            vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    print("Test 4 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    #21fF, 1000 slew rate
    asic.set_register_bit(  0, 0b00001000)
    test5 = vcal_noise_test(local_vcal=False,
                            sector_samples=5000,
                            all_sectors=False,
                            vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    print("Test 5 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))


    print("!!! All tests complete:")
    print("\t4) 14pF, 1000 slew rate test stored in {}".format(test4))
    print("\t5) 21pF, 1000 slew rate test stored in {}".format(test5))


def test_VCAL_14fF_slewRate_20220308():
    #testing the effect of changing the negative range

    asic = get_context('asic')

    timenow = time.localtime()
    print("Begin test {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    # Perform global mode before running this test, includes reset
    set_global_mode()


    # Set the feedback capacitence to 14fF
    asic.clear_register_bit(0, 0b00001000)
    asic.set_register_bit(  0, 0b00010000)

    #Set default slew rate
    set_clock_config(205)  # Use default 205 MHz TDC clock

    #Set default negative range
    asic.set_register_bit(0,0b01000000)

    #14fF, 0000 slew rate
    asic.set_all_ramp_bias(0b0000) #Slowest ramp slew       
    test2 = vcal_noise_test(local_vcal=False,
                            sector_samples=5000,
                            all_sectors=False,
                            vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()    
    print("Test 2 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))
    
    #7fF, 1111 slew rate
    asic.set_all_ramp_bias(0b1111) #fastest ramp slew
    test3 = vcal_noise_test(local_vcal=False,
                            sector_samples=5000,
                            all_sectors=False,
                            vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()    
    print("Test 3 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    print("!!! All tests complete:")
    print("\t2) 14fF, 0000 slew rate test stored in {}".format(test2))
    print("\t3) 14fF, 1111 slew rate test stored in {}".format(test3))

def test_VCAL_14fF_Ipre_20220311():
    #testing the effect of changing the negative range

    asic = get_context('asic')

    timenow = time.localtime()
    print("Begin test {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    # Perform global mode before running this test, includes reset
    set_global_mode()

    # Set the feedback capacitence to 14fF
    asic.clear_register_bit(0, 0b00001000)
    asic.set_register_bit(  0, 0b00010000)

    #Set default slew rate
    set_clock_config(205)  # Use default 205 MHz TDC clock

    #Set default negative range
    asic.set_register_bit(0,0b01000000)

    #14fF, 0000 slew rate
    asic.set_all_ramp_bias(0b1000) #Default ramp slew
    #setting double the Ibias
    asic.set_register_bit(0,0b00100000)

    test2 = vcal_noise_test(local_vcal=False,
                            sector_samples=5000,
                            all_sectors=False,
                            vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()    
    print("Test 2 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))
    

    print("!!! All tests complete:")
    print("\t2) 14fF, 1000, Ipre=1 slew rate test stored in {}".format(test2))

def test_VCAL_14fF_SinglePix_20220311():
    #testing the effect of changing the negative range

    asic = get_context('asic')

    timenow = time.localtime()
    print("Begin test {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    # Perform global mode before running this test, includes reset
    set_global_mode()

    # Set the feedback capacitence to 14fF
    asic.clear_register_bit(0, 0b00001000)
    asic.set_register_bit(  0, 0b00010000)

    #Set default slew rate
    set_clock_config(205)  # Use default 205 MHz TDC clock

    #Set default negative range
    asic.set_register_bit(0,0b01000000)

    #14fF, 0000 slew rate
    asic.set_all_ramp_bias(0b1000) #Default ramp slew
    #setting top left pixel pattern
    calibration_set_firstpixel(pattern=6)

    test2 = vcal_noise_test(local_vcal=False,
                            sector_samples=5000,
                            all_sectors=False,
                            vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()    
    print("Test 2 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))
    

    print("!!! All tests complete:")
    print("\t2) 14fF, 1000, top left pixel test stored in {}".format(test2))

def test_VCAL_14fF_TDC_20220311():
    #testing the effect of changing the negative range

    asic = get_context('asic')

    timenow = time.localtime()
    print("Begin test {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    # Perform global mode before running this test, includes reset
    set_global_mode()

    # Set the feedback capacitence to 14fF
    asic.clear_register_bit(0, 0b00001000)
    asic.set_register_bit(  0, 0b00010000)

    #Set default slew rate
    set_clock_config(205)  # Use default 205 MHz TDC clock

    #Set default negative range
    asic.set_register_bit(0,0b01000000)

    #14fF, 0000 slew rate
    asic.set_all_ramp_bias(0b1000) #Default ramp slew
    #setting top left pixel pattern

    test2 = vcal_noise_test(local_vcal=True,
                            sector_samples=5000,
                            all_sectors=False,
                            vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()    
    print("Test 2 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))
    

    print("!!! All tests complete:")
    print("\t2) 14fF, 1000, TDC test stored in {}".format(test2))


def serialiser_global_change(register=0,data=0):
    if register > 5:
        print ("Serialiser register byte does not exist: maximum value of 5 (index 0)")
        return
    for i in range(10):
        register_address= 66 + (6*i) + register
        data = data
        asic.write_register(register_adress,data)
        registers_strings = ["A","B","C","D","E","F"]
    print("changed all 10 segment controls for register part {0} to {1}".format(registers_strings[register],str(data)))


def test_VCAL_14fF_SinglePix_2patterns_range_globalBias_20220314():
    #testing the effect of changing the negative range

    asic = get_context('asic')

    timenow = time.localtime()
    print("Begin test {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    # Perform global mode before running this test, includes reset
    set_global_mode()

    # Set the feedback capacitence to 14fF
    asic.clear_register_bit(0, 0b00001000)
    asic.set_register_bit(  0, 0b00010000)

    #Set default slew rate
    set_clock_config(205)  # Use default 205 MHz TDC clock

    #Set default negative range
    asic.set_register_bit(0,0b01000000)

    #14fF, 0000 slew rate
    asic.set_all_ramp_bias(0b1000) #Default ramp slew

    #setting lowest current
    asic.write_register(130,0b00000000)
    # Create reference sample of -10keV range, limited sectors
    test1= vcal_noise_test(local_vcal=False,
                            sector_samples=5000,
                            all_sectors=False,
                            vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()
    print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    #setting highest current
    asic.write_register(130,0b11111111)
    # Create reference sample of -10keV range, limited sectors
    test2 = vcal_noise_test(local_vcal=False,
                            sector_samples=5000,
                            all_sectors=False,
                            vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()
    print("Test 2 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    #resetting to default current
    asic.write_register(130,0b11110000)
    #Set -20 keV negative range
    asic.clear_register_bit(0,0b01000000)

    # Create  sample of -20keV range, limited sectors
    test3 = vcal_noise_test(local_vcal=False,
                            sector_samples=5000,
                            all_sectors=False,
                            vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()
    print("Test 3 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    #setting -10 keV range
    asic.set_register_bit(0,0b01000000)
    #setting top left pixel pattern
    calibration_set_firstpixel(pattern=7)

    test4 = vcal_noise_test(local_vcal=False,
                            sector_samples=5000,
                            all_sectors=False,
                            vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()    
    print("Test 4 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    #setting top left pixel pattern
    calibration_set_firstpixel(pattern=8)

    test5 = vcal_noise_test(local_vcal=False,
                            sector_samples=5000,
                            all_sectors=False,
                            vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()    
    print("Test 5 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))
    

    print("!!! All tests complete:")
    print("\t1) 14fF, 1000, lowGlobalCurrent test stored in {}".format(test1))
    print("\t2) 14fF, 1000, highGlobalCurrent test stored in {}".format(test2))
    print("\t3) 14fF, 1000, -20 keV test stored in {}".format(test3))
    print("\t4) 14fF, 1000, pattern 7 test stored in {}".format(test4))
    print("\t5) 14fF, 1000, pattern 8 test stored in {}".format(test5))