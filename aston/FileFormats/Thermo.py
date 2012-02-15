from aston import Datafile
import struct
import time
import os

class ThermoCF(Datafile.Datafile):
    def __init__(self,*args,**kwargs):
        super(ThermoCF,self).__init__(*args,**kwargs)

    def _cacheData(self):
        if self.data is not None: return

        f = open(self.rawdata,'rb')
        f.seek(19)
        while True:
            f.seek(f.tell()-19)
            if f.read(19) == b'CRawDataScanStorage': break
            if f.read(1) == b'':
                f.close()
                return

        f.seek(f.tell()+62)
        nscans = struct.unpack('H',f.read(2))[0]

        self.times = []
        self.data = []
        f.seek(f.tell()+35)
        for _ in range(nscans):
            self.times.append(struct.unpack('<f',f.read(4))[0] / 60.)
            ms = map(lambda x,y:(x,y),(44,45,46),struct.unpack('<ddd',f.read(24)))
            self.data.append(dict(ms))
        f.close()

    def _updateInfoFromFile(self):
        d = {}
        d['r-opr'] = ''
        d['m'] = ''
        #try: #TODO: this crashes in python 3; not clear why?
        d['r-date'] = time.ctime(os.path.getctime(self.rawdata))
        #except:
        #    pass
        #info['file name'] = os.path.basename(self.filename)
        d['name'] = os.path.splitext(os.path.basename(self.rawdata))[0]
        d['r-type'] = 'Sample'
        self.info.update(d)

class ThermoDXF(Datafile.Datafile):
    def __init__(self,*args,**kwargs):
        super(ThermoDXF,self).__init__(*args,**kwargs)

    def _cacheData(self):
        if self.data is not None: return
        self.times = []
        self.data = []

        f = open(self.rawdata,'rb')
        f.seek(11)
        while True:
            f.seek(f.tell()-11)
            if f.read(11) == b'CEvalGCData': break
            if f.read(1) == b'':
                f.close()
                return

        f.read(4) #not sure what this value means

        #next line assumes all record are 28 bytes long ('fddd')
        nscans = int(struct.unpack('<I',f.read(4))[0]/28.0)

        for _ in range(nscans):
            self.times.append(struct.unpack('<f',f.read(4))[0] / 60.)
            ms = map(lambda x,y:(x,y),(44,45,46),struct.unpack('<ddd',f.read(24)))
            self.data.append(dict(ms))
        f.close()

    def _updateInfoFromFile(self):
        d = {}
        d['r-opr'] = ''
        d['m'] = ''
        #try: #TODO: this crashes in python 3; not clear why?
        d['date'] = time.ctime(os.path.getctime(self.rawdata))
        #except:
        #    pass
        #info['file name'] = os.path.basename(self.filename)
        d['name'] = os.path.splitext(os.path.basename(self.rawdata))[0]
        d['r-type'] = 'Sample'
        self.info.update(d)
