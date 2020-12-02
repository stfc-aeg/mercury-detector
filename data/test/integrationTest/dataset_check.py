import h5py
import numpy as np
import argparse

from nose.tools import assert_equals, assert_true, assert_false,\
    assert_equal, assert_not_equal


class DatasetChecker:

    def __init__(self, args):

        # open file
        # read datasets into a variable of some sort
        with h5py.File(args.filename, "r") as data_file:
            print("Keys: {}".format(data_file.keys()))

            self.data = np.array(data_file[args.dataset_name])
            self.raw = np.array(data_file["raw_frames"])
            # print(self.data)

    def check_addition_averages(self):

        processed_frame = self.data[0]
        raw_frame = self.raw[0]
        # go through raw_frame
        # if raw pixel = 0, processed should also be 0
        # if not 0, then need to check surrounding pixels for values
        #   if no surrouding values, processed = raw
        # suppose we could just generate what we think the processed frame should be then compare

        # pad with a single 0 on each axis, so that we can still look "around" every pixel
        expected_frame = np.pad(raw_frame, 1, mode='constant')  # expected frame is now shaped (82, 82)
        cols = expected_frame.shape[1]
        rows = expected_frame.shape[0]
        for i in range(rows):
            for j in range(cols):
                pixel = expected_frame[i, j]
                if not pixel == 0:
                    # list the pixels neighbours
                    # this ends up being a 3 by 3 square array with the original pixel in the middle
                    # print("Pixel Position: {}".format((i, j)))
                    neighbours = expected_frame[i - 1:i + 2, j - 1:j + 2]
                    neighbour_sum = np.sum(neighbours)
                    max_pos = np.unravel_index(neighbours.argmax(), neighbours.shape)
                    max_pos = tuple(np.subtract(max_pos, (1, 1)))
                    actual_pos = tuple(np.add((i, j), max_pos))

                    # set all neighbours to 0
                    expected_frame[i - 1:i + 2, j - 1:j + 2] = 0
                    # set pixel @ max_pos to the sum
                    expected_frame[actual_pos[0], actual_pos[1]] = neighbour_sum
                    # print(expected_frame[i - 1:i + 2, j - 1:j + 2])

        # trim the padding back off now that processing is complete
        expected_frame = expected_frame[1:rows-1, 1:cols-1]
        # we now have what the processed frame SHOULD look like when using Addition Plugin
        assert_equal(processed_frame.shape, expected_frame.shape)
        assert_true(np.array_equal(processed_frame, expected_frame))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--filename", type=str, default='test_2_000001.h5', dest="filename",
                        help="Filename of the datatype to read in")
    parser.add_argument("--dataset", type=str, default="processed_frames", dest="dataset_name",
                        help="Name of the dataset required")
    args = parser.parse_args()

    checker = DatasetChecker(args)

    checker.check_addition_averages()
