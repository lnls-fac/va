
import numpy
import mathphys
import va.excitation_curve

class Magnet(object):

    def __init__(self, accelerator, indices, exc_curve_filename):
        """Magnet with power supplies

        Reads current from power supplies and sets Accelerator elements fields
        using value converted with excitation curve.
        """
        self._power_supplies = set()
        self._accelerator = accelerator
        self._prev_brho = accelerator.brho

        if isinstance(indices, int):
            self._indices = [indices]
        else:
            self._indices = indices
        self._nr_segs = len(self._indices)

        self._excitation_curve = va.excitation_curve.ExcitationCurve(exc_curve_filename)
        self._len_fields = max(self._excitation_curve.harmonics) + 1

        total_length = 0.0
        total_angle  = 0.0
        len_polynom  = min(len(self._accelerator[self._indices[0]].polynom_b),
                       len(self._accelerator[self._indices[0]].polynom_a))
        self._len_profile = max(len_polynom, self._len_fields)
        self._field_profile_a  = numpy.zeros((self._nr_segs, self._len_profile))
        self._field_profile_b  = numpy.zeros((self._nr_segs, self._len_profile))

        for i in range(self._nr_segs):
            idx = self._indices[i]
            total_length += self._accelerator[idx].length
            total_angle  += self._accelerator[idx].angle

            if len_polynom < self._len_fields:
                self._accelerator[idx].polynom_b = resize_polynom(self._accelerator[idx].polynom_b, self._len_fields)
                self._accelerator[idx].polynom_a = resize_polynom(self._accelerator[idx].polynom_a, self._len_fields)

            self._field_profile_b[i,:] = - self._accelerator[idx].polynom_b*self._accelerator[idx].length
            self._field_profile_a[i,:] = - self._accelerator[idx].polynom_a*self._accelerator[idx].length
            if self._excitation_curve.main_harmonic == 0:
                self._field_profile_b[i,0] -= self._accelerator[idx].angle

        self._length = total_length
        self._nominal_angle = total_angle

        # field profiles
        if self._nr_segs == 1:
            self._field_profile_b = numpy.array([[1]*self._len_profile])
            self._field_profile_a = numpy.array([[1]*self._len_profile])
        else:
            for n in range(self._len_profile):
                sum_fb = numpy.sum(self._field_profile_b[:,n])
                sum_fa = numpy.sum(self._field_profile_a[:,n])
                if sum_fa != 0:
                    self._field_profile_a[:,n] = self._field_profile_a[:,n]/sum_fa
                else:
                    self._field_profile_a[:,n] = numpy.array([1/self._nr_segs]*self._nr_segs)
                if sum_fb != 0:
                    self._field_profile_b[:,n] = self._field_profile_b[:,n]/sum_fb
                else:
                    self._field_profile_b[:,n] = numpy.array([1/self._nr_segs]*self._nr_segs)

        self._current = self.get_current_from_field()

    def add_power_supply(self, power_supply):
        self._power_supplies.add(power_supply)

    def process(self):
        """Change strengths of the magnet when the current is changed"""
        prev_current = self._current
        prev_normal_fields = self._excitation_curve.get_normal_fields_from_current(prev_current)
        prev_skew_fields   = self._excitation_curve.get_skew_fields_from_current(prev_current)

        current = 0.0
        for ps in self._power_supplies:
            current += ps.current
        new_normal_fields = self._excitation_curve.get_normal_fields_from_current(current)
        new_skew_fields   = self._excitation_curve.get_skew_fields_from_current(current)

        delta_normal_fields = numpy.array(new_normal_fields) - numpy.array(prev_normal_fields)
        delta_skew_fields   = numpy.array(new_skew_fields) - numpy.array(prev_skew_fields)

        self.value = [delta_normal_fields, delta_skew_fields]
        self._current = current

    def renormalize_magnet(self):
        """Change strengths of the magnet when accelerator energy is changed"""
        for i in self._indices:
            self._accelerator[i].polynom_b = self._accelerator[i].polynom_b*(self._prev_brho/self._accelerator.brho)
            self._accelerator[i].polynom_a = self._accelerator[i].polynom_a*(self._prev_brho/self._accelerator.brho)
        self._prev_brho = self._accelerator.brho

    @property
    def value(self):
        """Get integrated field"""
        return self._get_value()

    @value.setter
    def value(self, delta_integrated_fields):
        """Set integrated field"""
        self._set_value(delta_integrated_fields)

    def get_current_from_field(self):
        current = self._excitation_curve.get_current_from_field(self.value)
        return current

    def _get_value(self):
        # Get the integrated field correspondent to the main harmonic value
        value = 0.0
        for i in self._indices:
            polynom = getattr(self._accelerator[i], self._polynom)
            value += polynom[self._excitation_curve.main_harmonic]*self._accelerator[i].length

        if self._excitation_curve.main_harmonic == 0:
            main_field = -(value + self._nominal_angle)*self._accelerator.brho
        else:
            main_field = -value*self._accelerator.brho

        return main_field

    def _set_value(self, integrated_fields):
        normal_fields = self._fill_with_zeros(integrated_fields[0])
        skew_fields   = self._fill_with_zeros(integrated_fields[1])

        len_polynom  = min(len(self._accelerator[self._indices[0]].polynom_b),
                       len(self._accelerator[self._indices[0]].polynom_a))

        for i in range(self._nr_segs):
            idx = self._indices[i]

            field_profile_b = resize_polynom(self._field_profile_b[i,:], len_polynom)
            field_profile_a = resize_polynom(self._field_profile_a[i,:], len_polynom)
            normal_fields   = resize_polynom(normal_fields, len_polynom)
            skew_fields     = resize_polynom(skew_fields,   len_polynom)

            delta_polynom_b = -field_profile_b*normal_fields/(self._accelerator[idx].length*self._accelerator.brho)
            delta_polynom_a = -field_profile_a*skew_fields  /(self._accelerator[idx].length*self._accelerator.brho)

            self._accelerator[idx].polynom_b += delta_polynom_b
            self._accelerator[idx].polynom_a += delta_polynom_a

    def _fill_with_zeros(self, integrated_field):
        field = numpy.zeros(self._len_fields)
        for j in range(len(self._excitation_curve.harmonics)):
            n = self._excitation_curve.harmonics[j]
            field[n] = integrated_field[n]
        return field

class BoosterDipoleMagnet(Magnet):

    def __init__(self, accelerator, indices, exc_curve_filename):
        self._polynom = 'polynom_b'
        super().__init__(accelerator, indices, exc_curve_filename)
        e0 = mathphys.constants.electron_rest_energy*mathphys.constants._joule_2_eV
        self._light_speed = mathphys.constants.light_speed
        self._electron_rest_energy_ev = e0

    def process(self, change_energy = False):
        prev_current = self._current
        prev_normal_fields = self._excitation_curve.get_normal_fields_from_current(prev_current)
        prev_skew_fields   = self._excitation_curve.get_skew_fields_from_current(prev_current)

        current = 0.0
        for ps in self._power_supplies:
            current += ps.current/2.0
        new_normal_fields = self._excitation_curve.get_normal_fields_from_current(current)
        new_skew_fields   = self._excitation_curve.get_skew_fields_from_current(current)

        delta_normal_fields = numpy.array(new_normal_fields) - numpy.array(prev_normal_fields)
        delta_skew_fields   = numpy.array(new_skew_fields) - numpy.array(prev_skew_fields)

        if change_energy:
            delta_energy = self._light_speed*(- delta_normal_fields[0]/self._nominal_angle)
            energy = self._accelerator.energy + delta_energy
            # Avoid division by zero and math domain error
            if energy > self._electron_rest_energy_ev:
                self._accelerator.energy = energy
            else:
                self._accelerator.energy = self._electron_rest_energy_ev + 1

        # Don't change the main harmonic value of polynom_b
        delta_normal_fields[0] = 0.0
        self.value = [delta_normal_fields, delta_skew_fields]
        self._current = current


class NormalMagnet(Magnet):

    def __init__(self, accelerator, indices, exc_curve_filename):
        self._polynom = 'polynom_b'
        super().__init__(accelerator, indices, exc_curve_filename)


class SkewMagnet(Magnet):

    def __init__(self, accelerator, indices, exc_curve_filename):
        self._polynom = 'polynom_a'
        super().__init__(accelerator, indices, exc_curve_filename)


def resize_polynom(polynom, length):
    p = numpy.array([x for x in polynom])
    if len(polynom) < length:
        p.resize(length, refcheck=False)
    return p
