from aston.Features.DBObject import DBObject


class Project(DBObject):
    pass


class PeakGroup(DBObject):
    def __init__(self, *args, **kwargs):
        super(PeakGroup, self).__init__(*args, **kwargs)
        self.db_type = 'peakgroup'
        self.childtypes = ('peak', )

    def baseline(self, times=None):
        #TODO: be able to save baseline as TimeSeries
        #TODO: recalculate TimeSeries using new times
        return self.rawdata
