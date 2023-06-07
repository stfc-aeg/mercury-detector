import time
import os

provides = [
        'fastdata_quickstart',
        'single_capture',
        'example_extended_capture',
]

requires = [
        'serialiser_tests',
        '_9_gpib_support',
        'utility',
        'diamond202212_support',
        ]

def fastdata_quickstart(bypass_asic_reset=False, bypass_diamond_default_registers=False):
    asic = get_context('asic')
    carrier = get_context('carrier')
    print("Preparing to enable fast data:")

    progress_steps = 7
    progress_count = 0

    # Power Cycle The Regulators
    # carrier.vreg_power_cycle_init(None)
    # while not self._get_vreg_en():
    #     pass
    if not carrier.get_vreg_en():
        raise Exception('Regulators are not enabled')
    progress_count = progress_count + 1; set_progress(progress_count, progress_steps);

    # Ensure FireFlies are Turned on, all channels
    print("\tChecking FireFlies are enabled")
    for FF_ID in [1, 2]:                        # Both FireFlies
        while True:                             # Loop until all channels enabled

            # Search for any disabled channel
            disabled_channel_found = False
            for channel_no in range(0, 12):
                if carrier.get_firefly_tx_channel_disabled(FF_ID, channel_no):
                    print("\t\tChannel {} of FireFly {} is disabled".format(channel_no, FF_ID))
                    disabled_channel_found = True
                    break

            # If any disabled channel is found, re-enable all channels on both devices
            if disabled_channel_found:
                print("\t\tEnabling all FireFly Channels on FireFly {} (at least one found disabled)".format(FF_ID))
                time.sleep(1.0)
                carrier.set_firefly_tx_enable_all()   # Set all channels enabled
                time.sleep(3.0)
            else:
                print("\tAll channels on FireFly {} are enabled".format(FF_ID))
                break
    progress_count = progress_count + 1; set_progress(progress_count, progress_steps);

    # Enter Global Mode
    if bypass_asic_reset:
        if asic.get_enabled:
            print("\tASIC enabled, and bypassing global mode reset")
        else:
            raise Excetion("ASIC reset cannot be bypassed if ASIC is in reset")
    else:
        print("\tEntering global mode...")
        asic.enter_global_mode()
    progress_count = progress_count + 1; set_progress(progress_count, progress_steps);

    # Setting Diamond Default Registers
    if not bypass_diamond_default_registers:
        Set_DiamondDefault_Registers()
        print("\tDIAMOND default registers set")
    else:
        print("\tDIAMOND default register settings skipped")
    progress_count = progress_count + 1; set_progress(progress_count, progress_steps);

    # Enter and Exit Serialiser Reset
    print("\tResetting Serialisers...")
    time.sleep(0.5)
    ser_enter_reset()
    time.sleep(0.5)
    ser_exit_reset()
    progress_count = progress_count + 1; set_progress(progress_count, progress_steps);

    # Enter Bonding Mode
    print("\tEntering Bonding Mode...")
    time.sleep(0.5)
    enter_bonding_mode()
    progress_count = progress_count + 1; set_progress(progress_count, progress_steps);

    # Enter Data Mode
    print("\tEntering Data Mode...")
    time.sleep(0.5)
    enter_data_mode()
    progress_count = progress_count + 1; set_progress(progress_count, progress_steps);

    print("Device is now outputting fast data")

def log_instrument_values(output_fullpath, output_filename, associated_data_file="", log_localtime=None):
    carrier = get_context('carrier')

    # should have .csv extension
    if '.csv' not in output_filename:
        output_filename = output_filename + '.csv'

    # Get latest readings
    try:
        vol, cur = get_psu_measurements()
        temp = get_peltier_status()
    except Exception as e:
        print('Failed to retrieve instrument readings; {}'.format(e))
        return

    # Get ASIC Temperature Reading from carrier
    asic_temp = carrier.get_cached_asic_temperature()

    # Get latest time if one is not supplied
    if log_localtime is None:
        log_localtime = time.localtime()

    # Format the time code
    datefmt = '{:02d}/{:02d}/{:04d}'.format(
            log_localtime.tm_mday,
            log_localtime.tm_mon,
            log_localtime.tm_year)
    timefmt = '{:02d}:{:02d}:{:02d}'.format(
            log_localtime.tm_hour,
            log_localtime.tm_min,
            log_localtime.tm_sec)

    # If the file does not exist, attempt to create it, along with header row
    if not os.path.exists(output_fullpath + '/' + output_filename):
        try:
            os.makedirs(output_fullpath)
        except FileExistsError:
            #raise Exception('This directory has already been used, choose another')
            pass

        with open(output_fullpath + '/' + output_filename, 'a') as file:
            file.write(','.join(['date','time','asic temperature', 'peltier temperature','bias current','bias voltage', 'file']))
            file.write('\n')
            print('Instrument data will be stored in {}'.format(output_fullpath + '/' + output_filename))

    # Write data to the file
    with open(output_fullpath + '/' + output_filename, 'a') as file:
        file.write(','.join([str(x) for x in [datefmt, timefmt, asic_temp, temp, cur, vol, associated_data_file]]))
        file.write('\n')

def example_extended_capture(output_folder="default", filename="capture", suffix="", ignore_instrument_info=False, period_s=600, interval_s=60, num_frames=100000, num_batches=1, timeout=20):
    # This will demonstrate what it might be like to log ASIC bias measurements as well
    # as capturing data spaced out over a long period of time.
    # Suffix is used to record parameter values along with the data. This will be split 
    # per file for fast data, but grouped for instrument readings.

    carrier = get_context('carrier')
    asic = get_context('asic')
    gpib = get_context('gpib')
    munir = get_context('munir')

    # Check filename is not too large. 32 is max, and 4 to be conservative in case names are auto generated
    if len(filename) >= (100-4):
        raise Exception('Filename was too long ({} vs 32)'.format(len(filename)))

    # Fast data is stored on seneca, and instrument data on loki
    fastdata_output_root = "/mnt/raid/loki/" + output_folder + '/'
    loki_output_root = "/opt/loki-detector/exports/instrumentdata/" + output_folder + "/"

    # Check that the ASIC has been brought into data mode
    if carrier.get_asic_serialiser_mode() != 'data':
        raise Exception('ASIC is not in data mode. Has fastdata_quickstart() been executed?')

    # Ensure that the loki path has been created (cannot do the fast data path as not this machine)
    try:
        os.makedirs(loki_output_root)
    except FileExistsError:
        #raise Exception('This directory has already been used, choose another')
        pass

    localtime_teststart= time.localtime()

    # Loop for 10 mins, capturing 100,000 frames (one file) each 1 minute
    total_period_s = period_s
    interval_s = interval_s
    time_start = time.time()
    time_end = time_start + total_period_s
    capture_count = 0
    while (time.time() < time_end):
        #set_progress(capture_count, total_period_s / interval_s)
        print('\n')
        print('Starting new capture {}/{}'.format(capture_count, total_period_s / interval_s))

        # Generate the file name to store data in for this capture with appended date & count
        data_filename = "{}_{:04d}{:02d}{:02d}-{:02d}{:02d}{:02d}_{}".format(
                filename + '_' + suffix,
                localtime_teststart.tm_year,
                localtime_teststart.tm_mon,
                localtime_teststart.tm_mday,
                localtime_teststart.tm_hour,
                localtime_teststart.tm_min,
                localtime_teststart.tm_sec,
                capture_count)

        # Log PSU measurements, file shares folder and filename with experimental fast data
        # Output filename will match the data capture filename
        if not ignore_instrument_info:
            log_instrument_values(
                output_fullpath=loki_output_root,
                output_filename=filename, 
                associated_data_file=data_filename)

        return_code = capture_data(
            path=fastdata_output_root,
            file_name=data_filename,
            num_frames=num_frames,
            num_batches=num_batches,
            include_stdout=True,
            timeout=timeout
        )

        if return_code != 0:
            raise Exception('Capture failed, aborting run')

        capture_count += 1
        #set_progress(capture_count, total_period_s / interval_s)

        # If this was the last capture, end early
        if (time.time() + interval_s) > time_end:
            return

        print('Delaying for {}s until next capture...'.format(interval_s))
        if _sleep_abortable(interval_s): return

def single_capture(output_folder = "default", filename = "capture", suffix="", num_frames = 100000, num_batches = 1, timeout=20):
    output_folder = 'dssg/' + output_folder
    example_extended_capture(
        output_folder=output_folder,
        filename=filename,
        suffix=suffix,
        ignore_instrument_info=False,
        period_s=10,
        interval_s=100,
        num_frames=num_frames,
        num_batches=num_batches,
        timeout=timeout)

