
from . import model
from . import si_pvs
from . import bo_pvs

import os as _os
with open(_os.path.join(__path__[0], 'VERSION'), 'r') as _f:
    __version__ = _f.read().strip()
