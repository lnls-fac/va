
import sirius as _sirius
from .pvs import si as _pvs_si
from . import ring_model as _ring_model


class SiModel(_ring_model.RingModel):

    prefix = 'SI'
    model_module = _sirius.si
    pv_module = _pvs_si

    # def __init__(self, pipe, interval, **kwargs):
    #     super().__init__(pipe, interval)
