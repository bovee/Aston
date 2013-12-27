from aston.database.Base import Base
#TODO: separate out


class Group(Base):
    __tablename__ = 'groups'
    pass


class Run(Base):
    __tablename__ = 'runs'
    pass


class Analysis(Base):
    __tablename__ = 'analyses'
    pass
