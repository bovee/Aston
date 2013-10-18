from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.engine import create_engine

Base = declarative_base()


class AlchemyDatabase(object):
    def __init__(self, database):
        engine = create_engine(database, echo=False)
        self.db = scoped_session(sessionmaker(expire_on_commit=False))
        self.db.configure(bind=engine)
        Base.metadata.bind = engine
        Base.metadata.create_all(engine)

    def __enter__(self):
        pass

    def __exit__(self, type, value, traceback):
        pass

    def get_children(self, obj):
        pass

    def children(self):
        self.db.query(DBObject).filter_by(parent=None)

    def start_child_mod(self, parent, add_c, del_c):
        pass

    def end_child_mod(self, parent, add_c, del_c):
        pass

    def all_keys(self):
        pass

    def get_key(self, key, dflt=''):
        pass

    def set_key(self, key, val):
        pass

    def save_object(self, obj):
        pass

    def delete_object(self, obj):
        pass

    def object_from_id(self, db_id, parent=None):
        pass
