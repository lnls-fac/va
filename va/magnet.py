
class Magnet(object):

    def __init__(self, accelerator, indices, exc_curve_filename):
        """Magnet with power supplies

        Reads current from power supplies and sets Accelerator elements fields
        using value converted with excitation curve."""
        self._power_supplies = set()
        self._accelerator = accelerator

        if isinstance(indices, int):
            self._indices = [indices]
        else:
            self._indices = indices

        length = 0.0
        for i in self._indices:
            length += self._accelerator[i].length
        self._length = length

        self._load_excitation_curve(exc_curve_filename)

    def add_power_supply(self, power_supply):
        self._power_supplies.add(power_supply)

    def process(self):
        current = 0.0
        for ps in self._power_supplies:
            current += ps.current
        new_value = numpy.interp(current, self._i, self._f)
        self.value = new_value

    @property
    def value(self):
        return self._get_value()

    @value.setter
    def value(self, integrated_field):
        """Set integrated field

        If element is segmented, all segments are assigned the same polynom
        value.
        """
        self._set_value(integrated_field)


    @property
    def current(self):
        return numpy.interp(self.value, self._f, self._i)

    def _get_value(self):
        v = 0.0
        for i in self._indices:
            polynom = getattr(self._accelerator[i], self._polynom)
            v += polynom[self._polynom_index]*self._accelerator[i].length

        integrated_field = v*self._accelerator.brho
        return integrated_field

    def _set_value(self, integrated_field):
        strength = integrated_field/(self._length*self._accelerator.brho)
        for i in self._indices:
            polynom = getattr(self._accelerator[i], self._polynom)
            polynom[self._polynom_index] = strength

    def _load_excitation_curve(self, filename):
        try:
            data = numpy.loadtxt(filename)
        except FileNotFoundError:
            # Default conversion table: F = I/2
            data = numpy.array([[-1000, 1000], [-500, 500]]).transpose()
        self._i = data[:, 0]
        self._f = data[:, 1]


class DipoleMagnet(Magnet):

    def __init__(self, accelerator, indices, exc_curve_filename):
        """Gets and sets beam energy [eV]

        DipoleMagnet is processed differently from other Magnet objects: it
        averages the current over the set of power supplies.
        """
        super().__init__(accelerator, indices, exc_curve_filename)
        e0 = mathphys.constants.electron_rest_energy*mathphys.constants._joule_2_eV
        self._electron_rest_energy_ev = e0
        self._energy = self._accelerator.energy

    @property
    def value(self):
        """Get beam energy [eV]"""
        # return self._accelerator.energy
        return self._energy

    @value.setter
    def value(self, energy):
        """Set beam energy [eV]"""
        # Avoid division by zero and math domain error
        if energy > self._electron_rest_energy_ev:
            self._accelerator.energy = energy
        else:
            self._accelerator.energy = self._electron_rest_energy_ev + 1 # OK?

        self._energy = energy

    def process(self):
        current = 0.0
        n = len(self._power_supplies)
        if n > 0:
            for ps in self._power_supplies:
                current += ps.current
            new_value = numpy.interp(current/n, self._i, self._f)
        else:
            new_value = 0.0

        self.value = new_value

class SeptumMagnet(Magnet):

    def __init__(self, accelerator, indices, exc_curve_filename):
        super().__init__(accelerator, indices, exc_curve_filename)
        """Gets and sets deflection angle [rad]"""
        self._polynom = 'polynom_b'
        self._polynom_index = 0

        angle = 0.0
        for i in self._indices:
            angle += self._accelerator[i].angle
        self._nominal_angle = angle

    def _get_value(self):
        v = 0.0
        for i in self._indices:
            polynom = getattr(self._accelerator[i], self._polynom)
            v += polynom[self._polynom_index]*self._accelerator[i].length
        angle = v + self._nominal_angle
        return angle

    def _set_value(self, angle):
        delta_angle = angle - self._nominal_angle
        strength = delta_angle/self._length
        for i in self._indices:
            polynom = getattr(self._accelerator[i], self._polynom)
            polynom[self._polynom_index] = strength

class QuadrupoleMagnet(Magnet):

    def __init__(self, accelerator, indices, exc_curve_filename):
        """Gets and sets integrated field [T]"""
        super().__init__(accelerator, indices, exc_curve_filename)
        self._polynom = 'polynom_b'
        self._polynom_index = 1

class SextupoleMagnet(Magnet):

    def __init__(self, accelerator, indices, exc_curve_filename):
        """Gets and sets integrated field [T/m]"""
        super().__init__(accelerator, indices, exc_curve_filename)
        self._polynom = 'polynom_b'
        self._polynom_index = 2


class CorrectorMagnet(Magnet):

    def __init__(self, accelerator, indices, exc_curve_filename):
        """Gets and sets integrated field [T·m]"""
        super().__init__(accelerator, indices, exc_curve_filename)
        self._polynom_index = 0
        self._pass_method = self._accelerator[self._indices[0]].pass_method

    @property
    def value(self):
        """Get integrated field [T·m]"""
        if self._pass_method != 'corrector_pass':
            return self._get_value()
        else:
            v = 0.0
            for i in self._indices:
                v += getattr(self._accelerator[i], self._kick)
            integrated_field = v*self._accelerator.brho
            return integrated_field

    @value.setter
    def value(self, integrated_field):
        """Set integrated field [T·m]

        If element is segmented, all segments are assigned the same B.
        """
        if self._pass_method != 'corrector_pass':
            self._set_value(integrated_field)
        else:
            total_kick = integrated_field/self._accelerator.brho
            for i in self._indices:
                kick = total_kick*self._accelerator[i].length/self._length
                setattr(self._accelerator[i], self._kick, kick)


class HorizontalCorrectorMagnet(CorrectorMagnet):

    def __init__(self, accelerator, indices, exc_curve_filename):
        """Gets and sets integrated field [T·m]"""
        super().__init__(accelerator, indices, exc_curve_filename)
        self._kick = 'hkick'
        self._polynom = 'polynom_b'


class VerticalCorrectorMagnet(CorrectorMagnet):

    def __init__(self, accelerator, indices, exc_curve_filename):
        """Gets and sets integrated field [T·m]"""
        super().__init__(accelerator, indices, exc_curve_filename)
        self._kick = 'vkick'
        self._polynom = 'polynom_a'


class SkewQuadrupoleMagnet(Magnet):

    def __init__(self, accelerator, indices, exc_curve_filename):
        """Gets and sets integrated field [T]"""
        super().__init__(accelerator, indices, exc_curve_filename)
        self._polynom = 'polynom_a'
        self._polynom_index = 1
