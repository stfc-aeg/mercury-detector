import time

provides = ['ser_set_pattern',
'ser_set_pattern_auto',
'print_serialiser_configs',
'set_pattern_all',
'set_cml_en_all',
'ser_enter_reset',
'ser_exit_reset',
'set_single_cml',
'cycle_cml_drivers',
'bypass_scramble_all']

def ser_set_pattern(serialiser_number=1, pattern=7):
    asic = get_context('asic')
    # Default is to set PRBS (7)

    # Mask to 3 bits
    pattern = pattern & 0b111

    # Encode bit locations as (register, bit)
    bit_locations = [((71+(serialiser_number-1)*6), 0b00000001),
                     ((70+(serialiser_number-1)*6), 0b10000000),
                     ((70+(serialiser_number-1)*6), 0b01000000)]

    for pattern_index in range(0, 3):
        pattern_bit = 1 if (pattern & (0b1 << pattern_index)) != 0 else 0
        register, setbit = bit_locations[pattern_index]

        if pattern_bit == 1:
            print("Setting register {} bit {}".format(register, setbit))
            asic.set_register_bit(register, setbit)
        else:
            print("Clearing register {} bit {}".format(register, setbit))
            asic.clear_register_bit(register, setbit)

    print("Set serialiser {} pattern to {}".format(serialiser_number, pattern))

def ser_set_pattern_auto(serialiser_number=1, pattern=7):
    asic = get_context('asic')

    print("Seting serialiser {} pattern to {}".format(serialiser_number, pattern))    

    # Write the pattern
    asic.set_serialiser_patternControl(serialiser_number, pattern)

    print("\tForce read and reprint:")
    asic._read_serialiser_config(serialiser_number)
    ser_config_check = asic._serialiser_block_configs[serialiser_number-1]
    print("\t", ser_config_check)

def print_serialiser_configs():
    asic = get_context('asic')
    i = 0
    for serialiser in asic._serialiser_block_configs:
        i += 1
        print("Serialiser {} config data: ".format(i), serialiser.__repr__())

def set_pattern_all(pattern=7):
    asic = get_context('asic')
    mercury_carrier = get_context('carrier')

    # Ensure global reset completed (so that sync is asserted)

    # Power on FireFlies all channels
    # print("Powering on FireFlies")
    # for ff_num in [1, 2]:
    #     for channel in range (0, 10):
    #         mercury_carrier.set_firefly_tx_channel_disabled(ff_num, channel, False)

    # Configure all serialisers
    print("Enabling CML and pattern {} for serialisers".format(pattern))
    i = 1
    for serialiser in asic._serialiser_block_configs:
        print("Setting serialiser {}".format(i))
        # serialiser.cml_en = 0b11                        # Enable CML drivers 1 & 2
        serialiser.patternControl = pattern & 0b111

        asic._write_serialiser_config(i)    # Force pack and write to config
        i += 1
        # time.sleep(3)

def set_cml_en_all(enable=True):
    asic = get_context('asic')
    mercury_carrier = get_context('carrier')

    # Ensure global reset completed (so that sync is asserted)

    # Configure all serialisers
    print("Enabling CML {} for serialisers".format(enable))
    i = 1
    for serialiser in asic._serialiser_block_configs:
        print("Setting serialiser {}".format(i))
        serialiser.cml_en = 0b11 if enable else 0b00            # Enable CML drivers 1 & 2

        asic._write_serialiser_config(i)    # Force pack and write to config
        i += 1
        # time.sleep(3)

def set_reg_bit_serialiser(register, bit):
    asic = get_context('asic')

    serialiser_number = int((register - 66)/6) + 1
    print("Found register in serialiser {}".format(serialiser_number))

    # Force write to serialiser to set intermediate struct data
    asic._write_serialiser_config(serialiser_number)

    # Set register bit with asic function
    asic.set_register_bit(bit)

    # Read back into local copy
    asic._read_serialiser_config(serialiser_number)

def set_bit_serialiser(ser_number, bit_number):
    base_register = 66 + (ser_number) * 6
    register_offset = bit_number % 8
    register_bit_number = int(bit_number / 8)

def set_dll_phase_config(ser_number=1, bitval=0):
    asic._serialiser_block_configs

def ser_enter_reset():
    asic = get_context('asic')

    asic.clear_register_bit(2, 0b10)    # Ser ana
    asic.clear_register_bit(2, 0b1)     # Ser digi
    asic.clear_register_bit(1, 0b10)    # Ser PLL

    spi_read_reg("1")
    spi_read_reg("2")

def ser_exit_reset():
    asic = get_context('asic')

    asic.set_register_bit(2, 0b10)    # Ser ana
    asic.set_register_bit(2, 0b1)     # Ser digi
    asic.set_register_bit(1, 0b10)    # Ser PLL

    spi_read_reg("1")
    spi_read_reg("2")

def set_single_cml(serialiser_block_number=1, cml_en=0b00):
    # Defaults to both on (0b00)
    asic = get_context('asic')

    serialiser = asic._serialiser_block_configs[serialiser_block_number-1]
    serialiser.cml_en = cml_en
    asic._write_serialiser_config(serialiser_block_number)    # Force pack and write to config

    # print("Set ser blk {} cml en to {}".format(serialiser_block_number, cml_en))
    driver = {0b00:'both', 0b11:'none', 0b01:'2', 0b10:'1'}[cml_en]
    print("Set ser blk {} cml en to driver {}".format(serialiser_block_number, driver))

def cycle_cml_drivers():
    set_cml_en_all(True)    # Turn all off

    print("Begin cml enable test in 5s")
    time.sleep(5)

    for ser_blk_num in range(1, 11):
        print("       ")
        for setting in [0b10, 0b01, 0b11]:
            set_single_cml(ser_blk_num, setting)
            time.sleep(0.5)

def bypass_scramble_all(enable=True):
    asic = get_context('asic')
    mercury_carrier = get_context('carrier')

    # Ensure global reset completed (so that sync is asserted)

    # Configure all serialisers
    print("Setting bypass scramble {} for serialisers".format(enable))
    i = 1
    for serialiser in asic._serialiser_block_configs:
        print("Setting serialiser {}".format(i))
        serialiser.bypassScramble = 0b1 if enable else 0b0            # Enable CML drivers 1 & 2

        asic._write_serialiser_config(i)    # Force pack and write to config
        i += 1
        # time.sleep(3)