"""
DBObject is the base class for anything stored in a AstonDatabase.
"""


class DBObject(object):
    """
    Master class for peaks, features, and datafiles.
    """
    def __init__(self, db_type='none', db=None, db_id=None, \
      parent_id=None, info=None, data=None):
        self.db_type = db_type
        self.db = db
        self.db_id = db_id
        self.parent_id = parent_id
        self.type = db_type
        self.info = DBDict(self, info)
        self.rawdata = data

    @property
    def parent(self):
        return self.db.getObjectByID(self.parent_id)

    @property
    def children(self):
        return self.db.getChildren(self.db_id)

    def getParentOfType(self, cls=None):
        prt = self.parent
        if cls is None:
            return prt
        while True:
            if prt is None:
                return None
            elif prt.db_type == cls:
                return prt
            prt = prt.parent

    def getAllChildren(self, cls=None):
        if len(self.children) == 0:
            return []
        child_list = []
        for child in self.children:
            if child.db_type == cls:
                child_list += [child]
            child_list += child.getAllChildren(cls)
        return child_list

    def save_changes(self):
        """
        Save any changes in this object back to the database.
        """
        if self.db is None:
            return

        if self.db_id is not None:
            #update object
            self.db.updateObject(self)
        else:
            #create object
            self.db.addObject(self)

    #override in subclasses
    def _load_info(self, fld):
        pass

    def _calc_info(self, fld):
        return ''


class DBDict(dict):
    def __init__(self, dbobj, *args, **kwargs):
        self._dbobj = dbobj
        #TODO: check that this next part works
        if args == [None]:
            args = [{'name': ''}]
        return super(DBDict, self).__init__(*args, **kwargs)

    def get(self, key, d=None):
        if key not in self.keys():
            self._dbobj._load_info(key)

        if key in self.keys():
            data = super(DBDict, self).get(key)
            if data != '':
                return data
        data = self._dbobj._calc_info(key)
        if data != '':
            return data
        else:
            return d

    def del_items(self, fld):
        #TODO: does invoking del so many times cause a
        #performance hit because of the save_changes in it?
        for key in self.keys():
            if key.startswith(fld):
                del self[key]

    def __getitem__(self, key):
        return self.get(key, '')

    def __setitem__(self, key, val):
        return super(DBDict, self).__setitem__(key, val)

    def __delitem__(self, key):
        self._dbobj.save_changes()
        return super(DBDict, self).__delitem__(key)
