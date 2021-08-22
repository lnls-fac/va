
import math as _math
from siriuspy.pwrsupply.data import PSData as _PSData
from siriuspy.pwrsupply.csdev import Const as _Const


class PowerSupply(_PSData):

    PROPERTIES_SUBSET = (
        'OpMode-Sel',
        'OpMode-Sts',
        'PwrState-Sel',
        'PwrState-Sts',
        'Current-SP',
        'Current-RB',
        'CurrentRef-Mon',
        'Current-Mon',
        'Voltage-SP',
        'Voltage-RB',
        'Voltage-Mon',
        'Version-Cte',
        'CtrlMode-Mon',
        'CtrlLoop-Sel',
        'CtrlLoop-Sts',
        'IntlkSoft-Mon',
        'IntlkHard-Mon',
        )

    def __init__(self, magnets, model, psname):
        """Gets and sets current [A]
        Connected magnets are processed after current is set.
        """
        super().__init__(psname=psname)
        if ':PU' in psname:
            self.pulsedps = True
        else:
            self.pulsedps = False
        self._model = model
        self._magnets = magnets
        self.properties = self._get_propty_subset_database()
        for m in magnets:
            m.add_power_supply(self)

    def process(self):
        for m in self._magnets:
            m.process()

    def get_pv(self, pv_name, parts):
        """."""
        propty = parts.propty
        if propty in self.properties:
            propdb = self.properties[propty]
            value = propdb['value']
            return value
        return None

    def set_pv(self, pv_name, value, parts):
        """."""
        propty = parts.propty
        if not propty.endswith(('-SP', '-Sel', '-Cmd')) or \
                propty not in self.properties:
            return None

        changed_pvs = self._process_update_state(pv_name, propty, value)
        return changed_pvs

    def initialise(self):
        self.opmode_sel = _Const.OpMode.SlowRef
        self.pwrstate_sel = _Const.PwrStateSel.On
        self.ctrlloop_sel = _Const.OpenLoop.Closed

    @property
    def current_mon(self):
        if self.pulsedps:
            return self.properties['Voltage-Mon']['value']
        else:
            return self.properties['Current-Mon']['value']

    @property
    def pwrstate_sts(self):
        return self.properties['PwrState-Sts']['value']

    @property
    def pwrstate_sel(self):
        return self.properties['PwrState-Sel']['value']

    @pwrstate_sel.setter
    def pwrstate_sel(self, value):
        propty = 'PwrState-Sel'
        pv_name = self.psname + ':' + propty
        self._process_update_state(pv_name, propty, value)

    @property
    def opmode_sts(self):
        propty = 'OpMode-Sts'
        if propty in self.properties:
            return self.properties[propty]['value']
        else:
            return 0

    @property
    def opmode_sel(self):
        propty = 'OpMode-Sel'
        if propty in self.properties:
            return self.properties[propty]['value']
        else:
            return 0

    @opmode_sel.setter
    def opmode_sel(self, value):
        propty = 'OpMode-Sel'
        if propty in self.properties:
            self._process_update_state(self.psname + ':' + propty, propty, value)
        else:
            return

    @property
    def ctrlloop_sts(self):
        propty = 'CtrlLoop-Sts'
        if propty in self.properties:
            return self.properties[propty]['value']
        else:
            return 0

    @property
    def ctrlloop_sel(self):
        propty = 'CtrlLoop-Sel'
        if propty in self.properties:
            return self.properties[propty]['value']
        else:
            return 0

    @ctrlloop_sel.setter
    def ctrlloop_sel(self, value):
        propty = 'CtrlLoop-Sel'
        if propty in self.properties:
            self._process_update_state(self.psname + ':' + propty, propty, value)
        else:
            return


    def _process_update_state(self, pv_name, propty, value):
        changed_props = self._update_state(propty, value)

        # fill dict with PVs that need updating
        changed_pvs = dict()
        devname = pv_name.replace(propty, '')
        for property, value in changed_props.items():
            self.properties[property]['value'] = value
            changed_pvs[devname + property] = value

        self.process()

        return changed_pvs

    def _get_propty_subset_database(self):
        if PowerSupply.PROPERTIES_SUBSET is None:
            dbset =  self._propty_database
        else:
            dbset = dict()
            pdbase = self._propty_database
            for propty, dic in pdbase.items():
                if propty in PowerSupply.PROPERTIES_SUBSET:
                    dbset[propty] = dic
        return dbset

    def _update_state(self, propty, value):
        changed_pvs = dict()

        # check if in database
        if propty not in self.properties:
            return changed_pvs
        pvdb = self.properties[propty]

        # check limits
        value_ = value
        value_ = min(value_, pvdb.get('hihi', value_))
        value_ = max(value_, pvdb.get('lolo', value_))

        # add prop itself to changed pvs list
        changed_pvs[propty] = value_

        if propty == 'OpMode-Sel' and propty in self.properties:
            changed_pvs['OpMode-Sts'] = value_ + 3

        if propty == 'PwrState-Sel' and propty in self.properties:
            changed_pvs['PwrState-Sts'] = value_

        if propty == 'CtrlLoop-Sel' and propty in self.properties:
            changed_pvs['CtrlLoop-Sts'] = value_

        if propty == 'Current-SP' and propty in self.properties:
            changed_pvs['Current-RB'] = value_
            if self.pwrstate_sts == _Const.PwrStateSts.On and self.opmode_sts == _Const.States.SlowRef:
                changed_pvs['CurrentRef-Mon'] = value_
                if self.ctrlloop_sts == _Const.OpenLoop.Closed:
                    changed_pvs['Current-Mon'] = value_

        if propty == 'Voltage-SP' and propty in self.properties:
            changed_pvs['Voltage-RB'] = value_
            if self.pwrstate_sts == _Const.PwrStateSts.On:
                changed_pvs['Voltage-Mon'] = value_

        return changed_pvs


class FamilyPowerSupply(PowerSupply):

    def __init__(self, magnets, model, psname, current=None):
        """Initialises current from average integrated field in magnets"""
        super().__init__(magnets, model=model, psname=psname)
        if (current is None) and (len(magnets) > 0):
            total_current = 0.0
            for m in magnets:
                total_current += m.get_current_from_field()
            self.current_sp = total_current/len(magnets)
        else:
            self.current_sp = 0.0


class IndividualPowerSupply(PowerSupply):

    def __init__(self, magnets, model, psname, current=None):
        super().__init__(magnets, model=model, psname=psname)
        if len(magnets) > 1:
            raise Exception('Individual Power Supply')
        elif (current is None) and (len(magnets) > 0):
            m = list(magnets)[0]
            total_current = m.get_current_from_field()
            power_supplies = m._power_supplies.difference({self})
            ps_current = 0.0
            for ps in power_supplies:
                ps_current += ps.current_mon
            self.current_sp = (total_current - ps_current) \
                if _math.fabs((total_current - ps_current)) > 1e-10 else 0.0
        else:
            self.current_sp = 0.0


class PulsedMagnetPowerSupply(IndividualPowerSupply):

    def __init__(self, magnets, model, psname, current=None):
        super().__init__(magnets, model=model, psname=psname)
        if current is not None:
            self.current_sp = current

    @property
    def enabled(self):
        magnet = list(self._magnets)[0]
        if hasattr(magnet, 'enabled'):
            return magnet.enabled
        else:
            return True

    @property
    def magnet_idx(self):
        magnet = list(self._magnets)[0]
        idx = magnet.indices[0]
        return idx
