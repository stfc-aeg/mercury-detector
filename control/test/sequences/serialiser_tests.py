provides = ['ser_set_pattern',
'ser_set_pattern_auto']

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