
import unittest
import numpy
import pyaccel
import trackcpp
import sirius
import va
import epics


class TestSI(unittest.TestCase):

    def setUp(self):
        self.model = va.model.SiModel(log_func = lambda message1, message2, c, a: None)
        epics.caput('TestVA-SIFK-RESET',0)

    #@unittest.skip("long test")
    def test_bpms(self):
        pvs_bpm = va.si_pvs.di_bpms
        print(pvs_bpm)
        for pv in pvs_bpm:
            r1 = self.model.get_pv(pv)
            r2 = epics.caget('TestVA-' + pv)
            self.assertAlmostEqual(r1[0], r2[0], 15)
            self.assertAlmostEqual(r1[1], r2[1], 15)

    @unittest.skip("long test")
    def test_ps_correctors_read(self):
        pvs = va.si_pvs.ps
        for pv in pvs:
            if '-CH' in pv or '-CV' in pv:
                r1 = self.model.get_pv(pv)
                r2 = epics.caget('TestVA-' + pv)
                self.assertAlmostEqual(r1, r2, 15)

    @unittest.skip("long test")
    def test_ps_correctors_write(self):
        pvs = va.si_pvs.ps
        for pv in pvs:
            if '-CH' in pv or '-CV' in pv:
                self.model.set_pv(pv, 1.13)
                epics.caput('TestVA-' + pv, 1.13)
                r1 = self.model.get_pv(pv)
                r2 = epics.caget('TestVA-' + pv)
                #self.assertAlmostEqual(r1, r2, 15)

def si_suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSI)
    return suite


def get_suite():
    suite_list = []
    suite_list.append(si_suite())
    return unittest.TestSuite(suite_list)
