import numpy as np
try:
    from pyms.GCMS.Class import GCMS_data, Scan, IonChromatogram
except ImportError:
    GCMS_data = object


class AstonPyMS(GCMS_data):
    """
    Adapter to allow pyms routines to run on aston files.

    Note: initialization uses Chromatogram, not scan lists
    as in pyms.


    Example
    -------
    from aston.tracefile.TraceFile import TraceFile
    from aston.trace.PyMS import AstonPyMS
    from pyms.GCMS.Function import build_intensity_matrix
    from pyms.Deconvolution.BillerBiemann.Function import BillerBiemann

    astonfile = TraceFile('~/Agilent.d/DATA.MS')
    raw_data = AstonPyMS(astonfile.data)

    a.info()

    im = build_intensity_matrix(raw_data)
    peaks = BillerBiemann(im)
    """

    def __init__(self, data):
        if 'Scan' not in vars():
            raise Exception('pyms is not installed')
        self.data = data

    def __len__(self):
        return self.data.shape[0]

    def get_min_mass(self):
        return min(self.data.columns)

    def get_max_mass(self):
        return max(self.data.columns)

    def get_index_at_time(self, time):
        time *= 60.0
        return np.argmin(np.abs(self.data.index - time))

    def get_time_list(self):
        return (self.data.index * 60.0).tolist()

    @property
    def scan_list(self):
        return self._scan_list

    @property
    def _scan_list(self):
        for scan in self.data.scans():
            yield Scan(scan.x.tolist(), scan.abn.tolist())

    def get_scan_list(self):
        return list(self._scan_list)

    def get_tic(self):
        return IonChromatogram(self.data.trace().values.T[0],
                               (self.data.index * 60.0).tolist())

    def trim(self, begin=None, end=None):
        if begin is None and end is None:
            return

        if begin is None:
            st_idx = 0
        elif isinstance(begin, int):
            st_idx = begin
        else:
            st_idx = self.get_index_at_time(float(begin)) + 1

        if begin is None:
            en_idx = 0
        elif isinstance(end, int):
            en_idx = end
        else:
            st_idx = self.get_index_at_time(float(end)) + 1

        self.data = self.data[st_idx:en_idx]

    def info(self, print_scan_n=False):
        print(" Data retention time range: %.3f min -- %.3f min" %
              (min(self.data.index), max(self.data.index)))
        tdiffs = np.diff(self.data.index)
        print(" Time step: %.3f s (std=%.3f s)" %
              (np.mean(tdiffs), np.std(tdiffs)))
        print(" Number of scans: %d" % len(self))
        print(" Minimum m/z measured: %.3f" % self.get_min_mass())
        print(" Maximum m/z measured: %.3f" % self.get_max_mass())

        dfc = self.data.values.copy()
        dfc[dfc.nonzero()] = 1
        dfc = dfc.sum(axis=1)
        print(" Mean number of m/z values per scan: %d" % np.mean(dfc))
        print(" Median number of m/z values per scan: %d" % np.median(dfc))

    def write(self, file_root):
        f1name, f2name = file_root + '.I.csv', file_root + '.mz.csv'
        with open(f1name, 'w') as f1, open(f2name, 'w') as f2:
            for scan in self._scan_list:
                i_list = scan.get_intensity_list()
                f1.write(','.join('%.4f' % v for v in i_list))
                f1.write('\n')

                m_list = scan.get_mass_list()
                f2.write(','.join('%.4f' % v for v in m_list))
                f2.write('\n')

    def write_intensities_stream(self, file_name):
        with open(file_name, 'w') as f:
            for scan in self._scan_list:
                for i in scan.get_intensity_list():
                    f.write('%8.4f\n' % i)
