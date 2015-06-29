
from . import model
from . import pvs_li
from . import pvs_tb
from . import pvs_bo
from . import pvs_ts
from . import pvs_si
from . import pvs_ti
from . import fake_rnames_li
from . import fake_rnames_tb
from . import fake_rnames_bo
from . import fake_rnames_ts
from . import fake_rnames_si
from . import fake_rnames_ti

import os as _os
with open(_os.path.join(__path__[0], 'VERSION'), 'r') as _f:
    __version__ = _f.read().strip()
