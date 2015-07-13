"""Virtual Accelerator with Channel Access Server"""

import os as _os
from . import server


with open(_os.path.join(__path__[0], 'VERSION'), 'r') as _f:
    __version__ = _f.read().strip()
