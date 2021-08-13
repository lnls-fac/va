import os as _os

VACA_LAB = _os.environ.get('VACA_LAB', default='sirius')
VACA_LAB = 'VA-' if VACA_LAB == '' else VACA_LAB

lab_models = None
if VACA_LAB.lower() == 'sirius':
    import pymodels as lab_models
elif VACA_LAB.lower() == 'ilsf':
    import pymodels.ilsf as lab_models

laboratory = lab_models.laboratory

