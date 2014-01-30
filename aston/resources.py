import os.path as op
import pkg_resources


# look up for resource files
def resfile(res_pkg, res_path):
    res_pkg = res_pkg.split('/')
    res_path = op.join(*res_path.split('/'))
    if op.exists(op.join(op.join(*res_pkg), res_path)):
        return op.join(op.join(*res_pkg), res_path)
    else:
        res_pkg = '.'.join(res_pkg)
        return pkg_resources.resource_filename(res_pkg, res_path)

# caching function
try:
    from functools import lru_cache as cache
except ImportError:  # Python 2
    from aston.cache import lru_cache as cache

# translation function
from PyQt4.QtCore import QObject
tr = lambda s: QObject().trUtf8(s)
