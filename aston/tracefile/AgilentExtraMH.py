# -*- coding: utf-8 -*-
import struct
from xml.etree import ElementTree
import numpy as np
from aston.trace.Trace import AstonSeries
from aston.tracefile.TraceFile import TraceFile


class AgilentMHPump(TraceFile):
    fnm = 'CAPPUMP1.CD'
    traces = ['pres', 'flow', 'slvb']

    def _trace(self, name, twin):
        return read_mh_trace(self.filename, name).twin(twin)


class AgilentMHTemp(TraceFile):
    fnm = 'TCC1.CD'
    traces = ['temp']

    def _trace(self, name, twin):
        return read_mh_trace(self.filename, name).twin(twin)


class AgilentMHAcqMethod(TraceFile):
    fnm = 'ACQ_METHOD.XML'

    @property
    def info(self):
        d = super(AgilentMHAcqMethod, self).info
        try:
            r = ElementTree.parse(self.filename).getroot()
            d['run_length'] = r.find('.//CapPump//Stoptime').text
            d['flow'] = r.find('.//CapPump//Flow').text
            d['solv'] = r.find('.//CapPump//SolvNameA').text
            d['solv-b'] = r.find('.//CapPump//SolvNameB').text
            d['solv-b-per'] = r.find('.//CapPump//SolvRatioB').text
            d['solv-c'] = r.find('.//CapPump//SolvNameC').text
            d['solv-d'] = r.find('.//CapPump//SolvNameD').text
            d['temp'] = r.find('.//TCC//LeftTemp').text
        except AttributeError:
            #e.g. if LeftTemp is not set, find will
            #return None and None has no attribute text
            #TODO: better fix for this
            pass
        return d


class AgilentMHSampleInfo(TraceFile):
    fnm = 'SAMPLE_INFO.XML'

    @property
    def info(self):
        try:
            u = lambda s: s.decode('utf-8')
            u('')
        except:
            u = lambda s: s

        d = super(AgilentMHAcqMethod, self).info
        r = ElementTree.parse(self.filename).getroot()
        info = {i.find('Name').text: i.find('Value').text \
                for i in r.findall('Field')}
        d['name'] = info.get('Sample Name', '')
        d['vial_pos'] = info.get('Sample Position', '')
        d['inst'] = info.get('InstrumentName', '')
        d['operator'] = info.get('OperatorName', '')
        d['date'] = info.get('AcqTime', '').replace('T', \
          ' ').rstrip('Z')
        d['inj_size'] = info.get(u('Inj Vol (µl)'), '')
        return d


def read_mh_trace(filename, trace_name):
    f = open(filename, 'rb')
    fdat = open(filename[:-3] + '.cg', 'rb')

    ttab = {'pres': 'Pressure', 'flow': 'Flow', 'slvb': '%B', \
            'temp': 'Temperature of Left Heat Exchanger'}

    # convenience function for reading in data
    rd = lambda st: struct.unpack(st, f.read(struct.calcsize(st)))

    f.seek(0x4c)
    num_traces = rd('<I')[0]
    for _ in range(num_traces):
        cloc = f.tell()
        f.seek(cloc + 2)
        sl = rd('<B')[0]
        cur_trace_name = rd('<' + str(sl) + 's')[0]
        if ttab[trace_name] == cur_trace_name:
            f.seek(f.tell() + 4)
            foff = rd('<Q')[0]
            npts = rd('<I')[0] + 2  # +2 for the extra time info
            fdat.seek(foff)
            pts = struct.unpack('<' + npts * 'd', fdat.read(8 * npts))
            #TODO: pts[0] is not the true offset?
            t = pts[0] + pts[1] * np.arange(npts - 2)
            d = np.array(pts[2:])
            # get the units
            f.seek(f.tell() + 40)
            sl = rd('<B')[0]
            y_units = rd('<' + str(sl) + 's')[0]
            if y_units == 'bar':
                d *= 0.1  # convert to MPa for metricness
            elif y_units == '':
                pass  # TODO: ul/min to ml/min
            return AstonSeries(d, t, name=trace_name)

        f.seek(cloc + 87)
