"""Definition of all Sirius Area Structures."""

import os as _os
import numpy as _np

from siriuspy.namesys import SiriusPVName as _PVName
import pymodels as _pymodels

from .timesys import TimingSimulation as _TimingSimulation
from .pvs import As as _pvs_As
from .pvs import li as _pvs_li
from .pvs import tb as _pvs_tb
from .pvs import bo as _pvs_bo
from .pvs import ts as _pvs_ts
from .pvs import si as _pvs_si
from . import accelerators_model as _accelerators_model
from . import area_structure as _area_structure
from .fluctuations import PVFluctuation as _PVFluctuation


VACA_LAB = _os.environ.get('VACA_LAB', default='sirius')
VACA_LAB = 'VA-' if VACA_LAB == '' else VACA_LAB


class ASModel(_area_structure.AreaStructure):
    """Definition of AS area structure."""

    _first_accelerator_prefix = 'LI'
    _bunch_separation = 6*(1/_pvs_li.model.frequency)
    _rf_frequency = _pvs_li.model.frequency/6

    pv_module = _pvs_As
    device_names = pv_module.device_names
    prefix = device_names.section.upper()
    database = pv_module.get_database()
    pvs_fluctuation = _PVFluctuation(database, dict())

    def __init__(self, **kwargs):
        """Initialize the instance."""
        super().__init__(**kwargs)
        self._init_timing_devices()
        self._init_sp_pv_values()
        # NOTE: without it CTRL+C ends up without BrokenPipeError
        self._send_initialisation_sign()

    def _init_timing_devices(self):
        self._timing = _TimingSimulation(
            self._rf_frequency, callbacks={self._uuid: self._callback})
        self._timing.add_injection_callback(self._uuid, self._injection_cycle)

    def _callback(self, propty, value, **kwargs):
        self._others_queue['driver'].put(('s', (propty, value)))

    def _get_pv(self, pv_name):
        parts = _PVName(pv_name)
        var = None
        if parts.dis == 'TI':
            var = self._timing.get_propty(pv_name)
        return var

    def _set_pv(self, pv_name, value):
        parts = _PVName(pv_name)
        if parts.dis == 'TI':
            return self._timing.set_propty(pv_name, value)
        return False


    # Not used in the moment.
    def _single_pulse_synchronism(self, triggers):
        self._log(message1='cycle', message2='--')
        self._log(
            message1='cycle',
            message2='Sending Synchronism Triggers' +
                     ' from Events in Single Mode.')
        self._log(message1='cycle', message2='-- ' + self.prefix + ' --')
        _dict = {'single_cycle': {'triggers': triggers}}
        for acc in ('LI', 'TB', 'BO', 'TS', 'SI'):
            self._send_parameters_to_other_area_structure(
                prefix=acc, _dict=_dict)

    def _injection_cycle(self, injection_bunch, triggers):
        self._log(message1='cycle', message2='--')
        self._log(message1='cycle', message2='Starting injection')
        self._log(message1='cycle', message2='-- ' + self.prefix + ' --')
        master_delay = injection_bunch * self._bunch_separation
        _dict = {'injection_cycle': {
            'triggers': triggers,
            'master_delay': master_delay,
            'injection_bunch': injection_bunch,
            'bunch_separation': self._bunch_separation}}
        self._send_parameters_to_other_area_structure(
            prefix=self._first_accelerator_prefix, _dict=_dict)


class LiModel(_accelerators_model.LinacModel):
    """Definition of LI area structure."""

    pv_module = _pvs_li
    model_module = pv_module.model
    device_names = pv_module.device_names
    prefix = device_names.section.upper()
    database = pv_module.get_database()
    accelerator_data = model_module.accelerator_data
    pvs_fluctuation = _PVFluctuation(
        database, {
            '.*:PS-.*:Current-Mon': 0.005,  # [A]
            '.*:DI-.*:Pos(X|Y)-Mon': 500,  # [nm]
            })

    # Injection parameters
    _downstream_accelerator_prefix = 'TB'
    _delta_rx, _delta_angle = _pymodels.coordinate_system.parameters(prefix)
    _emittance = accelerator_data['emittance']
    _energy_spread = accelerator_data['energy_spread']
    _global_coupling = accelerator_data['global_coupling']
    _twiss_at_match = accelerator_data['twiss_at_match'].make_dict()
    _frequency = model_module.frequency
    _single_bunch_charge = model_module.single_bunch_charge
    _multi_bunch_charge = model_module.multi_bunch_charge
    _single_bunch_pulse_duration = model_module.single_bunch_pulse_duration
    _multi_bunch_pulse_duration = model_module.multi_bunch_pulse_duration
    nr_bunches = int(_frequency*_multi_bunch_pulse_duration/6)


class TbModel(_accelerators_model.TLineModel):
    """Definition of TB area structure."""

    pv_module = _pvs_tb
    model_module = pv_module.model
    device_names = pv_module.device_names
    prefix = device_names.section.upper()
    database = pv_module.get_database()
    pvs_fluctuation = _PVFluctuation(
        database, {
            '.*:PS-.*:Current-Mon': 0.005,  # [A]
            '.*:PU-.*:Voltage-Mon': 0.1,  # [V]
            '.*:DI-.*:Pos(X|Y)-Mon': 500,  # [nm]
            })

    # Injection parameters
    nr_bunches = LiModel.nr_bunches
    _downstream_accelerator_prefix = 'BO'
    _delta_rx, _delta_angle = _pymodels.coordinate_system.parameters(prefix)


class BoModel(_accelerators_model.BoosterModel):
    """Definition of BO area structure."""

    pv_module = _pvs_bo
    model_module = pv_module.model
    device_names = pv_module.device_names
    prefix = device_names.section.upper()
    database = pv_module.get_database()
    pvs_fluctuation = _PVFluctuation(
        database, {
            '.*:PS-.*:Current-Mon': 0.005,  # [A]
            '.*:PU-.*:Voltage-Mon': 0.1,  # [V]
            '.*:DI-.*:Pos(X|Y)-Mon': 500,  # [nm]
            '.*:DI-DCCT:Current-Mon': 0.002,  # [mA]
            })

    init_energy = _pvs_bo.accelerator.energy

    # Injection parameters
    nr_bunches = model_module.harmonic_number
    _downstream_accelerator_prefix = 'TS'
    _global_coupling = model_module.accelerator_data['global_coupling']
    _pressure_profile = model_module.accelerator_data['pressure_profile']
    _delta_rx, _delta_angle = _pymodels.coordinate_system.parameters(prefix)
    _injection_point_label = 'InjSept'
    _extraction_point_label = 'EjeSeptF'
    _ramp_interval = 0.23


class TsModel(_accelerators_model.TLineModel):
    """Definition of TS area structure."""

    pv_module = _pvs_ts
    model_module = pv_module.model
    device_names = pv_module.device_names
    prefix = device_names.section.upper()
    database = pv_module.get_database()
    pvs_fluctuation = _PVFluctuation(
        database, {
            '.*:PS-.*:Current-Mon': 0.005,  # [A]
            '.*:PU-.*:Voltage-Mon': 0.1,  # [V]
            '.*:DI-.*:Pos(X|Y)-Mon': 500,  # [nm]
            })

    # Injection parameters
    nr_bunches = BoModel.nr_bunches
    _downstream_accelerator_prefix = 'SI'
    _delta_rx, _delta_angle = _pymodels.coordinate_system.parameters(prefix)


class SiModel(_accelerators_model.StorageRingModel):
    """Definition of SI area structure."""

    pv_module = _pvs_si
    model_module = pv_module.model
    device_names = pv_module.device_names
    prefix = device_names.section.upper()
    database = pv_module.get_database()
    pvs_fluctuation = _PVFluctuation(
        database, {
            '.*:PS-.*:Current-Mon': 0.005,  # [A]
            '.*:PU-.*:Voltage-Mon': 0.1,  # [V]
            '.*:DI-.*:Pos(X|Y)-Mon': 500,  # [nm]
            '.*:DI-DCCT:Current-Mon': 0.002,  # [mA]
            })

    # Injection parameters
    nr_bunches = model_module.harmonic_number
    _global_coupling = model_module.accelerator_data['global_coupling']
    _pressure_profile = model_module.accelerator_data['pressure_profile']
    _delta_rx, _delta_angle = _pymodels.coordinate_system.parameters(prefix)
    _injection_point_label = 'InjSeptF'
