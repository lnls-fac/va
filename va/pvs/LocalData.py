import copy as _copy

from siriuspy.namesys import SiriusPVName as _PVName
from siriuspy.namesys import join_name as _join_name
from siriuspy.pwrsupply import csdev as _pwrsupply_csdev

from ..power_supply import PowerSupply as _PowerSupply
from ..timesys import TimingSimulation


class DeviceNames:
    pvnaming_glob = 'Glob'
    pvnaming_fam = 'Fam'
    pvnaming_inj = 'Inj'

    def __init__(
            self, section, el_names, fam_names, glob_names, inj_names,
            excitation_curves_mapping, pulse_curve_mapping,
            get_family_data=None):
        self.section = section
        # All these Family names must be defined in family_data dictionary:
        self.el_names = el_names
        self.fam_names = fam_names
        # These Family names can be any name:
        self.glob_names = glob_names
        self.inj_names = inj_names
        self.disciplines = sorted(el_names.keys() | fam_names.keys() |
                                  glob_names.keys() | inj_names.keys())
        # #### Excitation Curves ######
        self.excitation_curves_mapping = excitation_curves_mapping
        # #### Pulsed Magnets ######
        self.pulse_curve_mapping = pulse_curve_mapping
        # #### Family Data Function #####
        self.get_family_data = get_family_data

    def join_name(
            self, subsection, discipline, device, instance=None, proper=None,
            field=None):
        """."""
        name = _join_name(
            sec=self.section, sub=subsection, dis=discipline, dev=device,
            idx=instance, propty=proper, field=field)

        return name

    # #### Device Names ####
    def get_device_names(self, accelerator=None, discipline=None):
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

        if discipline is None:
            discipline = self.disciplines
        if not isinstance(discipline, (list, tuple)):
            discipline = [discipline.upper()]
        else:
            discipline = [s.upper() for s in discipline]

        _dict = {}
        for dis in discipline:
            if family_data is not None:
                names = self.el_names.get(dis) or []
                for el in names:
                    subsec = family_data[el]['subsection']
                    num = family_data[el]['instance']
                    idx = family_data[el]['index']
                    for i in range(len(subsec)):
                        dev_name = self.join_name(subsec[i], dis, el, num[i])
                        dev_name = self._particular_dev_renaming(dev_name)
                        _dict.update({dev_name: {el: idx[i]}})

                fams = self.fam_names.get(dis) or []
                for fam in fams:
                    idx = family_data[fam]['index']
                    dev_name = self.join_name(self.pvnaming_fam, dis, fam)
                    _dict.update({dev_name: {fam: idx}})

            globs = self.glob_names.get(dis) or []
            for glob in globs:
                dev_name = self.join_name(self.pvnaming_glob, dis, glob)
                _dict.update({dev_name: {}})

            injs = self.inj_names.get(dis) or []
            for inj in injs:
                dev_name = self.join_name(self.pvnaming_inj, dis, inj)
                _dict.update({dev_name: {}})

        return _dict

    def get_magnet_names(self, accelerator):
        _dict = self.get_device_names(accelerator, 'ma')
        _dict.update(self.get_device_names(accelerator, 'pm'))
        return _dict

    # ###### Power Supplies ########
    def get_magnet2power_supply_mapping(self, accelerator):
        """Get mapping from power supply to magnet names and inverse mapping

        Returns mapping, inverse_mapping.
        """
        mapping = dict()
        for mag, power in zip(['ma', 'pm'], ['ps', 'pu']):

            # create a mapping of lattice index and magnet name
            idx2mag = dict()
            magdevs = self.get_device_names(accelerator, mag)
            for mag_name, mag_prop in magdevs.items():
                if self.pvnaming_fam in mag_name:
                    continue
                idx = list(mag_prop.values())[0][0]
                # there could be more than one magnet per index
                if idx not in idx2mag:
                    idx2mag[idx] = {mag_name}
                else:
                    idx2mag[idx].add(mag_name)

            # check through lattice indices magnets / power supply links
            psdevs = self.get_device_names(accelerator, power)
            for ps_name, ps_prop in psdevs.items():
                psdevname = _PVName(ps_name).dev
                idx = list(ps_prop.values())[0]
                idx = [idx[0]] if self.pvnaming_fam not in ps_name else \
                    [i[0] for i in idx]  # if Fam then indcs are list of lists
                for i in idx:
                    mag_names = idx2mag[i]
                    for mag_name in mag_names:
                        magdevname = _PVName(mag_name).dev
                        if (magdevname not in psdevname) and \
                           (psdevname not in magdevname):
                            # WARNING: WILL FAIL IF THE POWER SUPPLY DOES NOT
                            # HAVE THE MAGNET NAME ON ITSELF OR VICE VERSA.
                            continue
                        if mapping.get(mag_name) is None:
                            mapping[mag_name] = set()
                        mapping[mag_name] |= {ps_name}

        # finally find the inverse map
        inverse_mapping = dict()
        for key, value in mapping.items():
            for v in value:
                if inverse_mapping.get(v) is None:
                    inverse_mapping[v] = set()
                inverse_mapping[v].add(key)

        return mapping, inverse_mapping

    ####### Pulsed Magnets #########
    def _get_pulsed_magnet_mapping(self, accelerator, delay_or_enbl):
        mapping = {}
        tis_dev = set(self.get_device_names(accelerator, 'TI').keys())
        pms_dev = set(self.get_device_names(accelerator, 'PM').keys())
        for pm in pms_dev:
            parts = _PVName(pm)
            dev = parts.dev
            ins = parts.idx
            dev += '-'+ins if ins else ins
            ti = [i for i in tis_dev if dev in i][0]
            mapping[pm] = ti + delay_or_enbl + '-SP'
            mapping[pm] = ti + delay_or_enbl + '-RB'

        inverse_mapping = dict()
        for key, value in mapping.items():
            inverse_mapping[value] = key

        return mapping, inverse_mapping

    def get_magnet_delay_mapping(self, accelerator):
        """Get mapping from pulsed magnet to timing delay

        Returns dict.
        """
        return self._get_pulsed_magnet_mapping(accelerator, ':Delay')

    def get_magnet_enabled_mapping(self, accelerator):
        """Get mapping from pulsed magnet to timing enabled

        Returns dict.
        """
        return self._get_pulsed_magnet_mapping(accelerator, ':Enbl')

    def get_pulse_curve_mapping(self, accelerator):
        """Get mapping from pulsed magnet to pulse curve file names

        Returns dict.
        """
        mapping = {}
        pms_dev = set(self.get_device_names(accelerator, 'PM').keys())
        for pm in pms_dev:
            dev = _PVName(pm).dev
            mapping[pm] = self.pulse_curve_mapping[dev]

        return mapping

    ####### Excitation Curves #########
    def get_excitation_curve_mapping(self, accelerator):
        """Get mapping from magnet to excitation curve file names

        Returns dict.
        """
        magnets = self.get_magnet_names(accelerator)

        ec = dict()
        for fams, curve in self.excitation_curves_mapping:
            if isinstance(fams[0], tuple):
                for name in magnets:
                    parts = _PVName(name)
                    device = parts.dev
                    sub = parts.sub
                    inst = parts.idx
                    if sub.endswith(fams[0][0]) and \
                            device.startswith(fams[0][1]) and \
                            inst.endswith(fams[0][2]):
                        ec[name] = curve
            else:
                for name in magnets:
                    parts = _PVName(name)
                    if parts.dev.startswith(fams):
                        ec[name] = curve
        return ec

    def _particular_dev_renaming(self, dev_name):
        if dev_name.startswith('LI') and 'Slnd' in dev_name:
            if dev_name[-2:] in ('14', '15', '16', '17', '18', '19', '20', '21'):
                dev_name = dev_name.replace('LI-01', 'LI-Fam')
        if dev_name.startswith('TS') and 'CV' in dev_name:
            dev_name = dev_name.replace('TS-01:PS-CV-2', 'TS-01:PS-CV-1E2')
            dev_name = dev_name.replace('TS-01:PS-CV-3', 'TS-01:PS-CV-2')
            dev_name = dev_name.replace('TS-02:PS-CV-1', 'TS-02:PS-CV-0')
            dev_name = dev_name.replace('TS-02:PS-CV-2', 'TS-02:PS-CV')
            dev_name = dev_name.replace('TS-04:PS-CV-1', 'TS-04:PS-CV-0')
            dev_name = dev_name.replace('TS-04:PS-CV-2', 'TS-04:PS-CV-1')
            dev_name = dev_name.replace('TS-04:PS-CV-3', 'TS-04:PS-CV-1E2')
            dev_name = dev_name.replace('TS-04:PS-CV-4', 'TS-04:PS-CV-2')
        return dev_name


class RecordNames:
    """RecordNames Class.

    Returns:
        [type]: [description]
    """
    def __init__(self, device_names, model=None, family_data=None):
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
            pass
        else:
            self.ti = []
        self._init_fk_record_names()

    def _init_di_record_names(self):
        _device_names = self.device_names.get_device_names(
            self.family_data, 'DI')
        _record_names = {}
        for dev_name in _device_names.keys():
            parts = _PVName(dev_name)
            if parts.dev == 'BPM':
                p1 = dev_name + ':PosX-Mon'
                _record_names[p1] = _device_names[dev_name]
                self.database[p1] = {
                    'type': 'float', 'unit':'nm', 'value': 0.0}
                p2 = dev_name + ':PosY-Mon'
                _record_names[p2] = _device_names[dev_name]
                self.database[p2] = {
                    'type': 'float', 'unit':'nm', 'value': 0.0}
            elif 'TuneP' in parts.dev:
                p = dev_name + ':Freq1-Mon'
                _record_names[p] = _device_names[dev_name]
                self.database[p] = {'type': 'float', 'value': 0.0}
                p = dev_name + ':Freq2-Mon'
                _record_names[p] = _device_names[dev_name]
                self.database[p] = {'type': 'float', 'value': 0.0}
                p = dev_name + ':Freq3-Mon'
                _record_names[p] = _device_names[dev_name]
                self.database[p] = {'type': 'float', 'value': 0.0}
            elif parts.dev == 'DCCT':
                p = dev_name + ':Current-Mon'
                _record_names[p] = _device_names[dev_name]
                self.database[p] = {'type': 'float', 'value': 0.0}
                p = dev_name + ':BbBCurrent-Mon'
                _record_names[p] = _device_names[dev_name]
                self.database[p] = {
                    'type': 'float', 'unit': 'mA',
                    'count': self.model.harmonic_number}
                p = dev_name + ':HwFlt-Mon'
                _record_names[p] = _device_names[dev_name]
                self.database[p] = {'type': 'float', 'value': 0.0}
                p = dev_name + ':CurrThold'
                _record_names[p] = _device_names[dev_name]
                self.database[p] = {'type': 'float', 'value': 0.0}
            else:
                _record_names[dev_name] = _device_names[dev_name]
                self.database[dev_name] = {'type': 'float', 'value': 0.0}

        self.all_record_names.update(_record_names)
        self.di_ro = []
        self.di_rw = []
        for rec in _record_names.keys():
            if rec.endswith(('CurrThold')):
                self.di_rw.append(rec)
            else:
                self.di_ro.append(rec)

    def _init_ps_record_names(self):
        _device_names = self.device_names.get_device_names(
            self.family_data, 'PS')
        if 'PU' in self.device_names.disciplines:
            _device_names.update(self.device_names.get_device_names(
                self.family_data, 'PU'))
        _record_names = {}
        for device_name in _device_names.keys():
            db = _pwrsupply_csdev.get_ps_propty_database(psname=device_name)
            for propty in db:
                if propty not in _PowerSupply.PROPERTIES:
                    continue
                value = db[propty]
                p = device_name + ':' + propty
                _record_names[p] = _device_names[device_name]
                if 'lolo' in value and value['lolo'] is None:
                    print("there is no value['lolo'] for  ", device_name)
                self.database[p] = value

        self.all_record_names.update(_record_names)
        self.ps_ro = []
        self.ps_rw = []
        for rec in _record_names.keys():
            if rec.endswith(('-RB', '-Sts', '-Mon')):
                self.ps_ro.append(rec)
            else:
                self.ps_rw.append(rec)

    def _init_ap_record_names(self):
        _record_names = dict()
        _device_names = self.device_names.get_device_names(
            self.family_data, 'AP')
        for dev_name in _device_names.keys():
            parts = _PVName(dev_name)
            if parts.dev == 'CurrLT':
                p = dev_name + ':CurrLT-Mon'
                _record_names[p] = _device_names[dev_name]
                self.database[p] = {'type': 'float', 'value': 0.0}
                p = dev_name + ':BbBCurrLT-Mon'
                _record_names[p] = _device_names[dev_name]
                self.database[p] = {
                    'type': 'float', 'count': self.model.harmonic_number,
                    'value': 0.0}
            else:
                _record_names[dev_name] = _device_names[dev_name]
                self.database[dev_name] = {
                    'type': 'float', 'count': 1, 'value': 0.0}

        self.all_record_names.update(_record_names)
        self.ap = list(_record_names.keys())

    def _init_rf_record_names(self):
        _device_names = self.device_names.get_device_names(
            self.family_data, 'RF')
        _record_names = {}
        for device_name in _device_names.keys():
            parts = _PVName(device_name)
            # if parts.dev.endswith('Cav'):
            if parts.dev in ('P5Cav', 'SRFCav'):
                p = device_name + ':Freq-SP'
                _record_names[p] = _device_names[device_name]
                self.database[p] = {
                    'type': 'float', 'count': 1, 'value': 0.0, 'prec': 10}
                p = device_name + ':Freq-RB'
                _record_names[p] = _device_names[device_name]
                self.database[p] = {
                    'type': 'float', 'count': 1, 'value': 0.0, 'prec': 10}
                p = device_name + ':Volt-SP'
                _record_names[p] = _device_names[device_name]
                self.database[p] = {
                    'type': 'float', 'count': 1, 'value': 0.0, 'prec': 10}
                p = device_name + ':Volt-RB'
                _record_names[p] = _device_names[device_name]
                self.database[p] = {
                    'type': 'float', 'count': 1, 'value': 0.0, 'prec': 10}
            else:
                _record_names[device_name] = _device_names[device_name]
                self.database[device_name] = {'type' : 'float', 'count': 1, 'value': 0.0, 'prec': 10}

        self.all_record_names.update(_record_names)
        self.rf = list(_record_names.keys())

    def _init_ti_record_names(self):
        self.ti_ro = []
        self.ti_rw = []
        _device_names = self.device_names.get_device_names(
            self.family_data, 'TI')
        _record_names = {}
        for device_name in _device_names.keys():
            parts = _PVName(device_name)
            if parts.dev == 'Timing':
                ioc = TimingSimulation
                db = ioc.get_database()
                self.database.update(db)
                devs = _device_names[device_name]
                _record_names.update({p: devs for p in db.keys()})
            else:
                p = device_name + ':Enbl-SP'
                _record_names[p] = _device_names[device_name]
                self.database[p] = {
                    'type': 'enum', 'enums': ('Dsbl', 'Enbl'), 'value': 1}
                p = device_name + ':Enbl-RB'
                _record_names[p] = _device_names[device_name]
                self.database[p] = {
                    'type': 'enum', 'enums': ('Dsbl', 'Enbl'), 'value': 1}
                p = device_name + ':Delay-SP'
                _record_names[p] = _device_names[device_name]
                self.database[p] = {
                    'type': 'float', 'count': 1, 'value': 0.0, 'prec': 10}
                p = device_name + ':Delay-RB'
                _record_names[p] = _device_names[device_name]
                self.database[p] = {
                    'type': 'float', 'count': 1, 'value': 0.0, 'prec': 10}

        self.all_record_names.update(_record_names)
        for rec_name in _record_names.keys():
            if rec_name.endswith(('-RB', '-Sts', '-Mon')):
                self.ti_ro.append(rec_name)
            else:
                self.ti_rw.append(rec_name)

    def _init_fk_record_names(self):
        _record_names = dict()  # get_fake_record_names(self.family_data)
        for p in _record_names.keys():
            self.database[p] = {'type': 'float', 'count': 1, 'value': 0.0}

        self.all_record_names.update(_record_names)
        self.fk = []
        self.fk_pos = []

    def _init_dynamical_pvs(self):
        self.dynamical_pvs = []
        for pv in self.di_ro.copy():
            if 'Current' in pv:
                self.dynamical_pvs.append(pv)
                self.di_ro.remove(pv)
        for pv in self.ap.copy():
            if 'CurrLT' in pv:
                self.dynamical_pvs.append(pv)
                self.ap.remove(pv)
        for pv in self.ps_ro.copy():
            if pv.endswith('TimestampUpdate-Mon'):
                self.dynamical_pvs.append(pv)
                self.ps_ro.remove(pv)

    def get_all_record_names(self):
        return _copy.deepcopy(self.all_record_names)

    def get_database(self):
        return _copy.deepcopy(self.database)

    def get_read_only_pvs(self):
        return self.di_ro + self.ap + self.ps_ro + self.ti_ro  # a copy!

    def get_read_write_pvs(self):
        # a copy!
        return self.di_rw + self.ps_rw + self.fk + self.rf + self.ti_rw

    def get_dynamical_pvs(self):
        return _copy.deepcopy(self.dynamical_pvs)

    def get_constant_pvs(self):
        return _copy.deepcopy(self.fk_pos)
