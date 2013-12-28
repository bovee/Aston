import json
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.types import TypeDecorator, UnicodeText
from sqlalchemy.ext.mutable import MutableDict


class JSONDict(TypeDecorator):
    impl = UnicodeText

    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)

MutableDict.associate_with(JSONDict)


DBSession = scoped_session(sessionmaker(expire_on_commit=False))
Base = declarative_base()


def initialize_sql(engine):
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)
    return DBSession
