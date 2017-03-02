import siriuspy

class DeviceNames:
    pvnaming_glob = 'Glob'
    pvnaming_fam  = 'Fam'
    pvnaming_inj  = 'Inj'

    def __init__(self, section, el_names, fam_names, glob_names, inj_names,
                excitation_curves_mapping, pulse_curve_mapping, get_family_data=None):
        self.section = section
        self.el_names = el_names  # All these Family names must be defined in family_data dictionary
        self.fam_names = fam_names  # All these Family names must be defined in family_data dictionary
        self.glob_names = glob_names # These Family names can be any name
        self.inj_names  = inj_names  # These Family names can be any name
        self.disciplines =  sorted(el_names.keys() | fam_names.keys() | glob_names.keys() | inj_names.keys())
        ##### Excitation Curves #######
        self.excitation_curves_mapping = excitation_curves_mapping
        ##### Pulsed Magnets #######
        self.pulse_curve_mapping = pulse_curve_mapping
        ##### Family Data Function ######
        self.get_family_data = get_family_data

    def split_name(self, name):
        return siriuspy.split_name(name)

    def join_name(self, discipline, device, subsection,
        instance=None, proper=None, field=None):
        return siriuspy.join_name(self.section, discipline, device, subsection,
        instance, proper, field)

    ##### Device Names ######
    def get_device_names(self, accelerator=None, discipline = None):
        """Return a dictionary of device names for given discipline
        each entry is another dictionary of model families whose
        values are the indices in the pyaccel model of the magnets
        that belong to the family. The magnet models can be segmented,
        in which case the value is a python list of lists."""
        family_data = accelerator
        if accelerator is None:
            family_data = None
        elif not isinstance(accelerator, dict):
            family_data = self.get_family_data(accelerator)

        if discipline == None:
            discipline = self.disciplines
        if not isinstance(discipline,(list,tuple)):
            discipline = [discipline.upper()]
        else:
            discipline = [s.upper() for s in discipline]

        _dict = {}
        for dis in discipline:
            if family_data is not None:
                names = self.el_names.get(dis) or []
                for el in names:
                    subsec = family_data[el]['subsection']
                    num    = family_data[el]['instance']
                    idx    = family_data[el]['index']
                    for i in range(len(subsec)):
                        device_name = self.join_name(dis, el, subsec[i], num[i])
                        _dict.update({ device_name:{el:idx[i]} })

                fams = self.fam_names.get(dis) or []
                for fam in fams:
                    idx = family_data[fam]['index']
                    device_name = self.join_name(dis, fam, self.pvnaming_fam)
                    _dict.update({ device_name:{fam:idx} })

            globs = self.glob_names.get(dis) or []
            for glob in globs:
                device_name = self.join_name(dis, glob, self.pvnaming_glob)
                _dict.update({ device_name:{} })

            injs = self.inj_names.get(dis) or []
            for inj in injs:
                device_name = self.join_name(dis, inj, self.pvnaming_inj)
                _dict.update({ device_name:{} })

        return _dict

    def get_magnet_names(self,accelerator):
        _dict = self.get_device_names(accelerator, 'ma')
        _dict.update(self.get_device_names(accelerator, 'pm'))
        return _dict


    ####### Power Supplies ########
    def get_magnet2power_supply_mapping(self, accelerator):
        """Get mapping from power supply to magnet names and inverse mapping

        Returns mapping, inverse_mapping.
        """
        mapping = dict()
        for mag, power in zip(['ma','pm'],['ps','pu']):
            # create a mapping of index in the lattice and magnet name
            mag_ind_dict = dict()
            for mag_name, mag_prop in self.get_device_names(accelerator,mag).items():
                if self.pvnaming_fam in mag_name: continue
                idx = list(mag_prop.values())[0][0]
                if mag_ind_dict.get(idx) is None: # there could be more than one magnet per index
                    mag_ind_dict[idx]  = set()
                mag_ind_dict[idx] |= {mag_name}

            #Use this mapping to see if the power supply is attached to the same element
            for ps_name, ps_prop in self.get_device_names(accelerator,power).items():
                ps = self.split_name(ps_name)['Device']
                idx = list(ps_prop.values())[0]
                idx = [idx[0]] if self.pvnaming_fam not in ps_name else [i[0] for i in idx] # if Fam then indices are list of lists
                for i in idx:
                    mag_names = mag_ind_dict[i]
                    for mag_name in mag_names:
                        m = self.split_name(mag_name)['Device']
                        if (m not in ps) and (ps not in m):
                            continue  # WARNING: WILL FAIL IF THE POWER SUPPLY DOES NOT HAVE THE MAGNET NAME ON ITSELF OR VICE VERSA.
                        if mapping.get(mag_name) is None:
                            mapping[mag_name]  = set()
                        mapping[mag_name] |= {ps_name}

        # Finally find the inverse map
        inverse_mapping = dict()
        for key, value in mapping.items():
            for v in value:
                if inverse_mapping.get(v) is None:
                    inverse_mapping[v] = set()
                inverse_mapping[v].add(key)

        return mapping, inverse_mapping


    ####### Pulsed Magnets #########
    def _get_pulsed_magnet_mapping(self, accelerator,delay_or_enbl):
        mapping = {}
        tis_dev = set(self.get_device_names(accelerator, 'TI').keys())
        pms_dev = set(self.get_device_names(accelerator, 'PM').keys())
        for pm in pms_dev:
            dev = split_name(pm)['Device']
            ins = split_name(pm)['Instance']
            dev += '-'+ins if ins else ins
            ti = [i for i in tis_dev if dev in i][0]
            mapping[pm] = ti + delay_or_enbl

        inverse_mapping = dict()
        for key, value in mapping.items():
            inverse_mapping[value] = key

        return mapping, inverse_mapping

    def get_magnet_delay_mapping(self, accelerator):
        """Get mapping from pulsed magnet to timing delay

        Returns dict.
        """
        return self._get_pulsed_magnet_mapping(accelerator,':Delay')

    def get_magnet_enabled_mapping(self, accelerator):
        """Get mapping from pulsed magnet to timing enabled

        Returns dict.
        """
        return self._get_pulsed_magnet_mapping(accelerator,':Enbl')

    def get_pulse_curve_mapping(self, accelerator):
        """Get mapping from pulsed magnet to pulse curve file names

        Returns dict.
        """
        mapping = {}
        pms_dev = set(self.get_device_names(accelerator, 'PM').keys())
        for pm in pms_dev:
            dev = split_name(pm)['Device']
            mapping[pm] = self.pulse_curve_mapping[dev]

        return mapping


    ####### Excitation Curves #########
    def get_excitation_curve_mapping(self,accelerator):
        """Get mapping from magnet to excitation curve file names

        Returns dict.
        """
        magnets = self.get_magnet_names(accelerator)

        ec = dict()
        for fams, curve in self.excitation_curves_mapping.items():
            for name in magnets:
                device = self.split_name(name)['Device']
                if device.startswith(fams): ec[name] = curve
        return ec


class RecordNames:

    def __init__(self, device_names, model=None, family_data = None):
        self.family_data = family_data
        self.model = model
        self.device_names = device_names
        self.build_data()

    def build_data(self):
        self._init_record_names()
        self._init_database()
        self._init_dynamical_pvs()

    def _init_record_names(self):
        self.all_record_names = {}
        if 'DI' in self.device_names.disciplines:
            self._init_di_record_names()
        else:
            self.di = []
        if 'PS' in self.device_names.disciplines:
            self._init_ps_record_names()
        else:
            self.ps = []
            self.ps_rb = []
        if 'AP' in self.device_names.disciplines:
            self._init_ap_record_names()
        else:
            self.ap = []
        if 'RF' in self.device_names.disciplines:
            self._init_rf_record_names()
        else:
            self.rf = []
        if 'TI' in self.device_names.disciplines:
            self._init_ti_record_names()
        else:
            self.ti = []
        self._init_fk_record_names()

    def _init_di_record_names(self):
        _device_names = self.device_names.get_device_names(self.family_data, 'DI')
        _record_names = {}
        for device_name in _device_names.keys():
            device = self.device_names.split_name(device_name)['Device']
            if device == 'BPM':
                _record_names[device_name + ':PosX-Mon'] = _device_names[device_name]
                _record_names[device_name + ':PosY-Mon'] = _device_names[device_name]
            elif 'TuneP' in device:
                _record_names[device_name + ':Freq1-Mon'] = _device_names[device_name]
                _record_names[device_name + ':Freq2-Mon'] = _device_names[device_name]
                _record_names[device_name + ':Freq3-Mon'] = _device_names[device_name]
            elif device == 'DCCT':
                _record_names[device_name + ':Current-Mon'] = _device_names[device_name]
                _record_names[device_name + ':BbBCurrent-Mon'] = _device_names[device_name]
            else:
                _record_names[device_name] = _device_names[device_name]
        self.all_record_names.update(_record_names)
        self.di = list(_record_names.keys())

    def _init_ps_record_names(self):
        _device_names = self.device_names.get_device_names(self.family_data, 'PS')
        if 'PU' in self.device_names.disciplines:
            _device_names.update(self.device_names.get_device_names(self.family_data, 'PU'))
        _record_names = {}
        for device_name in _device_names.keys():
            _record_names[device_name + ':Current-SP'] = _device_names[device_name]
            _record_names[device_name + ':Current-RB'] = _device_names[device_name]
            _record_names[device_name + ':PwrState-Sel'] = _device_names[device_name]
            _record_names[device_name + ':PwrState-Sts'] = _device_names[device_name]
            _record_names[device_name + ':OpMode-Sel'] = _device_names[device_name]
            _record_names[device_name + ':OpMode-Sts'] = _device_names[device_name]
            _record_names[device_name + ':CtrlMode-Mon'] = _device_names[device_name]
            _record_names[device_name + ':Reset-Cmd'] = _device_names[device_name]
        self.all_record_names.update(_record_names)
        self.ps_rb = []
        self.ps    = []
        for rec in _record_names.keys():
            if rec.endswith(('-RB','-Sts','-Mon')):
                self.ps_rb.append(rec)
            else:
                self.ps.append(rec)

    def _init_ap_record_names(self):
        _record_names = self.device_names.get_device_names(self.family_data, 'AP')
        self.all_record_names.update(_record_names)
        self.ap = list(_record_names.keys())

    def _init_rf_record_names(self):
        _device_names = self.device_names.get_device_names(self.family_data, 'RF')
        _record_names = {}
        for device_name in _device_names.keys():
            device = self.device_names.split_name(device_name)['Device']
            if device.endswith('Cav'):
                _record_names[device_name + ':Freq'] = _device_names[device_name]
                _record_names[device_name + ':Volt'] = _device_names[device_name]
            else:
                _record_names[device_name] = _device_names[device_name]
        self.all_record_names.update(_record_names)
        self.rf = list(_record_names.keys())

    def _init_ti_record_names(self):
        _device_names = self.device_names.get_device_names(self.family_data, 'TI')
        _record_names = {}
        for device_name in _device_names.keys():
            if 'Cycle' in device_name:
                _record_names[device_name + ':Start-Cmd']   = _device_names[device_name]
                _record_names[device_name + ':InjBun']      = _device_names[device_name]
                _record_names[device_name + ':InjBunIncr']  = _device_names[device_name]
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
                self.database[p] = {'type' : 'float', 'unit':'mA', 'count': self.model.harmonic_number}
            elif 'BPM' in p:
                if self.device_names.pvnaming_fam in p:
                    self.database[p] = {'type' : 'float', 'unit':'m', 'count': len(self.all_record_names[p]['BPM'])}
                else:
                    self.database[p] = {'type' : 'float', 'unit':'m', 'count': 1}
            else:
                self.database[p] = {'type' : 'float', 'count': 1, 'value': 0.0}
        for p in self.ps:
            if p.endswith('-SP'):
                self.database[p] = {'type' : 'float', 'unit':'A', 'count': 1, 'value': 0.0}
            elif p.endswith('PwrState-Sel'):
                self.database[p] = {'type' : 'enum', 'enums':('Off','On'), 'value':1}
            elif p.endswith('OpMode-Sel'):
                self.database[p] = {'type' : 'enum', 'enums':('SlowRef','FastRef','WfmRef','SigGen'), 'value':0}
            elif p.endswith('CtrlMode-Mon'):
                self.database[p] = {'type' : 'enum', 'enums':('Remote','Local'), 'value':0}
            elif p.endswith('Reset-Cmd'):
                self.database[p] = {'type' : 'int'}
            else:
                raise Exception('PS PV type not recognized!')
        for p in self.ps_rb:
            if p.endswith('PwrState-Sts'):
                self.database[p] = {'type' : 'enum', 'enums':('Off','On'), 'value':1}
            elif p.endswith('OpMode-Sts'):
                self.database[p] = {'type' : 'enum', 'enums':('SlowRef','FastRef','WfmRef','SigGen'), 'value':0}
            elif p.endswith('CtrlMode-Mon'):
                self.database[p] = {'type' : 'enum', 'enums':('Remote','Local'), 'value':0}
            else:
                self.database[p] = {'type' : 'float', 'unit':'A', 'count': 1, 'value': 0.0}
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
