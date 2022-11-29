import time

provides = [
        'report_munir_status',
        'test_capture',
        'register_read_test',
        'register_write_test',
        'sr_write_test',
        'sr_read_test',
        'list_gpib_devices',
        'set_asic_bias_enable',
        'get_psu_measurements',
]


def report_munir_status():
    munir = get_context('munir')

    print(munir.get_status())

def test_capture(path: str = "/tmp/", file_name: str = "capture.bin"):
    munir = get_context('munir')
    print(f"Executing capture to path: {path} file name: {file_name}")
    munir.execute_capture(path, file_name)

    while munir.is_executing():
        time.sleep(0.1)

    status = munir.get_status()
    print(f"Command execution completed with rc:{status['return_code']} output:{status['stdout']}")

def register_read_test():
    asic = get_context('asic')
    addr = 0x0
    response = asic.register_read(addr, 5)
    print(f"Register read : {format_response(response)}")

def register_write_test():
    asic = get_context('asic')
    addr = 0x1
    response = asic.register_write(addr, 1, 2, 3)
    #logging.debuf("oof")
    print(f"Register write : {format_response(response)}")

def sr_write_test():
    asic = get_context('asic')
    addr = asic.SR_CAL
    response = asic.register_write(addr, 1, 2, 3, 4, 5)

    vals = list(range(30))
    response = asic.register_write(addr, *vals)

    vals = list(range(20))
    addr = asic.SER_CONTROL10A
    response = asic.register_write(addr, *vals)

    asic.register_write(asic.TEST_SR, 4)

def sr_read_test(val: int = 0):

    print("val is {}".format(val))

    asic = get_context('asic')
    addr = asic.SER_CONTROL10A
    response = asic.register_read(addr, 20)
    print(f"SR read test: {format_response(response)}")

def format_response(response):

    addr = response[0] & 0x7F
    response_str = f"{addr:#x} : " + ' '.join([hex(val) for val in response[1:]])
    return 

def list_gpib_devices():
    gpib = get_context('gpib')
    devices_dict = gpib.identify_devices()
    print(gpib.identify_devices())
    print('GPIB Detected Devices:')

    if devices_dict['psu'] is not None:
        print('\tPower Supply: {}'.format(devices_dict['psu']['path']))
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
    print('ASIC Bias Measurements:')
    print('\tVoltage: {} v'.format(gpib.get_psu_voltage_measurement()))
    print('\tCurrent: {} A'.format(gpib.get_psu_current_measurement()))

