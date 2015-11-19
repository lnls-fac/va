
import sirius as _sirius

# Kingdom-dependent parameters
model = _sirius.si
prefix = 'SI'

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
        _fake_record_names = get_fake_record_names(family_data)
        _LocalData.all_record_names = dict()
        _LocalData.all_record_names.update(model.record_names.get_record_names(family_data))
        _LocalData.all_record_names.update(_fake_record_names)
        record_names = model.record_names.get_record_names(family_data)
        record_names = list(record_names.keys()) + list(_fake_record_names.keys())
        _LocalData.fk      = []
        _LocalData.fk_pos  = []
        _LocalData.pa      = []
        _LocalData.di      = []
        _LocalData.di_bpms = []
        _LocalData.ps      = []
        _LocalData.ps_ch   = []
        _LocalData.ps_cv   = []
        _LocalData.pu      = []
        _LocalData.rf      = []
        _LocalData.ti      = []
        for record_name in record_names:
            if 'DI-BPM-' in record_name:
                _LocalData.di_bpms.append(record_name)
            elif 'DI-' in record_name:
                _LocalData.di.append(record_name)
            elif 'PS-CH' in record_name:
                _LocalData.ps_ch.append(record_name)
            elif 'PS-CV' in record_name:
                _LocalData.ps_cv.append(record_name)
            elif 'PS-' in record_name:
                _LocalData.ps.append(record_name)
            elif 'PA-' in record_name:
                _LocalData.pa.append(record_name)
            elif 'FK-' in record_name and '-POS' in record_name:
                _LocalData.fk_pos.append(record_name)
            elif 'FK-' in record_name:
                _LocalData.fk.append(record_name)
            elif 'RF-' in record_name:
                _LocalData.rf.append(record_name)
            elif 'PU-' in record_name:
                _LocalData.pu.append(record_name)
            elif 'TI-' in record_name:
                _LocalData.ti.append(record_name)
            else:
                print('Parameter', record_name, 'not found!')
        _LocalData.ps = _LocalData.ps + _LocalData.ps_ch + _LocalData.ps_cv + _LocalData.pu
        _LocalData.di = _LocalData.di + _LocalData.di_bpms

    @staticmethod
    def _init_database():
        _LocalData.database = {}
        for p in _LocalData.di:
            if any([substring in p for substring in ('BCURRENT',)]):
                _LocalData.database[p] = {'type' : 'float', 'count': model.harmonic_number, 'value': 0.0}
            elif 'DI-BPM' in p:
                if 'FAM-X' in p:
                    _LocalData.database[p] = {'type' : 'float', 'count': len(_LocalData.all_record_names[p]['bpm'])}
                elif 'FAM-Y' in p:
                    _LocalData.database[p] = {'type' : 'float', 'count': len(_LocalData.all_record_names[p]['bpm'])}
                else:
                    _LocalData.database[p] = {'type' : 'float', 'count': 2}
            else:
                _LocalData.database[p] = {'type' : 'float', 'count': 1, 'value': 0.0}
        for p in _LocalData.ps:
            _LocalData.database[p] = {'type' : 'float', 'count': 1, 'value': 0.0}
        for p in _LocalData.pa:
            if any([substring in p for substring in ('BLIFETIME',)]):
                _LocalData.database[p] = {'type' : 'float', 'count': model.harmonic_number, 'value': 0.0}
            else:
                _LocalData.database[p] = {'type' : 'float', 'count': 1, 'value': 0.0}
        for p in _LocalData.ti:
            _LocalData.database[p] = {'type' : 'float', 'count': 1, 'value': 0.0}
        for p in _LocalData.rf:
            _LocalData.database[p] = {'type' : 'float', 'count': 1, 'value': 0.0}
        for p in _LocalData.fk:
            _LocalData.database[p] = {'type' : 'float', 'count': 1, 'value': 0.0}
        for p in _LocalData.fk_pos:
            _LocalData.database[p] = {'type' : 'float', 'count': len(_LocalData.all_record_names[p]['pos'])}

    @staticmethod
    def _init_dynamical_pvs():
        _LocalData.dynamical_pvs = []
        _pvs = [
            _LocalData._get_subsystem('DI-CURRENT'),
            _LocalData._get_subsystem('DI-BCURRENT'),
            _LocalData._get_subsystem('PA-LIFETIME'),
            _LocalData._get_subsystem('PA-BLIFETIME'),
        ]
        for pv in _pvs:
            if pv in _LocalData.all_record_names:
                _LocalData.dynamical_pvs.append(pv)
                if 'DI-' in pv:
                    _LocalData.di.remove(pv)
                elif 'PA-' in pv:
                    _LocalData.pa.remove(pv)

    @staticmethod
    def get_all_record_names():
        return _LocalData.all_record_names

    @staticmethod
    def get_database():
        return _LocalData.database

    @staticmethod
    def get_read_only_pvs():
        return _LocalData.di_bpms + _LocalData.pa + _LocalData.di + _LocalData.fk_pos

    @staticmethod
    def get_read_write_pvs():
        return _LocalData.ps + _LocalData.fk + _LocalData.rf + _LocalData.ti

    @staticmethod
    def get_dynamical_pvs():
        return _LocalData.dynamical_pvs

    @staticmethod
    def _get_subsystem(rn):
        return prefix + rn


def get_fake_record_names(accelerator):

    if not isinstance(accelerator, dict):
        family_data = model.get_family_data(accelerator)
    else:
        family_data = accelerator

    _dict = {}
    get_element_names = _sirius.si.record_names.get_element_names

    # Add fake CF pvs for errors
    _dict = {}
    _dict.update(get_element_names(family_data, 'cf', prefix='SIFK-ERRORX-'))
    _dict.update(get_element_names(family_data, 'cf', prefix='SIFK-ERRORY-'))
    _dict.update(get_element_names(family_data, 'cf', prefix='SIFK-ERRORR-'))
    # Add fake BEND pvs for errors
    _dict.update(get_element_names(family_data, 'bend', prefix='SIFK-ERRORX-'))
    _dict.update(get_element_names(family_data, 'bend', prefix='SIFK-ERRORY-'))
    _dict.update(get_element_names(family_data, 'bend', prefix='SIFK-ERRORR-'))
    # Add fake QUAD pvs for errors
    _dict.update(get_element_names(family_data, 'quad', prefix='SIFK-ERRORX-'))
    _dict.update(get_element_names(family_data, 'quad', prefix='SIFK-ERRORY-'))
    _dict.update(get_element_names(family_data, 'quad', prefix='SIFK-ERRORR-'))
    # Add fake SEXT pvs for errors
    _dict.update(get_element_names(family_data, 'sext', prefix='SIFK-ERRORX-'))
    _dict.update(get_element_names(family_data, 'sext', prefix='SIFK-ERRORY-'))
    _dict.update(get_element_names(family_data, 'sext', prefix='SIFK-ERRORR-'))

    # Add fake CV pvs for errors
    sext = get_element_names(family_data, 'sext')
    cv   = get_element_names(family_data, 'cv')
    indices = []
    for d in sext.values():
        for idx in d.values():
            indices += [idx]
    for key in cv.keys():
        for idx in cv[key].values():
            if idx not in indices:
                d = {'SIFK-ERRORX-'+ key : {'cv': idx},
                     'SIFK-ERRORY-'+ key : {'cv': idx},
                     'SIFK-ERRORR-'+ key : {'cv': idx}}
                _dict.update(d)

    _dict['SIFK-SAVEFLATFILE'] = {}

    # Add fake pvs for position
    elements = []
    elements += ['b1', 'b2', 'bc']
    elements += model.families.families_quadrupoles()
    elements += model.families.families_sextupoles()
    elements += model.families.families_horizontal_correctors()
    elements += model.families.families_vertical_correctors()
    elements += model.families.families_skew_correctors()
    elements += model.families.families_septa()
    elements += model.families.families_rf()
    elements += ['bpm']

    for element in elements:
        index = family_data[element]['index']
        _dict.update({prefix + 'FK-'+ element.upper()+'-POS': {'pos': index}})

    return _dict

_LocalData.build_data()

# --- Module API ---
get_all_record_names = _LocalData.get_all_record_names
get_database = _LocalData.get_database
get_read_only_pvs = _LocalData.get_read_only_pvs
get_read_write_pvs = _LocalData.get_read_write_pvs
get_dynamical_pvs = _LocalData.get_dynamical_pvs
