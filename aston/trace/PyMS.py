

class GSMC_data(object):
    """
    Adapter to allow pyms routines to run on aston files.

    Note: initialization uses pandas dataframe, not scan lists
    as in pyms.
    """

    def __init__(self, df):
        pass

    def __len__(self):
        pass

    def get_min_mass(self):
        pass

    def get_max_mass(self):
        pass

    def get_index_at_time(self, time):
        pass

    def get_time_list(self):
        pass

    def get_scan_list(self):
        pass

    def get_tic(self):
        pass

    def trim(self, begin=None, end=None):
        pass

    def info(self, print_scan_n=False):
        pass

    def write(self, file_root):
        pass

    def write_intensities_stream(self, file_name):
        pass


#TODO: not sure if these objects need to be shimmed out too?
class Scan(object):
    pass


class IntensityMatrix(object):
    pass


class IonChromatogram(object):
    pass


class MassSpectrum(object):
    pass
