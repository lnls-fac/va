
import time as _time
import math as _math
from siriuspy.namesys.implementation import SiriusPVName

from siriuspy.search import PSSearch as _PSSearch
from siriuspy.pwrsupply.data import PSData as _PSData
from siriuspy.pwrsupply.csdev import Const as _Const

from va import __version__


class Beagle:
        """."""

        PROPERTIES = {
            'SOFBMode-Sts': _Const.DsblEnbl.Dsbl,
            }

        def __init__(self, bbbname):
            self.bbbname = bbbname
            self.psnames = set()
            self.connected = True
            self.props = dict()
            self.props.update(Beagle.PROPERTIES)

        def __getitem__(self, propty):
            return self.props.get(propty, None)

        def __setitem__(self, propty, value):
            if propty in self.props:
                self.props[propty] = value


class BeagleBones:
    """Class that manages interconnection of power supplies through beagles."""

    def __init__(self):
        self._beagles = dict()
        self._pwrsupplies = dict()

    def add_power_supply(self, pwrsupply):
        """."""
        psname = pwrsupply.psname
        bbbname = BeagleBones.get_bbbname(psname, None)
        if bbbname is None:
            return None # power supply without beagle
        devices = _PSSearch.conv_bbbname_2_psnames(bbbname)
        if bbbname not in self._beagles:
            self._beagles[bbbname] = Beagle(bbbname)
        for psname, devid in devices:
            self._beagles[bbbname].psnames.add(psname)
            self._pwrsupplies[psname] = self._beagles[bbbname]
        return self._beagles[bbbname]

    def bsmp_disconnect(self, psname=None, bbbname=None):
        """."""
        self._set_bsmp_connection(psname, bbbname, False)

    def bsmp_connect(self, psname=None, bbbname=None):
        """."""
        self._set_bsmp_connection(psname, bbbname, True)

    def _set_bsmp_connection(self, psname, bbbname, state):
        bbbname = BeagleBones.get_bbbname(psname, bbbname)
        if bbbname in self._beagles:
            self._beagles[bbbname].connected = state

    @staticmethod
    def get_bbbname(psname, bbbname):
        if bbbname is None:
            try:
                bbbname = _PSSearch.conv_psname_2_bbbname(psname)
            except KeyError:
                bbbname = None
        return bbbname


class PowerSupply(_PSData):

    beaglebones = BeagleBones()

    PROPERTIES = (
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
        'PRUCtrlQueueSize-Mon',
        'SyncPulse-Cmd',
        'WfmIndex-Mon',
        'WfmSyncPulseCount-Mon',
        'WfmUpdateAuto-Sel',
        'WfmUpdateAuto-Sts',
        'SOFBMode-Sel',
        'SOFBMode-Sts',
        'TimestampBoot-Cte',
        'TimestampUpdate-Mon',
        )

    def __init__(self, magnets, model, psname):
        """Gets and sets current [A]
        Connected magnets are processed after current is set.
        """
        super().__init__(psname=psname)
        self._model = model
        self._magnets = magnets
        self.properties = self._get_propty_subset_database()
        self.pulsedps = ':PU' in psname
        self.sofbps = 'SOFBMode-Sel' in self.properties
        self.refmonps = 'CurrentRef-Mon' in self.properties
        self._initialisation()
        for m in magnets:
            m.add_power_supply(self)

        # add power supply to beaglebones and get controling beaglebone
        self.beagle = PowerSupply.beaglebones.add_power_supply(self)

    def process(self):
        for m in self._magnets:
            m.process()

    def get_pv(self, pv_name, parts):
        """."""
        propty = parts.propty
        if propty in self.properties:
            return self[propty]
        else:
            return self.beagle[propty]

    def set_pv(self, pv_name, value, parts):
        propty = parts.propty
        if not propty.endswith(('-SP', '-Sel', '-Cmd')) or \
                propty not in self.properties:
            return None

        changed_pvs = self._process_update_model_state(pv_name, propty, value)
        return changed_pvs

    def initialise(self):
        self.opmode_sel = _Const.OpMode.SlowRef
        self.pwrstate_sel = _Const.PwrStateSel.On
        self.ctrlloop_sel = _Const.OpenLoop.Closed
        if 'TimestampBoot-Cte' in self.properties:
            self['TimestampBoot-Cte'] = _time.time()

    @property
    def current_mon(self):
        propty = 'Voltage-Mon' if self.pulsedps else 'Current-Mon'
        return self[propty]

    @property
    def sofb_sts(self):
        propty = 'SOFBMode-Sts'
        status = 0 if not self.sofbps or self[propty] == 0 else 1
        return status

    @property
    def sofb_sel(self):
        return self['SOFBMode-Sel']

    @sofb_sel.setter
    def sofb_sel(self, value):
        propty = 'SOFBMode-Sel'
        pv_name = self.psname + ':' + propty
        self._process_update_model_state(pv_name, propty, value)

    @property
    def pwrstate_sts(self):
        return self['PwrState-Sts']

    @property
    def pwrstate_sel(self):
        return self['PwrState-Sel']

    @pwrstate_sel.setter
    def pwrstate_sel(self, value):
        propty = 'PwrState-Sel'
        pv_name = self.psname + ':' + propty
        self._process_update_model_state(pv_name, propty, value)

    @property
    def opmode_sts(self):
        propty = 'OpMode-Sts'
        return self[propty] if propty in self.properties else 0

    @property
    def opmode_sel(self):
        propty = 'OpMode-Sel'
        return self[propty] if propty in self.properties else 0

    @opmode_sel.setter
    def opmode_sel(self, value):
        propty = 'OpMode-Sel'
        if propty in self.properties:
            self._process_update_model_state(self.psname + ':' + propty, propty, value)

    @property
    def ctrlloop_sts(self):
        propty = 'CtrlLoop-Sts'
        return self[propty] if propty in self.properties else 0

    @property
    def ctrlloop_sel(self):
        propty = 'CtrlLoop-Sel'
        return self[propty] if propty in self.properties else 0

    @ctrlloop_sel.setter
    def ctrlloop_sel(self, value):
        propty = 'CtrlLoop-Sel'
        if propty in self.properties:
            self._process_update_model_state(self.psname + ':' + propty, propty, value)

    def __getitem__(self, propty):
        if propty in self.properties:
            return self.properties[propty]['value']
        else:
            return self.beagle[propty]

    def __setitem__(self, propty, value):
        if propty in self.properties:
            self.properties[propty]['value'] = value
        else:
            self.beagle[propty] = value

    def _process_update_model_state(self, pv_name, propty, value):

        changed_pvs = dict()

        # update model state (recursively)
        devname = pv_name.replace(propty, '')
        self._update_model_state(devname, propty, value, changed_pvs)

        # update state
        for pv_name, value in changed_pvs.items():
            pvname = SiriusPVName(pv_name)
            if pvname.device_name == self.psname:
                self[pvname.propty] = value

        # propagate changes to magnets
        self.process()

        return changed_pvs

    def _update_model_state(self, devname, propty, value, changed_pvs):
        """Update model state.

            This function inserts in a dict the pair (property/value) of
        changed properties of cascating model updating. It can be
        invoked recursively, if necessary."""

        # check if in database
        if propty not in self.properties:
            return changed_pvs
        pvdb = self.properties[propty]

        # check limits
        value_ = value
        value_ = min(value_, pvdb.get('hihi', value_))
        value_ = max(value_, pvdb.get('lolo', value_))

        # special case: SOFBMode setup
        if self.sofb_sts:
            if propty == 'SOFBMode-Sel':

                # add propty itself to changed pvs list
                changed_pvs[devname + propty] = value_

                # add PVs of other power supplies in the same beagle
                self.beagle.psnames
                for psname in self.beagle.psnames:
                    changed_pvs[psname + ':SOFBMode-Sts'] = value_

            return

        # add prop itself to changed pvs list
        changed_pvs[devname + propty] = value_

        # NOTE: for optimisation, cases should be ordered by estimated usage frequency
        if propty == 'Current-SP':
            changed_pvs[devname + 'Current-RB'] = value_
            if self.pwrstate_sts == _Const.PwrStateSts.On and self.opmode_sts == _Const.States.SlowRef:
                changed_pvs[devname + 'CurrentRef-Mon'] = value_
                if self.ctrlloop_sts == _Const.OpenLoop.Closed:
                    changed_pvs[devname + 'Current-Mon'] = value_
        elif propty == 'Voltage-SP':
            changed_pvs[devname + 'Voltage-RB'] = value_
            if self.pwrstate_sts == _Const.PwrStateSts.On:
                changed_pvs[devname + 'Voltage-Mon'] = value_
        elif propty == 'PwrState-Sel':
            changed_pvs[devname + 'PwrState-Sts'] = value_
            if value_ == _Const.PwrStateSel.Off:
                if self.pulsedps:
                    changed_pvs[devname + 'Voltage-RB'] = 0.0  # NOTE: Check this!
                    changed_pvs[devname + 'Voltage-Mon'] = 0.0
                else:
                    changed_pvs[devname + 'Current-RB'] = 0.0  # NOTE: Check this!
                    changed_pvs[devname + 'Current-Mon'] = 0.0
                    if self.refmonps:
                        changed_pvs[devname + 'CurrentRef-Mon'] = 0.0
        elif propty == 'OpMode-Sel':
            changed_pvs[devname + 'OpMode-Sts'] = value_ + 3
        elif propty == 'SOFBMode-Sel':
            changed_pvs[devname + 'SOFBMode-Sts'] = value_
        elif propty == 'WfmUpdateAuto-Sel':
            changed_pvs[devname + 'WfmUpdateAuto-Sts'] = value
        elif propty == 'CtrlLoop-Sel':
            changed_pvs[devname + 'CtrlLoop-Sts'] = value_
        elif propty.endswith('-Cmd'):
            changed_pvs[devname + propty] = self[propty] + 1
            if propty == 'SyncPulse-Cmd':
                if self.refmonps:
                    changed_pvs[devname + 'CurrentRef-Mon'] = self['Current-RB']
                    changed_pvs[devname + 'Current-Mon'] = self['Current-RB']
                propty_ = 'WfmSyncPulseCount-Mon'
                changed_pvs[devname + propty_] = self[propty_] + 1

    def _get_propty_subset_database(self):

        # filter property subset
        if PowerSupply.PROPERTIES is None:
            dbset =  self._propty_database
        else:
            dbset = dict()
            pdbase = self._propty_database
            for propty, dic in pdbase.items():
                if propty in PowerSupply.PROPERTIES:
                    dbset[propty] = dic

        # remove properties that belong to beaglebones
        for propty in Beagle.PROPERTIES:
            if propty in dbset:
                dbset.pop(propty)

        return dbset

    def _initialisation(self):
        if 'Version-Cte' in self.properties:
            self['Version-Cte'] = 'VACA_' + __version__


class FamilyPowerSupply(PowerSupply):

    def __init__(self, magnets, model, psname, current=None):
        """Initialises current from average integrated field in magnets"""
        super().__init__(magnets, model=model, psname=psname)
        if (current is None) and (len(magnets) > 0):
            total_current = 0.0
            n = 0
            for m in magnets:
                total_current += m.get_current_from_field()
                n += 1
            self.current_sp = total_current/n
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
