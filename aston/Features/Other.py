from aston.Database import DBObject

class Method(DBObject):
    def __init__(self, *args, **kwargs):
        super(Method, self).__init__('method', *args, **kwargs)

class Compound(DBObject):
    def __init__(self, *args, **kwargs):
        super(Method, self).__init__('method', *args, **kwargs)
