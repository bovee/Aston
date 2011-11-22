from .Datafile import Datafile

class AgilentMWD(Datafile):
    def __init__(self,*args,**kwargs):
        super(AgilentMWD,self).__init__(*args,**kwargs)
        #import os
        #self.filename = os.path.split(self.filename)[0] + '/mwd.ch'

    def _cacheData(self):
        import os
        #Because the spectra are stored in several files in the same directory,
        #we need to loop through them and return them together.
        if self.data is not None: return
        
        self.times = []
        self.data = []
        foldname = os.path.dirname(self.filename)
        if foldname == '': foldname = os.curdir
        for i in [os.path.join(foldname,i) for i in os.listdir(foldname)]:
            if i[-3:].upper() == '.CH':
                self._readIndFile(i)

    def _readIndFile(self,fname):
        import re, struct
        f = open(fname,'rb')
        
        f.seek(0x254)
        sig_name = str(f.read(struct.unpack('>B',f.read(1))[0]))
        #wavelength the file was collected at
        wv = float(re.search("Sig=(\d+),(\d+)",sig_name).group(1))

        f.seek(0x11A)
        start_time = struct.unpack('>i',f.read(4))[0] / 60000.
        #end_time 0x11E '>i'

        f.seek(0x284)
        del_ab = struct.unpack('>d',f.read(8))[0]
        
        f.seek(0x401)
        loc = 0
        while True:
            rec_len = struct.unpack('>B',f.read(1))[0]
            if rec_len == 0: break
            for i in range(rec_len):
                if len(self.data) <= loc:
                    self.times.append(start_time + loc * (400./60000.))
                    self.data.append({})
                inp = struct.unpack('>h',f.read(2))[0]
                if inp == -32768:
                    inp = struct.unpack('>i',f.read(4))[0]
                    self.data[loc][wv] = del_ab*inp
                elif loc == 0:
                    self.data[loc][wv] = del_ab*inp
                else:
                    self.data[loc][wv] = self.data[loc-1][wv] + del_ab*inp
                loc += 1
            f.read(1)
        f.close()

    def _getInfoFromFile(self):
        import struct #, os
        name = ''
        info = {}
        info['traces'] = 'TIC'
        #TODO: fix this so that it doesn't rely upon MWD1A.CH?
        #print self.filename
        #fname = os.path.join(os.path.dirname(self.filename),'mwd1A.ch')
        f = open(self.filename,'rb')
        f.seek(0x18)
        name = f.read(struct.unpack('>B',f.read(1))[0]).decode()
        f.seek(0x94)
        info['operator'] = f.read(struct.unpack('>B',f.read(1))[0]).decode()
        f.seek(0xE4)
        info['method'] = f.read(struct.unpack('>B',f.read(1))[0]).decode()
        try:
            f.seek(0xB2)
            info['date'] = f.read(struct.unpack('>B',f.read(1))[0]).decode()
        except: pass #TODO: find out why this chokes
        f.seek(0x244)
        info['units'] = f.read(struct.unpack('>B',f.read(1))[0]).decode()
        f.seek(0x254)
        #TODO: replace signal name with reference_wavelength?
        info['signal name'] = f.read(struct.unpack('>B',f.read(1))[0]).decode()
        info['type'] = 'Sample'
        info['data_type'] = 'AgilentMWD'
        
        f.close()
        return name, info

class AgilentDAD(Datafile):
#header data in DAD1.sd
#80 byte repetition
#offset = 0xA4, format = 'IIfIfffQIIdddd'
# 750 entries
#f.seek(0xA4); struct.unpack('<IddffIQIIdddd', f.read(80))

#time series in DAD1.sg
#all doubles, starts at 0x44
#750x 54 double entries
    def __init__(self,*args,**kwargs):
        super(AgilentDAD,self).__init__(*args,**kwargs)

    def _cacheData(self): 
        import struct
        if self.data is not None: return
        
        fhead = open(self.filename[:-3]+'.sd','rb')
        fdata = open(self.filename[:-3]+'.sp','rb')

        fhead.seek(0x50)
        nscans = struct.unpack('Q',fhead.read(8))[0]
        fhead.seek(0xA4)

        self.times = []
        self.data = []
        for i in range(nscans):
            t = struct.unpack('<IdddIQIIdddd', fhead.read(80))
            self.times.append(t[1])
            
            s = {}
            npts = t[7]
            fdata.seek(t[5]+16)
            for x in map(lambda x:t[8]+x*t[3],range(npts)):
                s[x] = struct.unpack('<d',fdata.read(8))[0]

            self.data.append(s)

        fhead.close()
        fdata.close()

    def _getInfoFromFile(self):
        import time, os.path as op
        from xml.etree import ElementTree

        name = ''
        info = {}
        info['traces'] = 'TIC'
        tree = ElementTree.parse(op.join(op.dirname(self.filename),'sample_info.xml'))
        for i in tree.iterfind('Field'):
            tagname = i.find('Name').text
            tagvalue = i.find('Value').text
            if tagname == 'Sample Name':
                name = tagvalue
            elif tagname == 'Sample Position':
                info['vial position'] = tagvalue
            elif tagname == 'Method':
                info['method'] = tagvalue.split('/')[-1]
        info['operator'] = ''
        info['date'] = time.ctime(op.getctime(self.filename))
        info['type'] = 'Sample'
        info['data_type'] = 'AgilentMasshunterDAD'
        return name,info

class AgilentCSDAD(Datafile):
    '''Interpreter for *.UV files from Agilent Chemstation'''
    def __init__(self,*args,**kwargs):
        super(AgilentCSDAD,self).__init__(*args,**kwargs)

    def _cacheData(self): 
        #TODO: the chromatograms this generates are not exactly the
        #same as the ones in the *.CH files. Maybe they need to be 0'd?
        import struct
        f = open(self.filename,'rb')

        f.seek(0x116)
        nscans = struct.unpack('>i',f.read(4))[0]

        self.times = nscans*[0]
        self.data = nscans*[{}]
        npos = 0x202
        for i in range(nscans):
            f.seek(npos)
            nd = struct.unpack('<H',f.read(2))[0]
            f.seek(f.tell()-2)
            npos += struct.unpack('<H',f.read(2))[0]
            self.times[i] = struct.unpack('<L',f.read(4))[0] / 60000.
            nm_srt = struct.unpack('<H',f.read(2))[0] / 20.
            nm_end = struct.unpack('<H',f.read(2))[0] / 20.
            nm_stp = struct.unpack('<H',f.read(2))[0] / 20.
            f.read(8)
            s = {}
            v = struct.unpack('<h',f.read(2))[0] / 2000.
            s[nm_srt] = v
            for j in range(1,int((nm_end-nm_srt)/nm_stp)):
                ov = struct.unpack('<h',f.read(2))[0]
                if ov == -32768:
                    v = struct.unpack('<i',f.read(4))[0] / 2000.
                else:
                    v += ov / 2000.
                s[nm_srt+j*nm_stp] = v
            self.data[i] = s

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
        f.seek(0x146)
        info['units'] = f.read(struct.unpack('>B',f.read(1))[0]).decode()
        f.seek(0xD0)
        info['instrument'] = f.read(struct.unpack('>B',f.read(1))[0]).decode()
        #TODO: are the next values correct?
        f.seek(0xFE) 
        info['vial position'] = str(struct.unpack('>h',f.read(2))[0])
        f.seek(0xFE) 
        info['sequence number'] = str(struct.unpack('>h',f.read(2))[0])

        #info['file name'] = op.join(op.basename(op.dirname(self.filename)),
        #                            op.basename(self.filename))
        info['type'] = 'Sample'
        info['data_type'] = 'AgilentChemstationDAD'
        f.close()
        return name,info
