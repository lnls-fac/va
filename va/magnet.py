
import numpy
import mathphys

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

        self._load_excitation_curve(exc_curve_filename)

        length = 0.0
        angle  = 0.0
        for i in self._indices:
            length += self._accelerator[i].length
            angle += self._accelerator[i].angle

            if len(self._accelerator[i].polynom_b) < numpy.amax(self._harmonics):
                pb = self._accelerator[i].polynom_b
                pb.resize(numpy.amax(self._harmonics), refcheck=False)
                self._accelerator[i].polynom_b = pb

            if len(self._accelerator[i].polynom_a) < numpy.amax(self._harmonics):
                pa = self._accelerator[i].polynom_a
                pa.resize(numpy.amax(self._harmonics), refcheck=False)
                self._accelerator[i].polynom_a = pa

        self._length = length
        self._nominal_angle = angle
        self._ps = 1.0

    def add_power_supply(self, power_supply):
        self._power_supplies.add(power_supply)

    def process(self):
        prev_current = self.current
        prev_value = [numpy.interp(prev_current, self._i, self._f[:,n]) for n in range(numpy.size(self._f,1))]

        current = 0.0
        for ps in self._power_supplies:
            current += ps.current/self._ps
        new_value = [numpy.interp(current, self._i, self._f[:,n]) for n in range(numpy.size(self._f,1))]

        self.value = numpy.array(new_value) - numpy.array(prev_value)

    @property
    def value(self):
        return self._get_value()

    @value.setter
    def value(self, integrated_fields):
        """Set integrated field
        If element is segmented, all segments are assigned the same polynom value.
        """
        self._set_value(integrated_fields)

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
        value = 0.0
        for i in self._indices:
            polynom = getattr(self._accelerator[i], self._polynom)
            value += polynom[self._main_harmonic-1]*self._accelerator[i].length

        if self._nominal_angle != 0:
            integrated_field = (value + self._nominal_angle)*self._accelerator.brho
        else:
            integrated_field = value*self._accelerator.brho

        return integrated_field

    def _set_value(self, integrated_fields):
        delta_polynom_b = numpy.zeros(numpy.amax(self._harmonics))
        delta_polynom_a = numpy.zeros(numpy.amax(self._harmonics))
        j = 0
        for n in self._harmonics:
            delta_polynom_b[n-1] = integrated_fields[j]/(self._length*self._accelerator.brho)
            delta_polynom_a[n-1] = integrated_fields[j+1]/(self._length*self._accelerator.brho)
            j += 2

        for i in self._indices:
            if len(self._accelerator[i].polynom_b) > numpy.amax(self._harmonics):
                delta_polynom_b.resize(len(self._accelerator[i].polynom_b), refcheck=False)
            if len(self._accelerator[i].polynom_a) > numpy.amax(self._harmonics):
                delta_polynom_a.resize(len(self._accelerator[i].polynom_a), refcheck=False)
            self._accelerator[i].polynom_b += delta_polynom_b
            self._accelerator[i].polynom_a += delta_polynom_a

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

        self._i = data[:,0]
        self._f = data[:,1:]


class Dipole2PS(Magnet):

    def __init__(self, accelerator, indices, exc_curve_filename):
        super().__init__(accelerator, indices, exc_curve_filename)
        self._polynom = 'polynom_b'
        self._ps = 2.0


class NormalMagnet(Magnet):

    def __init__(self, accelerator, indices, exc_curve_filename):
        super().__init__(accelerator, indices, exc_curve_filename)
        self._polynom = 'polynom_b'


class SkewMagnet(Magnet):

    def __init__(self, accelerator, indices, exc_curve_filename):
        super().__init__(accelerator, indices, exc_curve_filename)
        self._polynom = 'polynom_a'
