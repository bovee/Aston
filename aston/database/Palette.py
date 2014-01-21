from sqlalchemy import Column, Integer, UnicodeText, Unicode, ForeignKey
from sqlalchemy.orm import relationship
from aston.database import Base, JSONDict


class Palette(Base):
    __tablename__ = 'palettes'
    _palette_id = Column(Integer, primary_key=True)
    _group_id = Column(Integer)
    name = Column(Unicode(64))
    runs = relationship('PaletteRun', backref='palette')
    style = Column(JSONDict)  # TODO: include bounds in style?
    columns = Column(UnicodeText)


class PaletteRun(Base):
    __tablename__ = 'paletteruns'
    _paletterun_id = Column(Integer, primary_key=True)
    _palette_id = Column(Integer, ForeignKey('palettes._palette_id'))
    _run_id = Column(Integer, ForeignKey('runs._run_id'))
    traces = Column(UnicodeText)
    run = relationship('Run')
    #order?
    #visible?
