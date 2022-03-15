import time

# asic_spi.py
provides = ['set_global_mode_copy',
'vcal_noise_test_new',
'test_VCAL_large_range_20220225_copy',
'test_VCAL_large_range_TDC_20220225_copy',
'test_VCAL_capacitance_slewRate_20220303_copy']

def set_global_mode_copy():
    asic = get_context('asic')
    asic.enter_global_mode()
    print("Set global mode complete")


def vcal_noise_test_new(local_vcal=False, sector_samples=50, all_sectors=False, vcal_values=[0.2, 0.5, 1.0]):
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

def test_VCAL_large_range_20220225_copy():
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

def test_VCAL_large_range_TDC_20220225_copy():
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


def test_VCAL_capacitance_slewRate_20220303_copy():
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