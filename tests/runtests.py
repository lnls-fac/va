#!/usr/bin/env python3

import unittest
import test_model


suite_list = []
suite_list.append(test_model.get_suite())

tests = unittest.TestSuite(suite_list)
unittest.TextTestRunner(verbosity=2).run(tests)
