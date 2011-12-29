from .. import Datafile

class AgilentMS(Datafile.Datafile):
    def __init__(self,*args,**kwargs):
        super(AgilentMS,self).__init__(*args,**kwargs)

    def _getTotalTrace(self):
        import struct
        import numpy as np
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
        import struct
        if self.data is not None: return

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
        for i in range(nscans):
            npos = f.tell() + 2*struct.unpack('>H',f.read(2))[0]
            # the sampling rate is evidentally 60 kHz on all Agilent's MS's
            self.times.append(struct.unpack('>I',f.read(4))[0] / 60000.)

            #something is broken about LCMS files that needs this?
            #if npos == f.tell()-6: break

            f.seek(f.tell()+6)
            npts = struct.unpack('>H',f.read(2))[0] - 1

            s = {}
            f.seek(f.tell()+4)
            for i in range(npts+1):
                mz = struct.unpack('>HH',f.read(4))
                s[mz[0]/20.] = mz[1]

            self.data.append(s)
            f.seek(npos)
        
        f.close()

    def _getInfoFromFile(self):
        import struct
        #import os.path as op
        name = ''
        info = {}
        info['traces'] = 'TIC'
        f = open(self.filename,'rb')
        f.seek(0x18)
        name = f.read(struct.unpack('>B',f.read(1))[0]).decode().strip()
        f.seek(0x94)
        info['operator'] = f.read(struct.unpack('>B',f.read(1))[0]).decode()
        f.seek(0xE4)
        info['method'] = f.read(struct.unpack('>B',f.read(1))[0]).decode().strip()
        f.seek(0xB2)
        info['date'] = f.read(struct.unpack('>B',f.read(1))[0]).decode()
        #info['file name'] = op.join(op.basename(op.dirname(self.filename)),
        #                            op.basename(self.filename))
        info['type'] = 'Sample'
        info['data_type'] = 'AgilentMS'
        #TODO: vial number in here too?
        f.close()
        return name,info

class AgilentMSMSScan(Datafile.Datafile):
    def __init__(self,*args,**kwargs):
        super(AgilentMSMSScan,self).__init__(*args,**kwargs)

    def _getTotalTrace(self):
        import struct
        import numpy as np
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
        import struct
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
        for i in range(nscans):
            npos = f.tell() + 2*struct.unpack('>H',f.read(2))[0]
            # the sampling rate is evidentally 1000/60 Hz on all Agilent's MS's
            self.times.append(struct.unpack('>I',f.read(4))[0] / 60000.)

            #something is broken about LCMS files that needs this?
            #if npos == f.tell()-6: break

            f.seek(f.tell()+6)
            npts = struct.unpack('>H',f.read(2))[0] - 1

            s = {}
            f.seek(f.tell()+6)
            for i in range(npts+1):
                t = struct.unpack('>HH',f.read(4))
                s[t[1]/20.] = t[0]

            self.data.append(s)
            f.seek(npos)

        f.close()

    def _getInfoFromFile(self):
        import struct
        #import os.path as op
        name = ''
        info = {}
        info['traces'] = 'TIC'
        f = open(self.filename,'rb')
        f.seek(0x18)
        name = str(f.read(struct.unpack('>B',f.read(1))[0]).strip())
        f.seek(0x94)
        info['operator'] = str(f.read(struct.unpack('>B',f.read(1))[0]))
        f.seek(0xE4)
        info['method'] = str(f.read(struct.unpack('>B',f.read(1))[0]))
        f.seek(0xB2)
        info['date'] = str(f.read(struct.unpack('>B',f.read(1))[0]))
        #info['file name'] = op.join(op.basename(op.dirname(self.filename)),
        #                            op.basename(self.filename))
        info['type'] = 'Sample'
        info['data_type'] = 'AgilentMS'
        f.close()
        return name,info
    
    def _getOtherTrace(self,name):
        #TODO: read from MSPeriodicActuals.bin and TCC.* files
        import numpy as np
        return np.zeros(len(self.times))

class AgilentMSMSProf(Datafile.Datafile):
    def __init__(self,*args,**kwargs):
        super(AgilentMSMSProf,self).__init__(*args,**kwargs)
