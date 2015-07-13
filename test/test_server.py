
import unittest
import os
import signal
import multiprocessing
import numpy
import va
import epics


server_process = multiprocessing.Process(
    target=va.server.run,
    kwargs={'prefix': 'TEST-VA-'},
)


def setUpModule():
    print('inside setUpModule')
    global server_process
    server_process.start()


def tearDownModule():
    print('inside tearDownModule')
    global server_process
    va.server.stop_event.set()
    server_process.join()


class TestServer(unittest.TestCase):

    # def setUp(self):
    #     self.server_process = multiprocessing.Process(
    #         target=va.server.run,
    #         kwargs={'prefix': 'TEST-VA-'},
    #     )
    #     self.server_process.start()
    #
    # def tearDown(self):
    #     va.server.stop_event.set()

    def test_server(self):
        pass


def server_suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestServer)
    return suite


def get_suite():
    suite_list = []
    suite_list.append(server_suite())
    return unittest.TestSuite(suite_list)
