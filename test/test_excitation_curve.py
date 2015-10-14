
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

    def test_init_not_increasing_tables(self):
        file_name = os.path.join(EXC_CURVE_DIR, 'bad_test.txt')
        with self.assertRaises(ValueError):
            curve = ExcitationCurve(file_name)


class TestExcitationCurve(unittest.TestCase):

    def setUp(self):
        file_name = os.path.join(EXC_CURVE_DIR, 'test.txt')
        self.curve = ExcitationCurve(file_name)

    def test_read_main_harmonic(self):
        self.assertEqual(self.curve.main_harmonic, 1)

    def test_write_main_harmonic(self):
        with self.assertRaises(AttributeError):
            self.curve.main_harmonic = 0

    def test_read_harmonics(self):
        comparison = set(self.curve.harmonics) == set([1, 4, 9, 13])
        self.assertTrue(comparison)

    def test_write_harmonics(self):
        with self.assertRaises(AttributeError):
            self.curve.harmonics = [0, 1, 2, 3]

    def test_get_main_field(self):
        current = 25.2
        # Use values from excitation curve
        expected_main_field = (current/50.0)*(-0.4)
        main_field = self.curve.get_main_field_from_current(current)
        self.assertAlmostEqual(main_field, expected_main_field, 8)

        current = 55.1
        # Use values from excitation curve
        expected_main_field = -0.4 + (current-50.0)/(50.0)*(-0.6)
        main_field = self.curve.get_main_field_from_current(current)
        self.assertAlmostEqual(main_field, expected_main_field, 8)

    def test_get_current(self):
        main_field = -0.23
        # Use values from excitation curve
        expected_current = (-main_field/0.4)*50.0
        current = self.curve.get_current_from_main_field(main_field)
        self.assertAlmostEqual(current, expected_current, 8)

        main_field = -0.77
        # Use values from excitation curve
        expected_current = 50.0 + (main_field+0.4)/(-0.6)*50.0
        current = self.curve.get_current_from_main_field(main_field)
        self.assertAlmostEqual(current, expected_current, 8)


def init_exception_suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestInitException)
    return suite


def excitation_curve_suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestExcitationCurve)
    return suite


def get_suite():
    suite_list = []
    suite_list.append(init_exception_suite())
    suite_list.append(excitation_curve_suite())
    return unittest.TestSuite(suite_list)
