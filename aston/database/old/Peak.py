import numpy as np
from sqlalchemy import Column, Integer, ForeignKey, \
                       String, Unicode, LargeBinary
from sqlalchemy.orm import relationship
from chemiris.models import Base, JSONDict
from chemiris.timeseries.TimeSeries import dumps, loads
import chemiris.peaks.Math as peakmath


class Peak(Base):
    __tablename__ = 'peaks'
    peak_id = Column(Integer, primary_key=True)
    peak_type = Column(String(8))
    name = Column(Unicode(255))
    pt_id = Column(Integer, ForeignKey('palette_traces.palette_id'))
    peakgroup_id = Column(Integer, ForeignKey('peakgroups.peakgroup_id'))
    model = Column(JSONDict)
    other = Column(JSONDict)  # name, p-create, trace
    rawdata_ = Column(LargeBinary)
    baseline_ = Column(LargeBinary)

    children = []

    def __init__(self, name='', data=None, baseline=None, **kwargs):
        self.rawdata = data
        #if 'baseline' in kwargs:
        #    self.baseline = kwargs['baseline']
        #else:
        #    self.baseline = None
        pass

    @property
    def parent(self):
        if self.peakgroup is None:
            return self.cgram
        else:
            return self.peakgroup

    @property
    def rawdata(self):
        if self.rawdata_ is not None:
            return loads(self.rawdata_)

    @rawdata.setter
    def rawdata(self, value):
        if value is not None:
            self.rawdata_ = dumps(value)
        else:
            self.rawdata_ = None

    @property
    def data(self):
        #FIXME: make this return models too
        return self.rawdata

    def as_poly(self, ion=None, sub_base=False):
        # add in the baseline on either side
        if ion is None:
            row = 0
        elif not self.rawdata.has_ion(ion):
            row = 0
        else:
            try:
                row = self.rawdata.ions.index(float(ion))
            except ValueError:
                row = self.rawdata.ions.index(ion)
        pk = np.vstack([self.rawdata.times, self.rawdata.data.T[row]]).T
        #base = self.baseline(ion)
        #if sub_base:
        #    # this subtracts out the base line before returning it
        #    # it's useful for numerical fxns that don't take baseline
        #    if base is None:
        #        base_pts = np.interp(pk[:, 0], [pk[1, 0], pk[-1, 0]], \
        #                             [pk[0, 1], pk[-1, 1]])
        #    else:
        #        base_pts = np.interp(pk[:, 0], *base)

        #    ply = np.array([pk[:, 0], pk[:, 1] - base_pts]).T
        #if base is None:
        #    ply = pk
        #else:
        #    ply = np.vstack([base[0], pk, base[:0:-1]])
        ply = pk
        return ply[np.logical_not(np.any(np.isnan(ply), axis=1))]

    def contains(self, x, y, ion=None):
        if not self.data.has_ion(ion):
            return False
        return peakmath.contains(self.as_poly(ion), x, y)


class PeakGroup(Base):
    __tablename__ = 'peakgroups'
    peakgroup_id = Column(Integer, primary_key=True)
    cgram_id = Column(Integer, \
                             ForeignKey('chromatograms.cgram_id'))
    cgram = relationship('traces', backref='pkgps')
    start_time = ''
    end_time = ''
    peaks = relationship('Peak', backref='peakgroup')

    @property
    def children(self):
        return self.peaks

    @property
    def parent(self):
        return self.cgram
