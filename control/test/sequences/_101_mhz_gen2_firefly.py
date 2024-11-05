import time

provides = [
    'disable_all_chip_firefly_channels',
    'set_chip_channel_firefly_state',
    'loop_chip_firefly_channels',
]

def set_chip_channel_firefly_state(channel_number=0, state=False):
    carrier = get_context('carrier')
    carrier.mhz_firefly_set_channel_enabled(channel_number, en=state)

def disable_all_chip_firefly_channels():
    carrier = get_context('carrier')
    carrier.mhz_firefly_set_all_enabled(False)

def loop_chip_firefly_channels(delay_s=2, printout=False, continual_loop=False):

    def scan():
        time.sleep(delay_s*2)

        for chip_channel_number in range(0,20):
            set_chip_channel_firefly_state(chip_channel_number, True)

            if printout:
                print('MHz Channel {}'.format(chip_channel_number))

            time.sleep(delay_s)

            disable_all_chip_firefly_channels()

            if abort_sequence():
                return

    looping = True
    while looping:
        scan()
        looping = continual_loop
        if abort_sequence():
            return
