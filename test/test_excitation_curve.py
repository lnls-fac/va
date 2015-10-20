
import os
import unittest
import numpy
from va.excitation_curve import ExcitationCurve


EXC_CURVE_DIR = './excitation_curves'


class TestInitException(unittest.TestCase):

    def test_init_not_existent_file(self):
        file_name = os.path.join(EXC_CURVE_DIR, 'not_existent.txt')
        with self.assertRaises(FileNotFoundError):
            curve = ExcitationCurve(file_name)

    def test_init_not_increasing(self):
        file_name = os.path.join(EXC_CURVE_DIR, 'bad_test.txt')
        with self.assertRaises(ValueError):
            curve = ExcitationCurve(file_name)

    def test_init_no_main_harmonic(self):
        file_name = os.path.join(EXC_CURVE_DIR, 'bad_test_main_harmonic.txt')
        with self.assertRaises(AttributeError):
            curve = ExcitationCurve(file_name)

    def test_init_no_harmonics(self):
        file_name = os.path.join(EXC_CURVE_DIR, 'bad_test_harmonics.txt')
        with self.assertRaises(AttributeError):
            curve = ExcitationCurve(file_name)

    def test_init_bad_curve_type(self):
        file_name = os.path.join(EXC_CURVE_DIR, 'bad_curve_type.txt')
        with self.assertRaises(ValueError):
            curve = ExcitationCurve(file_name)


class TestNormalCurve(unittest.TestCase):

    def setUp(self):
        file_name = os.path.join(EXC_CURVE_DIR, 'testnormal.txt')
        self.curve = ExcitationCurve(file_name)

    def test_read_main_harmonic_normal(self):
        self.assertEqual(self.curve.main_harmonic, 1)

    def test_write_main_harmonic_normal(self):
        with self.assertRaises(AttributeError):
            self.curve.main_harmonic = 0

    def test_read_harmonics_normal(self):
        comparison = set(self.curve.harmonics) == set([1, 4, 9, 13])
        self.assertTrue(comparison)

    def test_write_harmonics_normal(self):
        with self.assertRaises(AttributeError):
            self.curve.harmonics = [0, 1, 2, 3]

    def test_get_normal_field(self):
        # First current interval
        current = 25.2
        # Use values from excitation curve
        expected_field = (current/50.0)*(-0.4)
        field = self.curve.get_field_from_current(current)
        self.assertAlmostEqual(field, expected_field, 8)

        # Second current interval
        current = 55.1
        # Use values from excitation curve
        expected_field = -0.4 + (current-50.0)/50.0*(-0.6)
        field = self.curve.get_field_from_current(current)
        self.assertAlmostEqual(field, expected_field, 8)

    def test_get_normal_fields(self):
        # First current interval
        current = 30.3
        # Use values from excitation curve
        fields_t1 = numpy.zeros(14)
        fields_t1[1] = -0.4
        fields_t1[4] = -1.2
        fields_t1[9] = -2.0
        fields_t1[13] = -2.8

        expected_fields = (current/50.0)*fields_t1
        fields = self.curve.get_normal_fields_from_current(current)
        self.assertEqual(len(fields), 14)
        for i in range(14):
            self.assertAlmostEqual(fields[i], expected_fields[i], 8)

        # Second current interval
        current = 70.9
        # Use values from excitation curve
        fields_t2 = numpy.zeros(14)
        fields_t2[1] = -1.0
        fields_t2[4] = -3.0
        fields_t2[9] = -5.0
        fields_t2[13] = -7.0

        expected_fields = fields_t1 + (current-50.0)/50.0*(fields_t2-fields_t1)
        fields = self.curve.get_normal_fields_from_current(current)
        for i in range(14):
            self.assertAlmostEqual(fields[i], expected_fields[i], 8)

    def test_get_skew_fields(self):
        # First current interval
        current = 22.1
        # Use values from excitation curve
        fields_t1 = numpy.zeros(14)
        fields_t1[1] = 0.8
        fields_t1[4] = 1.6
        fields_t1[9] = 2.4
        fields_t1[13] = 3.2

        expected_fields = (current/50.0)*fields_t1
        fields = self.curve.get_skew_fields_from_current(current)
        self.assertEqual(len(fields), 14)
        for i in range(14):
            self.assertAlmostEqual(fields[i], expected_fields[i], 8)

        # Second current interval
        current = 80.8
        # Use values from excitation curve
        fields_t2 = numpy.zeros(14)
        fields_t2[1] = 2.0
        fields_t2[4] = 4.0
        fields_t2[9] = 6.0
        fields_t2[13] = 8.0

        expected_fields = fields_t1 + (current-50.0)/50.0*(fields_t2-fields_t1)
        fields = self.curve.get_skew_fields_from_current(current)
        for i in range(14):
            self.assertAlmostEqual(fields[i], expected_fields[i], 8)

    def test_get_current_from_normal(self):
        # First field interval
        field = -0.23
        # Use values from excitation curve
        expected_current = (-field/0.4)*50.0
        current = self.curve.get_current_from_field(field)
        self.assertAlmostEqual(current, expected_current, 8)

        # Second field interval
        field = -0.77
        # Use values from excitation curve
        expected_current = 50.0 + (field+0.4)/(-0.6)*50.0
        current = self.curve.get_current_from_field(field)
        self.assertAlmostEqual(current, expected_current, 8)


class TestSkewCurve(unittest.TestCase):

    def setUp(self):
        file_name = os.path.join(EXC_CURVE_DIR, 'testskew.txt')
        self.curve = ExcitationCurve(file_name)

    def test_read_main_harmonic_skew(self):
        self.assertEqual(self.curve.main_harmonic, 1)

    def test_write_main_harmonic_skew(self):
        with self.assertRaises(AttributeError):
            self.curve.main_harmonic = 0

    def test_read_harmonics_skew(self):
        comparison = set(self.curve.harmonics) == set([1, 4, 9, 13])
        self.assertTrue(comparison)

    def test_write_harmonics_skew(self):
        with self.assertRaises(AttributeError):
            self.curve.harmonics = [0, 1, 2, 3]

    def test_get_skew_field(self):
        # First current interval
        current = 25.2
        # Use values from excitation curve
        expected_field = (current/50.0)*0.8
        field = self.curve.get_field_from_current(current)
        self.assertAlmostEqual(field, expected_field, 8)

        # Second current interval
        current = 55.1
        # Use values from excitation curve
        expected_field = 0.8 + (current-50.0)/(50.0)*1.2
        field = self.curve.get_field_from_current(current)
        self.assertAlmostEqual(field, expected_field, 8)

    def test_get_normal_fields(self):
        # First current interval
        current = 30.3
        # Use values from excitation curve
        fields_t1 = numpy.zeros(14)
        fields_t1[1] = -0.4
        fields_t1[4] = -1.2
        fields_t1[9] = -2.0
        fields_t1[13] = -2.8

        expected_fields = (current/50.0)*fields_t1
        fields = self.curve.get_normal_fields_from_current(current)
        self.assertEqual(len(fields), 14)
        for i in range(14):
            self.assertAlmostEqual(fields[i], expected_fields[i], 8)

        # Second current interval
        current = 70.9
        # Use values from excitation curve
        fields_t2 = numpy.zeros(14)
        fields_t2[1] = -1.0
        fields_t2[4] = -3.0
        fields_t2[9] = -5.0
        fields_t2[13] = -7.0

        expected_fields = fields_t1 + (current-50.0)/50.0*(fields_t2-fields_t1)
        fields = self.curve.get_normal_fields_from_current(current)
        for i in range(14):
            self.assertAlmostEqual(fields[i], expected_fields[i], 8)

    def test_get_skew_fields(self):
        # First current interval
        current = 22.1
        # Use values from excitation curve
        fields_t1 = numpy.zeros(14)
        fields_t1[1] = 0.8
        fields_t1[4] = 1.6
        fields_t1[9] = 2.4
        fields_t1[13] = 3.2

        expected_fields = (current/50.0)*fields_t1
        fields = self.curve.get_skew_fields_from_current(current)
        self.assertEqual(len(fields), 14)
        for i in range(14):
            self.assertAlmostEqual(fields[i], expected_fields[i], 8)

        # Second current interval
        current = 80.8
        # Use values from excitation curve
        fields_t2 = numpy.zeros(14)
        fields_t2[1] = 2.0
        fields_t2[4] = 4.0
        fields_t2[9] = 6.0
        fields_t2[13] = 8.0

        expected_fields = fields_t1 + (current-50.0)/50.0*(fields_t2-fields_t1)
        fields = self.curve.get_skew_fields_from_current(current)
        for i in range(14):
            self.assertAlmostEqual(fields[i], expected_fields[i], 8)

    def test_get_current_from_skew(self):
        # First field interval
        field = 0.46
        # Use values from excitation curve
        expected_current = (field/0.8)*50.0
        current = self.curve.get_current_from_field(field)
        self.assertAlmostEqual(current, expected_current, 8)

        # Second field interval
        field = 1.54
        # Use values from excitation curve
        expected_current = 50.0 + (field-0.8)/1.2*50.0
        current = self.curve.get_current_from_field(field)
        self.assertAlmostEqual(current, expected_current, 8)


def init_exception_suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestInitException)
    return suite


def normal_curve_suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestNormalCurve)
    return suite


def skew_curve_suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSkewCurve)
    return suite


def get_suite():
    suite_list = []
    suite_list.append(init_exception_suite())
    suite_list.append(normal_curve_suite())
    suite_list.append(skew_curve_suite())
    return unittest.TestSuite(suite_list)
