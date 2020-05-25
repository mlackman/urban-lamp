# Servicemock
[![Build Status](https://travis-ci.com/mlackman/urban-lamp.svg?branch=master)](https://travis-ci.com/mlackman/urban-lamp)

## Unittest example

```
import unittest
import servicemock as sm


class TestService(sm.ServiceMockTestCase):

    def test(self):
        # If the expected request is not made the test will fail
        sm.expect('http://service.com').to_receive(sm.Request('GET', '/v1/users')).and_responds(sm.HTTP200Ok(sm.JSON({'status': 'ok'})))
```
