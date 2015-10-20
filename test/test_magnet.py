
import os
import unittest
import unittest.mock
# import numpy
import pyaccel
import va


EXCITATION_CURVE_DIR = 'excitation_curves'
BRHO = 10.006922710777445


class TestBendMagnet(unittest.TestCase):

    def setUp(self):
        self.accelerator = pyaccel.accelerator.Accelerator(
            energy=3.0e9,
        )

        self.angle = 0.05
        self.bend = pyaccel.elements.rbend(
            fam_name='bend',
            length=0.5,
            angle=self.angle
        )
        self.accelerator.append(self.bend)

        self.bend_magnet = va.magnet.NormalMagnet(
            self.accelerator,
            [0],
            os.path.join(EXCITATION_CURVE_DIR, 'bend.txt')
        )

    def test_magnet_initial_values(self):
        expected_bl = -self.angle*BRHO
        # Excitation curve maps I: [0, 1000] <-> BL: [0, 1]
        expected_current = -1000*expected_bl

        self.assertAlmostEqual(self.bend_magnet.value, expected_bl, 8)
        self.assertAlmostEqual(self.bend_magnet.current, expected_current, 8)

    def test_bend_magnet_nominal_value(self):
        bl = self.bend_magnet.value
        current = self.bend_magnet.current
        ps = _get_mock_power_supply(current=current)
        self.bend_magnet.add_power_supply(ps)
        self.bend_magnet.process()

        # Check integrated field
        bl = self.bend_magnet.value
        expected_bl = -current/1000
        self.assertAlmostEqual(bl, expected_bl, 8)

        # Angle must still have nominal value
        self.assertEqual(self.accelerator[0].angle, self.angle)

        bend_magnet_strength = self.accelerator[0].polynom_b[0]
        self.assertAlmostEqual(bend_magnet_strength, 0.0, 15)

    def test_bend_magnet_changed_value(self):
        bl = self.bend_magnet.value
        current = self.bend_magnet.current
        current_factor = 1.1
        ps = _get_mock_power_supply(current=current_factor*current)
        self.bend_magnet.add_power_supply(ps)
        self.bend_magnet.process()

        # Check integrated field
        bl = self.bend_magnet.value
        expected_bl = -current_factor*current/1000
        self.assertAlmostEqual(bl, expected_bl, 8)

        # Angle must still have nominal value
        self.assertEqual(self.accelerator[0].angle, self.angle)

        # Difference must be put in polynom_b[0]
        delta_deflection_angle = -bl/BRHO - self.angle
        length = self.accelerator[0].length
        expected_strength = delta_deflection_angle/length
        bend_magnet_strength = self.accelerator[0].polynom_b[0]
        self.assertAlmostEqual(bend_magnet_strength, expected_strength, 8)


class TestSextupoleMagnet(unittest.TestCase):

    def setUp(self):
        self.accelerator = pyaccel.accelerator.Accelerator(
            energy=3.0e9,
        )

        self.sf_strength = 100.0
        self.sf_length = 0.2
        self.sf_element = pyaccel.elements.sextupole(
            fam_name='sf',
            length=self.sf_length,
            S=self.sf_strength
        )

        self.sd_strength = -50.0
        self.sd_length = 0.15
        self.sd_element = pyaccel.elements.sextupole(
            fam_name='sd',
            length=self.sd_length,
            S=self.sd_strength
        )

        self.accelerator.append(self.sf_element)
        self.accelerator.append(self.sd_element)

        self.sf = va.magnet.NormalMagnet(
            self.accelerator,
            [0],
            os.path.join(EXCITATION_CURVE_DIR, 'sf.txt')
        )
        self.sd = va.magnet.NormalMagnet(
            self.accelerator,
            [1],
            os.path.join(EXCITATION_CURVE_DIR, 'sd.txt')
        )

    def test_sextupole_initial_values(self):
        expected_sf_bl = -self.sf_strength*self.sf_length*BRHO
        expected_sd_bl = -self.sd_strength*self.sd_length*BRHO

        # Excitation curve maps I: [0, 200] <-> BL: [0, 400]
        expected_sf_current = -(200.0/400.0)*expected_sf_bl

        # Excitation curve maps I: [0, 200] <-> BL: [0, -350]
        expected_sd_current = (200.0/350.0)*expected_sd_bl

        self.assertAlmostEqual(self.sf.value, expected_sf_bl, 8)
        self.assertAlmostEqual(self.sf.current, expected_sf_current, 8)

        self.assertAlmostEqual(self.sd.value, expected_sd_bl, 8)
        self.assertAlmostEqual(self.sd.current, expected_sd_current, 8)

    def test_sextupole_changed_value(self):
        bl = self.sf.value
        current = self.sf.current
        current_factor = 1.1
        ps = _get_mock_power_supply(current=current_factor*current)
        self.sf.add_power_supply(ps)
        self.sf.process()

        # Check integrated field
        bl = self.sf.value
        expected_bl = -(400.0/200.0)*current_factor*current
        self.assertAlmostEqual(bl, expected_bl, 8)

        # Check strength
        expected_strength = -expected_bl/self.sf_length/BRHO
        sf_strength = self.accelerator[0].polynom_b[2]
        self.assertAlmostEqual(sf_strength, expected_strength, 8)

    def test_sextupole_with_orbit_corrector(self):
        bl = self.sf.value
        sextupole_current = self.sf.current
        ps = _get_mock_power_supply(current=sextupole_current)
        self.sf.add_power_supply(ps)
        self.sf.process()

        # Add corrector to sf
        corrector = va.magnet.NormalMagnet(
            self.accelerator,
            [0],
            os.path.join(EXCITATION_CURVE_DIR, 'corrector.txt')
        )

        corrector_current = 5.0
        ps = _get_mock_power_supply(current=corrector_current)
        corrector.add_power_supply(ps)
        corrector.process()

        # Check sextupole integrated field is still the same
        sextupole_bl = self.sf.value
        sextupole_expected_bl = -(400.0/200.0)*sextupole_current
        self.assertAlmostEqual(sextupole_bl, sextupole_expected_bl, 8)

        # Check corrector integrated
        corrector_bl = corrector.value
        # Excitation curve maps I: [-10, 10] <-> BL: [-0.01, 0.01]
        corrector_expected_bl = -corrector_current/1000
        self.assertAlmostEqual(corrector_bl, corrector_expected_bl, 8)

        # Check corrector strength
        expected_strength = -corrector_expected_bl/self.sf_length/BRHO
        corrector_strength = self.accelerator[0].polynom_b[0]
        self.assertAlmostEqual(corrector_strength, expected_strength, 8)

    def test_sextupole_with_skew_corrector(self):
        bl = self.sd.value
        sextupole_current = self.sd.current
        ps = _get_mock_power_supply(current=sextupole_current)
        self.sd.add_power_supply(ps)
        self.sd.process()

        # Add corrector to sd
        skew = va.magnet.SkewMagnet(
            self.accelerator,
            [1],
            os.path.join(EXCITATION_CURVE_DIR, 'skew.txt')
        )

        skew_current = -5.0
        ps = _get_mock_power_supply(current=skew_current)
        skew.add_power_supply(ps)
        skew.process()

        # Check sextupole integrated field is still the same
        sextupole_bl = self.sd.value
        sextupole_expected_bl = (350.0/200.0)*sextupole_current
        self.assertAlmostEqual(sextupole_bl, sextupole_expected_bl, 8)

        # Check skew integrated
        skew_kl = skew.value
        # Excitation curve maps I: [-10, 10] <-> KL: [-0.5, 0.5]
        skew_expected_kl = -skew_current/20
        self.assertAlmostEqual(skew_kl, skew_expected_kl, 8)

        # Check skew strength
        expected_strength = -skew_expected_kl/self.sd_length/BRHO
        skew_strength = self.accelerator[1].polynom_a[1]
        self.assertAlmostEqual(skew_strength, expected_strength, 8)


class TestMultipoleMagnet(unittest.TestCase):

    def setUp(self):
        self.accelerator = pyaccel.accelerator.Accelerator(
            energy=3.0e9,
        )

        # Focusing quadrupole
        self.quad_length = 0.15
        self.quad_strength = 2.0
        self.quad_element = pyaccel.elements.quadrupole(
            fam_name='quad',
            length=self.quad_length,
            K=self.quad_strength
        )
        self.accelerator.append(self.quad_element)

        self.quad = va.magnet.NormalMagnet(
            self.accelerator,
            [0],
            os.path.join(EXCITATION_CURVE_DIR, 'quad.txt')
        )

    def test_something(self):
        gl = self.quad.value
        quad_current = self.quad.current
        ps = _get_mock_power_supply(current=quad_current)
        self.quad.add_power_supply(ps)
        self.quad.process()

        # print()
        # print(gl)
        # print(quad_current)
        # print(self.accelerator[0].K)
        # print(self.accelerator[0].polynom_b)


def _get_mock_power_supply(current):
    ps = unittest.mock.MagicMock()
    ps_current = unittest.mock.PropertyMock(return_value=current)
    type(ps).current = ps_current
    return ps


def bend_magnet_suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBendMagnet)
    return suite


def sextupole_magnet_suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSextupoleMagnet)
    return suite


def multipole_magnet_suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMultipoleMagnet)
    return suite


def get_suite():
    suite_list = []
    suite_list.append(bend_magnet_suite())
    suite_list.append(sextupole_magnet_suite())
    suite_list.append(multipole_magnet_suite())
    return unittest.TestSuite(suite_list)
