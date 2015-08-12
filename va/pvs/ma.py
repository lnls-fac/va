
import sirius as _sirius


# Kingdom-dependent parameters
model = _sirius.si
def _subsys(rn):
    return 'MA' + rn


class _LocalData:

    @staticmethod
    def build_data():

        _LocalData._init_record_names()
        _LocalData._init_database()
        _LocalData._init_dynamical_pvs()

    @staticmethod
    def _init_record_names():
        _LocalData.all_record_names = ('MADI-CURRENT')

    @staticmethod
    def _init_database():
        _LocalData.database = {
            'MADI-CURRENT': {'type': 'float', 'count': 1, 'value': 1.2},
        }

    @staticmethod
    def _init_dynamical_pvs():
        return

    @staticmethod
    def get_all_record_names():
        return _LocalData.all_record_names

    @staticmethod
    def get_database():
        return _LocalData.database

    @staticmethod
    def get_read_only_pvs():
        return {}

    @staticmethod
    def get_read_write_pvs():
        return _Localdata.database

    @staticmethod
    def get_dynamical_pvs():
        return {}


_LocalData.build_data()

# --- Module API ---
get_all_record_names = _LocalData.get_all_record_names
get_database = _LocalData.get_database
get_read_only_pvs = _LocalData.get_read_only_pvs
get_read_write_pvs = _LocalData.get_read_write_pvs
get_dynamical_pvs = _LocalData.get_dynamical_pvs
