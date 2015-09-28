
import sirius as _sirius


# Kingdom-dependent parameters
model = _sirius.li
prefix = 'LI'

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
        _LocalData.ti = []
        _LocalData.co = []
        for record_name in record_names:
            if 'FK-' in record_name:
                _LocalData.fk.append(record_name)
            elif 'PA-' in record_name:
                _LocalData.pa.append(record_name)
            elif 'TI-' in record_name:
                _LocalData.ti.append(record_name)
            elif 'CO-' in record_name:
                _LocalData.co.append(record_name)
            else:
                print('Parameter', record_name, 'not found!')

    @staticmethod
    def _init_database():
        _LocalData.database = {}
        for p in _LocalData.pa:
            _LocalData.database[p] = {'type' : 'float', 'count': 1, 'value': 0.0}
        for p in _LocalData.fk:
            _LocalData.database[p] = {'type' : 'float', 'count': 1, 'value': 0.0}
        for p in _LocalData.ti:
            _LocalData.database[p] = {'type' : 'float', 'count': 1, 'value': 0.0}
        for p in _LocalData.co:
            _LocalData.database[p] = {'type' : 'float', 'count': 1, 'value': 0.0}

    @staticmethod
    def _init_dynamical_pvs():
        _LocalData.dynamical_pvs = []

    @staticmethod
    def get_database():
        return _LocalData.database

    @staticmethod
    def get_read_only_pvs():
        return _LocalData.pa

    @staticmethod
    def get_read_write_pvs():
        return _LocalData.pa + _LocalData.fk + _LocalData.co + _LocalData.ti

    @staticmethod
    def get_dynamical_pvs():
        return []


def _get_fake_record_names(accelerator, family_name=None):

    if not isinstance(accelerator, dict):
        family_data = model.get_family_data(accelerator)
    else:
        family_data = accelerator

    if family_name == None:
        families = ['lifk']
        record_names_dict = {}
        for i in range(len(families)):
            record_names_dict.update(_get_fake_record_names(family_data, families[i]))
        return record_names_dict

    if family_name.lower() == 'lifk':
        _dict = {'LIFK-MODE':{}}
        return _dict
    else:
        raise Exception('Family name %s not found'%family_name)


_LocalData.build_data()

# --- Module API ---
get_database = _LocalData.get_database
get_read_only_pvs = _LocalData.get_read_only_pvs
get_read_write_pvs = _LocalData.get_read_write_pvs
get_dynamical_pvs = _LocalData.get_dynamical_pvs
