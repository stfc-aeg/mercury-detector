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
