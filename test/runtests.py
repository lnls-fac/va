#!/usr/bin/env python3

import unittest
import test_server


suite_list = []
suite_list.append(test_server.get_suite())

tests = unittest.TestSuite(suite_list)
unittest.TextTestRunner(verbosity=2).run(tests)
