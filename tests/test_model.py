
import va.model
import unittest


class TestSiModel(unittest.TestCase):

    def setUp(self):
        self.model = va.model.SiModel()

    def test_attributes(self):
        self.assertTrue(True)


def si_model_suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSiModel)
    return suite


def get_suite():
    suite_list = []
    suite_list.append(si_model_suite())
    return unittest.TestSuite(suite_list)
