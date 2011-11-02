#TODO: link up with web databases, as below
#http://depth-first.com/articles/2007/01/24/thirty-two-free-chemistry-databases/
class CompoundDatabase():
    pass


class MethodDatabase():
    pass
# fields:
# 1. inst_type - HPLC, GC, etc
# 2. name - BARUA, RJBPROT.M, etc.
# 3. revision - version number of method - e.g. 1,2,3 or date
# 4. parameters -
# T, solv. % (A,B,C,D), flow rate, column type, mobile phase type
#
# opt. parameters: col. switches, main/bypass switches, rinses, inj. vol.
# 


class InstrumentDatabase():
    pass
#Like an instrument log...
# 1. event_id
# 2. event_type - new column, new standard
# 3. date/time
# 4. specifics - e.g. for isotope standard, tank d13C
