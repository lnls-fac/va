class _LocalData:

    def __init__(self,family_data,model):
        self.family_data = family_data
        self.model = model
        self.build_data()

    def build_data(self):
        _LocalData._init_record_names()
        _LocalData._init_database()
        _LocalData._init_dynamical_pvs()

    def _init_record_names(self):
        _LocalData.all_record_names = {}
        if 'DI' in self.model.device_names.disciplines:
            _LocalData._init_di_record_names()
        else:
            _LocalData.di = []
        if 'PS' in self.model.device_names.disciplines:
            _LocalData._init_ps_record_names()
        else:
            _LocalData.ps = []
        if 'AP' in self.model.device_names.disciplines:
            _LocalData._init_ap_record_names()
        else:
            _LocalData.ap = []
        if 'RF' in self.model.device_names.disciplines:
            _LocalData._init_rf_record_names()
        else:
            _LocalData.rf = []
        if 'TI' in self.model.device_names.disciplines:
            _LocalData._init_ti_record_names()
        else:
            _LocalData.ti = []
        _LocalData._init_fk_record_names()

    def _init_di_record_names(self):
        _device_names = self.model.get_device_names(self.family_data, 'di')
        _record_names = {}
        for device_name in _device_names.keys():
            device = _sirius.device_names.split_name(device_name)['device']
            if device == 'BPM':
                _record_names[device_name + ':PosX-Mon'] = _device_names[device_name]
                _record_names[device_name + ':PosY-Mon'] = _device_names[device_name]
            elif device == 'TuneP':
                _record_names[device_name + ':Freq1'] = _device_names[device_name]
                _record_names[device_name + ':Freq2'] = _device_names[device_name]
            elif device == 'DCCT':
                _record_names[device_name + ':Current'] = _device_names[device_name]
                _record_names[device_name + ':BbBCurrent'] = _device_names[device_name]
            else:
                _record_names[device_name] = _device_names[device_name]
        _LocalData.all_record_names.update(_record_names)
        _LocalData.di = list(_record_names.keys())

    def _init_ps_record_names(self):
        _device_names = self.model.get_device_names(self.family_data, 'PS')
        if 'PU' in self.model.device_names.disciplines:
            _device_names.update(self.model.get_device_names(self.family_data, 'PU'))
        _record_names = {}
        for device_name in _device_names.keys():
            _record_names[device_name + ':Current-SP'] = _device_names[device_name]
            _record_names[device_name + ':Current-RB'] = _device_names[device_name]
        _LocalData.all_record_names.update(_record_names)
        _LocalData.ps = list(_record_names.keys())

    def _init_ap_record_names(self):
        _record_names = self.model.get_device_names(self.family_data, 'AP')
        _LocalData.all_record_names.update(_record_names)
        _LocalData.ap = list(_record_names.keys())

    def _init_rf_record_names(self):
        _device_names = self.model.get_device_names(self.family_data, 'RF')
        _record_names = {}
        for device_name in _device_names.keys():
            device = _sirius.device_names.split_name(device_name)['device']
            if 'RFCav' in device:
                _record_names[device_name + ':Freq'] = _device_names[device_name]
                _record_names[device_name + ':Volt'] = _device_names[device_name]
            else:
                _record_names[device_name] = _device_names[device_name]
        _LocalData.all_record_names.update(_record_names)
        _LocalData.rf = list(_record_names.keys())

    def _init_ti_record_names(self):
        _device_names = self.model.get_device_names(self.family_data, 'TI')
        for device_name in _device_names.keys():
            _record_names[device_name + ':Enbl']  = _device_names[device_name]
            _record_names[device_name + ':Delay'] = _device_names[device_name]
        _LocalData.all_record_names.update(_record_names)
        _LocalData.ti = list(_record_names.keys())

    def _init_fk_record_names(self):
        _record_names = {} # get_fake_record_names(self.family_data)
        _LocalData.all_record_names.update(_record_names)
        _LocalData.fk = []
        _LocalData.fk_pos  = []

    def _init_database(self):
        _LocalData.database = {}
        for p in _LocalData.di:
            if any([substring in p for substring in ('BbBCurrent',)]):
                _LocalData.database[p] = {'type' : 'float', 'count': self.model.harmonic_number}
            elif 'BPM' in p:
                if _sirius.device_names.pvnaming_fam in p:
                    _LocalData.database[p] = {'type' : 'float', 'count': len(_LocalData.all_record_names[p]['BPM'])}
                else:
                    _LocalData.database[p] = {'type' : 'float', 'count': 1}
            else:
                _LocalData.database[p] = {'type' : 'float', 'count': 1, 'value': 0.0}
        for p in _LocalData.ps:
            _LocalData.database[p] = {'type' : 'float', 'count': 1, 'value': 0.0}
        for p in _LocalData.ap:
            if any([substring in p for substring in ('BbBCurrLT',)]):
                _LocalData.database[p] = {'type' : 'float', 'count': self.model.harmonic_number, 'value': 0.0}
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

    def _init_dynamical_pvs(self):
        _LocalData.dynamical_pvs = []
        for pv in _LocalData.di:
            if 'Current' in pv:
                _LocalData.dynamical_pvs.append(pv)
                _LocalData.di.remove(pv)
        for pv in _LocalData.ap:
            if 'CurrLT' in pv:
                _LocalData.dynamical_pvs.append(pv)
                _LocalData.ap.remove(pv)

    def get_all_record_names(self):
        return _LocalData.all_record_names

    def get_database(self):
        return _LocalData.database

    def get_read_only_pvs(self):
        return _LocalData.di + _LocalData.ap

    def get_read_write_pvs(self):
        return _LocalData.ps + _LocalData.fk + _LocalData.rf + _LocalData.ti

    def get_dynamical_pvs(self):
        return _LocalData.dynamical_pvs

    def get_constant_pvs(self):
        return _LocalData.fk_pos
