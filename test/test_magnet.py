
import os
import unittest
import unittest.mock
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
        BRHO = 10.006922710777445

        self.bend_magnet = va.magnet.NormalMagnet(
            self.accelerator,
            [0],
            os.path.join(EXCITATION_CURVE_DIR, 'bend.txt')
        )

    def test_magnet_initial_values(self):
        expected_bl = self.angle*BRHO
        # Excitation curve maps I: [0, 1000] <-> BL: [0, 1]
        expected_current = 1000*expected_bl

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
        expected_bl = current/1000
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
        expected_bl = current_factor*current/1000
        self.assertAlmostEqual(bl, expected_bl, 8)

        # Angle must still have nominal value
        self.assertEqual(self.accelerator[0].angle, self.angle)

        # Difference must be put in polynom_b[0]
        delta_deflection_angle = bl/BRHO - self.angle
        length = self.accelerator[0].length
        expected_strength = delta_deflection_angle/length
        bend_magnet_strength = self.accelerator[0].polynom_b[0]
        self.assertAlmostEqual(bend_magnet_strength, expected_strength, 8)


class TestMultipoleMagnet(unittest.TestCase):

    def setUp(self):
        self.accelerator = pyaccel.accelerator.Accelerator(
            energy=3.0e9,
        )

        self.sf_strength = 100.0
        self.sf_length = 0.2
        self.sf = pyaccel.elements.sextupole(
            fam_name='sf',
            length=self.sf_length,
            S=self.sf_strength
        )

        self.sd_strength = -50.0
        self.sd_length = 0.15
        self.sd = pyaccel.elements.sextupole(
            fam_name='sd',
            length=self.sd_length,
            S=self.sd_strength
        )

        self.accelerator.append(self.sf)
        self.accelerator.append(self.sd)

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
        expected_sf_bl = self.sf_strength*self.sf_length*BRHO
        expected_sd_bl = self.sd_strength*self.sd_length*BRHO

        # Excitation curve maps I: [0, 200] <-> BL: [0, 400]
        expected_sf_current = (200.0/400.0)*expected_sf_bl

        # Excitation curve maps I: [0, 200] <-> BL: [0, -350]
        expected_sd_current = -(200.0/350.0)*expected_sd_bl

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
        expected_bl = (400.0/200.0)*current_factor*current
        self.assertAlmostEqual(bl, expected_bl, 8)

        expected_strength = expected_bl/self.sf_length/BRHO
        sf_strength = self.accelerator[0].polynom_b[2]
        self.assertAlmostEqual(sf_strength, expected_strength, 8)


def _get_mock_power_supply(current):
    ps = unittest.mock.MagicMock()
    ps_current = unittest.mock.PropertyMock(return_value=current)
    type(ps).current = ps_current
    return ps


def bend_magnet_suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBendMagnet)
    return suite


def multipole_magnet_suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMultipoleMagnet)
    return suite


def get_suite():
    suite_list = []
    suite_list.append(bend_magnet_suite())
    suite_list.append(multipole_magnet_suite())
    return unittest.TestSuite(suite_list)
