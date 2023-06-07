import time
from pathlib import Path

# asic_spi.py
provides = [
'spi_read_reg',
'spi_write_reg',
'spi_read_burst',
'test_12bit_output',
'asic_reset',
'set_global_mode',
'sequence_2',
'change_to_external_bias',
'reset_safe_time',
'paged_register_test',
'shift_register_test',
'read_test_pattern',
'write_test_pattern',
'write_test_pattern2',
'write_test_pattern3',
'tdc_enable_local_vcal',
'lower_serialiser_bias',
'calibration_set_firstpixel',
'read_all_sector_gradient',
'all_sector_cal_capture',
'set_all_ram_bias',
'set_clock_config',
'printdir',
'serialiser_global_change',
'store_sector_readout',
'ASIC_register_dump',
'printcmds',
'timedel',
'set_experiment_session_name',
'get_experiment_session_name',
]

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

    # Force ASIC to 'forget' cached values that now may not be validCdZnTe_D320771_0V_initialTest_currentSettings_10000sampleshex(value)))

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

    print("Writing 4095 to sector {0}".format(sector))

def write_test_pattern3(sector=0):

    values = range(1000,3100,100)

    full_test_array = []
    for i in range(20):
        value = values[i]
        byte_a = (value >> 4) & 0xFF
        byte_b = ((value & 0x0F) << 4) | ((value & 0xF00) >> 8)
        byte_c = value & 0x0FF

        print('Representing value {} as bytes {} for sector {}'.format(value, [byte_a, byte_b, byte_c], i))
        # return

        # Add the triple byte to the array for each 12-bit pixel pair
        for pixel_pair in range(0, 8):
            full_test_array.append(byte_a)
            full_test_array.append(byte_b)
            full_test_array.append(byte_c)

    asic = get_context('asic')

    asic.write_register(0x07, 0x01 | (sector<<2))

    values_out = [0xFF for x in range(0, 480)]

    asic.burst_write(127, full_test_array)

    # Test reg to write mode and select image sector 0
    asic.write_register(0x07, 0x03 | (sector<<2))

    print("Writing scaling pattern to sector {0}".format(sector))

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
    elif pattern == 9:
        pass


    calibration_pattern = calibration_y + calibration_x
    print("Calibrating with pattern {}: {}".format(pattern, calibration_pattern))

    # Burst write to the calibration register
    asic.burst_write(126, calibration_pattern)


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


def printdir():
    asic = get_context('asic')
    carrier = get_context('carrier')

    print(dir(asic))
    print(dir(carrier))


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


# Use this in preference to vcal_noise_test
'''
sector_samples:
    Number of samples to take for each sector supplied
sector_array:
    An array of sector numbers that will be collected, all samples from each in turn
vcal_values:
    If multiples values are selected, each sector * sector samples will be sampled
    after changing the VCAL setting to each desired value.
test_name: (optional)
    A human name for the test. The results will be placed in a folder of this name
    with named files to distinguish results from different tests.
test_index: (optional)
    An index that will also be included in the filename, can be useful if a certain
    property is incremented over a set of tests.
suppress_progress_update: (optional)
    If set True, the progress bar will not be updated with the progress of samples
    taken. This could be useful if the caller wants to operate the progress bar with
    an external count.
timesleep: (optional)
    timesleep will sleep briefly before each sample reading. The minimum this can be
    set to keep the UI responsive is 1ms, which incurs ~20% time penalty. If it is
    set to 0, will run flat-out but freeze the UI.
'''
def store_sector_readout(sector_samples=50, sector_array=[9], vcal_values=[0.2, 0.5, 1.0], test_name='', test_suffix='', test_index=0, suppress_progress_update=False, timesleep=0.001):
    mercury_carrier = get_context('carrier')

    # Create a new destination directory for this batch of tests, using the current session
    export_root = "/opt/loki-detector/exports/" + get_experiment_session_name() + "/"
    export_subdir = export_root + test_name

    # Create the test directory if it does not exist
    Path(export_subdir).mkdir(parents=True, exist_ok=True)

    # Determine filename to store results in, based on test name and timestamp
    time_now = time.localtime()
    time_str = "{:04d}{:02d}{:02d}_{:02d}{:02d}{:02d}".format(time_now.tm_year, time_now.tm_mon, time_now.tm_mday, time_now.tm_hour, time_now.tm_min, time_now.tm_sec, int((time.time() % 1) * 1000))
    filename = "{}/{}_{}_{}_{}.csv".format(export_subdir, test_name, test_suffix, test_index, time_str)
    print("\tWill write to {}".format(filename))

    for vcal_setting in vcal_values:
        # Set the new vcal voltage
        mercury_carrier.set_vcal_in(vcal_setting)

        # Read out results from select sectors
        for sector in sector_array:
            print("\tBegin reading samples for sector {} with VCAL: {}".format(sector, vcal_setting))
            time.sleep(0.5)

            # Sample the sector by the number of times specified, one at a time
            with open(filename, 'a') as file:
                for sector_sample_number in range(0, sector_samples):
                    # Force a delay to keep the UI responsive (stops lock-up)
                    time.sleep(timesleep)

                    # Update progress bar
                    if not suppress_progress_update:
                        set_progress(sector_sample_number, sector_samples)

                    # Check if an execution abort has been requested
                    if abort_sequence():
                        # A cleaner solution would be to simply return, which would allow the caller
                        # to perform their own cleanup. However, this will stop execution even if the
                        # caller never checks the flag.
                        raise Exception('Sequence has been aborted')
                        #return

                    sample = read_test_pattern(sector=sector, num_samples=1, store=False, printout=False)[0]

                    # Store some setup settings in the first column
                    first_columns = [vcal_setting, sector, sector_sample_number]

                    # Write a line for each sample, with sample number, sector and vcal setting
                    # Only open the file to write for each sample (minimal RAM impact)
                    # with open(filename, 'a') as file:
                    file.write(','.join([str(x) for x in (first_columns + sample)]))
                    file.write('\n')

    print("\tVCAL samples gathered and stored in {}".format(filename))

    return filename

def ASIC_register_dump(path='/opt/loki-detector/exports/regdumps/', prefix='HEXITEC-MHz-Dump-', include_shift_regs=False):
    time_now = time.gmtime()
    filename = path + prefix + '-'.join( [str(x) for x in [time_now.tm_year, time_now.tm_mon, time_now.tm_mday, time_now.tm_hour, time_now.tm_min, time_now.tm_sec]]) + '.csv'

    # Create the output directory if it does not exist
    Path(path).mkdir(parents=True, exist_ok=True)

    asic = get_context('asic')

    print("Reading full set of ASIC registers...")
    with open(filename, 'w') as f:
        # Read registers from the first page
        regdump_firstpage_singles = asic.burst_read(0, 126)[1:] # 0 - 125, first value is echo
        for regnum in range(0, 126):
            f.write('{},{}\n'.format(regnum, regdump_firstpage_singles[regnum]))
            set_progress(regnum, 126 + 20 + 480 + 16)
        print("\tPage 1 Single Registers (<126) Done")

        # Read shift registers manually because read-through behaviour is unknown
        if include_shift_regs:
            regdump_126 = asic.burst_read(126, 20)[1:]
            f.write('126,{}\n'.format('-'.join([str(x) for x in regdump_126])))
            set_progress(126 + 20, 126 + 20 + 480 + 16)
            print("\tPage 1 Shift Register 126 Done")
            regdump_127 = asic.burst_read(127, 480)[1:]
            f.write('127,{}\n'.format('-'.join([str(x) for x in regdump_127])))
            set_progress(126 + 20 + 480, 126 + 20 + 480 + 16)
            print("\tPage 1 Shift Register 127 Done")

        # Read registers from the second page (16 registers, starting at 130)
        regdump_secondpage_singles = asic.burst_read(130, 16)[1:]
        for regcount in range(0, 16):
            regnum = regcount + 130
            f.write('{},{}\n'.format(regnum, regdump_secondpage_singles[regcount]))
            set_progress(126 + 20 + 480 + regcount, 126 + 20 + 480 + 16)
        print("\tPage 2 Single Registers Done")

def printcmds():
    asic = get_context('asic')
    carrier = get_context('carrier')

    asic_dir = dir(asic)
    carrier_dir = dir(carrier)

    # Filter hidden functions
    asic_dir = [i for i in asic_dir if not i.startswith('_')]
    carrier_dir = [i for i in carrier_dir if not i.startswith('_')]

    print("ASIC Functions: ", "\n\t".join(asic_dir))
    print("Carrier Functions: ", "\n\t".join(carrier_dir))

def timedel():
    time.sleep(10)

SESSION_NAME_FILE_LOCATION = '/opt/loki-detector/exports/SESSION'
SESSION_NAME_READ_DUE = True                                        # If file not read yet
SESSION_NAME = None
def set_experiment_session_name(session_name='default'):
    # Allow the user to store a non-volatile (assumed) session name
    # that will define the folder all experiments will be saved to
    # (within their own sub-folders). This is stored within the
    # exports directory, which for an experimental setup will have
    # been bound to a non-volatile filesystem.

    with open(SESSION_NAME_FILE_LOCATION, 'w') as f:
        f.write(session_name)
        SESSION_NAME_READ_DUE = True
        print("Saved new session name as {}".format(session_name))

def get_experiment_session_name():
    # Return the above stored session name, or a default value if one
    # has not been set.

    if SESSION_NAME_READ_DUE:
        try:
            with open(SESSION_NAME_FILE_LOCATION, 'r') as f:
                session_name = f.readline()
                print("Recovered session name {} from file".format(session_name))
                return session_name
        except FileNotFoundError:
            print("Failed to recover session name, using default")
            return 'default'
    else:
        return SESSION_NAME
