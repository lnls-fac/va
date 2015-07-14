
import sirius as _sirius
from .pvs import si as _pvs_si
from .pvs import bo as _pvs_bo
from . import ring_model as _ring_model


class SiModel(_ring_model.RingModel):

    prefix = 'SI'
    model_module = _sirius.si
    pv_module = _pvs_si
    database = _pvs_si.get_database()
    _all_pvs = _pvs_si.get_all_record_names()

    # def __init__(self, pipe, interval, **kwargs):
    #     super().__init__(pipe, interval)


class BoModel(_ring_model.RingModel):

    prefix = 'BO'
    model_module = _sirius.bo
    pv_module = _pvs_bo
    database = _pvs_bo.get_database()
    _all_pvs = _pvs_bo.get_all_record_names()
