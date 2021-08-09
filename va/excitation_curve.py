
import numpy as _numpy
# from siriuspy.envars import folder_lnls_sirius_csconstants
from siriuspy.clientweb import magnets_excitation_data_read
import os as _os


class ExcitationCurve:

    def __init__(self, fname, polarity=1, method='filename'): # generalise: pass label name
        """Conversion between current and field

        Keyword argument:
        fname -- magnet excitation curve file name
        """

        if method == 'filename':
            pass
        #     _excitation_curves_dir = _os.path.join(folder_lnls_sirius_csconstants, 'magnets', 'excitation-data')
        #     filename = _os.path.join(_excitation_curves_dir, fname)
        #     with open(filename, encoding='latin-1') as f:
        #         lines = f.readlines()
        #     self._load_excitation_curve(lines,polarity)

        elif method == 'filename_web':
            self._filename = fname
            try:
                text = magnets_excitation_data_read(fname)
            except:
                print('Error trying to read excdata {}'.format(fname))
                raise
            lines = text.split('\n')
            self._load_excitation_curve(lines,polarity)


    @property
    def main_harmonic(self):
        return self._main_harmonic

    @property
    def harmonics(self):
        return self._harmonics

    @property
    def curve_type(self):
        return self._curve_type

    @property
    def current_range(self):
        return (self._i_to_f_current[0], self._i_to_f_current[-1])

    @property
    def field_range(self):
        return (self._f_to_i_field[0], self._f_to_i_field[-1])

    def get_field_from_current(self, current):
        self._check_value_in_range(current, self.current_range)
        field_array = self._i_to_f_main_field
        return self._interpolate_current(current, field_array)

    def get_normal_fields_from_current(self, current):
        fields_array = self._i_to_f_normal_fields
        return self._get_fields_from_current(current, fields_array)

    def get_skew_fields_from_current(self, current):
        fields_array = self._i_to_f_skew_fields
        return self._get_fields_from_current(current, fields_array)

    def get_current_from_field(self, main_field):
        self._check_value_in_range(main_field, self.field_range)
        field_array = self._f_to_i_field
        current_array =  self._f_to_i_current

        return self._interpolate_main_field(main_field, field_array,
            current_array)

    def _check_value_in_range(self, value, value_range):
        low = value_range[0]
        high = value_range[1]
        if not low <= value <= high:
            print(self._filename)
            msg = 'value %f out of range (%f, %f)' % (value, low, high)
            raise ValueError(msg)

    def _interpolate_current(self, current, field_array):
        current_array =  self._i_to_f_current
        return _numpy.interp(current, current_array, field_array)

    def _get_fields_from_current(self, current, fields_array):
        self._check_value_in_range(current, self.current_range)
        fields = _numpy.zeros(self._highest_harmonic+1)
        for h, i in zip(self._harmonics, range(len(self._harmonics))):
            fields[h] = self._interpolate_current(current, fields_array[:, i])

        return fields

    def _interpolate_main_field(self, field, field_array, current_array):
        return _numpy.interp(field, field_array, current_array)

    def _load_excitation_curve(self, lines, polarity):

        # first parse the header to get the main harmonics and the harmonics:
        for line in lines:
            if not line.strip().startswith('#'):
                continue
            words = line[1:].strip().lower().split()
            if 'main_harmonic' in words:
                self._main_harmonic = int(words[1])
                if len(words) <= 2:
                    self._curve_type = 'normal' # default
                elif words[2] in ('normal', 'skew'):
                    self._curve_type = words[2]
                else:
                    raise ValueError("invalid curve type: '" + words[2] + "'")
            elif 'harmonics' in words:
                self._harmonics = [int(n) for n in words[1:]]
                self._highest_harmonic = max(self._harmonics)

        if not hasattr(self, '_main_harmonic'): raise AttributeError('missing main_harmonic')
        if not hasattr(self, '_harmonics'):     raise AttributeError('missing harmonics')
        self._main_harmonic_index = self._harmonics.index(self._main_harmonic)

        # Now load the curve
        data = _numpy.loadtxt(lines)
        current = data[:, 0] # current
        fields = polarity*data[:, 1:] # integrated fields (normal and skew)

        # Check consistency
        if _numpy.size(fields, 1) != 2*(len(self._harmonics)):
            msg = ('Mismatch between number of columns and size of ' +
                'harmonics list in excitation curve')
            raise Exception(msg)

        # Interpolation requires increasing x
        main_index = self._get_main_field_index()
        self._prepare_i_to_f_interpolation_table(current, fields, main_index)
        self._prepare_f_to_i_interpolation_table(current, fields, main_index)

    def _get_main_field_index(self):
        if self._curve_type == 'normal':
            return 2*self._main_harmonic_index
        else:
            return 2*self._main_harmonic_index + 1

    def _prepare_i_to_f_interpolation_table(self, current, fields, main_index):
        i, f = self._get_strictly_increasing_x_array(current, fields)

        self._i_to_f_current = i
        self._i_to_f_normal_fields = f[:, 0::2] # even columns
        self._i_to_f_skew_fields = f[:, 1::2] # odd columns
        self._i_to_f_main_field = f[:, main_index]

    def _prepare_f_to_i_interpolation_table(self, current, fields, main_index):
        field = fields[:, main_index]
        f, i = self._get_strictly_increasing_x_array(field, current)

        self._f_to_i_field = f
        self._f_to_i_current = i

    def _get_strictly_increasing_x_array(self, x_array, y_array):
        if self._is_strictly_increasing(x_array):
            x, y = x_array, y_array
        elif self._is_strictly_decreasing(x_array):
            x, y = self._reverse(x_array, y_array)
        else:
            msg = 'x array must be strictly increasing or decreasing'
            raise ValueError(msg)

        return x, y

    def _is_strictly_increasing(self, array):
        return _numpy.all(_numpy.diff(array) > 0)

    def _is_strictly_decreasing(self, array):
        return _numpy.all(_numpy.diff(array) < 0)

    def _reverse(self, *args):
        result = [arg[::-1] for arg in args]
        return tuple(result)
