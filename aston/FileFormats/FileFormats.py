def file_adaptors():
    from aston.FileFormats.AgilentMS \
      import AgilentMS, AgilentMSMSProf, AgilentMSMSScan
    from aston.FileFormats.Thermo \
      import ThermoCF, ThermoDXF
    from aston.FileFormats.AgilentUV \
      import AgilentDAD, AgilentMWD, AgilentCSDAD
    from aston.FileFormats.OtherFiles \
      import AgilentFID, CSVFile
    return [AgilentMS, AgilentMSMSProf, AgilentMSMSScan, \
      ThermoCF, ThermoDXF, AgilentDAD, AgilentMWD, AgilentCSDAD, \
      AgilentFID, CSVFile]

    #for cls_str in dir(fl):
    #    cls = fl.__dict__[cls_str]
    #    if hasattr(cls, '__base__'):
    #        if cls.__base__ == aston.Datafile.Datafile:
    #            pass


def ftype_to_class(ftype):
    for cls in file_adaptors():
        if cls.__name__ == ftype:
            return cls
    return None


def guess_filetype(ext, magic=None):
    #TODO:.BAF : Bruker instrument data format
    #TODO:.FID : Bruker instrument data format
    #TODO:.PKL : MassLynx associated format
    #TODO:.RAW : Micromass MassLynx directory format
    #TODO:.WIFF: ABI/Sciex (QSTAR and QTRAP instrument) format
    #TODO:.YEP : Bruker instrument data format
    #TODO:.RAW : PerkinElmer TurboMass file format

    for cls in file_adaptors():
        if ext == cls.ext and magic == cls.mgc:
            return cls.__name__
    return None
