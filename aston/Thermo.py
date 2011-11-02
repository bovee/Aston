from .Datafile import Datafile

class ThermoIRMS(Datafile):
    def __init__(self,*args,**kwargs):
        super(ThermoIRMS,self).__init__(*args,**kwargs)

    def _cacheData(self):
        import struct
        if self.data is not None: return

        f = open(self.filename,'rb')
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
        for i in range(nscans):
            self.times.append(struct.unpack('<f',f.read(4))[0] / 60.)
            self.data.append(dict(map(lambda x,y:(x,y),(44,45,46),struct.unpack('ddd',f.read(24)))))
        f.close()

    def _getInfoFromFile(self):
        import time, os
        name = ''
        info = {}
        info['traces'] = 'TIC'
        info['operator'] = ''
        info['method'] = ''
        #try: #TODO: this crashes in python 3; not clear why?
        info['date'] = time.ctime(os.path.getctime(self.filename))
        #except:
        #    pass
        #info['file name'] = os.path.basename(self.filename)
        name = os.path.splitext(os.path.basename(self.filename))[0]
        info['type'] = 'Sample'
        info['data_type'] = 'Thermo Isodat'
        return name,info
