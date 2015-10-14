
import numpy as _numpy


HEADER_CHAR = '#'


class ExcitationCurve:

    def __init__(self, magnet): # generalise: pass magnet name
        self._load_excitation_curve(magnet)

    @property
    def main_harmonic(self):
        return self._main_harmonic

    @property
    def harmonics(self):
        return self._harmonics

    def get_main_field_from_current(self, current):
        current_array =  self._i_to_f_current
        main_field_array = self._i_to_f_fields[:, self._main_harmonic_index]

        return _numpy.interp(current, current_array, main_field_array)

    def get_current_from_main_field(self, main_field):
        field_array = self._f_to_i_main_field
        current_array =  self._f_to_i_current

        return _numpy.interp(main_field, field_array, current_array)

    def _load_excitation_curve(self, magnet):
        """Generalise in a future version: read from DB?"""
        self._read_excitation_curve_from_file(file_name=magnet)

    def _read_excitation_curve_from_file(self, file_name):
        with open(file_name, encoding='latin-1') as f:
            lines = [line.strip() for line in f]

        conversion_data = []
        for line in lines:
            if line.startswith(HEADER_CHAR):
                self._process_header_line(line)
            else:
                conversion_data.append([float(word) for word in line.split()])

        self._main_harmonic_index = self._harmonics.index(self._main_harmonic)

        conversion_data = _numpy.array(conversion_data)

        if _numpy.size(conversion_data[:,1:], 1) != 2*(len(self._harmonics)):
            raise Exception('Mismatch between number of columns and size of harmonics list in excitation curve')

        current = conversion_data[:, 0] # current
        fields = conversion_data[:, 1:] # integrated fields (normal and skew)

        self._prepare_interpolation_tables(current, fields)

    def _process_header_line(self, line):
        words = self._get_words_from_line(line)
        if 'main_harmonic' in words:
            self._read_main_harmonic_from_words(words)
        elif 'harmonics' in words:
            self._read_harmonics_from_words(words)

    def _get_words_from_line(self, line):
        lowercase_header_line = line.lower()
        lowercase_line = lowercase_header_line.strip(HEADER_CHAR)
        words = lowercase_line.split()

        return words

    def _read_main_harmonic_from_words(self, words):
        self._main_harmonic = int(words[1])

    def _read_harmonics_from_words(self, words):
        self._harmonics = [int(n) for n in words[1:]]

    def _prepare_interpolation_tables(self, current, fields):
        # Interpolation requires increasing x
        if _numpy.all(_numpy.diff(current) > 0):
            self._i_to_f_current = current
            self._i_to_f_fields = fields
        elif _numpy.all(_numpy.diff(current) < 0):
            self._i_to_f_current = current[::-1]
            self._i_to_f_fields = fields[::-1, :]
        else:
            msg = 'current must be strictly increasing or decreasing'
            raise ValueError(msg)

        main_field = fields[:, self._main_harmonic_index]
        if _numpy.all(_numpy.diff(main_field) > 0):
            self._f_to_i_current = current
            self._f_to_i_main_field = main_field
        elif _numpy.all(_numpy.diff(main_field) < 0):
            self._f_to_i_current = current[::-1]
            self._f_to_i_main_field = main_field[::-1]
        else:
            msg = 'main field must be strictly increasing or decreasing'
            raise ValueError(msg)
