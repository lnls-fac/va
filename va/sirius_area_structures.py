import uuid as _uuid
import siriuspy as _siriuspy
import pymodels as _pymodels
from .pvs import As as _pvs_As
from .pvs import li as _pvs_li
from .pvs import tb as _pvs_tb
from .pvs import bo as _pvs_bo
from .pvs import ts as _pvs_ts
from .pvs import si as _pvs_si
from . import accelerators_model
from . import area_structure


class ASModel(area_structure.AreaStructure):
    _first_accelerator_prefix = 'LI'
    _bunch_separation  = 6*(1/_pvs_li.model.frequency)
    _rf_frequency      = _pvs_li.model.frequency/6

    pv_module = _pvs_As
    device_names = pv_module.device_names
    prefix = device_names.section.upper()
    database = pv_module.get_database()


    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._uuid = _uuid.uuid4()
        self.evg = _siriuspy.timesys.EVGIOC(self._rf_frequency,
                                            callbacks = {self._uuid: self._callback},
                                            prefix = self.prefix + '-Glob:TI-EVG:')
        self.evg.add_injection_callback(self.uuid,self._injection_cycle)
        self.evg.add_single_callback(self.uuid,self._single_pulse_synchronism)
        self._init_sp_pv_values()

    def _callback(self, propty, value, **kwargs):
        self._others_queue['driver'].put(('s', (propty, value)))

    def _get_pv(self, pv_name):
        parts = _siriuspy.namesys.SiriusPVName(pv_name)
        if parts.discipline == 'TI' and parts.device == 'EVG':
            return self.evg.get_propty(parts.property)
        return None

    def _set_pv(self,pv_name, value):
        parts = _siriuspy.namesys.SiriusPVName(pv_name)
        if parts.discipline == 'TI' and parts.dev_type == 'EVG':
            return self.evg.set_propty(parts.property, value)
        else: return False
        return True

    def _single_pulse_synchronism(self,events):
        self._log(message1 = 'cycle', message2 = '--')
        self._log(message1 = 'cycle', message2='Sending Synchronism Events in Single Mode.')
        self._log(message1 = 'cycle', message2 = '-- ' + self.prefix + ' --')
        _dict = {'single_cycle' : {'events': events}}
        for acc in ('LI','TB','BO','TS','SI'):
            self._send_parameters_to_other_area_structure(prefix = acc, _dict  = _dict)

    def _injection_cycle(self,injection_bunch,events):
        self._log(message1 = 'cycle', message2 = '--')
        self._log(message1 = 'cycle', message2='Starting injection')
        self._log(message1 = 'cycle', message2 = '-- ' + self.prefix + ' --')
        master_delay = injection_bunch * self._bunch_separation
        _dict = {'injection_cycle' : {'events': events,
                                      'master_delay':master_delay,
                                      'injection_bunch': injection_bunch,
                                      'bunch_separation': self._bunch_separation}}
        self._send_parameters_to_other_area_structure(
                            prefix = self._first_accelerator_prefix,
                            _dict  = _dict)


class LiModel(accelerators_model.LinacModel):

    pv_module = _pvs_li
    model_module = pv_module.model
    device_names = pv_module.device_names
    prefix = device_names.section.upper()
    database = pv_module.get_database()

    # Injection parameters
    _downstream_accelerator_prefix = 'TB'
    _delta_rx, _delta_angle        = 0.0, 0.0 #_pymodels.coordinate_system.parameters(prefix)
    _emittance                     = model_module.accelerator_data['emittance']
    _energy_spread                 = model_module.accelerator_data['energy_spread']
    _global_coupling               = model_module.accelerator_data['global_coupling']
    _twiss_at_match                = model_module.accelerator_data['twiss_at_match'].make_dict()
    _frequency                     = model_module.frequency
    _single_bunch_charge           = model_module.single_bunch_charge
    _multi_bunch_charge            = model_module.multi_bunch_charge
    _single_bunch_pulse_duration   = model_module.single_bunch_pulse_duration
    _multi_bunch_pulse_duration    = model_module.multi_bunch_pulse_duration
    nr_bunches                     = int(_frequency*_multi_bunch_pulse_duration/6)


class TbModel(accelerators_model.TLineModel):

    pv_module = _pvs_tb
    model_module = pv_module.model
    device_names = pv_module.device_names
    prefix = device_names.section.upper()
    database = pv_module.get_database()

    # Injection parameters
    nr_bunches = LiModel.nr_bunches
    _downstream_accelerator_prefix = 'BO'
    _delta_rx, _delta_angle = _pymodels.coordinate_system.parameters(prefix)


class BoModel(accelerators_model.BoosterModel):

    pv_module = _pvs_bo
    model_module = pv_module.model
    device_names = pv_module.device_names
    prefix = device_names.section.upper()
    database = pv_module.get_database()

    # Injection parameters
    nr_bunches = model_module.harmonic_number
    _downstream_accelerator_prefix = 'TS'
    _global_coupling               = model_module.accelerator_data['global_coupling']
    _pressure_profile              = model_module.accelerator_data['pressure_profile']
    _delta_rx, _delta_angle = _pymodels.coordinate_system.parameters(prefix)
    _injection_point_label  = 'InjS'
    _extraction_point_label = 'EjeSF'
    _ramp_interval          = 0.23


class TsModel(accelerators_model.TLineModel):

    pv_module = _pvs_ts
    model_module = pv_module.model
    device_names = pv_module.device_names
    prefix = device_names.section.upper()
    database = pv_module.get_database()

    # Injection parameters
    nr_bunches = BoModel.nr_bunches
    _downstream_accelerator_prefix = 'SI'
    _delta_rx, _delta_angle = _pymodels.coordinate_system.parameters(prefix)


class SiModel(accelerators_model.StorageRingModel):

    pv_module = _pvs_si
    model_module = pv_module.model
    device_names = pv_module.device_names
    prefix = device_names.section.upper()
    database = pv_module.get_database()

    # Injection parameters
    nr_bunches = model_module.harmonic_number
    _global_coupling               = model_module.accelerator_data['global_coupling']
    _pressure_profile              = model_module.accelerator_data['pressure_profile']
    _delta_rx, _delta_angle = _pymodels.coordinate_system.parameters(prefix)
    _injection_point_label  = 'InjSF'
