from aston.Features.DBObject import DBObject


class Method(DBObject):
    def __init__(self, *args, **kwargs):
        super(Method, self).__init__(*args, **kwargs)
        self.db_type = 'method'
        self.childtypes = ('calibration', )


class Compound(DBObject):
    def __init__(self, *args, **kwargs):
        super(Compound, self).__init__(*args, **kwargs)
        self.db_type = 'compound'
        self.childtypes = ('spectrum', 'peak')
