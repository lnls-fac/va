
import numpy as _numpy
import os as _os
from siriuspy.envars import folder_lnls_sirius_csconstants


_HEADER_CHAR = '#'


class PulseCurve:

    def __init__(self, fname, method='filename'):

        if method == 'filename':
            _pulse_curves_dir = _os.path.join(folder_lnls_sirius_csconstants, 'magnet', 'pulse-curve-data')
            filename = _os.path.join(_pulse_curves_dir, fname)
            self._load_pulse_curve(filename)
        elif method == 'filename_web':
            self._load_pulse_curve_web(filename)

    @property
    def rise_time(self):
        return self._rise_time

    @property
    def flat_top(self):
        return self._flat_top

    def get_pulse_shape(self, time):
        return _numpy.interp(time, self._pulse_time, self._pulse_shape, left=0, right=0)

    def _load_pulse_curve(self, magnet):
        self._read_pulse_curve_from_file(file_name=magnet)

    def _load_pulse_curve_web(filename):
        raise NotImplemented

    def _read_pulse_curve_from_file(self, file_name):
        with open(file_name, encoding='latin-1') as f:
            lines = [line.strip() for line in f]

        self._process_pulse_curve_file_lines(lines)

    def _process_pulse_curve_file_lines(self, lines):
        conversion_data = []
        for line in lines:
            if line.startswith(_HEADER_CHAR):
                self._process_header_line(line)
            else:
                conversion_data.append([float(word) for word in line.split()])

        self._build_interpolation_tables_from_conversion_data(conversion_data)

    def _process_header_line(self, line):
        words = self._get_words_from_header_line(line)
        if 'risetime' in words:
            self._read_rise_time_from_words(words)
        elif 'flattop' in words:
            self._read_flat_top_from_words(words)

    def _get_words_from_header_line(self, line):
        lowercase_header_line = line.lower()
        lowercase_line = lowercase_header_line.strip(_HEADER_CHAR)
        words = lowercase_line.split()
        return words

    def _read_rise_time_from_words(self, words):
        self._rise_time = float(words[1])

    def _read_flat_top_from_words(self, words):
        self._flat_top = float(words[1])

    def _build_interpolation_tables_from_conversion_data(self, data):
        data = _numpy.array(data)
        self._pulse_time = data[:, 0]
        self._pulse_shape = data[:, 1]/max(data[:,1])
