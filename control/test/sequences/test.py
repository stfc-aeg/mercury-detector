import time

provides = [
    'show_contexts', 'test_capture', 'register_read_test', 'register_write_test', 'sr_write_test', 'sr_read_test'
]

def show_contexts():
    detector = get_context('detector')
    print(f"Loaded the detector context: {type(detector).__name__}")
    asic = get_context('asic')
    print(f"Loaded the asic context: {type(asic).__name__}")
    munir = get_context('munir')
    print(f"Loaded the munir proxy context: {type(munir).__name__}")

def test_capture(path: str = "/tmp/", file_name: str = "capture.bin"):

    munir = get_context('munir')

    response = munir.get('args')
    print(f"Current arguments: {response}")

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
    return response_str