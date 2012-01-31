from aston import Datafile
import struct
import numpy as np

class AgilentMS(Datafile.Datafile):
    def __init__(self,*args,**kwargs):
        super(AgilentMS,self).__init__(*args,**kwargs)

    def _getTotalTrace(self):
        f = open(self.filename,'rb')

        # get number of scans to read in
        f.seek(0x5)
        if f.read(4) == 'GC':
            f.seek(0x142)
        else:
            f.seek(0x118)
        nscans = struct.unpack('>H',f.read(2))[0]

        # find the starting location of the data
        f.seek(0x10A)
        f.seek(2*struct.unpack('>H',f.read(2))[0]-2)

        tme = np.zeros(nscans)
        tic = np.zeros(nscans)

        for i in range(nscans):
            npos = f.tell() + 2*struct.unpack('>H',f.read(2))[0]
            tme[i] = struct.unpack('>I',f.read(4))[0] / 60000.
            f.seek(npos-4)
            tic[i] = struct.unpack('>I',f.read(4))[0] 
            f.seek(npos)
        f.close()
        return tic

    def _cacheData(self):
        if self.data is not None:
            return

        f = open(self.filename,'rb')

        # get number of scans to read in
        # note that GC and LC chemstation store this in slightly different
        # places
        f.seek(0x5)
        if f.read(4) == 'GC':
            f.seek(0x142)
        else:
            f.seek(0x118)
        nscans = struct.unpack('>H',f.read(2))[0]

        # find the starting location of the data
        f.seek(0x10A)
        f.seek(2*struct.unpack('>H',f.read(2))[0]-2)

        self.times = []
        self.data = []
        for _ in range(nscans):
            npos = f.tell() + 2*struct.unpack('>H',f.read(2))[0]
            # the sampling rate is evidentally 60 kHz on all Agilent's MS's
            self.times.append(struct.unpack('>I',f.read(4))[0] / 60000.)

            #something is broken about LCMS files that needs this?
            #if npos == f.tell()-6: break

            f.seek(f.tell()+6)
            npts = struct.unpack('>H',f.read(2))[0] - 1

            s = {}
            f.seek(f.tell()+4)
            for _ in range(npts+1):
                mz = struct.unpack('>HH',f.read(4))
                s[mz[0]/20.] = mz[1]

            self.data.append(s)
            f.seek(npos)
        
        f.close()

    def _updateInfoFromFile(self):
        d = {}
        f = open(self.filename,'rb')
        f.seek(0x18)
        d['name'] = f.read(struct.unpack('>B',f.read(1))[0]).decode().strip()
        f.seek(0x94)
        d['r-opr'] = f.read(struct.unpack('>B',f.read(1))[0]).decode()
        f.seek(0xE4)
        d['m'] = f.read(struct.unpack('>B',f.read(1))[0]).decode().strip()
        f.seek(0xB2)
        d['r-date'] = f.read(struct.unpack('>B',f.read(1))[0]).decode()
        d['r-type'] = 'Sample'
        d['s-file-type'] = 'AgilentMS'
        #TODO: vial number in here too?
        f.close()
        self.info.update(d)

class AgilentMSMSScan(Datafile.Datafile):
    def __init__(self,*args,**kwargs):
        super(AgilentMSMSScan,self).__init__(*args,**kwargs)

    def _getTotalTrace(self):
        f = open(self.filename,'rb')

        # get number of scans to read in
        f.seek(0x5)
        if f.read(4) == 'GC': f.seek(0x142)
        else: f.seek(0x118)
        nscans = struct.unpack('>H',f.read(2))[0]

        # find the starting location of the data
        f.seek(0x10A)
        f.seek(2*struct.unpack('>H',f.read(2))[0]-2)

        tme = np.zeros(nscans)
        tic = np.zeros(nscans)

        for i in range(nscans):
            npos = f.tell() + 2*struct.unpack('>H',f.read(2))[0]
            tme[i] = struct.unpack('>I',f.read(4))[0] / 60000.
            f.seek(npos-4)
            tic[i] = struct.unpack('>I',f.read(4))[0] 
            f.seek(npos)

        f.close()
        return tic

    def _cacheData(self):
        if self.data is not None: return

        f = open(self.filename,'rb')

        # get number of scans to read in
        # note that GC and LC chemstation store this in slightly different
        # places
        f.seek(0x118) #TODO: this?
        nscans = struct.unpack('>H',f.read(2))[0]

        # find the starting location of the data
        f.seek(0x058)
        f.seek(struct.unpack('>H',f.read(2))[0])

        self.times = []
        self.data = []
        for _ in range(nscans):
            npos = f.tell() + 2*struct.unpack('>H',f.read(2))[0]
            # the sampling rate is evidentally 1000/60 Hz on all Agilent's MS's
            self.times.append(struct.unpack('>I',f.read(4))[0] / 60000.)

            #something is broken about LCMS files that needs this?
            #if npos == f.tell()-6: break

            f.seek(f.tell()+6)
            npts = struct.unpack('>H',f.read(2))[0] - 1

            s = {}
            f.seek(f.tell()+6)
            for _ in range(npts+1):
                t = struct.unpack('>HH',f.read(4))
                s[t[1]/20.] = t[0]

            self.data.append(s)
            f.seek(npos)

        f.close()

    def _updateInfoFromFile(self):
        d = {}
        f = open(self.filename,'rb')
        f.seek(0x18)
        d['name'] = str(f.read(struct.unpack('>B',f.read(1))[0]).strip())
        f.seek(0x94)
        d['r-opr'] = str(f.read(struct.unpack('>B',f.read(1))[0]))
        f.seek(0xE4)
        d['m'] = str(f.read(struct.unpack('>B',f.read(1))[0]))
        f.seek(0xB2)
        d['r-date'] = str(f.read(struct.unpack('>B',f.read(1))[0]))
        d['r-type'] = 'Sample'
        d['s-file-type'] = 'AgilentMS'
        f.close()
        self.info.update(i)
    
    def _getOtherTrace(self,name):
        #TODO: read from MSPeriodicActuals.bin and TCC.* files
        return np.zeros(len(self.times))

class AgilentMSMSProf(Datafile.Datafile):
    def __init__(self,*args,**kwargs):
        super(AgilentMSMSProf,self).__init__(*args,**kwargs)
