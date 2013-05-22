from aston.Features.DBObject import DBObject


class Method(DBObject):
    def __init__(self, *args, **kwargs):
        super(Method, self).__init__(*args, **kwargs)
        self.db_type = 'method'
        self.childtypes = ('calibration', )


class Calibration(DBObject):
    """
    Types of calibration:
        isotopic - linearity correction for isotopic peaks
        with internal standard - corr. for ratio of "unk" to IS
        w/o internal standard - corr for peak area of "unk"

        Good ref? Lavagnini & Magno 2007
    """
    def __init__(self, *args, **kwargs):
        super(Calibration, self).__init__(*args, **kwargs)
        self.db_type = 'calib'
        self.childtypes = ()

    def convert(self, raw_val, proc_val):
        pass


class Compound(DBObject):
    def __init__(self, *args, **kwargs):
        super(Compound, self).__init__(*args, **kwargs)
        self.db_type = 'compound'
        self.childtypes = ('spectrum', 'peak')
