
import sirius as _sirius


# kingdom-dependent parameters
_model = _sirius.li
def _subsys(rn):
    return 'LI'+rn


class _LocalData:

    @staticmethod
    def build_data():

        _LocalData._init_record_names()
        _LocalData._init_database()
        _LocalData._init_dynamical_pvs()

    @staticmethod
    def _init_record_names():
        _fake_record_names = _get_fake_record_names()
        _LocalData.all_record_names = dict()
        _LocalData.all_record_names.update(_model.record_names.get_record_names())
        _LocalData.all_record_names.update(_fake_record_names)
        record_names = _model.record_names.get_record_names()
        record_names = list(record_names.keys()) + list(_fake_record_names.keys())
        _LocalData.fk = []
        _LocalData.pa = []
        for record_name in record_names:
            if 'FK-' in record_name:
                fk.append(record_name)
            else:
                pa.append(record_name)

    @staticmethod
    def _init_database():
        _LocalData.database = {}
        for p in _LocalData.pa:
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
        return []

    @staticmethod
    def get_read_write_pvs():
        return _LocalData.pa + _LocalData.fk

    @staticmethod
    def get_dynamical_pvs():
        return []

def _get_fake_record_names(family_name=None):
    if family_name == None:
        families = ['lifk']
        record_names_dict = {}
        for i in range(len(families)):
            record_names_dict.update(_get_fake_record_names(families[i]))
        return record_names_dict

    if family_name.lower() == 'lifk':
        _dict = {}
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