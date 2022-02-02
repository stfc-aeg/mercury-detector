#pcb_tests.py
import time

provides = ['pcbtest_001_firefly_channels', 'pcbtest_002_val_setpoints', 'pcbtest_003_vreg_en', 'pcbtest_004_list_clkconfigs', 'pcbtest_005_lvds_pulse', 'pcbtest_006_nrst', 'pcbtest_007_cycle_clkconfigs','pcbtest_008_ambient']

def pcbtest_001_firefly_channels ():
    loki_backplane = get_context('carrier')

    print("delay 5 seconds")
    time.sleep(5)

    for channel_num in [1,3,5,7,9,11]:
        print("Turning on firefly 1 channnel {}".format(channel_num))
        loki_backplane.set_firefly_tx_channel_disabled(1, channel_num, disabled=False)
        time.sleep(2)

    print("waiting 5 seconds")
    time.sleep(5)

    print("Disabling all channels")
    for channel_num in range(0,12):
        loki_backplane.set_firefly_tx_channel_disabled(1, channel_num, disabled=True)

def pcbtest_002_val_setpoints():
    loki_backplane = get_context('carrier')

    for setpoint in [0.0, 0.5, 0.7, 0.9, 1.1, 1.3, 1.5, 1.7]:#range(0.5, 1.5, 0.1):
        print("setting vcal to {}".format(setpoint))
        loki_backplane.set_vcal_in(setpoint)
        time.sleep(2)

def pcbtest_003_vreg_en():
    mercury_carrier = get_context('carrier')

    print("Setting VREG_EN Off")
    mercury_carrier.set_vreg_en(False)

    time.sleep(10)

    print("Setting VREG_EN On")
    mercury_carrier.set_vreg_en(True)

def pcbtest_004_list_clkconfigs():
    mercury_carrier = get_context('carrier')

    print(mercury_carrier.get_clk_config_avail())

def pcbtest_007_cycle_clkconfigs():
    mercury_carrier = get_context('carrier')

    configs = mercury_carrier.get_clk_config_avail()
    print("Available clock configurations: {}".format(configs))

    current_index = configs.index(mercury_carrier.get_clk_config())
    print("Current index is {}".format(current_index))

    next_config = configs[(current_index+1) % len(configs)]
    print("Switching to next clock config: {}".format(next_config))

    mercury_carrier.set_clk_config(next_config)


def pcbtest_005_lvds_pulse():
    mercury_carrier = get_context('carrier')

    mercury_carrier.send_sync()

def pcbtest_006_nrst():
    mercury_carrier = get_context('carrier')

    mercury_carrier.set_asic_rst(True)

    time.sleep(0.2)

    mercury_carrier.set_asic_rst(False)

def pcbtest_008_ambient():
    mercury_carrier = get_context('carrier')

    print(mercury_carrier.get_ambient_temperature()," C")
    print(mercury_carrier.get_ambient_pressure()," hPa")
    print(mercury_carrier.get_ambient_humidity()," %")