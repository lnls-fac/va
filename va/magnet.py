
import numpy
import mathphys

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

        self._load_excitation_curve(exc_curve_filename)

        total_length = 0.0
        total_angle  = 0.0
        field_profile = numpy.zeros(len(self._indices))
        for i in range(len(self._indices)):
            idx = self._indices[i]
            length = self._accelerator[idx].length
            angle = self._accelerator[idx].angle
            total_length += length
            total_angle  += angle

            polynom = getattr(self._accelerator[idx], self._polynom)
            field_profile[i] = polynom[self._main_harmonic-1]*length + angle

            # Resize polynom_a and polynom_b
            if len(self._accelerator[idx].polynom_b) < numpy.amax(self._harmonics):
                pb = self._accelerator[idx].polynom_b
                pb.resize(numpy.amax(self._harmonics), refcheck=False)
                self._accelerator[idx].polynom_b = pb
            if len(self._accelerator[idx].polynom_a) < numpy.amax(self._harmonics):
                pa = self._accelerator[idx].polynom_a
                pa.resize(numpy.amax(self._harmonics), refcheck=False)
                self._accelerator[idx].polynom_a = pa

        self._length = total_length
        self._nominal_angle = total_angle

        # Main harmonic field profile
        if len(self._indices) == 1:
            self._field_profile = [1]
        else:
            try:
                # If the magnet is segmented, all the magnet's multipoles will be set
                # following the main harmonic initial field profile
                self._field_profile = field_profile/numpy.sum(field_profile)
            except ZeroDivisionError:
                # If the main harmonic initial field is zero,
                # all segments are assigned the same polynom value.
                self._field_profile = numpy.array([1/len(self._indices)]*len(self._indices))

    def add_power_supply(self, power_supply):
        self._power_supplies.add(power_supply)

    def process(self):
        """Change strengths of the magnet when the current is changed"""
        prev_current = self.current
        prev_value = [numpy.interp(prev_current, self._i, self._f[:,n]) for n in range(numpy.size(self._f,1))]

        current = 0.0
        for ps in self._power_supplies:
            current += ps.current
        new_value = [numpy.interp(current, self._i, self._f[:,n]) for n in range(numpy.size(self._f,1))]

        self.value = numpy.array(new_value) - numpy.array(prev_value)

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

    @property
    def current(self):
        if self._polynom == 'polynom_b':
            index = 2*(self._harmonics.index(self._main_harmonic))
        else:
            index = 2*(self._harmonics.index(self._main_harmonic))+1
        if numpy.all(numpy.diff(self._f[:,index]) > 0):
            current = numpy.interp(self.value, self._f[:,index], self._i)
        elif numpy.all(numpy.diff(self._f[:,index][::-1]) > 0):
            current = numpy.interp(self.value, self._f[:,index][::-1], self._i[::-1] )
        else:
            raise Exception('Integrated field should be increasing or decreasing function of the current')
        return current

    def _get_value(self):
        # Get the integrated field correspondent to the main harmonic value
        value = 0.0
        for i in self._indices:
            polynom = getattr(self._accelerator[i], self._polynom)
            value += polynom[self._main_harmonic-1]*self._accelerator[i].length

        if self._nominal_angle != 0:
            integrated_field = (value + self._nominal_angle)*self._accelerator.brho
        else:
            integrated_field = value*self._accelerator.brho

        return integrated_field

    def _set_value(self, delta_integrated_fields):
        # Add the changes to the magnet multipoles (Don't overwrite previous multipole errors)
        delta_ifb = numpy.zeros(numpy.amax(self._harmonics))
        delta_ifa = numpy.zeros(numpy.amax(self._harmonics))
        j = 0
        for n in self._harmonics:
            delta_ifb[n-1] = delta_integrated_fields[j]
            delta_ifa[n-1] = delta_integrated_fields[j+1]
            j += 2

        for i in range(len(self._indices)):
            idx = self._indices[i]
            length = self._accelerator[idx].length
            if len(self._accelerator[idx].polynom_b) > numpy.amax(self._harmonics):
                delta_ifb.resize(len(self._accelerator[idx].polynom_b), refcheck=False)
            if len(self._accelerator[idx].polynom_a) > numpy.amax(self._harmonics):
                delta_ifa.resize(len(self._accelerator[idx].polynom_a), refcheck=False)

            delta_polynom_b = self._field_profile[i]*delta_ifb/(length*self._accelerator.brho)
            delta_polynom_a = self._field_profile[i]*delta_ifa/(length*self._accelerator.brho)

            self._accelerator[idx].polynom_b += delta_polynom_b
            self._accelerator[idx].polynom_a += delta_polynom_a

    def _load_excitation_curve(self, filename):
        lines = [line.strip() for line in open(filename, encoding='latin-1')]
        data = []
        for line in lines:
            if line.startswith('#'):
                words = line.lower().strip('#').split()
                if 'main_harmonic' in words:
                    self._main_harmonic = int(words[1])
                elif 'harmonics' in words:
                    self._harmonics = [int(n) for n in words[1:]]
            else:
                data.append([float(word) for word in line.split()])
        data = numpy.array(data)

        if numpy.size(data[:,1:], 1) != 2*(len(self._harmonics)):
            raise Exception('Mismatch between number of columns and size of harmonics list in excitation curve')

        self._i = data[:,0]  # current
        self._f = data[:,1:] # integrated fields (normal and skew)


class BoosterDipoleMagnet(Magnet):

    def __init__(self, accelerator, indices, exc_curve_filename):
        self._polynom = 'polynom_b'
        super().__init__(accelerator, indices, exc_curve_filename)
        e0 = mathphys.constants.electron_rest_energy*mathphys.constants._joule_2_eV
        self._light_speed = mathphys.constants.light_speed
        self._electron_rest_energy_ev = e0
        self._energy = self._accelerator.energy

    def process(self, change_energy = False):
        prev_current = self.current
        prev_value = [numpy.interp(prev_current, self._i, self._f[:,n]) for n in range(numpy.size(self._f,1))]

        current = 0.0
        for ps in self._power_supplies:
            current += ps.current/2.0 # Booster dipoles have two power supplies
        new_value = [numpy.interp(current, self._i, self._f[:,n]) for n in range(numpy.size(self._f,1))]

        delta_integrated_fields = numpy.array(new_value) - numpy.array(prev_value)

        if change_energy:
            delta_energy = self._light_speed*delta_integrated_fields[0]/self._nominal_angle
            energy = self._energy + delta_energy
            # Avoid division by zero and math domain error
            if energy > self._electron_rest_energy_ev:
                self._accelerator.energy = energy
            else:
                self._accelerator.energy = self._electron_rest_energy_ev + 1

        # Don't change the main harmonic value of polynom_b
        delta_integrated_fields[0] = 0.0
        self.value = delta_integrated_fields


class NormalMagnet(Magnet):

    def __init__(self, accelerator, indices, exc_curve_filename):
        self._polynom = 'polynom_b'
        super().__init__(accelerator, indices, exc_curve_filename)


class SkewMagnet(Magnet):

    def __init__(self, accelerator, indices, exc_curve_filename):
        self._polynom = 'polynom_a'
        super().__init__(accelerator, indices, exc_curve_filename)
