from chemiris.models import Base
from sqlalchemy import Column, Integer, Float, Enum, Text


class Method(Base):
    __tablename__ = 'methods'
    method_id = Column(Integer, primary_key=True)
    name = Column(Text)
    mtype = Column(Enum('GC', 'LC', 'CE'))  # chromatography type
    col_man = Column(Text)  # column manufacturer
    col_type = Column(Text)  # column phase
    col_dim = Column(Text)  # tuple: column dimensions (mm x mm)
    inj_size = Column(Float)
    run_len = Column(Float)
    run_temp = Column(Text)
    run_pres = Column(Text)
    run_flow = Column(Text)
    mobile_phase = Column(Text)  # tuple of solvents
    detector = Column(Enum('MS', 'MS-MS', 'UV', 'IRMS'))
    det_interface = Column(Enum('ESI', 'APCI', 'APPI', 'EI', \
                                'CI'))  # for MS: ESI, APCI, etc
