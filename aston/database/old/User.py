from sqlalchemy import Column, Integer, Unicode, UnicodeText, \
                       DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from chemiris.models import Base


group_user = Table('group_user', Base.metadata,
                   Column('user_id', Integer, ForeignKey('users.user_id')),
                   Column('group_id', Integer, ForeignKey('groups.group_id')))


class User(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True)
    username = Column(Unicode(255), unique=True, nullable=False)
    password = Column(Unicode(255), nullable=False)
    fullname = Column(Unicode(255))
    # abbreviated names: matched in files read in
    nicknames = Column(UnicodeText)
    last_login = Column(DateTime)
    db_chrom_columns = Column(UnicodeText)

    def __init__(self, name='', password=''):
        self.username = name
        self.password = password


class Group(Base):
    __tablename__ = 'groups'
    group_id = Column(Integer, primary_key=True)
    users = relationship('User', secondary=group_user,
                         backref='groups')
    name = Column(Unicode(255), unique=True, nullable=False)
    views = relationship('View', backref='group')

    def __init__(self, name):
        self.name = name


class Pref(Base):
    __tablename__ = 'prefs'
    key = Column(Unicode(32), primary_key=True, unique=True)
    value = Column(Unicode(128))

    def __init__(self, key, value):
        self.key = key
        self.value = value
