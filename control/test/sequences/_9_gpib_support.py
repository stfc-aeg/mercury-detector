import time

provides = [
        'report_munir_status',
        'set_peltier_wait',
        'set_peltier_enable',
        'get_peltier_status',
        'get_psu_measurements',
        'set_asic_bias_enable',
        'list_gpib_devices',
        'enable_hdf5',
        'capture_data',
        'autoset_asic_temp',
        ]

def report_munir_status(include_stdout=True):
    # Setting include_cmd to false will omit the last command output in case it is very long.
    munir = get_context('munir')

    print('\n')
    print('munir DKDP adapter status:')
    print('='*25 + ':')

    status = munir.get_status()
    if not status:
        raise Exception('Failed to contact munir')

    for key, value in munir.get_status().items():

        if (not include_stdout) and key == 'stdout':
            continue

        print('\t', key, ' : ', value)

def enable_hdf5(use_hdf5=True):
    munir = get_context('munir')
    munir.enable_hdf5(use_udf5)
    print('HDF5 output {}'.format('enabled' if enable else 'disabled'))

def list_gpib_devices():
    gpib = get_context('gpib')
    devices_dict = gpib.identify_devices()
    #print(gpib.identify_devices())
    print('GPIB Detected Devices:')

    if devices_dict['psu'] is not None:
        print('\tPower Supply: {} (ASIC Bias)'.format(devices_dict['psu']['path']))
        for part in devices_dict['psu']['ident'].split(','):
            print('\t\t{}'.format(part))

    if devices_dict['peltier'] is not None:
        print('\tPeltier Controller: {}'.format(devices_dict['peltier']['path']))
        for part in devices_dict['peltier']['ident'].split(','):
            print('\t\t{}'.format(part))

def set_asic_bias_enable(enable=True):
    gpib = get_context('gpib')
    gpib.set_psu_output_state(enable)
    print('ASIC bias {}'.format('enabled' if enable else 'disabled'))

def get_psu_measurements():
    gpib = get_context('gpib')
    voltage = gpib.get_psu_voltage_measurement()
    current = gpib.get_psu_current_measurement()

    print('ASIC Bias Measurements:')
    print('\tVoltage: {} v'.format(voltage))
    print('\tCurrent: {} A'.format(current))

    return voltage, current

def get_peltier_status():
    gpib = get_context('gpib')

    setpoint = gpib.get_peltier_setpoint()
    actual = gpib.get_peltier_measurement()
    enabled = gpib.get_peltier_enabled()
    print('Peltier Temperature Status:')
    print('\tSetpoint Temperature: {}C'.format(setpoint))
    print('\tActual Temperature: {}C'.format(actual))
    print('\tControl status: {}'.format('on' if enabled else 'off'))

    return actual

def set_peltier_enable(enable=True):
    gpib = get_context('gpib')
    gpib.set_peltier_enabled(enable)
    print('Peltier output {}'.format('enabled' if enable else 'disabled'))

def set_peltier_wait(temp=10, degrees_tolerance=0.1):
    gpib = get_context('gpib')
    # Set the peltier to target a temperature, and wait until it reaches it

    # Set the temperature and ensure the output is enabled
    gpib.set_peltier_temp(temp)
    gpib.set_peltier_enabled(True)

    # Wait for the desired temperature to be reached, print progress
    old_temp = gpib.get_peltier_measurement()
    print_step = abs(temp - old_temp) / 20
    while (abs(gpib.get_peltier_measurement() - temp) > degrees_tolerance):
        time.sleep(1.0)
        current_temp = gpib.get_peltier_measurement()
        progress_steps = int(abs(current_temp - old_temp) / print_step)
        print('{:.2f}C --> {:.2f}C\t['.format(old_temp, temp),
                '='*(progress_steps) + ' '*(20 - progress_steps),
                ']\t({:.3f}C)'.format(current_temp))
        if abort_sequence():
            print('SEQUENCE ABORT...')
            return

    print('Target temperature has been reached')

def autoset_asic_temp(target_temp=10, rounds=2):
    carrier = get_context('carrier')
    gpib = get_context('gpib')

    # Each round, make tolerance finer by 10*
    tolerance = 0.1
    for currentround in range(0,rounds):

        current_temp = carrier.get_cached_asic_temperature()
        while current_temp is None:
            current_temp = carrier.get_cached_asic_temperature()

        peltier_temp = gpib.get_peltier_setpoint()

        # Get current difference between ASIC and peltier
        peltier_difference = peltier_temp - current_temp

        # Immediately set the peltier to meet the desired ASIC temperature, assuming this difference
        # remains constant, and let it settle
        peltier_target = target_temp + peltier_difference
        print('Setting peltier to {} to acieve an ASIC temperature of {}'.format(peltier_target, target_temp))
        set_peltier_wait(peltier_target)

        print('Adjusted round {}/{} with tolerance {}, ASIC at {}'.format(
            currentround+1, rounds, tolerance,
            carrier.get_cached_asic_temperature()))

        tolerance = tolerance * 0.1

        print('Wait 5s between rounds')
        time.sleep(5)


def capture_data(
        path: str = "/dev/null",
        file_name: str = "capture",
        num_frames: int = 100000,
        num_batches: int = 1,
        timeout: int = 20,
        include_stdout=True
        ):
    if path == '/dev/null':
        raise Exception('Sensible destination path not set')

    # Due to bug(?) cannot create a boolean with default value of True. It will just use false in UI.
    munir = get_context('munir')

    # Trigger munir data capture
    print('Beginning fast data capture of {} frames to {} {}'.format(num_frames, path, file_name))
    response = munir.execute_capture(path, file_name, num_frames, timeout, num_batches)

    if response:
        #print('response: {} (type {})'.format(response, type(response)))
        print('Capture has started, waiting for completion...')
    else:
        raise Exception('No response from munir')

    # Wait for success, and reassure the user that execution is still occurring
    reassure_s = 5
    reassured = 0
    timestart = time.time()
    while munir.is_executing():
        duration_s = int((time.time() - timestart))
        if duration_s % reassure_s == 0 and reassured != duration_s:
            print('\tExecuting for {}s...'.format(duration_s))
            reassured = duration_s

        time.sleep(0.1)

        if abort_sequence():
            print('SEQUENCE ABORT...')
            break

    status = munir.get_status()
    return_code = status['return_code']
    stdout = status['stdout']
    stderr = status['stderr']
    exception = status['exception']

    if include_stdout:
        print(stdout)
    print(f"Command execution completed with rc:{return_code}")
    if return_code != 0:
        print(f"Stderr: {stderr}")
        print(f"Exception: {exception}")

    return return_code
