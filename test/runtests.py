#!/usr/bin/env python3

import unittest
import test_si

suite_list = []
suite_list.append(test_si.get_suite())
#suite_list.append(test_bo.get_suite())

print()
print('!!! VA server needs to be running with prefix "TestVA-"')
print()
tests = unittest.TestSuite(suite_list)
unittest.TextTestRunner(verbosity=2).run(tests)
