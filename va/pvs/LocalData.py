import time
import copy as _copy
import siriuspy.namesys as _namesys
#import siriuspy.magnet as _magnet
import siriuspy.pwrsupply as _pwrsupply
from siriuspy.timesys.time_simul import TimingSimulation



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

    def join_name(self, discipline, device, subsection,
        instance=None, proper=None, field=None):
        return _namesys.join_name(self.section, discipline, device, subsection,
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
                ps = _namesys.SiriusPVName(ps_name).dev_type
                idx = list(ps_prop.values())[0]
                idx = [idx[0]] if self.pvnaming_fam not in ps_name else [i[0] for i in idx] # if Fam then indices are list of lists
                for i in idx:
                    mag_names = mag_ind_dict[i]
                    for mag_name in mag_names:
                        m = _namesys.SiriusPVName(mag_name).dev_type
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
            parts = _namesys.SiriusPVName(pm)
            dev = parts.dev_type
            ins = parts.dev_instance
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
            dev = _namesys.SiriusPVName(pm).dev_type
            mapping[pm] = self.pulse_curve_mapping[dev]

        return mapping

    ####### Excitation Curves #########
    def get_excitation_curve_mapping(self,accelerator):
        """Get mapping from magnet to excitation curve file names

        Returns dict.
        """
        magnets = self.get_magnet_names(accelerator)

        ec = dict()
        for fams, curve in self.excitation_curves_mapping:
            if isinstance(fams[0],tuple):
                for name in magnets:
                    parts = _namesys.SiriusPVName(name)
                    device = parts.dev_type
                    sub    = parts.subsection
                    inst   = parts.dev_instance
                    if sub.endswith(fams[0][0]) and device.startswith(fams[0][1]) and inst.endswith(fams[0][2]):
                        ec[name] = curve
            else:
                for name in magnets:
                    parts = _namesys.SiriusPVName(name)
                    if parts.dev_type.startswith(fams): ec[name] = curve
        return ec


class RecordNames:

    def __init__(self, device_names, model=None, family_data = None):
        self.family_data = family_data
        self.database = dict()
        self.model = model
        self.device_names = device_names
        self._build_data()

    def _build_data(self):
        self._init_record_names()
        self._init_dynamical_pvs()

    def _init_record_names(self):
        self.all_record_names = {}
        if 'DI' in self.device_names.disciplines:
            self._init_di_record_names()
        else:
            self.di_ro = []
            self.di_rw = []
        if 'PS' in self.device_names.disciplines:
            self._init_ps_record_names()
        else:
            self.ps_ro = []
            self.ps_rw = []
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
        for dev_name in _device_names.keys():
            parts = _namesys.SiriusPVName(dev_name)
            if parts.dev_type== 'BPM':
                p1 = dev_name + ':PosX-Mon'
                _record_names[p1] = _device_names[dev_name]
                p2 = dev_name + ':PosY-Mon'
                _record_names[p2] = _device_names[dev_name]
                if parts.subsection == self.device_names.pvnaming_fam:
                    self.database[p1] = {'type' : 'float', 'unit':'m', 'count': len(_device_names[dev_name]['BPM'])}
                    self.database[p2] = {'type' : 'float', 'unit':'m', 'count': len(_device_names[dev_name]['BPM'])}
                else:
                    self.database[p1] = {'type' : 'float', 'value': 0.0}
                    self.database[p2] = {'type' : 'float', 'value': 0.0}
            elif 'TuneP' in parts.dev_type:
                p = dev_name + ':Freq1-Mon'
                _record_names[p] = _device_names[dev_name]
                self.database[p] = {'type' : 'float', 'value': 0.0}
                p = dev_name + ':Freq2-Mon'
                _record_names[p] = _device_names[dev_name]
                self.database[p] = {'type' : 'float', 'value': 0.0}
                p = dev_name + ':Freq3-Mon'
                _record_names[p] = _device_names[dev_name]
                self.database[p] = {'type' : 'float', 'value': 0.0}
            elif parts.dev_type== 'DCCT':
                p = dev_name + ':Current-Mon'
                _record_names[p] = _device_names[dev_name]
                self.database[p] = {'type' : 'float', 'value': 0.0}
                p = dev_name + ':BbBCurrent-Mon'
                _record_names[p] = _device_names[dev_name]
                self.database[p] = {'type' : 'float', 'unit':'mA', 'count': self.model.harmonic_number}
                p = dev_name + ':HwFlt-Mon'
                _record_names[p] = _device_names[dev_name]
                self.database[p] = {'type' : 'float', 'value': 0.0}
                p = dev_name + ':CurrThold'
                _record_names[p] = _device_names[dev_name]
                self.database[p] = {'type' : 'float', 'value': 0.0}
            else:
                _record_names[dev_name] = _device_names[dev_name]
                self.database[dev_name] = {'type' : 'float', 'value': 0.0}
        self.all_record_names.update(_record_names)
        #self.di_ro = list(_record_names.keys())
        self.di_ro = []
        self.di_rw = []
        for rec in _record_names.keys():
            if rec.endswith(('CurrThold')):
                self.di_rw.append(rec)
            else:
                self.di_ro.append(rec)

    def _init_ps_record_names(self):
        _device_names = self.device_names.get_device_names(self.family_data, 'PS')
        if 'PU' in self.device_names.disciplines:
            _device_names.update(self.device_names.get_device_names(self.family_data, 'PU'))
        _record_names = {}
        for device_name in _device_names.keys():

            # this could be improved: the code could reuse PS objects from power_supply.py or vice-versa.
            if device_name.startswith('LI-'):
                ps = _pwrsupply.PowerSupply(psname = device_name)
            else:
                ps = _pwrsupply.PowerSupply(psname = device_name)
            db = ps.database
            for propty in db:
                value = db[propty]
                p = device_name + ':' + propty
                _record_names[p] = _device_names[device_name]
                if 'lolo' in value and value['lolo'] is None:
                    print("there is no value['lolo'] for  ", device_name, ps.pstype)
                self.database[p] = value

        self.all_record_names.update(_record_names)
        self.ps_ro = []
        self.ps_rw = []
        for rec in _record_names.keys():
            if rec.endswith(('-RB','-Sts','-Mon')):
                self.ps_ro.append(rec)
            else:
                self.ps_rw.append(rec)

    def _init_ap_record_names(self):
        _record_names = dict()
        _device_names = self.device_names.get_device_names(self.family_data, 'AP')
        for dev_name in _device_names.keys():
            parts = _namesys.SiriusPVName(dev_name)
            if parts.dev_type== 'CurrLT':
                p = dev_name + ':CurrLT-Mon'
                _record_names[p] = _device_names[dev_name]
                self.database[p] = {'type' : 'float', 'value': 0.0}
                p = dev_name + ':BbBCurrLT-Mon'
                _record_names[p] = _device_names[dev_name]
                self.database[p] = {'type' : 'float', 'count': self.model.harmonic_number, 'value': 0.0}
            else:
                _record_names[dev_name] = _device_names[dev_name]
                self.database[dev_name] = {'type' : 'float', 'count': 1, 'value': 0.0}
        self.all_record_names.update(_record_names)
        self.ap = list(_record_names.keys())

    def _init_rf_record_names(self):
        _device_names = self.device_names.get_device_names(self.family_data, 'RF')
        _record_names = {}
        for device_name in _device_names.keys():
            parts = _namesys.SiriusPVName(device_name)
            #if parts.dev_type.endswith('Cav'):
            if parts.dev_type in ('P5Cav','SRFCav'):
                p = device_name + ':Freq-SP'
                _record_names[p] = _device_names[device_name]
                self.database[p] = {'type' : 'float', 'count': 1, 'value': 0.0, 'prec': 10}
                p = device_name + ':Freq-RB'
                _record_names[p] = _device_names[device_name]
                self.database[p] = {'type' : 'float', 'count': 1, 'value': 0.0, 'prec': 10}
                p = device_name + ':Volt-SP'
                _record_names[p] = _device_names[device_name]
                self.database[p] = {'type' : 'float', 'count': 1, 'value': 0.0, 'prec': 10}
                p = device_name + ':Volt-RB'
                _record_names[p] = _device_names[device_name]
                self.database[p] = {'type' : 'float', 'count': 1, 'value': 0.0, 'prec': 10}
            else:
                _record_names[device_name] = _device_names[device_name]
                self.database[device_name] = {'type' : 'float', 'count': 1, 'value': 0.0, 'prec': 10}
        self.all_record_names.update(_record_names)
        self.rf = list(_record_names.keys())

    def _init_ti_record_names(self):
        _device_names = self.device_names.get_device_names(self.family_data, 'TI')
        _record_names = {}
        for device_name in _device_names.keys():
            parts = _namesys.SiriusPVName(device_name)
            if parts.dev_type == 'Timing':
                ioc = TimingSimulation
                db = ioc.get_database()
                self.database.update(db)
                devs = _device_names[device_name]
                _record_names.update({p:devs for p in db.keys()})
            else:
                p = device_name + ':Enbl'
                _record_names[p] = _device_names[device_name]
                self.database[p] = {'type' : 'enum', 'enums':('Dsbl','Enbl'), 'value':1}
                p = device_name + ':Delay'
                _record_names[p] = _device_names[device_name]
                self.database[p] = {'type' : 'float', 'count': 1, 'value': 0.0, 'prec': 10}
        self.all_record_names.update(_record_names)
        self.ti_ro = []
        self.ti_rw = []
        for rec_name in _record_names.keys():
            if rec_name.endswith(('-RB','-Sts','-Mon')):
                self.ti_ro.append(rec_name)
            else:
                self.ti_rw.append(rec_name)

    def _init_fk_record_names(self):
        _record_names = dict() # get_fake_record_names(self.family_data)
        for p in _record_names.keys():
            self.database[p] = {'type' : 'float', 'count': 1, 'value': 0.0}
        self.all_record_names.update(_record_names)
        self.fk = []
        self.fk_pos  = []

    def _init_dynamical_pvs(self):
        self.dynamical_pvs = []
        for pv in self.di_ro:
            if 'Current' in pv:
                self.dynamical_pvs.append(pv)
                self.di_ro.remove(pv)
        for pv in self.ap:
            if 'CurrLT' in pv:
                self.dynamical_pvs.append(pv)
                self.ap.remove(pv)

    def get_all_record_names(self):
        return _copy.deepcopy(self.all_record_names)

    def get_database(self):
        return _copy.deepcopy(self.database)

    def get_read_only_pvs(self):
        return self.di_ro + self.ap + self.ps_ro + self.ti_ro # a copy!

    def get_read_write_pvs(self):
        return self.di_rw + self.ps_rw + self.fk + self.rf + self.ti_rw # a copy!

    def get_dynamical_pvs(self):
        return _copy.deepcopy(self.dynamical_pvs)

    def get_constant_pvs(self):
        return _copy.deepcopy(self.fk_pos)
