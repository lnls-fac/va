
from . import model
from . import li_pvs
from . import bo_pvs
from . import si_pvs
from . import ti_pvs
from . import li_fake_record_names
from . import tb_fake_record_names
from . import bo_fake_record_names
from . import ts_fake_record_names
from . import si_fake_record_names
from . import ti_fake_record_names

import os as _os
with open(_os.path.join(__path__[0], 'VERSION'), 'r') as _f:
    __version__ = _f.read().strip()
