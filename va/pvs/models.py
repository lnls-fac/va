import os as _os

LAB_PREFIX = _os.environ.get('LAB_PREFIX', default='sirius')
LAB_PREFIX = 'VA-' if LAB_PREFIX == '' else LAB_PREFIX

lab_models = None
if LAB_PREFIX.lower() == 'sirius':
    import pymodels as lab_models
elif LAB_PREFIX.lower() == 'ilsf':
    import pymodels.ilsf as lab_models

laboratory = lab_models.laboratory

