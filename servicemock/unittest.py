import unittest

import servicemock as sm


class ServiceMockTestCase(unittest.TestCase):
    """
    Base class for unittest based testcases.

    servicemock.start() and servicemock.verify() calls are called automatically
    """

    def run(self, *args, **kwargs):
        sm.start()
        result = super().run(*args, **kwargs)
        sm.verify()
        return result
