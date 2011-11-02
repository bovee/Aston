class Peak(object):
    def __init__(self,verts,ion,peaktype='',ids=None):
        import numpy as np
        #peakType (gaussian, lognormal, data)
        self.peaktype = peaktype
        if peaktype == 'gaussian':
            pass
        elif peaktype == 'lognormal':
            pass
        else:
            self.verts = np.array(verts)
        self.ion = ion
        #ids = (peak_id,compound_id,file_id)
        if ids is None:
            self.ids = [None,None,None]
        else:
            self.ids = list(ids)
        self.visible = True

    def area(self):
        csum = 0
        x, y = self.verts[-1,:]
        for i in self.verts:
            csum += i[0] * y - i[1] * x
            x, y = i
        return abs(csum / 2.)

    def length(self, pwhm=False):
        import numpy as np
        if pwhm:
            #TODO: better way to pick these points
            pt1,pt2 = self.verts[0], self.verts[-1]
            #TODO: there's an error in here when pt1 or pt2 is below 0
            #adjust the y value on every point to remove "baseline"
            #m = (pt2[0]-pt1[0]) / (pt2[1]-pt1[1])
            #b = (pt2[0]*pt1[1] - pt1[0]*pt2[1]) / (pt2[0]-pt1[0])
            #avs = np.array([(pt[0],(pt[1] - m*pt[0] - b)) for pt in self.verts])
            #print avs
            #print np.array(self.verts)
            m = (pt2[1]-pt1[1]) / (pt2[0]-pt1[0])
            avs = np.array([(pt[0],(pt[1] - m*(pt[0]-pt1[0]) - pt1[1])) for pt in self.verts])

            #calculate the height of half-max
            half_y = max(avs[:,1]) / 2.0
            lw_x,hi_x = float('nan'), float('nan')
            #loop through all of the line segments
            for i in range(len(avs)-1):
                #does this line segment intersect half-max?
                if (avs[i,1]<half_y and avs[i+1,1]>half_y) or (avs[i,1]>half_y and avs[i+1,1]<half_y):
                    print self.time()
                    m = (avs[i+1,1]-avs[i,1]) / (avs[i+1,0]-avs[i,0])
                    b = (avs[i+1,0]*avs[i,1] - avs[i,0]*avs[i+1,1]) / (avs[i+1,0]-avs[i,0])
                    if np.isnan(lw_x) and np.isnan(hi_x):
                        lw_x,hi_x = (half_y-b)/m, (half_y-b)/m
                    else:
                        lw_x,hi_x = min((half_y-b)/m,lw_x), max((half_y-b)/m,hi_x)
            return hi_x - lw_x
        else:
            return self.verts[:,0].max() - self.verts[:,0].min()

    def height(self):
        return self.verts[:,1].max() - self.verts[:,1].min()

    def time(self):
        if self.verts[1,0] < self.verts[:,0].max():
            return self.verts[self.verts[:,1].argmax(),0]
        else: # inverted peak
            return self.verts[self.verts[:,1].argmin(),0]
        pass

    def contains(self,x,y):
        #from: http://www.ariel.com.au/a/python-point-int-poly.html
        n = len(self.verts)
        inside = False

        p1x, p1y = self.verts[0]
        for i in range(n+1):
            p2x, p2y = self.verts[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y-p1y)*(p2x-p1x)/(p2y-p1y)+p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        return inside

    def changePeakType(self,peak_type):
        #TODO: implement
        pass

class Compound(object):
    def __init__(self, name, database, cmpd_id=None, cmpd_type='None'):
        self.name = name
        self.database = database
        self.cmpd_id = cmpd_id
        self.peaks = database.getPeaks(cmpd_id)
        self.cmpd_type = cmpd_type

    def getPeaks(self,file_ids):
        return [i for i in self.peaks if i.ids[2] in file_ids]

    def addPeak(self,peak):
        peak.ids[1] = self.cmpd_id
        self.peaks.append(peak)
        self.database.addPeak(peak)

    def delPeak(self,peak):
        self.peaks.remove(peak)
        self.database.delPeak(peak.ids[0])
        del peak

    def isotopeValue(self):
        pk44, pk45, pk46 = None, None, None
        for pk in self.peaks:
            try: ion = float(pk.ion)
            except: ion = 0 #e.g. ion = "TIC"
            if abs(ion - 44.0) < 0.1: pk44 = pk
            if abs(ion - 45.0) < 0.1: pk45 = pk
            if abs(ion - 46.0) < 0.1: pk46 = pk

        if pk44 is None or pk45 is None or pk46 is None: return float('NaN')
        a44, a45, a46 = pk44.area(), pk45.area(), pk46.area()
        #a44, a45, a46 = 1397.84, 1581.49, 2027.15
        A, K = 0.5164, 0.0092
        rcpdb, rosmow = 0.011237, 0.002005

        #need to determine these correction factors from data?
        #TODO: construct corr. factor curve over time from standards
        #throughout the run
        r45std, r46std = (1581.49/1397.84),(2027.15/1397.84)
        #r45std, r46std = a45/a44, a46/a44
        r13std, r18std = (-37.19/1000.+1)*rcpdb, (0/1000.+1)*rosmow

        #determine the correction factors
        c45 = (r13std + 2*K*r18std**A)/r45std
        c46 = ((K*r18std**A)**2 + 2*r13std*K*r18std**A + 2*r18std)/r46std
        
        #correct the voltage ratios to ion ratios
        r45 = (a45/float(a44)) * c45
        r46 = (a46/float(a44)) * c46
        
        r18 = rosmow #best guess for oxygen ratio (VSMOW value)
        #newton's method to find 18/17O
        for i in range(4):
            r18 -= (-3*(K*r18**A)**2 + 2*K*r45*r18**A + 2*r18 - r46) / \
                   (-6*A*K**2*r18**(2*A-1) + 2*A*K*r45*r18**(A-1) + 2)
        r13 = r45-2*K*r18**A
        return 1000*(r13/rcpdb-1)
