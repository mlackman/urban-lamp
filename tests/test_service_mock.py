from typing import Any

import requests
import requests_mock  # type: ignore
import pytest  # type: ignore

from .context import servicemock as sm


@pytest.fixture(scope="function")
def servicemock():
    sm.clean()
    return sm


def test_when_service_is_not_called_informative_exception_is_raised(requests_mock: requests_mock.Mocker, servicemock):
    sm.expect('http://my-service.com', requests_mock).to_receive(sm.Request('GET', '/v1/status-check'))

    with pytest.raises(AssertionError) as e:
        sm.verify()
    assert "Expected request 'GET http://my-service.com/v1/status-check' was not made." in str(e.value)


def test_when_request_is_made_to_not_expected_end_point_informative_exception_is_raised(servicemock: Any):
    with requests_mock.Mocker(adapter=sm.Adapter()) as m:
        sm.expect('http://my-service.com', m).to_receive(sm.Request('GET', '/v1/status-check'))

        with pytest.raises(Exception) as e:
            requests.get('http://service/user')

        expected_error_description = (
            "Received unexpected request 'GET http://service/user'.\n"
            "Expected requests are:\n"
            "  - GET http://my-service.com/v1/status-check"
        )
        assert expected_error_description == str(e.value)


def test_when_expected_request_is_made_then_verify_does_not_raise_exception(servicemock: Any):
    with sm.Mocker() as m:
        sm.expect('http://my-service.com', m).to_receive(sm.Request('GET', '/v1/status-check'))

        requests.get('http://my-service.com/v1/status-check')

        sm.verify()  # no exceptions should be raised


def test_default_response(servicemock: Any):
    with sm.Mocker() as m:
        sm.expect('http://my-service.com', m).to_receive(sm.Request('GET', '/v1/status-check'))

        res = requests.get('http://my-service.com/v1/status-check')
        assert res.status_code == 200
        assert res.reason == 'OK'


def test_given_response_is_returned(servicemock: Any):
    with sm.Mocker() as m:
        (sm.expect('http://my-service.com', m)
            .to_receive(sm.Request('GET', '/v1/status-check'))
            .and_responds(sm.HTTP200Ok(sm.JSON({'status': 'ok'}))))

        res = requests.get('http://my-service.com/v1/status-check')
        assert res.json() == {"status": "ok"}


def test_headers_can_be_set_from_body_and_actual_response(servicemock: Any):
    with sm.Mocker() as m:
        (sm.expect('http://my-service.com', m)
            .to_receive(sm.Request('GET', '/v1/status-check'))
            .and_responds(sm.HTTP200Ok(
                sm.JSON({'status': 'ok'}, headers={'Content-Type': 'application/json'}),
                headers={'Cf-Ipcountry': 'US'})
            ))

        res = requests.get('http://my-service.com/v1/status-check')
        assert res.headers == {'Content-Type': 'application/json', 'Cf-Ipcountry': 'US'}
