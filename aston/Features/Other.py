from aston.Features.DBObject import DBObject


class Method(DBObject):
    def __init__(self, *args, **kwargs):
        super(Method, self).__init__(*args, **kwargs)
        self.db_type = 'method'


class Compound(DBObject):
    def __init__(self, *args, **kwargs):
        super(Compound, self).__init__(*args, **kwargs)
        self.db_type = 'compound'
