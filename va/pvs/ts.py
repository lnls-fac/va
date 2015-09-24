
import sirius as _sirius


# Kingdom-dependent parameters
model = _sirius.ts
prefix = 'TS'

accelerator = model.create_accelerator()
family_data = model.get_family_data(accelerator)

def _get_subsystem(rn):
    return prefix + rn


class _LocalData:

    @staticmethod
    def build_data():
        _LocalData._init_record_names()
        _LocalData._init_database()
        _LocalData._init_dynamical_pvs()

    @staticmethod
    def _init_record_names():
        _fake_record_names = _get_fake_record_names(family_data)
        _LocalData.all_record_names = dict()
        _LocalData.all_record_names.update(model.record_names.get_record_names(family_data))
        _LocalData.all_record_names.update(_fake_record_names)
        record_names = model.record_names.get_record_names(family_data)
        record_names = list(record_names.keys()) + list(_fake_record_names.keys())
        _LocalData.fk = []
        _LocalData.pa = []
        _LocalData.di = []
        _LocalData.di_bpms = []
        _LocalData.ps = []
        _LocalData.ps_ch = []
        _LocalData.ps_cv = []
        _LocalData.pu = []
        _LocalData.ti = []
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
            elif 'FK-' in record_name:
                _LocalData.fk.append(record_name)
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
            if 'DI-BPM' in p:
                if 'FAM-X' in p:
                    _LocalData.database[p] = {'type' : 'float', 'count': len(_LocalData.all_record_names[_get_subsystem('DI-BPM-FAM-X')]['bpm'])}
                elif 'FAM-Y' in p:
                    _LocalData.database[p] = {'type' : 'float', 'count': len(_LocalData.all_record_names[_get_subsystem('DI-BPM-FAM-Y')]['bpm'])}
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
        for p in _LocalData.fk:
            _LocalData.database[p] = {'type' : 'float', 'count': 1, 'value': 0.0}

    @staticmethod
    def _init_dynamical_pvs():
        _LocalData.dynamical_pvs = []

    @staticmethod
    def get_all_record_names():
        return _LocalData.all_record_names

    @staticmethod
    def get_database():
        return _LocalData.database

    @staticmethod
    def get_read_only_pvs():
        return _LocalData.di_bpms + _LocalData.pa

    @staticmethod
    def get_read_write_pvs():
        return _LocalData.ps + _LocalData.fk + _LocalData.pu + _LocalData.ti

    @staticmethod
    def get_dynamical_pvs():
        return _LocalData.dynamical_pvs

def _get_fake_record_names(accelerator, family_name = None):

    if not isinstance(accelerator, dict):
        family_data = _families.get_family_data(accelerator)
    else:
        family_data = accelerator

    if family_name == None:
        families = ['tsfk']
        record_names_dict = {}
        for i in range(len(families)):
            record_names_dict.update(_get_fake_record_names(family_data, families[i]))
        return record_names_dict

    if family_name.lower() == 'tsfk':
        _dict = {}

        get_element_names = _sirius.ts.record_names.get_element_names

        # adds fake Corrector pvs for errors
        _dict.update(get_element_names(family_data, 'corr', prefix = 'TSFK-ERRORX-'))
        _dict.update(get_element_names(family_data, 'corr', prefix = 'TSFK-ERRORY-'))
        _dict.update(get_element_names(family_data, 'corr', prefix = 'TSFK-ERRORR-'))
        # adds fake BEND pvs for errors
        _dict.update(get_element_names(family_data, 'bend', prefix = 'TSFK-ERRORX-'))
        _dict.update(get_element_names(family_data, 'bend', prefix = 'TSFK-ERRORY-'))
        _dict.update(get_element_names(family_data, 'bend', prefix = 'TSFK-ERRORR-'))
        # adds fake SEP pvs for errors
        _dict.update(get_element_names(family_data, 'septa', prefix = 'TSFK-ERRORX-'))
        _dict.update(get_element_names(family_data, 'septa', prefix = 'TSFK-ERRORY-'))
        _dict.update(get_element_names(family_data, 'septa', prefix = 'TSFK-ERRORR-'))
        #adds fake QUAD pvs for errors
        _dict.update(get_element_names(family_data, 'quad', prefix = 'TSFK-ERRORX-'))
        _dict.update(get_element_names(family_data, 'quad', prefix = 'TSFK-ERRORY-'))
        _dict.update(get_element_names(family_data, 'quad', prefix = 'TSFK-ERRORR-'))

        return _dict
    else:
        raise Exception('Family name %s not found'%family_name)


_LocalData.build_data()


# --- Module API ---
get_all_record_names = _LocalData.get_all_record_names
get_database = _LocalData.get_database
get_read_only_pvs = _LocalData.get_read_only_pvs
get_read_write_pvs = _LocalData.get_read_write_pvs
get_dynamical_pvs = _LocalData.get_dynamical_pvs
