import time

provides = [
    'test_meta_20220211_TDC_frequency',
    'test_VCAL_large_range_20220225',
    'test_VCAL_large_range_TDC_20220225',
    'test_VCAL_capacitance_slewRate_20220303',
    'test_VCAL_single_pixel_20220307',
    'test_VCAL_bias_20220308',
    'test_VCAL_recordLowCurrent_20220308',
    'test_VCAL_capacitance_20220311',
    'test_VCAL_14fF_slewRate_20220308',
    'test_VCAL_14fF_Ipre_20220311',
    'test_VCAL_14fF_SinglePix_20220311',
    'test_VCAL_14fF_TDC_20220311',
    'test_VCAL_14fF_SinglePix_2patterns_range_globalBias_20220314',
    'test_VCAL_14fF_allSectors_20220317',
    'test_VCAL_14fF_LawrenceTests_20220322',
    'test_VCAL_14fF_NoVCAL_Lawrence_tests_20220322',
    'test_VCAL_14fF_NoVCAL_Lawrence_testsbatch2_20220322',
    'test_VCAL_14fF_NoVCAL_Lawrence_testsbatch3_20220323',
    'test_VCAL_14fF_NoVCAL_Lawrence_testsbatch4_slewrate_20220323',
    'test_VCAL_14fF_NoVCAL_Lawrence_testsbatch5_capacitors_20220324',
    'test_VCAL_14fF_NoVCAL_Lawrence_testsbatch6_fullArray_20220324',
    'test_VCAL_14fF_NoVCAL_Lawrence_testsbatch7_fullArray_20220328',
    'test_VCAL_14fF_VCAL_Lawrence_testsbatch8_linearity_20220328',
    'test_VCAL_14fF_VCAL_Lawrence_testsbatch8_linearity_7and21_20220328',
    'test_VCAL_Lawrence_testsbatch9_newSettings_20220331',
    'test_VCAL_Lawrence_testsbatch10_newSettingsIndividual_20220401',
    'test_VCAL_Lawrence_testsbatch11_register18testing_20220404',
    'CdZnTe_D320771_0V_initialTest_currentSettings',
    'CdZnTe_D320771_0V_initialTest_currentSettings_shorter',
    'CdZnTe_D320771_1000V_VCAL_currentSettings',
    'CdZnTe_D320771_0V_initialTest_currentSettings_1000samples',
    'CdZnTe_D320771_0V_initialTest_currentSettings_10000samples',
    'CdZnTe_D320771_0V_initialTest_currentSettings_30000samples',
    'CdZnTe_D320771_0V_initialTest_currentSettings_400000samples_singleSector',
    'CdZnTe_D320771_0V_initialTest_currentSettings_shorter_lowGain',
    'CdZnTe_D320771_0V_initialTest_currentSettings_400000samples_singleSector_lowGain',
    'CdZnTe_D320771_0V_initialTest_currentSettings_1000samples_highGain',
    'CdZnTe_D320771_0V_initialTest_currentSettings_400000samples_singleSector10',
    'set_capacitance',
    'set_slewRate',
    'set_negativeRange',
    'CdZnTe_D320771_0V_initialTest_currentSettings_400000samples_singleSector11_lowGain',
]
requires = [
    'asic_spi',
    'asic_spi_legacy'   # Do not include this in later test files
]

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
    asic.set_all_ramp_bias(0b1111)        # Fast ramp slew
    set_clock_config(225)           # Use 225Mhz TDC clock
    test4 = vcal_noise_test(local_vcal=False,
                            sector_samples=1000,
                            all_sectors=True,
                            vcal_values=[0, 0.5, 1.0])
    timenow = time.localtime()
    print("Test 4 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    # Check effect of CDS reset, with reset on full time, still at 225 and 0b1111. Only one VCAL necessary
    asic.set_all_ramp_bias(0b1111)        # Fast ramp slew
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

def test_VCAL_14fF_allSectors_20220317():
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

    # Create reference sample of -10keV range, limited sectors
    test1= vcal_noise_test(local_vcal=False,
                            sector_samples=5000,
                            all_sectors=True,
                            vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()
    print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))    

    print("!!! All tests complete:")
    print("\t1) All sectors 14 fF test stored in {}".format(test1))


def test_VCAL_14fF_LawrenceTests_20220322():
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

    asic.clear_register_bit(0,0b00100000)
    asic.write_register(12,6)
    asic.write_register(14,20)

    # Create reference sample of -10keV range, limited sectors
    test1= vcal_noise_test(local_vcal=False,
                            sector_samples=5000,
                            all_sectors=False,
                            vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()
    print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))    

    asic.set_register_bit(0,0b00100000)
    asic.write_register(12,6)
    asic.write_register(14,20)

    test2= vcal_noise_test(local_vcal=False,
                            sector_samples=5000,
                            all_sectors=False,
                            vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()
    print("Test 2 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))    

    print("!!! All tests complete:")
    print("\t1) Lawrence test1 stored in {}".format(test1))
    print("\t2) Lawrence test2 stored in {}".format(test2))


def test_VCAL_14fF_NoVCAL_Lawrence_tests_20220322():
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

    asic.clear_register_bit(0,0b00000100)

    print(asic.read_register(0))

    asic.clear_register_bit(0,0b00100000)
    asic.write_register(12,6)
    asic.write_register(14,20)

    # Create reference sample of -10keV range, limited sectors
    test1= vcal_noise_test(local_vcal=False,
                            sector_samples=5000,
                            all_sectors=False,
                            vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()
    print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))    

    asic.set_register_bit(0,0b00100000)
    asic.write_register(12,6)
    asic.write_register(14,20)

    test2= vcal_noise_test(local_vcal=False,
                            sector_samples=5000,
                            all_sectors=False,
                            vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()
    print("Test 2 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))    

    print("!!! All tests complete:")
    print("\t1) Lawrence test1; No VCAL stored in {}".format(test1))
    print("\t2) Lawrence test2; No VCAL stored in {}".format(test2))

def test_VCAL_14fF_NoVCAL_Lawrence_testsbatch2_20220322():
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

    asic.clear_register_bit(0,0b00000100)

    print(asic.read_register(0))

    asic.clear_register_bit(0,0b00100000)
    asic.write_register(12,6)
    asic.write_register(14,20)
    asic.write_register(9,0b10000000)

    # Create reference sample of -10keV range, limited sectors
    test1= vcal_noise_test(local_vcal=False,
                            sector_samples=5000,
                            all_sectors=False,
                            vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()
    print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))    

    asic.write_register(9,0b10001100)

    test2= vcal_noise_test(local_vcal=False,
                            sector_samples=5000,
                            all_sectors=False,
                            vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()
    print("Test 2 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))    

    print("!!! All tests complete:")
    print("\t1) Lawrence batch 2 test1; No VCAL stored in {}".format(test1))
    print("\t2) Lawrence batch 2 test2; No VCAL stored in {}".format(test2))

def test_VCAL_14fF_NoVCAL_Lawrence_testsbatch3_20220323():
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

    asic.clear_register_bit(0,0b00000100)

    print(asic.read_register(0))

    asic.clear_register_bit(0,0b00100000)
    asic.write_register(12,6)
    asic.write_register(14,20)
    asic.write_register(9,0b10001110)

    # Create reference sample of -10keV range, limited sectors
    test1= vcal_noise_test(local_vcal=False,
                            sector_samples=5000,
                            all_sectors=False,
                            vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()
    print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))    

    asic.write_register(9,0b10001111)

    test2= vcal_noise_test(local_vcal=False,
                            sector_samples=5000,
                            all_sectors=False,
                            vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()
    print("Test 2 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))    

    print("!!! All tests complete:")
    print("\t1) Lawrence batch 3 test1; No VCAL stored in {}".format(test1))
    print("\t2) Lawrence batch 3 test2; No VCAL stored in {}".format(test2))

def test_VCAL_14fF_NoVCAL_Lawrence_testsbatch4_slewrate_20220323():
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
    asic.set_all_ramp_bias(0b0010)

    asic.clear_register_bit(0,0b00000100)

    print(asic.read_register(0))

    asic.clear_register_bit(0,0b00100000)
    asic.write_register(12,6)
    asic.write_register(14,20)
    asic.write_register(9,0b10001111)

    # Create reference sample of -10keV range, limited sectors
    test1= vcal_noise_test(local_vcal=False,
                            sector_samples=5000,
                            all_sectors=False,
                            vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()
    print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))    
   

    print("!!! All tests complete:")
    print("\t1) Lawrence batch4 slew rate test; No VCAL stored in {}".format(test1))

def test_VCAL_14fF_NoVCAL_Lawrence_testsbatch5_capacitors_20220324():
    #testing the effect of changing the negative range

    asic = get_context('asic')
    
    timenow = time.localtime()
    print("Begin test {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    # Perform global mode before running this test, includes reset
    set_global_mode()

    # Set the feedback capacitence to 7fF
    asic.set_register_bit(0, 0b00001000)
    asic.clear_register_bit(  0, 0b00010000)

    #Set default slew rate
    set_clock_config(205)  # Use default 205 MHz TDC clock

    #Set default negative range
    asic.set_register_bit(0,0b01000000)

    #14fF, 0000 slew rate
    asic.set_all_ramp_bias(0b0010)

    asic.clear_register_bit(0,0b00100000)
    asic.write_register(12,6)
    asic.write_register(14,20)
    asic.write_register(9,0b10001111)

    # Create reference sample of -10keV range, limited sectors
    test1= vcal_noise_test(local_vcal=False,
                            sector_samples=5000,
                            all_sectors=False,
                            vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()
    print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))    
   
     # Set the feedback capacitence to 7fF
    asic.clear_register_bit(0, 0b00001000)
    asic.set_register_bit(  0, 0b00010000)

    test2= vcal_noise_test(local_vcal=False,
                            sector_samples=5000,
                            all_sectors=False,
                            vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()
    print("Test 2 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))    

    asic.set_register_bit(0, 0b00001000)
    asic.set_register_bit(  0, 0b00010000)

    test3= vcal_noise_test(local_vcal=False,
                            sector_samples=5000,
                            all_sectors=False,
                            vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()
    print("Test 3 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))    

    print("!!! All tests complete:")
    print("\t1) Lawrence batch5 7 fF test; No VCAL stored in {}".format(test1))
    print("\t2) Lawrence batch5 14 fF test; No VCAL stored in {}".format(test2))
    print("\t3) Lawrence batch5 21 fF test; No VCAL stored in {}".format(test3))


def test_VCAL_14fF_NoVCAL_Lawrence_testsbatch6_fullArray_20220324():
    #testing the effect of changing the negative range

    asic = get_context('asic')
    
    timenow = time.localtime()
    print("Begin test {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    # Perform global mode before running this test, includes reset
    set_global_mode()

    # Set the feedback capacitence to 7fF
    asic.clear_register_bit(0, 0b00001000)
    asic.set_register_bit(  0, 0b00010000)

    #Set default slew rate
    set_clock_config(205)  # Use default 205 MHz TDC clock

    #Set default negative range
    asic.set_register_bit(0,0b01000000)

    #14fF, 0000 slew rate
    asic.set_all_ramp_bias(0b0010)

    asic.clear_register_bit(0,0b00100000)
    asic.write_register(12,6)
    asic.write_register(14,20)
    asic.write_register(9,0b10001111)

    # Create reference sample of -10keV range, limited sectors
    test1= vcal_noise_test(local_vcal=False,
                            sector_samples=5000,
                            all_sectors=True,
                            vcal_values=[0.5])
    timenow = time.localtime()
    print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))    
   
    asic.clear_register_bit(0,0b00000100)
    print(asic.read_register(0))
    
    test2= vcal_noise_test(local_vcal=False,
                            sector_samples=5000,
                            all_sectors=True,
                            vcal_values=[0.5])
    timenow = time.localtime()
    print("Test 2 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))       

    print("!!! All tests complete:")
    print("\t1) Lawrence batch6 14 fF full array test; VCAL stored in {}".format(test1))
    print("\t2) Lawrence batch5 14 fF full array test; No VCAL stored in {}".format(test2))


def test_VCAL_14fF_NoVCAL_Lawrence_testsbatch7_fullArray_20220328():
    #testing the effect of changing the negative range

    asic = get_context('asic')
    
    timenow = time.localtime()
    print("Begin test {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    # Perform global mode before running this test, includes reset
    set_global_mode()

    # Set the feedback capacitence to 7fF
    asic.clear_register_bit(0, 0b00001000)
    asic.set_register_bit(  0, 0b00010000)

    #Set default slew rate
    set_clock_config(205)  # Use default 205 MHz TDC clock

    #Set default negative range
    asic.set_register_bit(0,0b01000000)

    #14fF, 0000 slew rate
    asic.set_all_ramp_bias(0b0000)

    asic.clear_register_bit(0,0b00100000)
    asic.write_register(12,6)
    asic.write_register(14,20)
    asic.write_register(9,0b10001111)

    # Create reference sample of -10keV range, limited sectors
    test1= vcal_noise_test(local_vcal=False,
                            sector_samples=5000,
                            all_sectors=True,
                            vcal_values=[0.5])
    timenow = time.localtime()
    print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))    
   
    asic.clear_register_bit(0,0b00000100)
    print(asic.read_register(0))
    
    test2= vcal_noise_test(local_vcal=False,
                            sector_samples=5000,
                            all_sectors=True,
                            vcal_values=[0.5])
    timenow = time.localtime()
    print("Test 2 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))       

    print("!!! All tests complete:")
    print("\t1) Lawrence batch6 14 fF full array test; VCAL stored in {}".format(test1))
    print("\t2) Lawrence batch5 14 fF full array test; No VCAL stored in {}".format(test2))

def test_VCAL_14fF_VCAL_Lawrence_testsbatch8_linearity_20220328():
    #testing the effect of changing the negative range

    asic = get_context('asic')
    
    timenow = time.localtime()
    print("Begin test {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    # Perform global mode before running this test, includes reset
    set_global_mode()

    # Set the feedback capacitence to 7fF
    asic.clear_register_bit(0, 0b00001000)
    asic.set_register_bit(  0, 0b00010000)

    #Set default slew rate
    set_clock_config(205)  # Use default 205 MHz TDC clock

    #Set default negative range
    asic.set_register_bit(0,0b01000000)

    #14fF, 0000 slew rate
    asic.set_all_ramp_bias(0b0000)

    asic.clear_register_bit(0,0b00100000)
    asic.write_register(12,6)
    asic.write_register(14,20)
    asic.write_register(9,0b10001111)

    # Create reference sample of -10keV range, limited sectors
    test1= vcal_noise_test(local_vcal=False,
                            sector_samples=5000,
                            all_sectors=False,
                            vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()
    print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))    
   
    print("\t1) Lawrence batch8 14 fF linearity test; VCAL stored in {}".format(test1))


def test_VCAL_14fF_VCAL_Lawrence_testsbatch8_linearity_7and21_20220328():
    #testing the effect of changing the negative range

    asic = get_context('asic')
    
    timenow = time.localtime()
    print("Begin test {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    # Perform global mode before running this test, includes reset
    set_global_mode()

    # Set the feedback capacitence to 7fF
    asic.set_register_bit(0, 0b00001000)
    asic.clear_register_bit(  0, 0b00010000)

    #Set default slew rate
    set_clock_config(205)  # Use default 205 MHz TDC clock

    #Set default negative range
    asic.set_register_bit(0,0b01000000)

    #14fF, 0000 slew rate
    asic.set_all_ramp_bias(0b0000)

    asic.clear_register_bit(0,0b00100000)
    asic.write_register(12,6)
    asic.write_register(14,20)
    asic.write_register(9,0b10001111)

    # Create reference sample of -10keV range, limited sectors
    test1= vcal_noise_test(local_vcal=False,
                            sector_samples=5000,
                            all_sectors=False,
                            vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()
    print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    asic.set_register_bit(0, 0b00001000)
    asic.set_register_bit(  0, 0b00010000)

    test2= vcal_noise_test(local_vcal=False,
                        sector_samples=5000,
                        all_sectors=False,
                        vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()
    print("Test 2 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))   
   
    print("\t1) Lawrence batch8 7 fF linearity test; VCAL stored in {}".format(test1))
    print("\t2) Lawrence batch8 21 fF linearity test; VCAL stored in {}".format(test2))


def test_VCAL_Lawrence_testsbatch9_newSettings_20220331():
    #testing the effect of changing the negative range

    asic = get_context('asic')
    
    timenow = time.localtime()
    print("Begin test {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    # Perform global mode before running this test, includes reset
    set_global_mode()

    # Set the feedback capacitence to 7fF
    asic.set_register_bit(0, 0b00001000)
    asic.clear_register_bit(  0, 0b00010000)

    #Set default slew rate
    set_clock_config(205)  # Use default 205 MHz TDC clock

    #Set default negative range
    asic.set_register_bit(0,0b01000000)

    #14fF, 0000 slew rate
    asic.set_all_ramp_bias(0b0000)

    asic.clear_register_bit(0,0b00100000)
    asic.write_register(12,6)
    asic.write_register(14,20)
    asic.write_register(9,0b10001111)
    asic.write_register(17,174)
    asic.write_register(18,198)
    asic.write_register(21,190)

    # Create reference sample of -10keV range, limited sectors
    test1= vcal_noise_test(local_vcal=False,
                            sector_samples=5000,
                            all_sectors=False,
                            vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()
    print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    asic.clear_register_bit(0, 0b00001000)
    asic.set_register_bit(0, 0b00010000)

    test2= vcal_noise_test(local_vcal=False,
                        sector_samples=5000,
                        all_sectors=False,
                        vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()
    print("Test 2 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    asic.set_register_bit(0, 0b00001000)
    asic.set_register_bit(0, 0b00010000)

    test3= vcal_noise_test(local_vcal=False,
                        sector_samples=5000,
                        all_sectors=False,
                        vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()
    print("Test 3 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))  

    asic.clear_register_bit(0,0b00000100)
    print(asic.read_register(0))
    asic.clear_register_bit(0, 0b00001000)
    asic.set_register_bit(0, 0b00010000)

    test4= vcal_noise_test(local_vcal=False,
                        sector_samples=5000,
                        all_sectors=True,
                        vcal_values=[0.5])
    timenow = time.localtime()
    print("Test 4 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec)) 
   
    print("\t1) Lawrence batch9 7 fF linearity test; VCAL stored in {}".format(test1))
    print("\t2) Lawrence batch9 14 fF linearity test; VCAL stored in {}".format(test2))
    print("\t3) Lawrence batch9 21 fF linearity test; VCAL stored in {}".format(test3))
    print("\t3) Lawrence batch9 14 fF linearity test; no VCAL stored in {}".format(test4))


def test_VCAL_Lawrence_testsbatch10_newSettingsIndividual_20220401():
    #testing the effect of changing the negative range

    asic = get_context('asic')
    
    timenow = time.localtime()
    print("Begin test {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    # Perform global mode before running this test, includes reset
    set_global_mode()

    # Set the feedback capacitence to 7fF
    asic.set_register_bit(0, 0b00001000)
    asic.clear_register_bit(  0, 0b00010000)

    #Set default slew rate
    set_clock_config(205)  # Use default 205 MHz TDC clock

    #Set default negative range
    asic.set_register_bit(0,0b01000000)

    #14fF, 0000 slew rate
    asic.set_all_ramp_bias(0b0000)

    asic.clear_register_bit(0,0b00100000)
    asic.write_register(12,6)
    asic.write_register(14,20)
    asic.write_register(9,0b10001111)
    asic.write_register(17,174)

    # Create reference sample of -10keV range, limited sectors
    test1= vcal_noise_test(local_vcal=False,
                            sector_samples=5000,
                            all_sectors=False,
                            vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()
    print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    asic.clear_register_bit(0, 0b00001000)
    asic.set_register_bit(0, 0b00010000)

    test2= vcal_noise_test(local_vcal=False,
                        sector_samples=5000,
                        all_sectors=False,
                        vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()
    print("Test 2 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    asic.set_register_bit(0, 0b00001000)
    asic.set_register_bit(0, 0b00010000)

    test3= vcal_noise_test(local_vcal=False,
                        sector_samples=5000,
                        all_sectors=False,
                        vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()
    print("Test 3 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))  

    asic.clear_register_bit(0,0b00000100)
    print(asic.read_register(0))
    asic.clear_register_bit(0, 0b00001000)
    asic.set_register_bit(0, 0b00010000)

    test4= vcal_noise_test(local_vcal=False,
                        sector_samples=5000,
                        all_sectors=True,
                        vcal_values=[0.5])
    timenow = time.localtime()
    print("Test 4 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec)) 


    set_global_mode()

    # Set the feedback capacitence to 7fF
    asic.set_register_bit(0, 0b00001000)
    asic.clear_register_bit(  0, 0b00010000)

    #Set default slew rate
    set_clock_config(205)  # Use default 205 MHz TDC clock

    #Set default negative range
    asic.set_register_bit(0,0b01000000)

    #14fF, 0000 slew rate
    asic.set_all_ramp_bias(0b0000)

    asic.clear_register_bit(0,0b00100000)
    asic.write_register(12,6)
    asic.write_register(14,20)
    asic.write_register(9,0b10001111)
    asic.write_register(18,198)

    # Create reference sample of -10keV range, limited sectors
    test5= vcal_noise_test(local_vcal=False,
                            sector_samples=5000,
                            all_sectors=False,
                            vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()
    print("Test 5 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    asic.clear_register_bit(0, 0b00001000)
    asic.set_register_bit(0, 0b00010000)

    test6= vcal_noise_test(local_vcal=False,
                        sector_samples=5000,
                        all_sectors=False,
                        vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()
    print("Test 6 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    asic.set_register_bit(0, 0b00001000)
    asic.set_register_bit(0, 0b00010000)

    test7= vcal_noise_test(local_vcal=False,
                        sector_samples=5000,
                        all_sectors=False,
                        vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()
    print("Test 7 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))  

    asic.clear_register_bit(0,0b00000100)
    print(asic.read_register(0))
    asic.clear_register_bit(0, 0b00001000)
    asic.set_register_bit(0, 0b00010000)

    test8= vcal_noise_test(local_vcal=False,
                        sector_samples=5000,
                        all_sectors=True,
                        vcal_values=[0.5])
    timenow = time.localtime()
    print("Test 8 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec)) 

    set_global_mode()

    # Set the feedback capacitence to 7fF
    asic.set_register_bit(0, 0b00001000)
    asic.clear_register_bit(  0, 0b00010000)

    #Set default slew rate
    set_clock_config(205)  # Use default 205 MHz TDC clock

    #Set default negative range
    asic.set_register_bit(0,0b01000000)

    #14fF, 0000 slew rate
    asic.set_all_ramp_bias(0b0000)

    asic.clear_register_bit(0,0b00100000)
    asic.write_register(12,6)
    asic.write_register(14,20)
    asic.write_register(9,0b10001111)
    asic.write_register(21,190)

     # Create reference sample of -10keV range, limited sectors
    test9= vcal_noise_test(local_vcal=False,
                            sector_samples=5000,
                            all_sectors=False,
                            vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()
    print("Test 9 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    asic.clear_register_bit(0, 0b00001000)
    asic.set_register_bit(0, 0b00010000)

    test10= vcal_noise_test(local_vcal=False,
                        sector_samples=5000,
                        all_sectors=False,
                        vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()
    print("Test 10 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    asic.set_register_bit(0, 0b00001000)
    asic.set_register_bit(0, 0b00010000)

    test11= vcal_noise_test(local_vcal=False,
                        sector_samples=5000,
                        all_sectors=False,
                        vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()
    print("Test 11 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))  

    asic.clear_register_bit(0,0b00000100)
    print(asic.read_register(0))
    asic.clear_register_bit(0, 0b00001000)
    asic.set_register_bit(0, 0b00010000)

    test12= vcal_noise_test(local_vcal=False,
                        sector_samples=5000,
                        all_sectors=True,
                        vcal_values=[0.5])
    timenow = time.localtime()
    print("Test 12 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec)) 

   
    print("\t1) Lawrence batch9 7 fF linearity test; VCAL stored in {}".format(test1))
    print("\t2) Lawrence batch9 14 fF linearity test; VCAL stored in {}".format(test2))
    print("\t3) Lawrence batch9 21 fF linearity test; VCAL stored in {}".format(test3))
    print("\t4) Lawrence batch9 14 fF linearity test; no VCAL stored in {}".format(test4))
    print("\t5) Lawrence batch9 7 fF linearity test; VCAL stored in {}".format(test5))
    print("\t6) Lawrence batch9 14 fF linearity test; VCAL stored in {}".format(test6))
    print("\t7) Lawrence batch9 21 fF linearity test; VCAL stored in {}".format(test7))
    print("\t8) Lawrence batch9 14 fF linearity test; no VCAL stored in {}".format(test8))
    print("\t9) Lawrence batch9 7 fF linearity test; VCAL stored in {}".format(test9))
    print("\t10) Lawrence batch9 14 fF linearity test; VCAL stored in {}".format(test10))
    print("\t11) Lawrence batch9 21 fF linearity test; VCAL stored in {}".format(test11))
    print("\t12) Lawrence batch9 14 fF linearity test; no VCAL stored in {}".format(test12))

def test_VCAL_Lawrence_testsbatch11_register18testing_20220404():
    #testing the effect of changing the negative range

    asic = get_context('asic')
    
    timenow = time.localtime()
    print("Begin test {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    # Perform global mode before running this test, includes reset
    set_global_mode()

    # Set the feedback capacitence to 7fF
    asic.set_register_bit(0, 0b00001000)
    asic.clear_register_bit(  0, 0b00010000)

    #Set default slew rate
    set_clock_config(205)  # Use default 205 MHz TDC clock

    #Set default negative range
    asic.set_register_bit(0,0b01000000)

    #14fF, 0000 slew rate
    asic.set_all_ramp_bias(0b0000)

    asic.clear_register_bit(0,0b00100000)
    asic.write_register(12,6)
    asic.write_register(14,20)
    asic.write_register(9,0b10001111)
    asic.write_register(17,174)
    asic.write_register(21,190)
    asic.write_register(18,196)

    # Create reference sample of -10keV range, limited sectors
    test1= vcal_noise_test(local_vcal=False,
                            sector_samples=5000,
                            all_sectors=False,
                            vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()
    print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    asic.clear_register_bit(0, 0b00001000)
    asic.set_register_bit(0, 0b00010000)

    test2= vcal_noise_test(local_vcal=False,
                        sector_samples=5000,
                        all_sectors=False,
                        vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()
    print("Test 2 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    asic.set_register_bit(0, 0b00001000)
    asic.set_register_bit(0, 0b00010000)

    test3= vcal_noise_test(local_vcal=False,
                        sector_samples=5000,
                        all_sectors=False,
                        vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()
    print("Test 3 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))  

    asic.clear_register_bit(0,0b00000100)
    print(asic.read_register(0))
    asic.clear_register_bit(0, 0b00001000)
    asic.set_register_bit(0, 0b00010000)

    test4= vcal_noise_test(local_vcal=False,
                        sector_samples=5000,
                        all_sectors=True,
                        vcal_values=[0.5])
    timenow = time.localtime()
    print("Test 4 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec)) 


    set_global_mode()

    # Set the feedback capacitence to 7fF
    asic.set_register_bit(0, 0b00001000)
    asic.clear_register_bit(  0, 0b00010000)

    #Set default slew rate
    set_clock_config(205)  # Use default 205 MHz TDC clock

    #Set default negative range
    asic.set_register_bit(0,0b01000000)

    #14fF, 0000 slew rate
    asic.set_all_ramp_bias(0b0000)

    asic.clear_register_bit(0,0b00100000)
    asic.write_register(12,6)
    asic.write_register(14,20)
    asic.write_register(9,0b10001111)
    asic.write_register(17,174)
    asic.write_register(21,190)
    asic.write_register(18,197)

    # Create reference sample of -10keV range, limited sectors
    test5= vcal_noise_test(local_vcal=False,
                            sector_samples=5000,
                            all_sectors=False,
                            vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()
    print("Test 5 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    asic.clear_register_bit(0, 0b00001000)
    asic.set_register_bit(0, 0b00010000)

    test6= vcal_noise_test(local_vcal=False,
                        sector_samples=5000,
                        all_sectors=False,
                        vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()
    print("Test 6 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    asic.set_register_bit(0, 0b00001000)
    asic.set_register_bit(0, 0b00010000)

    test7= vcal_noise_test(local_vcal=False,
                        sector_samples=5000,
                        all_sectors=False,
                        vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()
    print("Test 7 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))  

    asic.clear_register_bit(0,0b00000100)
    print(asic.read_register(0))
    asic.clear_register_bit(0, 0b00001000)
    asic.set_register_bit(0, 0b00010000)

    test8= vcal_noise_test(local_vcal=False,
                        sector_samples=5000,
                        all_sectors=True,
                        vcal_values=[0.5])
    timenow = time.localtime()
    print("Test 8 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec)) 

    set_global_mode()

    # Set the feedback capacitence to 7fF
    asic.set_register_bit(0, 0b00001000)
    asic.clear_register_bit(  0, 0b00010000)

    #Set default slew rate
    set_clock_config(205)  # Use default 205 MHz TDC clock

    #Set default negative range
    asic.set_register_bit(0,0b01000000)

    #14fF, 0000 slew rate
    asic.set_all_ramp_bias(0b0000)

    asic.clear_register_bit(0,0b00100000)
    asic.write_register(12,6)
    asic.write_register(14,20)
    asic.write_register(9,0b10001111)
    asic.write_register(17,174)
    asic.write_register(21,190)
    asic.write_register(18,0)

     # Create reference sample of -10keV range, limited sectors
    test9= vcal_noise_test(local_vcal=False,
                            sector_samples=5000,
                            all_sectors=False,
                            vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()
    print("Test 9 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    asic.clear_register_bit(0, 0b00001000)
    asic.set_register_bit(0, 0b00010000)

    test10= vcal_noise_test(local_vcal=False,
                        sector_samples=5000,
                        all_sectors=False,
                        vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()
    print("Test 10 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    asic.set_register_bit(0, 0b00001000)
    asic.set_register_bit(0, 0b00010000)

    test11= vcal_noise_test(local_vcal=False,
                        sector_samples=5000,
                        all_sectors=False,
                        vcal_values=[0,0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    timenow = time.localtime()
    print("Test 11 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))  

    asic.clear_register_bit(0,0b00000100)
    print(asic.read_register(0))
    asic.clear_register_bit(0, 0b00001000)
    asic.set_register_bit(0, 0b00010000)

    test12= vcal_noise_test(local_vcal=False,
                        sector_samples=5000,
                        all_sectors=True,
                        vcal_values=[0.5])
    timenow = time.localtime()
    print("Test 12 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec)) 

   
    print("\t1) Lawrence batch11 7 fF linearity test; VCAL stored in {}".format(test1))
    print("\t2) Lawrence batch11 14 fF linearity test; VCAL stored in {}".format(test2))
    print("\t3) Lawrence batch11 21 fF linearity test; VCAL stored in {}".format(test3))
    print("\t4) Lawrence batch11 14 fF linearity test; no VCAL stored in {}".format(test4))
    print("\t5) Lawrence batch11 7 fF linearity test; VCAL stored in {}".format(test5))
    print("\t6) Lawrence batch11 14 fF linearity test; VCAL stored in {}".format(test6))
    print("\t7) Lawrence batch11 21 fF linearity test; VCAL stored in {}".format(test7))
    print("\t8) Lawrence batch11 14 fF linearity test; no VCAL stored in {}".format(test8))
    print("\t9) Lawrence batch11 7 fF linearity test; VCAL stored in {}".format(test9))
    print("\t10) Lawrence batch11 14 fF linearity test; VCAL stored in {}".format(test10))
    print("\t11) Lawrence batch11 21 fF linearity test; VCAL stored in {}".format(test11))
    print("\t12) Lawrence batch11 14 fF linearity test; no VCAL stored in {}".format(test12))


def CdZnTe_D320771_0V_initialTest_currentSettings():
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
    asic.set_all_ramp_bias(0b0000)

    asic.clear_register_bit(0,0b00000100)
    asic.clear_register_bit(0,0b00100000)
    asic.write_register(12,6)
    asic.write_register(14,20)
    asic.write_register(9,0b10001111)
    asic.write_register(17,174)
    asic.write_register(21,190)
    asic.write_register(18,196)

    # Create reference sample of -10keV range, limited sectors
    test1= vcal_noise_test(local_vcal=False,
                            sector_samples=15000,
                            all_sectors=True,
                            vcal_values=[0])
    timenow = time.localtime()
    print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

       
    print("\t1) CdZnTe_D320771_initial_test stored in {}".format(test1))

def CdZnTe_D320771_0V_initialTest_currentSettings_shorter():
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
    asic.set_all_ramp_bias(0b0000)

    asic.clear_register_bit(0,0b00000100)
    asic.clear_register_bit(0,0b00100000)
    asic.write_register(12,6)
    asic.write_register(14,20)
    asic.write_register(9,0b10001111)
    asic.write_register(17,174)
    asic.write_register(21,190)
    asic.write_register(18,196)

    # Create reference sample of -10keV range, limited sectors
    test1= vcal_noise_test(local_vcal=False,
                            sector_samples=5000,
                            all_sectors=True,
                            vcal_values=[0])
    timenow = time.localtime()
    print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

       
    print("\t1) CdZnTe_D320771_initial_test stored in {}".format(test1))
   


def CdZnTe_D320771_0V_initialTest_currentSettings_shorter():
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
    asic.set_all_ramp_bias(0b0000)

    asic.clear_register_bit(0,0b00000100)
    asic.clear_register_bit(0,0b00100000)
    asic.write_register(12,6)
    asic.write_register(14,20)
    asic.write_register(9,0b10001111)
    asic.write_register(17,174)
    asic.write_register(21,190)
    asic.write_register(18,196)

    # Create reference sample of -10keV range, limited sectors
    test1= vcal_noise_test(local_vcal=False,
                            sector_samples=5000,
                            all_sectors=True,
                            vcal_values=[0])
    timenow = time.localtime()
    print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

       
    print("\t1) CdZnTe_D320771_initial_test stored in {}".format(test1))

def CdZnTe_D320771_1000V_VCAL_currentSettings():
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
    asic.set_all_ramp_bias(0b0000)

    asic.set_register_bit(0,0b00000100)
    asic.clear_register_bit(0,0b00100000)
    asic.write_register(12,6)
    asic.write_register(14,20)
    asic.write_register(9,0b10001111)
    asic.write_register(17,174)
    asic.write_register(21,190)
    asic.write_register(18,196)

    # Create reference sample of -10keV range, limited sectors
    test1= vcal_noise_test_subsection(local_vcal=False,
                            sector_samples=20000,
                            all_sectors=False,
                            vcal_values=[0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0,1.1,1.2,1.3,1.4,1.5])
    timenow = time.localtime()
    print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

       
    print("\t1) CdZnTe_D320771_VCAL_test stored in {}".format(test1))


def CdZnTe_D320771_0V_initialTest_currentSettings_1000samples():
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
    asic.set_all_ramp_bias(0b0000)

    asic.clear_register_bit(0,0b00000100)
    asic.clear_register_bit(0,0b00100000)
    asic.write_register(12,6)
    asic.write_register(14,20)
    asic.write_register(9,0b10001111)
    asic.write_register(17,174)
    asic.write_register(21,190)
    asic.write_register(18,196)

    # Create reference sample of -10keV range, limited sectors
    test1= vcal_noise_test(local_vcal=False,
                            sector_samples=1000,
                            all_sectors=True,
                            vcal_values=[0])
    timenow = time.localtime()
    print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

       
    print("\t1) CdZnTe_D320771_1000_sample_measurement stored in {}".format(test1))

def CdZnTe_D320771_0V_initialTest_currentSettings_10000samples():
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
    asic.set_all_ramp_bias(0b0000)

    asic.clear_register_bit(0,0b00000100)
    asic.clear_register_bit(0,0b00100000)
    asic.write_register(12,6)
    asic.write_register(14,20)
    asic.write_register(9,0b10001111)
    asic.write_register(17,174)
    asic.write_register(21,190)
    asic.write_register(18,196)

    # Create reference sample of -10keV range, limited sectors
    test1= vcal_noise_test(local_vcal=False,
                            sector_samples=10000,
                            all_sectors=True,
                            vcal_values=[0])
    timenow = time.localtime()
    print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

       
    print("\t1) CdZnTe_D320771_1000_sample_measurement stored in {}".format(test1))

def CdZnTe_D320771_0V_initialTest_currentSettings_30000samples():
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
    asic.set_all_ramp_bias(0b0000)

    asic.clear_register_bit(0,0b00000100)
    asic.clear_register_bit(0,0b00100000)
    asic.write_register(12,6)
    asic.write_register(14,20)
    asic.write_register(9,0b10001111)
    asic.write_register(17,174)
    asic.write_register(21,190)
    asic.write_register(18,196)

    # Create reference sample of -10keV range, limited sectors
    test1= vcal_noise_test(local_vcal=False,
                            sector_samples=30000,
                            all_sectors=True,
                            vcal_values=[0])
    timenow = time.localtime()
    print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

       
    print("\t1) CdZnTe_D320771_1000_sample_measurement stored in {}".format(test1))

def CdZnTe_D320771_0V_initialTest_currentSettings_400000samples_singleSector():
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
    asic.set_all_ramp_bias(0b0000)

    asic.clear_register_bit(0,0b00000100)
    asic.clear_register_bit(0,0b00100000)
    asic.write_register(12,6)
    asic.write_register(14,20)
    asic.write_register(9,0b10001111)
    asic.write_register(17,174)
    asic.write_register(21,190)
    asic.write_register(18,196)

    # Create reference sample of -10keV range, limited sectors
    test1= vcal_noise_test_sector9(local_vcal=False,
                            sector_samples=40000,
                            all_sectors=False,
                            vcal_values=[0])
    timenow = time.localtime()
    print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

       
    print("\t1) CdZnTe_D320771_400000_sample_measurement stored in {}".format(test1))


def CdZnTe_D320771_0V_initialTest_currentSettings_shorter_lowGain():
    #testing the effect of changing the negative range

    asic = get_context('asic')
    
    timenow = time.localtime()
    print("Begin test {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    # Perform global mode before running this test, includes reset
    set_global_mode()

    # Set the feedback capacitence to 14fF
    asic.set_register_bit(0, 0b00001000)
    asic.clear_register_bit(  0, 0b00010000)

    #Set default slew rate
    set_clock_config(205)  # Use default 205 MHz TDC clock

    #Set default negative range
    asic.set_register_bit(0,0b01000000)

    #14fF, 0000 slew rate
    asic.set_all_ramp_bias(0b0000)

    asic.clear_register_bit(0,0b00000100)
    asic.clear_register_bit(0,0b00100000)
    asic.write_register(12,6)
    asic.write_register(14,20)
    asic.write_register(9,0b10001111)
    asic.write_register(17,174)
    asic.write_register(21,190)
    asic.write_register(18,196)

    # Create reference sample of -10keV range, limited sectors
    test1= vcal_noise_test(local_vcal=False,
                            sector_samples=5000,
                            all_sectors=True,
                            vcal_values=[0])
    timenow = time.localtime()
    print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

       
    print("\t1) CdZnTe_D320771_initial_test stored in {}".format(test1))

def CdZnTe_D320771_0V_initialTest_currentSettings_400000samples_singleSector_lowGain():
    #testing the effect of changing the negative range

    asic = get_context('asic')
    
    timenow = time.localtime()
    print("Begin test {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    # Perform global mode before running this test, includes reset
    set_global_mode()

    # Set the feedback capacitence to 14fF
    asic.set_register_bit(0, 0b00001000)
    asic.clear_register_bit(  0, 0b00010000)

    #Set default slew rate
    set_clock_config(205)  # Use default 205 MHz TDC clock

    #Set default negative range
    asic.set_register_bit(0,0b01000000)

    #14fF, 0000 slew rate
    asic.set_all_ramp_bias(0b0000)

    asic.clear_register_bit(0,0b00000100)
    asic.clear_register_bit(0,0b00100000)
    asic.write_register(12,6)
    asic.write_register(14,20)
    asic.write_register(9,0b10001111)
    asic.write_register(17,174)
    asic.write_register(21,190)
    asic.write_register(18,196)

    # Create reference sample of -10keV range, limited sectors
    test1= vcal_noise_test_sector9(local_vcal=False,
                            sector_samples=40000,
                            all_sectors=False,
                            vcal_values=[0])
    timenow = time.localtime()
    print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

       
    print("\t1) CdZnTe_D320771_400000_sample_measurement stored in {}".format(test1))

def CdZnTe_D320771_0V_initialTest_currentSettings_1000samples_highGain():
    #testing the effect of changing the negative range

    asic = get_context('asic')
    
    timenow = time.localtime()
    print("Begin test {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    # Perform global mode before running this test, includes reset
    set_global_mode()

    # Set the feedback capacitence to 14fF
    asic.set_register_bit(0, 0b00001000)
    asic.clear_register_bit(  0, 0b00010000)

    #Set default slew rate
    set_clock_config(205)  # Use default 205 MHz TDC clock

    #Set default negative range
    asic.set_register_bit(0,0b01000000)

    #14fF, 0000 slew rate
    asic.set_all_ramp_bias(0b0000)

    asic.clear_register_bit(0,0b00000100)
    asic.clear_register_bit(0,0b00100000)
    asic.write_register(12,6)
    asic.write_register(14,20)
    asic.write_register(9,0b10001111)
    asic.write_register(17,174)
    asic.write_register(21,190)
    asic.write_register(18,196)

    # Create reference sample of -10keV range, limited sectors
    test1= vcal_noise_test(local_vcal=False,
                            sector_samples=1000,
                            all_sectors=True,
                            vcal_values=[0])
    timenow = time.localtime()
    print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

       
    print("\t1) CdZnTe_D320771_1000_sample_measurement stored in {}".format(test1))

def CdZnTe_D320771_0V_initialTest_currentSettings_400000samples_singleSector10():
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
    asic.set_all_ramp_bias(0b0000)

    asic.clear_register_bit(0,0b00000100)
    asic.clear_register_bit(0,0b00100000)
    asic.write_register(12,6)
    asic.write_register(14,20)
    asic.write_register(9,0b10001111)
    asic.write_register(17,174)
    asic.write_register(21,190)
    asic.write_register(18,196)

    # Create reference sample of -10keV range, limited sectors
    test1= vcal_noise_test_sector10(local_vcal=False,
                            sector_samples=40000,
                            all_sectors=False,
                            vcal_values=[0])
    timenow = time.localtime()
    print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

def set_capacitance(value=14):

    if value == 7:
        asic.set_register_bit(0, 0b00001000)
        asic.clear_register_bit(  0, 0b00010000)
        print("Operating in 7fF mode")
    elif value == 14:
        asic.clear_register_bit(0, 0b00001000)
        asic.set_register_bit(  0, 0b00010000)
        print("Operating in 14fF mode")
    elif value == 21:
        asic.set_register_bit(0, 0b00001000)
        asic.set_register_bit(  0, 0b00010000)
        print("Operating in 21fF mode")
    else:
        print("Incorrect capacitance value set")
    
def set_slewRate(value=0b0000):
    
    asic.set_all_ramp_bias(value)

    print("Setting all ramp slew rates to {0}".format(value))

def set_negativeRange(value=10):

    if value == 10:
        asic.set_register_bit(0,0b01000000)
        print("Negative range set to -10 keV")
    elif value == 20:
        asic.clear_register_bit(0,0b01000000)
        print("Negative range set to -20 keV")
    else:
        print("Incorrect negative range set")
    
def CdZnTe_D320771_0V_initialTest_currentSettings_400000samples_singleSector11_lowGain():
    #testing the effect of changing the negative range

    asic = get_context('asic')
    
    timenow = time.localtime()
    print("Begin test {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    # Perform global mode before running this test, includes reset
    set_global_mode()

    # Set the feedback capacitence to 14fF
    asic.set_register_bit(0, 0b00001000)
    asic.clear_register_bit(  0, 0b00010000)

    #Set default slew rate
    set_clock_config(205)  # Use default 205 MHz TDC clock

    #Set default negative range
    asic.set_register_bit(0,0b01000000)

    #14fF, 0000 slew rate
    asic.set_all_ramp_bias(0b0000)

    asic.clear_register_bit(0,0b00000100)
    asic.clear_register_bit(0,0b00100000)
    asic.write_register(12,6)
    asic.write_register(14,20)
    asic.write_register(9,0b10001111)
    asic.write_register(17,174)
    asic.write_register(21,190)
    asic.write_register(18,196)

    # Create reference sample of -10keV range, limited sectors
    test1= vcal_noise_test_sector11(local_vcal=False,
                            sector_samples=40000,
                            all_sectors=False,
                            vcal_values=[0])
    timenow = time.localtime()
    print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    
    print("\t1) CdZnTe_D320771_400000_sample_measurement stored in {}".format(test1))
