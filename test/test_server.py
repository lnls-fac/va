
import unittest
import multiprocessing
import time
import os
import signal
import numpy
import va
import epics


INIT_WAIT = 2.0


server_process = multiprocessing.Process(
    target=va.server.run,
    kwargs={'prefix': 'TEST-VA-'},
)


def setUpModule():
    global server_process
    server_process.start()
    print('\nWaiting %d seconds for server initialisation...\n' % INIT_WAIT)
    time.sleep(INIT_WAIT)


def tearDownModule():
    global server_process
    os.kill(server_process.pid, signal.SIGINT)
    server_process.join(1.0)


class TestServer(unittest.TestCase):

    def test_server(self):
        pass


def server_suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestServer)
    return suite


def get_suite():
    suite_list = []
    suite_list.append(server_suite())
    return unittest.TestSuite(suite_list)
