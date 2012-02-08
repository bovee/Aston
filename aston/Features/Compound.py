'''This module handles database access for Aston.'''
#pylint: disable=C0103

class Compound(object):
    def __init__(self, name, database, cmpd_id=None, cmpd_type='None'):
        self.name = name
        self.database = database
        self.cmpd_id = cmpd_id
        self.feats = database.getFeats(cmpd_id)
        self.cmpd_type = cmpd_type

    def getFeats(self, file_ids):
        return [i for i in self.feats if i.ids[2] in file_ids]

    def getPeaks(self, file_ids):
        return [i for i in self.feats if i.ids[2] in file_ids and 'Peak' in i.cls]

    def addFeat(self, ft):
        ft.ids[1] = self.cmpd_id
        self.feats.append(ft)
        self.database.addFeat(ft)

    def delFeat(self, ft):
        self.feats.remove(ft)
        self.database.delFeat(ft.ids[0])
        del ft

    def isotopeValue(self):
        pk44, pk45, pk46 = None, None, None
        for pk in self.feats:
            try:
                ion = float(pk.ion)
            except ValueError:
                ion = 0 #e.g. ion = "TIC"
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
        for _ in range(4):
            r18 -= (-3*(K*r18**A)**2 + 2*K*r45*r18**A + 2*r18 - r46) / \
                   (-6*A*K**2*r18**(2*A-1) + 2*A*K*r45*r18**(A-1) + 2)
        r13 = r45-2*K*r18**A
        return 1000*(r13/rcpdb-1)
