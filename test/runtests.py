#!/usr/bin/env python3

import unittest
import test_server_init
import test_server
import test_magnet
import test_excitation_curve


suite_list = []
# suite_list.append(test_server_init.get_suite())
# suite_list.append(test_server.get_suite())
suite_list.append(test_magnet.get_suite())
suite_list.append(test_excitation_curve.get_suite())

tests = unittest.TestSuite(suite_list)
unittest.TextTestRunner(verbosity=2).run(tests)
