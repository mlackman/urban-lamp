import unittest

import servicemock as sm


class TestUnittestIntegration(unittest.TestCase):

    def test_unittest_inheriting_from_ServiceMockTestCase_does_not_need_to_call_verify_or_init(self):
        class TestAccountService(sm.ServiceMockTestCase):

            def test(self):
                sm.expect('http://service.com').to_receive(sm.Request('GET', '/v1/users'))

        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(TestAccountService)

        result = unittest.TestResult()
        with self.assertRaises(AssertionError):
            suite.run(result)
