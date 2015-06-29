
import sirius as _sirius
from va import fake_rnames_bo as _model_fake_rnames

# kingdom-dependent parameters
_model = _sirius.bo
def _subsys(rn): return 'BO'+rn


class _LocalData:

    @staticmethod
    def build_data():

        _LocalData._init_record_names()
        _LocalData._init_database()
        _LocalData._init_dynamical_pvs()

    @staticmethod
    def _init_record_names():
        _fake_record_names = _model_fake_rnames.get_record_names()
        _LocalData.all_record_names = dict()
        _LocalData.all_record_names.update(_model.record_names.get_record_names())
        _LocalData.all_record_names.update(_fake_record_names)
        record_names = _model.record_names.get_record_names()
        record_names = list(record_names.keys()) + list(_fake_record_names.keys())
        _LocalData.fk = []
        _LocalData.pa = []
        _LocalData.di = []
        _LocalData.di_bpms = []
        _LocalData.ps = []
        _LocalData.ps_ch = []
        _LocalData.ps_cv = []
        _LocalData.rf = []
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
            elif 'RF-' in record_name:
                _LocalData.rf.append(record_name)
            else:
                print('Parameter', record_name, 'not found!')
        _LocalData.ps = _LocalData.ps + _LocalData.ps_ch + _LocalData.ps_cv
        _LocalData.di = _LocalData.di + _LocalData.di_bpms

    @staticmethod
    def _init_database():
        _LocalData.database = {}
        for p in _LocalData.di:
            if any([substring in p for substring in ('BCURRENT',)]):
                _LocalData.database[p] = {'type' : 'float', 'count': _model.harmonic_number, 'value': 0.0}
            elif 'DI-BPM' in p:
                if 'FAM-X' in p:
                    _LocalData.database[p] = {'type' : 'float', 'count': len(_LocalData.all_record_names[_subsys('DI-BPM-FAM-X')]['bpm'])}
                elif 'FAM-Y' in p:
                    _LocalData.database[p] = {'type' : 'float', 'count': len(_LocalData.all_record_names[_subsys('DI-BPM-FAM-Y')]['bpm'])}
                else:
                    _LocalData.database[p] = {'type' : 'float', 'count': 2}
            else:
                _LocalData.database[p] = {'type' : 'float', 'count': 1, 'value': 0.0}
        for p in _LocalData.ps:
            _LocalData.database[p] = {'type' : 'float', 'count': 1, 'value': 0.0}
        for p in _LocalData.pa:
            if any([substring in p for substring in ('BLIFETIME',)]):
                _LocalData.database[p] = {'type' : 'float', 'count': _model.harmonic_number, 'value': 0.0}
            else:
                _LocalData.database[p] = {'type' : 'float', 'count': 1, 'value': 0.0}
        for p in _LocalData.rf:
            _LocalData.database[p] = {'type' : 'float', 'count': 1, 'value': 0.0}
        for p in _LocalData.fk:
            _LocalData.database[p] = {'type' : 'float', 'count': 1, 'value': 0.0}

    @staticmethod
    def _init_dynamical_pvs():
        _LocalData.dynamical_pvs = [
            _subsys('DI-CURRENT'),
            _subsys('DI-BCURRENT'),
            _subsys('PA-LIFETIME'),
            _subsys('PA-BLIFETIME'),
        ]
        for pv in _LocalData.dynamical_pvs:
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
        return _LocalData.di_bpms + _LocalData.pa + _LocalData.di

    @staticmethod
    def get_read_write_pvs():
        return _LocalData.ps + _LocalData.ps_ch + _LocalData.ps_cv + _LocalData.fk + _LocalData.rf

    @staticmethod
    def get_dynamical_pvs():
        return _LocalData.dynamical_pvs


_LocalData.build_data()

# --- Module API ---

get_all_record_names = _LocalData.get_all_record_names
get_database = _LocalData.get_database
get_read_only_pvs = _LocalData.get_read_only_pvs
get_read_write_pvs = _LocalData.get_read_write_pvs
get_dynamical_pvs = _LocalData.get_dynamical_pvs
