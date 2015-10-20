
import numpy as _numpy


HEADER_CHAR = '#'


class ExcitationCurve:

    def __init__(self, magnet): # generalise: pass magnet name
        """Conversion between current and field

        Keyword argument:
        magnet -- magnet excitation curve file name
        """
        self._magnet = magnet
        self._load_excitation_curve(magnet)

    @property
    def main_harmonic(self):
        return self._main_harmonic

    @property
    def harmonics(self):
        return self._harmonics

    def get_normal_main_field_from_current(self, current):
        field_array = self._get_main_field_column(self._i_to_f_normal_fields)
        return self._interpolate_current(current, field_array)

    def get_skew_main_field_from_current(self, current):
        field_array = self._get_main_field_column(self._i_to_f_skew_fields)
        return self._interpolate_current(current, field_array)

    def _get_main_field_column(self, fields_table):
        return fields_table[:, self._main_harmonic_index]

    def get_normal_fields_from_current(self, current):
        fields_array = self._i_to_f_normal_fields
        return self._get_fields_from_current(current, fields_array)

    def get_skew_fields_from_current(self, current):
        fields_array = self._i_to_f_skew_fields
        return self._get_fields_from_current(current, fields_array)

    def _get_fields_from_current(self, current, fields_array):
        fields = _numpy.zeros(self._highest_harmonic+1)
        for h, i in zip(self._harmonics, range(len(self._harmonics))):
            fields[h] = self._interpolate_current(current, fields_array[:, i])

        return fields

    def _interpolate_current(self, current, field_array):
        current_array =  self._i_to_f_current
        return _numpy.interp(current, current_array, field_array)

    def get_current_from_normal_main_field(self, main_field):
        field_array = self._f_to_i_normal_main_field
        current_array =  self._f_to_i_normal_current

        return self._interpolate_main_field(main_field, field_array,
            current_array)

    def get_current_from_skew_main_field(self, main_field):
        field_array = self._f_to_i_skew_main_field
        current_array =  self._f_to_i_skew_current

        return self._interpolate_main_field(main_field, field_array,
            current_array)

    def _interpolate_main_field(self, field, field_array, current_array):
        return _numpy.interp(field, field_array, current_array)

    def _load_excitation_curve(self, magnet):
        self._read_excitation_curve_from_file(file_name=magnet)

    def _read_excitation_curve_from_file(self, file_name):
        with open(file_name, encoding='latin-1') as f:
            lines = [line.strip() for line in f]

        self._process_excitation_curve_file_lines(lines)

    def _process_excitation_curve_file_lines(self, lines):
        conversion_data = []
        for line in lines:
            if line.startswith(HEADER_CHAR):
                self._process_header_line(line)
            else:
                conversion_data.append([float(word) for word in line.split()])

        self._check_harmonics()
        self._build_interpolation_tables_from_conversion_data(conversion_data)

    def _process_header_line(self, line):
        words = self._get_words_from_header_line(line)
        if 'main_harmonic' in words:
            self._read_main_harmonic_from_words(words)
        elif 'harmonics' in words:
            self._read_harmonics_from_words(words)

    def _get_words_from_header_line(self, line):
        lowercase_header_line = line.lower()
        lowercase_line = lowercase_header_line.strip(HEADER_CHAR)
        words = lowercase_line.split()

        return words

    def _read_main_harmonic_from_words(self, words):
        self._main_harmonic = int(words[1])

    def _read_harmonics_from_words(self, words):
        self._harmonics = [int(n) for n in words[1:]]
        self._highest_harmonic = max(self._harmonics)

    def _check_harmonics(self):
        if not hasattr(self, '_main_harmonic'):
            raise AttributeError('missing main_harmonic')
        if not hasattr(self, '_harmonics'):
            raise AttributeError('missing harmonics')
        self._main_harmonic_index = self._harmonics.index(self._main_harmonic)

    def _build_interpolation_tables_from_conversion_data(self, data):
        data = _numpy.array(data)
        current = data[:, 0] # current
        fields = data[:, 1:] # integrated fields (normal and skew)

        self._check_fields_table_size(fields)
        self._prepare_interpolation_tables(current, fields)

    def _check_fields_table_size(self, fields):
        if _numpy.size(fields, 1) != 2*(len(self._harmonics)):
            msg = ('Mismatch between number of columns and size of ' +
                'harmonics list in excitation curve')
            raise Exception(msg)

    def _prepare_interpolation_tables(self, current, fields):
        # Interpolation requires increasing x
        self._prepare_i_to_f_interpolation_table(current, fields)
        self._prepare_f_to_i_interpolation_table(current, fields)

    def _prepare_i_to_f_interpolation_table(self, current, fields):
        if _numpy.all(_numpy.diff(current) >= 0):
            self._i_to_f_current = current
            self._i_to_f_normal_fields = fields[:, 0::2]
            self._i_to_f_skew_fields = fields[:, 1::2]
        elif _numpy.all(_numpy.diff(current) <= 0):
            self._i_to_f_current = current[::-1]
            self._i_to_f_normal_fields = fields[::-1, 0::2]
            self._i_to_f_skew_fields = fields[::-1, 1::2]
        else:
            msg = 'current must be strictly increasing or decreasing'
            raise ValueError(msg)

    def _prepare_f_to_i_interpolation_table(self, current, fields):
        # Field tables alternate normal and skew components
        self._prepare_f_to_i_normal_interpolation_table(current, fields)
        self._prepare_f_to_i_skew_interpolation_table(current, fields)

    def _prepare_f_to_i_normal_interpolation_table(self, current, fields):
        normal_field = fields[:, 2*self._main_harmonic_index]
        if _numpy.all(_numpy.diff(normal_field) >= 0):
            self._f_to_i_normal_current = current
            self._f_to_i_normal_main_field = normal_field
        elif _numpy.all(_numpy.diff(normal_field) <= 0):
            self._f_to_i_normal_current = current[::-1]
            self._f_to_i_normal_main_field = normal_field[::-1]
        else:
            print(self._magnet)
            msg = 'main field must be strictly increasing or decreasing'
            raise ValueError(msg)

    def _prepare_f_to_i_skew_interpolation_table(self, current, fields):
        skew_field = fields[:, 2*self._main_harmonic_index+1]
        if _numpy.all(_numpy.diff(skew_field) >= 0):
            self._f_to_i_skew_current = current
            self._f_to_i_skew_main_field = skew_field
        elif _numpy.all(_numpy.diff(skew_field) <= 0):
            self._f_to_i_skew_current = current[::-1]
            self._f_to_i_skew_main_field = skew_field[::-1]
        else:
            print(self._magnet)
            msg = 'main field must be strictly increasing or decreasing'
            raise ValueError(msg)
