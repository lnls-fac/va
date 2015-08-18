
import unittest
import multiprocessing
import time
import os
import signal
import va


INIT_WAIT = 5.0


class TestServerInit(unittest.TestCase):

    @unittest.skip('long test')
    @unittest.removeHandler
    def test_server_initialisation_and_shutdown(self):
        server_process = multiprocessing.Process(
            target=va.server.run,
            kwargs={'prefix': 'TEST-VA-'},
        )

        server_process.start()
        print('Waiting %d seconds for server initialisation...' % INIT_WAIT)
        time.sleep(INIT_WAIT)
        self.assertTrue(server_process.is_alive())
        os.kill(server_process.pid, signal.SIGINT)
        server_process.join(1.0)
        self.assertFalse(server_process.is_alive())


def server_init_suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestServerInit)
    return suite


def get_suite():
    suite_list = []
    suite_list.append(server_init_suite())
    return unittest.TestSuite(suite_list)
