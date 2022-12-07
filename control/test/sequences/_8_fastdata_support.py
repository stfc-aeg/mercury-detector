import time
import os

provides = [
        'example_extended_capture',
        'fastdata_quickstart'
]

requires = [
        'serialiser_tests',
        '_9_gpib_support',
        'utility',
        ]

def fastdata_quickstart(bypass_asic_reset=False):
    asic = get_context('asic')
    carrier = get_context('carrier')
    print("Preparing to enable fast data:")

    # Power Cycle The Regulators
    # carrier.vreg_power_cycle_init(None)
    # while not self._get_vreg_en():
    #     pass
    if not carrier.get_vreg_en():
        raise Exception('Regulators are not enabled')
    set_progress(1, 6)

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
    set_progress(2, 6)

    # Enter Global Mode
    if bypass_asic_reset:
        if asic.get_enabled:
            print("\tASIC enabled, and bypassing global mode reset")
        else:
            raise Excetion("ASIC reset cannot be bypassed if ASIC is in reset")
    else:
        print("\tEntering global mode...")
        asic.enter_global_mode()
    set_progress(3, 6)

    # Enter and Exit Serialiser Reset
    print("\tResetting Serialisers...")
    time.sleep(0.5)
    ser_enter_reset()
    time.sleep(0.5)
    ser_exit_reset()
    set_progress(4, 6)

    # Enter Bonding Mode
    print("\tEntering Bonding Mode...")
    time.sleep(0.5)
    enter_bonding_mode()
    set_progress(5, 6)

    # Enter Data Mode
    print("\tEntering Data Mode...")
    time.sleep(0.5)
    enter_data_mode()
    set_progress(6, 6)

    print("Device is now outputting fast data")

def log_instrument_values(output_fullpath, output_filename, log_localtime=None):
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
            file.write(','.join(['date','time','peltier temperature','bias current','bias voltage']))
            file.write('\n')
            print('Instrument data will be stored in {}'.format(output_fullpath + '/' + output_filename))

    # Write data to the file
    with open(output_fullpath + '/' + output_filename, 'a') as file:
        file.write(','.join([str(x) for x in [datefmt, timefmt, temp, cur, vol]]))
        file.write('\n')


def example_extended_capture(output_folder="default", filename="capture", store_instrument_info=False, period_s=600, interval_s=60):
    # This will demonstrate what it might be like to log ASIC bias measurements as well
    # as capturing data spaced out over a long period of time.
    carrier = get_context('carrier')
    asic = get_context('asic')
    gpib = get_context('gpib')
    munir = get_context('munir')

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
        set_progress(capture_count, total_period_s / interval_s)
        print('\n')
        print('Starting new capture {}/{}'.format(capture_count, total_period_s / interval_s))

        # Log PSU measurements, file shares folder and filename with experimental fast data
        if store_instrument_info:
            log_instrument_values(loki_output_root, filename)

        return_code = capture_data(
            path=fastdata_output_root,
            file_name="{}_{:04d}{:02d}{:02d}-{:02d}{:02d}{:02d}_{}".format(filename,
                localtime_teststart.tm_year,
                localtime_teststart.tm_mon,
                localtime_teststart.tm_mday,
                localtime_teststart.tm_hour,
                localtime_teststart.tm_min,
                localtime_teststart.tm_sec,
                capture_count),
            num_frames=100000,
            num_batches=1,
            include_stdout=True
        )

        if return_code != 0:
            raise Exception('Capture failed, aborting run')

        capture_count += 1
        set_progress(capture_count, total_period_s / interval_s)

        print('Delaying for {}s until next capture...'.format(interval_s))
        if _sleep_abortable(interval_s): return
