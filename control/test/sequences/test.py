import logging

provides = ['show_context', 'register_read_test', 'register_write_test', 'sr_write_test']

def show_context():
    detector = get_context('detector')
    print(f"Loaded the detector context: {type(detector).__name__}")

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
    addr = 126
    response = asic.register_write(addr, 1, 2, 3, 4, 5)

    vals = list(range(30))
    response = asic.register_write(addr, *vals)

    vals = list(range(20))
    addr = 120
    response = asic.register_write(addr, *vals)

def format_response(response):

    addr = response[0] & 0x7F
    response_str = f"{addr:#x} : " + ' '.join([hex(val) for val in response[1:]])
    return response_str