from sqlalchemy import Column, Integer, Unicode, UnicodeText, \
                       ForeignKey, Table
from sqlalchemy.orm import relationship
from aston.database import Base, JSONDict


group_user = Table('group_user', Base.metadata, \
                   Column('user_id', Integer, \
                          ForeignKey('users._user_id')), \
                   Column('group_id', Integer, \
                          ForeignKey('groups._group_id')))


class User(Base):
    __tablename__ = 'users'
    _user_id = Column(Integer, primary_key=True)
    username = Column(Unicode(64), unique=True)
    password = Column(Unicode(64))
    prefs = Column(JSONDict)


class Group(Base):
    __tablename__ = 'groups'
    _group_id = Column(Integer, primary_key=True)
    groupname = Column(UnicodeText, unique=True)
    users = relationship('User', secondary=group_user, backref='groups')
