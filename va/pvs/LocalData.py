class _LocalData:

    def __init__(self,family_data,model):
        self.family_data = family_data
        self.model = model
        self.build_data()

    def build_data(self):
        self._init_record_names()
        self._init_database()
        self._init_dynamical_pvs()

    def _init_record_names(self):
        self.all_record_names = {}
        if 'DI' in self.model.device_names.disciplines:
            self._init_di_record_names()
        else:
            self.di = []
        if 'PS' in self.model.device_names.disciplines:
            self._init_ps_record_names()
        else:
            self.ps = []
        if 'AP' in self.model.device_names.disciplines:
            self._init_ap_record_names()
        else:
            self.ap = []
        if 'RF' in self.model.device_names.disciplines:
            self._init_rf_record_names()
        else:
            self.rf = []
        if 'TI' in self.model.device_names.disciplines:
            self._init_ti_record_names()
        else:
            self.ti = []
        self._init_fk_record_names()

    def _init_di_record_names(self):
        _device_names = self.model.get_device_names(self.family_data, 'DI')
        _record_names = {}
        for device_name in _device_names.keys():
            device = self.model.device_names.split_name(device_name)['Device']
            if device == 'BPM':
                _record_names[device_name + ':PosX-Mon'] = _device_names[device_name]
                _record_names[device_name + ':PosY-Mon'] = _device_names[device_name]
            elif 'TuneP' in device:
                _record_names[device_name + ':Freq1'] = _device_names[device_name]
                _record_names[device_name + ':Freq2'] = _device_names[device_name]
                _record_names[device_name + ':Freq3'] = _device_names[device_name]
            elif device == 'DCCT':
                _record_names[device_name + ':Current-Mon'] = _device_names[device_name]
                _record_names[device_name + ':BbBCurrent-Mon'] = _device_names[device_name]
            else:
                _record_names[device_name] = _device_names[device_name]
        self.all_record_names.update(_record_names)
        self.di = list(_record_names.keys())

    def _init_ps_record_names(self):
        _device_names = self.model.get_device_names(self.family_data, 'PS')
        if 'PU' in self.model.device_names.disciplines:
            _device_names.update(self.model.get_device_names(self.family_data, 'PU'))
        _record_names = {}
        for device_name in _device_names.keys():
            _record_names[device_name + ':Current-SP'] = _device_names[device_name]
            _record_names[device_name + ':Current-RB'] = _device_names[device_name]
        self.all_record_names.update(_record_names)
        self.ps_rb = []
        self.ps    = []
        for rec in _record_names.keys():
            if rec.endswith('-RB'):
                self.ps_rb.append(rec)
            else:
                self.ps.append(rec)

    def _init_ap_record_names(self):
        _record_names = self.model.get_device_names(self.family_data, 'AP')
        self.all_record_names.update(_record_names)
        self.ap = list(_record_names.keys())

    def _init_rf_record_names(self):
        _device_names = self.model.get_device_names(self.family_data, 'RF')
        _record_names = {}
        for device_name in _device_names.keys():
            device = self.model.device_names.split_name(device_name)['Device']
            if device.endswith('Cav'):
                _record_names[device_name + ':Freq'] = _device_names[device_name]
                _record_names[device_name + ':Volt'] = _device_names[device_name]
            else:
                _record_names[device_name] = _device_names[device_name]
        self.all_record_names.update(_record_names)
        self.rf = list(_record_names.keys())

    def _init_ti_record_names(self):
        _device_names = self.model.get_device_names(self.family_data, 'TI')
        _record_names = {}
        for device_name in _device_names.keys():
            if 'Cycle' in device_name:
                _record_names[device_name + ':StartInj'] = _device_names[device_name]
                _record_names[device_name + ':InjBun'] = _device_names[device_name]
            else:
                _record_names[device_name + ':Enbl']  = _device_names[device_name]
                _record_names[device_name + ':Delay'] = _device_names[device_name]
        self.all_record_names.update(_record_names)
        self.ti = list(_record_names.keys())

    def _init_fk_record_names(self):
        _record_names = {} # get_fake_record_names(self.family_data)
        self.all_record_names.update(_record_names)
        self.fk = []
        self.fk_pos  = []

    def _init_database(self):
        self.database = {}
        for p in self.di:
            if any([substring in p for substring in ('BbBCurrent',)]):
                self.database[p] = {'type' : 'float', 'count': self.model.harmonic_number}
            elif 'BPM' in p:
                if self.model.device_names.pvnaming_fam in p:
                    self.database[p] = {'type' : 'float', 'count': len(self.all_record_names[p]['BPM'])}
                else:
                    self.database[p] = {'type' : 'float', 'count': 1}
            else:
                self.database[p] = {'type' : 'float', 'count': 1, 'value': 0.0}
        for p in self.ps:
            self.database[p] = {'type' : 'float', 'count': 1, 'value': 0.0}
        for p in self.ps_rb:
            self.database[p] = {'type' : 'float', 'count': 1, 'value': 0.0}
        for p in self.ap:
            if any([substring in p for substring in ('BbBCurrLT',)]):
                self.database[p] = {'type' : 'float', 'count': self.model.harmonic_number, 'value': 0.0}
            else:
                self.database[p] = {'type' : 'float', 'count': 1, 'value': 0.0}
        for p in self.ti:
            self.database[p] = {'type' : 'float', 'count': 1, 'value': 0.0}
        for p in self.rf:
            self.database[p] = {'type' : 'float', 'count': 1, 'value': 0.0, 'prec': 10}
        for p in self.fk:
            self.database[p] = {'type' : 'float', 'count': 1, 'value': 0.0}
        for p in self.fk_pos:
            self.database[p] = {'type' : 'float', 'count': len(self.all_record_names[p]['pos'])}

    def _init_dynamical_pvs(self):
        self.dynamical_pvs = []
        for pv in self.di:
            if 'Current' in pv:
                self.dynamical_pvs.append(pv)
                self.di.remove(pv)
        for pv in self.ap:
            if 'CurrLT' in pv:
                self.dynamical_pvs.append(pv)
                self.ap.remove(pv)

    def get_all_record_names(self):
        return self.all_record_names

    def get_database(self):
        return self.database

    def get_read_only_pvs(self):
        return self.di + self.ap + self.ps_rb

    def get_read_write_pvs(self):
        return self.ps + self.fk + self.rf + self.ti

    def get_dynamical_pvs(self):
        return self.dynamical_pvs

    def get_constant_pvs(self):
        return self.fk_pos
