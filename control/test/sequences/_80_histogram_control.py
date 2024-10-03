# This file provides some updated fast data capture functions that are intended to work with the histogram-based
# munir control of the data path.

# There are two versions:
#   - 'compatible': runs using only a few arguments built into the original munir system, and will work with
#                   built-in software image for the LOKI control system as of 16th July 2024.
#   - 'advanced':   supports more arguments, but requires running from a host mounted, and modified (and currently
#                   not mainline) version of the control software.
#                   (NOT YET IMPLEMENTED)

requires = [
        '_8_fastdata_support',
]

provides = [
]


############################
#  Compatibility Versions  #
############################

# Modified wrapper for example_extended_capture, the sequence for capturing an arbitrary number of data captures
# at given intervals.
def extended_capture_histogramming(frames_per_histogram=100000, **kwargs):

    if 'num_batches' in kwargs.keys():
        print('WARNING: you are supplying num_batches, but in histogramming mode this is overridden by number of frames per histogram')

    kwargs.update({'num_batches': frames_per_histogram})

    # Call the base extended capture function
    example_extended_capture(**kwargs)

# Modified wrapper for single_capture, a special case of the extended capture that captures only one set of frames.
def single_capture_histogramming(frames_per_histogram=100000, **kwargs):

    if 'num_batches' in kwargs.keys():
        print('WARNING: you are supplying num_batches, but in histogramming mode this is overridden by number of frames per histogram')

    kwargs.update({'num_batches': frames_per_histogram})

    # Call the base single capture function
    single_capture(**kwargs)
