import numpy as _np
from siriuspy.clientweb import magnets_excitation_data_read


_HEADER_CHAR = '#'


class PulseCurve:

    def __init__(self, fname):
        self._rise_time = 0
        self._flat_top = 0
        self._load_pulse_curve_web(fname)

    @property
    def rise_time(self):
        return self._rise_time

    @property
    def flat_top(self):
        return self._flat_top

    def get_pulse_shape(self, time):
        return _np.interp(
            time, 
            self._pulse_time, 
            self._pulse_shape, left=0, right=0)

    def _load_pulse_curve_web(self, filename):
        try:
            text = magnets_excitation_data_read(
                '../pulse-curve-data/'+filename)
        except:
            print('Error trying to read excdata {}'.format(filename))
            raise
        lines = text.split('\n')
        self._process_pulse_curve_file_lines(lines)

    def _process_pulse_curve_file_lines(self, lines):
        conversion_data = []
        for line in lines:
            if line.startswith(_HEADER_CHAR):
                self._process_header_line(line)
            elif not line:
                continue
            else:
                data = [float(word) for word in line.strip().split()]
                conversion_data.append(data)

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
        data = _np.array(data)
        self._pulse_time = data[:, 0]
        self._pulse_shape = data[:, 1]/max(data[:, 1])
