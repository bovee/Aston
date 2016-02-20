# -*- coding: utf-8 -*-
import struct
from xml.etree import ElementTree
import numpy as np
from aston.trace import Trace
from aston.tracefile import TraceFile


class AgilentMHPump(TraceFile):
    mime = 'application/vnd-agilent-masshunter-pump'
    traces = ['pres', 'flow', 'slvb']

    def _trace(self, name, twin):
        return read_mh_trace(self.filename, name).twin(twin)


class AgilentMHTemp(TraceFile):
    mime = 'application/vnd-agilent-masshunter-temp'
    traces = ['temp']

    def _trace(self, name, twin):
        return read_mh_trace(self.filename, name).twin(twin)


class AgilentMHAcqMethod(TraceFile):
    mime = 'application/vnd-agilent-masshunter-acqmethod'

    @property
    def info(self):
        d = super(AgilentMHAcqMethod, self).info
        try:
            r = ElementTree.parse(self.filename).getroot()
            d['r-en-time'] = r.find('.//CapPump//Stoptime').text
            d['m-flw'] = r.find('.//CapPump//Flow').text
            d['m-slv'] = r.find('.//CapPump//SolvNameA').text
            d['m-slv-b'] = r.find('.//CapPump//SolvNameB').text
            d['m-slv-b-per'] = r.find('.//CapPump//SolvRatioB').text
            d['m-slv-c'] = r.find('.//CapPump//SolvNameC').text
            d['m-slv-d'] = r.find('.//CapPump//SolvNameD').text
            d['m-tmp'] = r.find('.//TCC//LeftTemp').text
        except AttributeError:
            # e.g. if LeftTemp is not set, find will
            # return None and None has no attribute text
            # TODO: better fix for this
            pass
        return d


class AgilentMHSampleInfo(TraceFile):
    mime = 'application/vnd-agilent-masshunter-sampleinfo'

    @property
    def info(self):
        try:
            def u(s):
                return s.decode('utf-8')
            u('')
        except AttributeError:
            def u(s):
                return s

        d = super(AgilentMHSampleInfo, self).info
        r = ElementTree.parse(self.filename).getroot()
        info = {i.find('Name').text: i.find('Value').text
                for i in r.findall('Field')}
        d['r-smp'] = info.get('Sample Name', '')
        d['r-vial-pos'] = info.get('Sample Position', '')
        d['r-inst'] = info.get('InstrumentName', '')
        d['r-opr'] = info.get('OperatorName', '')
        d['r-date'] = info.get('AcqTime', '').replace('T', ' ').rstrip('Z')
        d['m-inj-size'] = info.get(u('Inj Vol (µl)'), '')
        return d


def read_mh_trace(filename, trace_name):
    f = open(filename, 'rb')
    fdat = open(filename[:-3] + '.cg', 'rb')

    ttab = {'pres': 'Pressure', 'flow': 'Flow', 'slvb': '%B',
            'temp': 'Temperature of Left Heat Exchanger'}

    # convenience function for reading in data
    def rd(st):
        return struct.unpack(st, f.read(struct.calcsize(st)))

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
            # TODO: pts[0] is not the true offset?
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
            return Trace(d, t, name=trace_name)

        f.seek(cloc + 87)
