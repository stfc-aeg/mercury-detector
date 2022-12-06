import time

provides = [
        '_sleep_abortable'
        ]

def _sleep_abortable(secs=1):
    # Returns 1 if sleep was aborted, 0 otherwise (after delay)
    for i in range(0, secs):
        if abort_sequence():
            print('SEQUENCE ABORT...')
            return 1
        time.sleep(1)

    return 0
