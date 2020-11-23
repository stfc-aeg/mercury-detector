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
            # print(self.data)

    def check_averages(self):
        # this is very hard coded to the specific pattern used, work out some way to generalise it
        frame = self.data[0]
        assert_equal(frame[3, 3], 11)
        assert_equal(frame[35, 30], 0)
        assert_equal(frame[35, 31], 44)
        assert_equal(frame[3, 31], 22)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--filename", type=str, default='test_2_000001.h5', dest="filename",
                        help="Filename of the datatype to read in")
    parser.add_argument("--dataset", type=str, default="processed_frames", dest="dataset_name",
                        help="Name of the dataset required")
    args = parser.parse_args()

    checker = DatasetChecker(args)

    checker.check_averages()
