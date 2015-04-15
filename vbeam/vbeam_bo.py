import sirius.BO_V901 as _sirius
import pyaccel as _pyaccel
import si_accelerator_object as _ao

# need of semaphores since many clients may be connected simultaneously
# maybe the VABeam for SI,BO,LI,... should be derived from a general VABeam...

class VAccelerator:

    def __init__(self, clock):

        self.clock = clock # global clock from master VABeam
        self.the_ring = _sirius.create_accelerator()
        self.the_ring.radiation_on = True
        self.the_ring.cavity_on = True
        self.the_ring.vchamber_on = True

        # -- auxiliary structures --
        self.bpmx_orbit = None
        self.bpmy_orbit = None
        self.beam_current = None
        self.beamsizes = None

        self.orbit_state_depricated = True
        self.current_state_depricated = True
        self.beamsizes_state_depricated = True

    def update_beam_orbit():
        self.closed_orbit = _pyaccel.tracking.findorbit6(self.the_ring)
        bpmx_idx = _ao.bpmx.pyaccel_indices
        self.bpmx_orbit = self.closed_orbit[0,bpmx_idx]
        bpmy_idx = _ao.bpmy.pyaccel_indices
        self.bpmy_orbit = self.closed_orbit[0,bpmy_idx]

    def update_beam_current():
        pass

    def update_beamsizes():
        pass

    def update_beam_state():
        update_orbit()
        self.magnet_changed = False

    def read_bpmx(bpm):
        if self.orbit_state_depricated:
            update_beam_orbit()
            self.orbit_state_depricated = False
        return self.bpmx_orbit[0]

    def read_bpmy(bpms):
        if self.orbit_state_depricated:
            update_beam_orbit()
            self.orbit_state_depricated = False
        return self.bpmy_orbit[0]

    def set_corrector(magnet, hardware_value):
        self.orbit_state_depricated = True

    def set_quadrupole(magnet, hardware_value):
        self.orbit_state_depricated = True
        self.beamsizes_state_depricated = True

    def read_pv(pv):
        pass

    def write_pv(pv, value):
        pass
