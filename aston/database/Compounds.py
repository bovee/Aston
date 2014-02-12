from aston.database import Base


class Method(Base):
    db_type = 'method'
    childtypes = ('calibration', )


class Calibration(Base):
    """
    Types of calibration:
        isotopic - linearity correction for isotopic peaks
        with internal standard - corr. for ratio of "unk" to IS
        w/o internal standard - corr for peak area of "unk"

        Good ref? Lavagnini & Magno 2007
    """
    db_type = 'calib'
    childtypes = ()

    def convert(self, raw_val, proc_val):
        pass


class Compound(Base):
    db_type = 'compound'
    childtypes = ('spectrum', 'peak')
