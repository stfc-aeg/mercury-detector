import time

provides = [
        'Set_DiamondDefault_Registers',
        'Set_DiamondDefault_Registers_NegRange',
]

def Set_DiamondDefault_Registers():
    #testing the effect of changing the negative range

    asic = get_context('asic')

    timenow = time.localtime()
    print("Begin test {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

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

    print("Finished setting registers")

def Set_DiamondDefault_Registers_NegRange():
    #testing the effect of changing the negative range

    asic = get_context('asic')

    timenow = time.localtime()
    print("Begin test {}:{}:{}".format(timenow.tm_hour, timenow.tm_min, timenow.tm_sec))

    #Set default negative range
    asic.clear_register_bit(0,0b01000000)

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

    print("Finished setting registers")

