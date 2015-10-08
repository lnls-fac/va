
import os
import unittest
import unittest.mock
import pyaccel
import va


EXCITATION_CURVE_DIR = 'excitation_curves'


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
        # self.sextupole = pyaccel.elements.sextupole(
        #     fam_name='sextupole',
        #     length=0.2,
        #     S=3.0
        # )
        self.accelerator.append(self.bend)
        # self.accelerator.append(self.sextupole)
        self.brho = 10.006922710777445

        self.bend_magnet = va.magnet.NormalMagnet(
            self.accelerator,
            [0],
            os.path.join(EXCITATION_CURVE_DIR, 'bend.txt')
        )

    def test_magnet_initial_values(self):
        expected_bl = self.angle*self.brho
        expected_current = 1000*expected_bl

        self.assertAlmostEqual(self.bend_magnet.value, expected_bl, 8)
        self.assertAlmostEqual(self.bend_magnet.current, expected_current, 8)

    def test_bend_magnet_integrated_field(self):
        bl = self.bend_magnet.value
        current = self.bend_magnet.current
        ps = self._get_mock_power_supply(current=current)

        self.bend_magnet.add_power_supply(ps)
        self.bend_magnet.process()

        # Check integrated field
        bl = self.bend_magnet.value
        expected_bl = current/1000
        self.assertAlmostEqual(bl, expected_bl, 8)

        # Angle must still have nominal value
        self.assertEqual(self.accelerator[0].angle, self.angle)

        # Difference in polynom_b[0] must be zero
        delta_deflection_angle = bl/self.brho - self.angle
        length = self.accelerator[0].length
        expected_strength = delta_deflection_angle/length
        bend_magnet_strength = self.accelerator[0].polynom_b[0]
        self.assertAlmostEqual(bend_magnet_strength, expected_strength, 14)

    def _get_mock_power_supply(self, current):
        ps = unittest.mock.MagicMock()
        ps_current = unittest.mock.PropertyMock(return_value=current)
        type(ps).current = ps_current
        return ps


def magnet_suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBendMagnet)
    return suite


def get_suite():
    suite_list = []
    suite_list.append(magnet_suite())
    return unittest.TestSuite(suite_list)
