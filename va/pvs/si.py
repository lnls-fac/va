from sirius import si as model
from .LocalData import LocalData

# Kingdom-dependent parameters
model = _sirius.si

accelerator = model.create_accelerator()
family_data = model.get_family_data(accelerator)

# build local data
_local_data = LocalData(family_data,model)
del LocalData

# --- Module API ---
get_all_record_names = _local_data.get_all_record_names
get_database = _local_data.get_database
get_read_only_pvs = _local_data.get_read_only_pvs
get_read_write_pvs = _local_data.get_read_write_pvs
get_dynamical_pvs = _local_data.get_dynamical_pvs
get_constant_pvs = _local_data.get_constant_pvs
