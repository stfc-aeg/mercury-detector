import time

requires = [
    'asic_spi',
    'asic_spi_legacy'   # Do not include this in later test files
]

provides = [
'Si_Diamond_Chosensamples_sector11_defaultsettings_100keVGain',
'Si_Diamond_Chosensamples_sector11_defaultsettings_200keVGain',
'Si_Diamond_Chosensamples_sector11_defaultsettings_300keVGain',
'Diamond_5000samples_allsectors_defaultsettings_highGain',
'Diamond_1000samples_allsectors_defaultsettings_highGain',
'Diamond_1000samples_sector9_defaultsettings_highGain',
'Diamond_10000samples_sector9_defaultsettings_highGain',
'Diamond_100000samples_sector9_defaultsettings_highGain',
'Diamond_400000samples_sector9_defaultsettings_highGain',
'Diamond_overnight1_600000samplesPerGrap_sector9_defaultsettings_highGain',
'Diamond_overnight1_100samplesPerGrapTest_sector9_defaultsettings_highGain',
'Diamond_overnight1_100000samplesPerGrap_sector9_defaultsettings_highGain',
'Diamond_Chosensamples_sector9_defaultsettings_highGain',
'Diamond_Chosensamples_sector9_defaultsettings_200keVGain',
'Diamond_Chosensamples_sector9_defaultsettings_300keVGain',
'Diamond_Overnight2_sector9_BiasRampScan_100keVGain',
'Diamond_Overnight2_sector9_BiasRampScan_100keVGain_Darks',
'Diamond_Chosensamples_sector9_GlobalBias_100keVGain',
'Diamond_Chosensamples_sector9_PLL_VoltageRegular_100keVGain_scan',
'Diamond_Chosensamples_sector9_PLL_ChargePump_100keVGain_scan',
'Diamond_sector9_reset_scan_100keVGain_darks',
'Diamond_sector9_reset_scan_100keVGain',
'Si_Diamond_sector11_Overnight_100keVGain_darks',
'Si_Diamond_sector11_Overnight_100keVGain'
]


def Diamond_5000samples_allsectors_defaultsettings_highGain():
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

    asic.clear_register_bit(0,0b00000100)
    asic.clear_register_bit(0,0b00100000)
    asic.write_register(12,6)
    asic.write_register(14,20)
    asic.write_register(9,0b10001111)
    asic.write_register(17,174)
    asic.write_register(21,190)
    asic.write_register(18,197)

    # Create reference sample of -10keV range, limited sectors
    test1= vcal_noise_test(local_vcal=False,
                            sector_samples=5000,
                            all_sectors=True,
                            vcal_values=[0])
    timenow = time.localtime()
    print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

def Diamond_1000samples_allsectors_defaultsettings_highGain():
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

    asic.clear_register_bit(0,0b00000100)
    asic.clear_register_bit(0,0b00100000)
    asic.write_register(12,6)
    asic.write_register(14,20)
    asic.write_register(9,0b10001111)
    asic.write_register(17,174)
    asic.write_register(21,190)
    asic.write_register(18,197)

    # Create reference sample of -10keV range, limited sectors
    test1= vcal_noise_test(local_vcal=False,
                            sector_samples=1000,
                            all_sectors=True,
                            vcal_values=[0])
    timenow = time.localtime()
    print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

def Diamond_1000samples_sector9_defaultsettings_highGain():
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

    asic.clear_register_bit(0,0b00000100)
    asic.clear_register_bit(0,0b00100000)
    asic.write_register(12,6)
    asic.write_register(14,20)
    asic.write_register(9,0b10001111)
    asic.write_register(17,174)
    asic.write_register(21,190)
    asic.write_register(18,197)

    # Create reference sample of -10keV range, limited sectors
    test1= vcal_noise_test_sector9(local_vcal=False,
                            sector_samples=100,
                            all_sectors=False,
                            vcal_values=[0])
    timenow = time.localtime()
    print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

def Diamond_10000samples_sector9_defaultsettings_highGain():
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

    asic.clear_register_bit(0,0b00000100)
    asic.clear_register_bit(0,0b00100000)
    asic.write_register(12,6)
    asic.write_register(14,20)
    asic.write_register(9,0b10001111)
    asic.write_register(17,174)
    asic.write_register(21,190)
    asic.write_register(18,197)

    # Create reference sample of -10keV range, limited sectors
    test1= vcal_noise_test_sector9(local_vcal=False,
                            sector_samples=1000,
                            all_sectors=False,
                            vcal_values=[0])
    timenow = time.localtime()
    print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

def Diamond_100000samples_sector9_defaultsettings_highGain():
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

    asic.clear_register_bit(0,0b00000100)
    asic.clear_register_bit(0,0b00100000)
    asic.write_register(12,6)
    asic.write_register(14,20)
    asic.write_register(9,0b10001111)
    asic.write_register(17,174)
    asic.write_register(21,190)
    asic.write_register(18,197)

    # Create reference sample of -10keV range, limited sectors
    test1= vcal_noise_test_sector9(local_vcal=False,
                            sector_samples=10000,
                            all_sectors=False,
                            vcal_values=[0])
    timenow = time.localtime()
    print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

def Diamond_400000samples_sector9_defaultsettings_highGain():
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

    asic.clear_register_bit(0,0b00000100)
    asic.clear_register_bit(0,0b00100000)
    asic.write_register(12,6)
    asic.write_register(14,20)
    asic.write_register(9,0b10001111)
    asic.write_register(17,174)
    asic.write_register(21,190)
    asic.write_register(18,197)

    # Create reference sample of -10keV range, limited sectors
    test1= vcal_noise_test_sector9(local_vcal=False,
                            sector_samples=40000,
                            all_sectors=False,
                            vcal_values=[0])
    timenow = time.localtime()
    print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))


def Diamond_overnight1_600000samplesPerGrap_sector9_defaultsettings_highGain():
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

    asic.clear_register_bit(0,0b00000100)
    asic.clear_register_bit(0,0b00100000)
    asic.write_register(12,6)
    asic.write_register(14,20)
    asic.write_register(9,0b10001111)
    asic.write_register(17,174)
    asic.write_register(21,190)
    asic.write_register(18,197)

    for i in range(14):
    # Create reference sample of -10keV range, limited sectors
        test1= vcal_noise_test_sector9(local_vcal=False,
                                sector_samples=60000,
                                all_sectors=False,
                                vcal_values=[0])
        timenow = time.localtime()
        print("Test {} complete {}:{}:{}".format(i,timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

def Diamond_overnight1_100samplesPerGrapTest_sector9_defaultsettings_highGain():
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

    asic.clear_register_bit(0,0b00000100)
    asic.clear_register_bit(0,0b00100000)
    asic.write_register(12,6)
    asic.write_register(14,20)
    asic.write_register(9,0b10001111)
    asic.write_register(17,174)
    asic.write_register(21,190)
    asic.write_register(18,197)

    for i in range(14):
    # Create reference sample of -10keV range, limited sectors
        test1= vcal_noise_test_sector9(local_vcal=False,
                                sector_samples=10,
                                all_sectors=False,
                                vcal_values=[0])
        timenow = time.localtime()
        print("Test {} complete {}:{}:{}".format(i,timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

def Diamond_overnight1_100000samplesPerGrap_sector9_defaultsettings_highGain():
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

    asic.clear_register_bit(0,0b00000100)
    asic.clear_register_bit(0,0b00100000)
    asic.write_register(12,6)
    asic.write_register(14,20)
    asic.write_register(9,0b10001111)
    asic.write_register(17,174)
    asic.write_register(21,190)
    asic.write_register(18,197)

    for i in range(78):
    # Create reference sample of -10keV range, limited sectors
        test1= vcal_noise_test_sector9(local_vcal=False,
                                sector_samples=10000,
                                all_sectors=False,
                                vcal_values=[0])
        timenow = time.localtime()
        print("Test {} complete {}:{}:{}".format(i,timenow.tm_hour, timenow.tm_min, timenow.tm_sec))


def Diamond_Chosensamples_sector9_defaultsettings_highGain(samples=1000,name_of_test='Diamond_Aug22'):
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

    asic.clear_register_bit(0,0b00000100)
    asic.clear_register_bit(0,0b00100000)
    asic.write_register(12,6)
    asic.write_register(14,20)
    asic.write_register(9,0b10001111)
    asic.write_register(17,174)
    asic.write_register(21,190)
    asic.write_register(18,197)

    # Create reference sample of -10keV range, limited sectors
    test1= store_sector_readout(sector_samples=samples,sector_array=[9],vcal_values=[0],test_name=name_of_test)
    timenow = time.localtime()
    print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

def Diamond_Chosensamples_sector9_defaultsettings_200keVGain(samples=1000,name_of_test='Diamond_Aug22'):
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

    asic.clear_register_bit(0,0b00000100)
    asic.clear_register_bit(0,0b00100000)
    asic.write_register(12,6)
    asic.write_register(14,20)
    asic.write_register(9,0b10001111)
    asic.write_register(17,174)
    asic.write_register(21,190)
    asic.write_register(18,197)

    # Create reference sample of -10keV range, limited sectors
    test1= store_sector_readout(sector_samples=samples,sector_array=[9],vcal_values=[0],test_name=name_of_test)
    timenow = time.localtime()
    print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

def Diamond_Chosensamples_sector9_defaultsettings_300keVGain(samples=1000,name_of_test='Diamond_Aug22'):
    #testing the effect of changing the negative range

    asic = get_context('asic')
    
    timenow = time.localtime()
    print("Begin test {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    # Perform global mode before running this test, includes reset
    set_global_mode()

    # Set the feedback capacitence to 7fF
    asic.set_register_bit(0, 0b00001000)
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
    asic.write_register(18,197)

    # Create reference sample of -10keV range, limited sectors
    test1= store_sector_readout(sector_samples=samples,sector_array=[9],vcal_values=[0],test_name=name_of_test)
    timenow = time.localtime()
    print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))


def Diamond_Overnight2_sector9_BiasRampScan_100keVGain():
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

    asic.clear_register_bit(0,0b00000100)
    asic.clear_register_bit(0,0b00100000)
    asic.write_register(12,6)
    asic.write_register(14,20)
    asic.write_register(9,0b10001111)
    asic.write_register(17,174)
    asic.write_register(21,190)
    asic.write_register(18,197)


    bias_ramp_list = [0b0000,0b0011,0b0111,0b1011,0b1111]

    for i in range(12):
        for j in range(len(bias_ramp_list)):
            asic.set_all_ramp_bias(bias_ramp_list[j])
            print("Set bias ramp to {}".format(str(bias_ramp_list[j])))

            # Create reference sample of -10keV range, limited sectors
            test1= store_sector_readout(sector_samples=100000,sector_array=[9],vcal_values=[0],test_index=j,test_name="Overnight_Ramp_Bias_Scan")
            timenow = time.localtime()
            print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))
    
def Diamond_Overnight2_sector9_BiasRampScan_100keVGain_Darks():
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

    asic.clear_register_bit(0,0b00000100)
    asic.clear_register_bit(0,0b00100000)
    asic.write_register(12,6)
    asic.write_register(14,20)
    asic.write_register(9,0b10001111)
    asic.write_register(17,174)
    asic.write_register(21,190)
    asic.write_register(18,197)


    bias_ramp_list = [0b0000,0b0011,0b0111,0b1011,0b1111]

    for j in range(len(bias_ramp_list)):
        asic.set_all_ramp_bias(bias_ramp_list[j])
        print("Set bias ramp to {}".format(str(bias_ramp_list[j])))

        # Create reference sample of -10keV range, limited sectors
        test1= store_sector_readout(sector_samples=10000,sector_array=[9],vcal_values=[0],test_index=j,test_name="Overnight_Ramp_Bias_Scan")
        timenow = time.localtime()
        print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))


def Diamond_Chosensamples_sector9_GlobalBias_100keVGain(samples=100000,global_bias=0b00000000):
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

    asic.clear_register_bit(0,0b00000100)
    asic.clear_register_bit(0,0b00100000)
    asic.write_register(12,6)
    asic.write_register(14,20)
    asic.write_register(9,0b10001111)
    asic.write_register(17,174)
    asic.write_register(21,190)
    asic.write_register(18,197)

    asic.write_register(130,global_bias)
    print("Set global bias to {}".format(global_bias))

    time.sleep(60)

    # Create reference sample of -10keV range, limited sectors
    test1= store_sector_readout(sector_samples=samples,sector_array=[9],vcal_values=[0],test_name="Diamond_Aug22_Global_Bias")
    timenow = time.localtime()
    print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))


def Diamond_Chosensamples_sector9_PLL_VoltageRegular_100keVGain_scan(samples=10000):
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

    asic.clear_register_bit(0,0b00000100)
    asic.clear_register_bit(0,0b00100000)
    asic.write_register(12,6)
    asic.write_register(14,20)
    asic.write_register(17,174)
    asic.write_register(21,190)
    asic.write_register(18,197)

    vregs = [0b10000000,0b10001000,0b10001100,0b10001110,0b10001111,0b10000100]

    for i in range(len(vregs)):
        asic.write_register(9,vregs[i])
        print("Set PLL Regulator bits to {}".format(vregs[i]))
        time.sleep(60)
        # Create reference sample of -10keV range, limited sectors
        test1= store_sector_readout(sector_samples=samples,sector_array=[9],vcal_values=[0],test_name="Diamond_Aug22_PLL_Voltage_Regulator")
        timenow = time.localtime()
        print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))


def Diamond_Chosensamples_sector9_PLL_ChargePump_100keVGain_scan(samples=10000):
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

    asic.clear_register_bit(0,0b00000100)
    asic.clear_register_bit(0,0b00100000)
    asic.write_register(12,6)
    asic.write_register(14,20)
    asic.write_register(17,174)
    asic.write_register(21,190)
    asic.write_register(18,197)

    vregs = [0b00001111,0b10001111,0b11001111,0b11101111,0b11111111]

    for i in range(len(vregs)):
        asic.write_register(9,vregs[i])
        print("Set PLL Charge Pump bits to {}".format(vregs[i]))
        time.sleep(60)
        # Create reference sample of -10keV range, limited sectors
        test1= store_sector_readout(sector_samples=samples,sector_array=[9],vcal_values=[0],test_name="Diamond_Aug22_PLL_Charge_Pump")
        timenow = time.localtime()
        print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

def Diamond_sector9_reset_scan_100keVGain(): 

    samples = 100000

    asic = get_context('asic') 
    timenow = time.localtime() 
    print("Begin test {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec)) 

    # Perform global mode before running this test, includes reset 
    set_global_mode() 
    
    # Set the feedback capacitence to 7fF   
    asic.set_register_bit(0, 0b00001000)   
    asic.clear_register_bit( 0, 0b00010000) 
       
    set_clock_config(205) # Use default 205 MHz TDC clock 
    asic.set_register_bit(0,0b01000000) 
    asic.set_all_ramp_bias(0b0000) 
    asic.clear_register_bit(0,0b00000100) 
    asic.clear_register_bit(0,0b00100000)
    asic.write_register(9,0b10001111) 
    asic.write_register(17,174) 
    asic.write_register(21,190) 
    asic.write_register(18,197) 
    
    for l in range(5):
        print("Starting loop {}".format(l))

        #pa & cds
        pa = [3,6,9,12]
        cds = [17,20,23,26]
        for i in range(len(pa)):
            asic.write_register(12,pa[i]) 
            asic.write_register(14,cds[i])
            
            print("Set Preamp reset to {}".format(pa[i]))
            print("Set CDS reset to {}".format(cds[i]))
            
            time.sleep(5)
            test1= store_sector_readout(sector_samples=samples,sector_array=[9],vcal_values=[0],test_index=i,test_name="Diamond_Aug22_constant_d14_gap") 
            timenow = time.localtime()  
            print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec)) 

            # Abort the sequence if requested
            if abort_sequence():
                return
        
        #gap & pa
        pa = [6,11,16,21,26,31,36]
        cds = [40,40,40,40,40,40,40]
        for i in range(len(pa)):
            asic.write_register(12,pa[i]) 
            asic.write_register(14,cds[i])
            
            print("Set Preamp reset to {}".format(pa[i]))
            print("Set CDS reset to {}".format(cds[i]))
            
            time.sleep(5)
            test1= store_sector_readout(sector_samples=samples,sector_array=[9],vcal_values=[0],test_index=i,test_name="Diamond_Aug22_constant_d40_cds") 
            timenow = time.localtime()  
            print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec)) 

            # Abort the sequence if requested
            if abort_sequence():
                return
        
        #gap & pa2
        pa = [3,6,9,12]
        cds = [20,20,20,20]
        for i in range(len(pa)):
            asic.write_register(12,pa[i]) 
            asic.write_register(14,cds[i])
            
            print("Set Preamp reset to {}".format(pa[i]))
            print("Set CDS reset to {}".format(cds[i]))
            
            time.sleep(5)
            test1= store_sector_readout(sector_samples=samples,sector_array=[9],vcal_values=[0],test_index=i,test_name="Diamond_Aug22_constant_d20_cds") 
            timenow = time.localtime()  
            print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec)) 

            # Abort the sequence if requested
            if abort_sequence():
                return
        
        #gap & cds
        pa = [6,6,6,6]
        cds = [15,20,25,30]
        for i in range(len(pa)):
            asic.write_register(12,pa[i]) 
            asic.write_register(14,cds[i])
            
            print("Set Preamp reset to {}".format(pa[i]))
            print("Set CDS reset to {}".format(cds[i]))
            
            time.sleep(5)
            test1= store_sector_readout(sector_samples=samples,sector_array=[9],vcal_values=[0],test_index=i,test_name="Diamond_Aug22_constant_d6_preamp") 
            timenow = time.localtime()  
            print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec)) 

            # Abort the sequence if requested
            if abort_sequence():
                return


def Diamond_sector9_reset_scan_100keVGain_darks(samples=10000): 

    asic = get_context('asic') 
    timenow = time.localtime() 
    print("Begin test {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec)) 

    # Perform global mode before running this test, includes reset 
    set_global_mode() 
    
    # Set the feedback capacitence to 7fF   
    asic.set_register_bit(0, 0b00001000)   
    asic.clear_register_bit( 0, 0b00010000) 
       
    set_clock_config(205) # Use default 205 MHz TDC clock 
    asic.set_register_bit(0,0b01000000) 
    asic.set_all_ramp_bias(0b0000) 
    asic.clear_register_bit(0,0b00000100) 
    asic.clear_register_bit(0,0b00100000)
    asic.write_register(9,0b10001111) 
    asic.write_register(17,174) 
    asic.write_register(21,190) 
    asic.write_register(18,197) 
    
    #pa & cds
    pa = [3,6,9,12]
    cds = [17,20,23,26]
    for i in range(len(pa)):
        asic.write_register(12,pa[i]) 
        asic.write_register(14,cds[i])
        
        print("Set Preamp reset to {}".format(pa[i]))
        print("Set CDS reset to {}".format(cds[i]))
        
        time.sleep(5)
        test1= store_sector_readout(sector_samples=samples,sector_array=[9],vcal_values=[0],test_index=i,test_name="Diamond_Aug22_constant_d14_gap") 
        timenow = time.localtime()  
        print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec)) 
    
    #gap & pa
    pa = [6,11,16,21,26,31,36]
    cds = [40,40,40,40,40,40,40]
    for i in range(len(pa)):
        asic.write_register(12,pa[i]) 
        asic.write_register(14,cds[i])
        
        print("Set Preamp reset to {}".format(pa[i]))
        print("Set CDS reset to {}".format(cds[i]))
        
        time.sleep(5)
        test1= store_sector_readout(sector_samples=samples,sector_array=[9],vcal_values=[0],test_index=i,test_name="Diamond_Aug22_constant_d40_cds") 
        timenow = time.localtime()  
        print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec)) 
    
    #gap & pa2
    pa = [3,6,9,12]
    cds = [20,20,20,20]
    for i in range(len(pa)):
       asic.write_register(12,pa[i]) 
       asic.write_register(14,cds[i])
       
       print("Set Preamp reset to {}".format(pa[i]))
       print("Set CDS reset to {}".format(cds[i]))
       
       time.sleep(5)
       test1= store_sector_readout(sector_samples=samples,sector_array=[9],vcal_values=[0],test_index=i,test_name="Diamond_Aug22_constant_d20_cds") 
       timenow = time.localtime()  
       print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec)) 
    
    #gap & cds
    pa = [6,6,6,6]
    cds = [15,20,25,30]
    for i in range(len(pa)):
       asic.write_register(12,pa[i]) 
       asic.write_register(14,cds[i])
       
       print("Set Preamp reset to {}".format(pa[i]))
       print("Set CDS reset to {}".format(cds[i]))
       
       time.sleep(5)
       test1= store_sector_readout(sector_samples=samples,sector_array=[9],vcal_values=[0],test_index=i,test_name="Diamond_Aug22_constant_d6_preamp") 
       timenow = time.localtime()  
       print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

def Si_Diamond_Chosensamples_sector11_defaultsettings_100keVGain(samples=1000,name_of_test='Diamond_Aug22_Si'):
    #testing the effect of changing the negative range

    asic = get_context('asic')
    
    timenow = time.localtime()
    print("Begin test {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))
    print("High Gain")

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

    asic.clear_register_bit(0,0b00000100)
    asic.clear_register_bit(0,0b00100000)
    asic.write_register(12,6)
    asic.write_register(14,20)
    asic.write_register(9,0b10001111)
    asic.write_register(17,174)
    asic.write_register(21,190)
    asic.write_register(18,197)

    # Create reference sample of -10keV range, limited sectors
    test1= store_sector_readout(sector_samples=samples,sector_array=[11],vcal_values=[0],test_name=name_of_test)
    timenow = time.localtime()
    print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

def Si_Diamond_Chosensamples_sector11_defaultsettings_200keVGain(samples=1000,name_of_test='Diamond_Aug22_Si'):
    #testing the effect of changing the negative range

    asic = get_context('asic')
    
    timenow = time.localtime()
    print("Begin test {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))
    print("Medium Gain")

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

    asic.clear_register_bit(0,0b00000100)
    asic.clear_register_bit(0,0b00100000)
    asic.write_register(12,6)
    asic.write_register(14,20)
    asic.write_register(9,0b10001111)
    asic.write_register(17,174)
    asic.write_register(21,190)
    asic.write_register(18,197)

    # Create reference sample of -10keV range, limited sectors
    test1= store_sector_readout(sector_samples=samples,sector_array=[11],vcal_values=[0],test_name=name_of_test)
    timenow = time.localtime()
    print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

def Si_Diamond_Chosensamples_sector11_defaultsettings_300keVGain(samples=1000,name_of_test='Diamond_Aug22_Si'):
    #testing the effect of changing the negative range


    asic = get_context('asic')
    
    timenow = time.localtime()
    print("Begin test {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))
    print("Low gain")

    # Perform global mode before running this test, includes reset
    set_global_mode()

    # Set the feedback capacitence to 7fF
    asic.set_register_bit(0, 0b00001000)
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
    asic.write_register(18,197)

    # Create reference sample of -10keV range, limited sectors
    test1= store_sector_readout(sector_samples=samples,sector_array=[11],vcal_values=[0],test_name=name_of_test)
    timenow = time.localtime()
    print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

def Si_Diamond_sector11_Overnight_100keVGain_darks(): 

    samples = 10000

    asic = get_context('asic') 
    timenow = time.localtime() 
    print("Begin test {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec)) 

    # Perform global mode before running this test, includes reset 
    set_global_mode() 
    
    # Set the feedback capacitence to 7fF   
    asic.set_register_bit(0, 0b00001000)   
    asic.clear_register_bit( 0, 0b00010000) 
       
    set_clock_config(205) # Use default 205 MHz TDC clock 
    asic.set_register_bit(0,0b01000000) 
    asic.set_all_ramp_bias(0b0000) 
    asic.clear_register_bit(0,0b00000100) 
    asic.clear_register_bit(0,0b00100000)
    asic.write_register(9,0b10001111) 
    asic.write_register(17,174) 
    asic.write_register(21,190) 
    asic.write_register(18,197) 

    asic.write_register(12,6)
    asic.write_register(14,20)

    print("Reset reset off to experiment defautl - now starting ramp bias scans")

    bias_ramp_list = [0b0000,0b0011,0b0111,0b1011,0b1111]

    # for j in range(len(bias_ramp_list)):
    #     asic.set_all_ramp_bias(bias_ramp_list[j])
    #     print("Set bias ramp to {}".format(str(bias_ramp_list[j])))

    #     # Create reference sample of -10keV range, limited sectors
    #     test1= store_sector_readout(sector_samples=samples,sector_array=[11],vcal_values=[0],test_index=j,test_name="Diamond_Aug22_Si_Ramp_Bias_Scan")
    #     timenow = time.localtime()
    #     print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))
    

    asic.set_all_ramp_bias(0b0000)
    print("Reset the ramp bias to experiment default - now starting reset scans")

    #pa & cds
    pa = [3,6,9,12]
    cds = [17,20,23,26]
    for i in range(len(pa)):
        asic.write_register(12,pa[i]) 
        asic.write_register(14,cds[i])
        
        print("Set Preamp reset to {}".format(pa[i]))
        print("Set CDS reset to {}".format(cds[i]))
        
        time.sleep(5)
        test1= store_sector_readout(sector_samples=samples,sector_array=[11],vcal_values=[0],test_index=i,test_name="Diamond_Aug22_Si_constant_d14_gap") 
        timenow = time.localtime()  
        print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec)) 
    
    #gap & pa
    pa = [6,11,16,21,26,31,36]
    cds = [40,40,40,40,40,40,40]
    for i in range(len(pa)):
        asic.write_register(12,pa[i]) 
        asic.write_register(14,cds[i])
        
        print("Set Preamp reset to {}".format(pa[i]))
        print("Set CDS reset to {}".format(cds[i]))
        
        time.sleep(5)
        test1= store_sector_readout(sector_samples=samples,sector_array=[11],vcal_values=[0],test_index=i,test_name="Diamond_Aug22_Si_constant_d40_cds") 
        timenow = time.localtime()  
        print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec)) 
    
    #gap & pa2
    pa = [3,6,9,12]
    cds = [20,20,20,20]
    for i in range(len(pa)):
        asic.write_register(12,pa[i]) 
        asic.write_register(14,cds[i])
        
        print("Set Preamp reset to {}".format(pa[i]))
        print("Set CDS reset to {}".format(cds[i]))
        
        time.sleep(5)
        test1= store_sector_readout(sector_samples=samples,sector_array=[11],vcal_values=[0],test_index=i,test_name="Diamond_Aug22_Si_constant_d20_cds") 
        timenow = time.localtime()  
        print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec)) 
    
    #gap & cds
    pa = [6,6,6,6]
    cds = [15,20,25,30]
    for i in range(len(pa)):
        asic.write_register(12,pa[i]) 
        asic.write_register(14,cds[i])
        
        print("Set Preamp reset to {}".format(pa[i]))
        print("Set CDS reset to {}".format(cds[i]))
        
        time.sleep(5)
        test1= store_sector_readout(sector_samples=samples,sector_array=[11],vcal_values=[0],test_index=i,test_name="Diamond_Aug22_Si_constant_d6_preamp") 
        timenow = time.localtime()  
        print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec)) 

def Si_Diamond_sector11_Overnight_100keVGain(): 

    samples = 100000

    asic = get_context('asic') 
    timenow = time.localtime() 
    print("Begin test {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec)) 

    # Perform global mode before running this test, includes reset 
    set_global_mode() 
    
    # Set the feedback capacitence to 7fF   
    asic.set_register_bit(0, 0b00001000)   
    asic.clear_register_bit( 0, 0b00010000) 
       
    set_clock_config(205) # Use default 205 MHz TDC clock 
    asic.set_register_bit(0,0b01000000) 
    asic.set_all_ramp_bias(0b0000) 
    asic.clear_register_bit(0,0b00000100) 
    asic.clear_register_bit(0,0b00100000)
    asic.write_register(9,0b10001111) 
    asic.write_register(17,174) 
    asic.write_register(21,190) 
    asic.write_register(18,197) 
    
    for l in range(5):

        print("Starting loop {}".format(l))

        asic.write_register(12,6)
        asic.write_register(14,20)

        print("Reset reset off to experiment defautl - now starting ramp bias scans")

        bias_ramp_list = [0b0000,0b0011,0b0111,0b1011,0b1111]

        for j in range(len(bias_ramp_list)):
            asic.set_all_ramp_bias(bias_ramp_list[j])
            print("Set bias ramp to {}".format(str(bias_ramp_list[j])))

            # Create reference sample of -10keV range, limited sectors
            test1= store_sector_readout(sector_samples=samples,sector_array=[11],vcal_values=[0],test_index=j,test_name="Diamond_Aug22_Si_Ramp_Bias_Scan")
            timenow = time.localtime()
            print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))
        

        asic.set_all_ramp_bias(0b0000)
        print("Reset the ramp bias to experiment default - now starting reset scans")

        #pa & cds
        pa = [3,6,9,12]
        cds = [17,20,23,26]
        for i in range(len(pa)):
            asic.write_register(12,pa[i]) 
            asic.write_register(14,cds[i])
            
            print("Set Preamp reset to {}".format(pa[i]))
            print("Set CDS reset to {}".format(cds[i]))
            
            time.sleep(5)
            test1= store_sector_readout(sector_samples=samples,sector_array=[11],vcal_values=[0],test_index=i,test_name="Diamond_Aug22_Si_constant_d14_gap") 
            timenow = time.localtime()  
            print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec)) 
        
        #gap & pa
        pa = [6,11,16,21,26,31,36]
        cds = [40,40,40,40,40,40,40]
        for i in range(len(pa)):
            asic.write_register(12,pa[i]) 
            asic.write_register(14,cds[i])
            
            print("Set Preamp reset to {}".format(pa[i]))
            print("Set CDS reset to {}".format(cds[i]))
            
            time.sleep(5)
            test1= store_sector_readout(sector_samples=samples,sector_array=[11],vcal_values=[0],test_index=i,test_name="Diamond_Aug22_Si_constant_d40_cds") 
            timenow = time.localtime()  
            print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec)) 
        
        #gap & pa2
        pa = [3,6,9,12]
        cds = [20,20,20,20]
        for i in range(len(pa)):
            asic.write_register(12,pa[i]) 
            asic.write_register(14,cds[i])
            
            print("Set Preamp reset to {}".format(pa[i]))
            print("Set CDS reset to {}".format(cds[i]))
            
            time.sleep(5)
            test1= store_sector_readout(sector_samples=samples,sector_array=[11],vcal_values=[0],test_index=i,test_name="Diamond_Aug22_Si_constant_d20_cds") 
            timenow = time.localtime()  
            print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec)) 
        
        #gap & cds
        pa = [6,6,6,6]
        cds = [15,20,25,30]
        for i in range(len(pa)):
            asic.write_register(12,pa[i]) 
            asic.write_register(14,cds[i])
            
            print("Set Preamp reset to {}".format(pa[i]))
            print("Set CDS reset to {}".format(cds[i]))
            
            time.sleep(5)
            test1= store_sector_readout(sector_samples=samples,sector_array=[11],vcal_values=[0],test_index=i,test_name="Diamond_Aug22_Si_constant_d6_preamp") 
            timenow = time.localtime()  
            print("Test 1 complete {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec)) 
