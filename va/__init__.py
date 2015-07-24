
"""Virtual Accelerator with Channel Access Server"""

import os as _os
from .pvs import li
from .pvs import tb
from .pvs import bo
from .pvs import ts
from .pvs import si
from .pvs import ti

with open(_os.path.join(__path__[0], 'VERSION'), 'r') as _f:
    __version__ = _f.read().strip()
