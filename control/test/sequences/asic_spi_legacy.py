import time

provides = [
    'vcal_noise_test',
    'vcal_noise_test_subsection',
    'vcal_noise_test_sector9',
    'vcal_noise_test_sector10',
    'vcal_noise_test_sector11',
]
requires = [
    'asic_spi'
]

# LEGACY: DO NOT USE (see store_sector_readout() instead)
def vcal_noise_test(local_vcal=False, sector_samples=50, all_sectors=False, vcal_values=[0.2, 0.5, 1.0]):
    mercury_carrier = get_context('carrier')
    asic = get_context('asic')

    if local_vcal:
        print("Enable TDC local vcal mode")
        tdc_enable_local_vcal()
        title = 'vcal_noise'
    else:
        title = 'DIAMOND_beamtime'

    if all_sectors:
        sector_array = range(0,20)
    else:
        sector_array = [0, 9, 19]

    time_now = time.localtime()
    #filename = "/opt/loki-detector/exports/" + title + "_{:04d}{:02d}{:02d}_{:02d}{:02d}{:02d}".format(time_now.tm_year, time_now.tm_mon, time_now.tm_mday, time_now.tm_hour, time_now.tm_min, time_now.tm_sec, int((time.time() % 1) * 1000)) + '.csv'
    filename = "/opt/loki-detector/exports/" + title + "_{:04d}{:02d}{:02d}_{:02d}{:02d}{:02d}".format(time_now.tm_year, time_now.tm_mon, time_now.tm_mday, time_now.tm_hour, time_now.tm_min, time_now.tm_sec, int((time.time() % 1) * 1000))
    print("Will write to {}".format(filename))
    time.sleep(3)

    #   with open(filename, 'w') as file:
    #       for vcal_setting in vcal_values:
    #           # Set the new VCAL voltage
    #           mercury_carrier.set_vcal_in(vcal_setting)

    #           # Read out the results from select sectors
    #           for sector in sector_array:
    #               print("Begin reading samples for sector {} with VCAL: {}".format(sector, vcal_setting))
    #               time.sleep(0.5)

    #               # Sample the sector 50 times
    #               samples_out = read_test_pattern(sector=sector, num_samples=sector_samples, store=False, printout=False)

    #               # Write a line for each sample, with sample number, sector and vcal setting
    #               for i in range(0,len(samples_out)):
    #                   sample = samples_out[i]
    #                   first_columns = [vcal_setting, sector, i]
    #                   file.write(','.join([str(x) for x in (first_columns + sample)]))
    #                   file.write('\n')

    for vcal_setting in vcal_values:
        # Set the new VCAL voltage
        mercury_carrier.set_vcal_in(vcal_setting)

        # Read out the results from select sectors
        for sector in sector_array:
            print("Begin reading samples for sector {} with VCAL: {}".format(sector, vcal_setting))
            time.sleep(0.5)

            for i in range(0, sector_samples):
                with open(filename+"{}.csv".format(sector), 'a') as file:
                    sample = asic.read_test_pattern(sector) # Get 12-bit sample
                    first_columns = [vcal_setting, sector, i]
                    file.write(','.join([str(x) for x in (first_columns + sample)]))
                    file.write('\n')

                # Check if an execution abort has been requested
                if abort_sequence():
                    return

    print("VCAL samples gathered and stored in {}".format(filename))

    return filename

# LEGACY: do not use
def vcal_noise_test_subsection(local_vcal=False, sector_samples=50, all_sectors=False, vcal_values=[0.2, 0.5, 1.0]):
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
        sector_array = [0, 4, 9, 14, 19]

    time_now = time.localtime()
    filename = "/opt/loki-detector/exports/" + title + "_{:04d}{:02d}{:02d}_{:02d}{:02d}{:02d}".format(time_now.tm_year, time_now.tm_mon, time_now.tm_mday, time_now.tm_hour, time_now.tm_min, time_now.tm_sec, int((time.time() % 1) * 1000)) + '.csv'
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

# LEGACY: do not use
def vcal_noise_test_sector9(local_vcal=False, sector_samples=50, all_sectors=False, vcal_values=[0.2, 0.5, 1.0]):
    mercury_carrier = get_context('carrier')

    if local_vcal:
        print("Enable TDC local vcal mode")
        tdc_enable_local_vcal()
        title = 'vcal_noise'
    else:
        title = 'DIAMOND_beamtime'

    if all_sectors:
        sector_array = range(0,20)
    else:
        sector_array = [9]*10

    time_now = time.localtime()
    filename = "/opt/loki-detector/exports/" + title + "_{:04d}{:02d}{:02d}_{:02d}{:02d}{:02d}".format(time_now.tm_year, time_now.tm_mon, time_now.tm_mday, time_now.tm_hour, time_now.tm_min, time_now.tm_sec, int((time.time() % 1) * 1000)) + '.csv'
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

# LEGACY: do not use
def vcal_noise_test_sector10(local_vcal=False, sector_samples=50, all_sectors=False, vcal_values=[0.2, 0.5, 1.0]):
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
        sector_array = [10]*10

    time_now = time.localtime()
    filename = "/opt/loki-detector/exports/" + title + "_{:04d}{:02d}{:02d}_{:02d}{:02d}{:02d}".format(time_now.tm_year, time_now.tm_mon, time_now.tm_mday, time_now.tm_hour, time_now.tm_min, time_now.tm_sec, int((time.time() % 1) * 1000)) + '.csv'
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

# LEGACY: do not use
def vcal_noise_test_sector11(local_vcal=False, sector_samples=50, all_sectors=False, vcal_values=[0.2, 0.5, 1.0]):
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
        sector_array = [11]*10

    time_now = time.localtime()
    filename = "/opt/loki-detector/exports/" + title + "_{:04d}{:02d}{:02d}_{:02d}{:02d}{:02d}".format(time_now.tm_year, time_now.tm_mon, time_now.tm_mday, time_now.tm_hour, time_now.tm_min, time_now.tm_sec, int((time.time() % 1) * 1000)) + '.csv'
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

