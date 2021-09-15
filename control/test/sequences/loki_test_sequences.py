import time

# loki_test_sequences.py
provides = ['ff_channel_toggle_test', 'mercury_carrier_init']

def ff_channel_toggle_test(firefly = 1, channel_min = 5, channel_max = 5, toggle_loops=2):
    print("SEQUENCE TEST: ff_channel_toggle_test begin")
    loki_backplane = get_context('carrier')

    disabled_start = True
    while toggle_loops > 0:
        print("SEQUENCE TEST: Test loop begin:")

        disabled_start = not(disabled_start)
        disabled = disabled_start
        for i in range(channel_min, channel_max+1):
            print("SEQUENCE TEST: setting channel {} to disabled={}".format(i, disabled))
            loki_backplane.set_firefly_tx_channel_disabled(firefly, i, disabled)
            time.sleep(1)
            disabled = not(disabled)

        print("SEQUENCE TEST: SLEEPING")
        # time.sleep(10)
        toggle_loops -= 1

    print("SEQUENCE TEST: Test loops complete")

def mercury_carrier_init():
    mercury_carrier = get_context('carrier')

    print("Holding ASIC in reset")
    mercury_carrier.set_asic_rst(True)

    print("Resetting regulators and board devices")
    mercury_carrier.vreg_power_cycle_init(None)

    #temporary, until async removed
    time.sleep(5)

    print("Setting VCal to 1.0v")
    mercury_carrier.set_vcal_in(1)

    print("Enabling all firefly channels")
    for ff in [1, 2]:
        for i in range(0,12):
            mercury_carrier.set_firefly_tx_channel_disabled(ff, i, False)

    print("Bringing ASIC out of reset")
    mercury_carrier.set_asic_rst(False)