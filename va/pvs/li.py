
import sirius as _sirius

# Kingdom-dependent parameters
model = _sirius.li

accelerator = model.create_accelerator()
family_data = model.get_family_data(accelerator)

class _LocalData:

    @staticmethod
    def build_data():
        _LocalData._init_record_names()
        _LocalData._init_database()
        _LocalData._init_dynamical_pvs()

    @staticmethod
    def _init_record_names():
        _LocalData.all_record_names = {}
        if 'DI' in model.device_names.disciplines:
            _LocalData._init_di_record_names()
        else:
            _LocalData.di = []
        if 'PS' in model.device_names.disciplines:
            _LocalData._init_ps_record_names()
        else:
            _LocalData.ps = []
        if 'AP' in model.device_names.disciplines:
            _LocalData._init_ap_record_names()
        else:
            _LocalData.ap = []
        if 'RF' in model.device_names.disciplines:
            _LocalData._init_rf_record_names()
        else:
            _LocalData.rf = []
        if 'TI' in model.device_names.disciplines:
            _LocalData._init_ti_record_names()
        else:
            _LocalData.ti = []
        _LocalData._init_fk_record_names()

    @staticmethod
    def _init_di_record_names():
        _device_names = model.device_names.get_device_names(family_data, 'DI')
        _record_names = {}
        for device_name in _device_names.keys():
            device = _sirius.naming_system.split_name(device_name)['device']
            if device == 'BPM':
                _record_names[device_name + ':MonitPosX'] = _device_names[device_name]
                _record_names[device_name + ':MonitPosY'] = _device_names[device_name]
            elif device == 'TuneP':
                _record_names[device_name + ':TuneX'] = _device_names[device_name]
                _record_names[device_name + ':TuneY'] = _device_names[device_name]
            elif device == 'DCCT':
                _record_names[device_name + ':Current'] = _device_names[device_name]
                _record_names[device_name + ':BCurrent'] = _device_names[device_name]
            else:
                _record_names[device_name] = _device_names[device_name]
        _LocalData.all_record_names.update(_record_names)
        _LocalData.di = list(_record_names.keys())

    @staticmethod
    def _init_ps_record_names():
        _device_names = model.device_names.get_device_names(family_data, 'PS')
        if 'PU' in model.device_names.disciplines:
            _device_names.update(model.device_names.get_device_names(family_data, 'PU'))
        _record_names = {}
        for device_name in _device_names.keys():
            _record_names[device_name + ':CurrentSP'] = _device_names[device_name]
            _record_names[device_name + ':CurrentRB'] = _device_names[device_name]
        _LocalData.all_record_names.update(_record_names)
        _LocalData.ps = list(_record_names.keys())

    @staticmethod
    def _init_ap_record_names():
        _record_names = model.device_names.get_device_names(family_data, 'AP')
        _LocalData.all_record_names.update(_record_names)
        _LocalData.ap = list(_record_names.keys())

    @staticmethod
    def _init_rf_record_names():
        _record_names = model.device_names.get_device_names(family_data, 'RF')
        _LocalData.all_record_names.update(_record_names)
        _LocalData.rf = list(_record_names.keys())

    @staticmethod
    def _init_ti_record_names():
        _record_names = model.device_names.get_device_names(family_data, 'TI')
        _LocalData.all_record_names.update(_record_names)
        _LocalData.ti = list(_record_names.keys())

    @staticmethod
    def _init_fk_record_names():
        _record_names = {} # get_fake_record_names(family_data)
        _LocalData.all_record_names.update(_record_names)
        _LocalData.fk = []
        _LocalData.fk_pos  = []

    @staticmethod
    def _init_database():
        _LocalData.database = {}
        for p in _LocalData.di:
            if any([substring in p for substring in ('BCurrent',)]):
                _LocalData.database[p] = {'type' : 'float', 'count': model.harmonic_number}
            elif 'BPM' in p:
                if _sirius.naming_system.pvnaming_fam in p:
                    _LocalData.database[p] = {'type' : 'float', 'count': len(_LocalData.all_record_names[p]['bpm'])}
                else:
                    _LocalData.database[p] = {'type' : 'float', 'count': 1}
            else:
                _LocalData.database[p] = {'type' : 'float', 'count': 1, 'value': 0.0}
        for p in _LocalData.ps:
            _LocalData.database[p] = {'type' : 'float', 'count': 1, 'value': 0.0}
        for p in _LocalData.ap:
            if any([substring in p for substring in ('BLifetime',)]):
                _LocalData.database[p] = {'type' : 'float', 'count': model.harmonic_number, 'value': 0.0}
            else:
                _LocalData.database[p] = {'type' : 'float', 'count': 1, 'value': 0.0}
        for p in _LocalData.ti:
            _LocalData.database[p] = {'type' : 'float', 'count': 1, 'value': 0.0}
        for p in _LocalData.rf:
            _LocalData.database[p] = {'type' : 'float', 'count': 1, 'value': 0.0, 'prec': 10}
        for p in _LocalData.fk:
            _LocalData.database[p] = {'type' : 'float', 'count': 1, 'value': 0.0}
        for p in _LocalData.fk_pos:
            _LocalData.database[p] = {'type' : 'float', 'count': len(_LocalData.all_record_names[p]['pos'])}


    @staticmethod
    def _init_dynamical_pvs():
        _LocalData.dynamical_pvs = []
        for pv in _LocalData.di:
            if 'Current' in pv:
                _LocalData.dynamical_pvs.append(pv)
                _LocalData.di.remove(pv)
        for pv in _LocalData.ap:
            if 'Lifetime' in pv:
                _LocalData.dynamical_pvs.append(pv)
                _LocalData.ap.remove(pv)

    @staticmethod
    def get_all_record_names():
        return _LocalData.all_record_names

    @staticmethod
    def get_database():
        return _LocalData.database

    @staticmethod
    def get_read_only_pvs():
        return _LocalData.di + _LocalData.ap

    @staticmethod
    def get_read_write_pvs():
        return _LocalData.ps + _LocalData.fk + _LocalData.rf + _LocalData.ti

    @staticmethod
    def get_dynamical_pvs():
        return _LocalData.dynamical_pvs

    @staticmethod
    def get_constant_pvs():
        return _LocalData.fk_pos


# def get_fake_record_names(accelerator):
#
#     if not isinstance(accelerator, dict):
#         family_data = model.get_family_data(accelerator)
#     else:
#         family_data = accelerator
#
#     _dict = {'LIFK-MODE':{}}
#     _dict['LIFK-SAVEFLATFILE'] = {}
#
#     return _dict


_LocalData.build_data()

# --- Module API ---
get_all_record_names = _LocalData.get_all_record_names
get_database = _LocalData.get_database
get_read_only_pvs = _LocalData.get_read_only_pvs
get_read_write_pvs = _LocalData.get_read_write_pvs
get_dynamical_pvs = _LocalData.get_dynamical_pvs
get_constant_pvs = _LocalData.get_constant_pvs
