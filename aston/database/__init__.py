import json
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.types import TypeDecorator, UnicodeText, LargeBinary
from sqlalchemy.ext.mutable import MutableDict
from aston.trace.Trace import decompress


class JSONDict(TypeDecorator):
    impl = UnicodeText

    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)


class AstonFrameBinary(TypeDecorator):
    impl = LargeBinary

    def process_bind_param(self, value, dialect):
        if value is not None:
            return value.compress()

    def process_result_value(self, value, dialect):
        if value is not None:
            return decompress(value)


MutableDict.associate_with(JSONDict)

Base = declarative_base()


def initialize_sql(engine):
    DBSession = scoped_session(sessionmaker(expire_on_commit=False))
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)
    return DBSession


def quick_sqlite(filename):
    from sqlalchemy import create_engine

    #TODO: close old session if still open?
    engine = create_engine('sqlite:///' + filename)
    session = initialize_sql(engine)
    return session
