import unittest
import logging
from helpers.decorators import log_method_call, catch_exceptions

class TestDecorators(unittest.TestCase):
    def test_log_method_call_output(self):
        @log_method_call
        def dummy(a, b):
            return a + b
        self.assertEqual(dummy(1, 2), 3)

    def test_catch_exceptions(self):
        @catch_exceptions
        def fail_func():
            raise ValueError("Boom")
        self.assertIsNone(fail_func())  # catch_exceptions returnează None la excepții