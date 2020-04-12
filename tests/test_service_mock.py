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
            "Received unexpected request 'GET http://service/user, "
            "headers: {'User-Agent': 'python-requests/2.23.0', 'Accept-Encoding': 'gzip, deflate', 'Accept': '*/*', 'Connection': 'keep-alive'}'.\n"
            "Expected requests are:\n"
            "  - GET http://my-service.com/v1/status-check"
        )
        assert expected_error_description == str(e.value)


def test_when_expected_request_is_made_then_verify_does_not_raise_exception(servicemock: Any):
    with sm.Mocker() as m:
        sm.expect('http://my-service.com', m).to_receive(sm.Request('GET', '/v1/status-check'))

        requests.get('http://my-service.com/v1/status-check')

        sm.verify()  # no exceptions should be raised


def test_when_header_is_not_the_expected_then_exception_is_raised(servicemock: Any):
    with sm.Mocker() as m:
        sm.expect('http://my-service.com', m).to_receive(sm.Request('GET', '/v1/status-check', headers={'x-token': 'deadbeef'}))

        with pytest.raises(Exception) as e:
            requests.get('http://my-service.com/v1/status-check', headers={'x-token': 'cafebabe'})

        expected_error_description = (
            "Received unexpected request 'GET http://my-service.com/v1/status-check, "
            "headers: {'User-Agent': 'python-requests/2.23.0', 'Accept-Encoding': 'gzip, deflate', "
            "'Accept': '*/*', 'Connection': 'keep-alive', 'x-token': 'cafebabe'}'.\n"
            "Expected requests are:\n"
            "  - GET http://my-service.com/v1/status-check, headers: {'x-token': 'deadbeef'}"
        )
        assert expected_error_description == str(e.value)


def test_when_header_matches_then_no_exception_is_raised(servicemock: Any):
    with sm.Mocker() as m:
        sm.expect('http://my-service.com', m).to_receive(sm.Request('GET', '/v1/status-check', headers={'x-token': 'deadbeef'}))

        requests.get('http://my-service.com/v1/status-check', headers={'x-token': 'deadbeef'})

        sm.verify()  # no exceptions should be raised


def test_when_expected_request_body_does_not_match_then_exception_is_raised(servicemock: Any):
    with sm.Mocker() as m:
        sm.expect('http://my-service.com', m).to_receive(sm.Request('POST', '/v1/users', body=sm.JSONRequestBody({'username': 'smithy'})))

        with pytest.raises(Exception) as e:
            requests.post('http://my-service.com/v1/users', json={'first_name': 'Mike'})

        expected_error_description = (
            "Received unexpected request 'POST http://my-service.com/v1/users, "
            "headers: {'User-Agent': 'python-requests/2.23.0', 'Accept-Encoding': 'gzip, deflate', "
            "'Accept': '*/*', 'Connection': 'keep-alive', 'Content-Length': '22', 'Content-Type': 'application/json'}', "
            "json: {'first_name': 'Mike'}.\n"
            "Expected requests are:\n"
            "  - POST http://my-service.com/v1/users, json: {'username': 'smithy'}"
        )
        assert expected_error_description == str(e.value)


def test_when_body_matches_then_exception_is_not_raised(servicemock: Any):
    with sm.Mocker() as m:
        sm.expect('http://my-service.com', m).to_receive(sm.Request('POST', '/v1/users', body=sm.JSONRequestBody({'name': 'john'})))

        requests.post('http://my-service.com/v1/users', json={'name': 'john'})

        sm.verify()  # no exceptions should be raised


def test_when_request_body_is_form_but_expecting_json_then_exception_is_raised(servicemock: Any):
    with sm.Mocker() as m:
        sm.expect('http://my-service.com', m).to_receive(sm.Request('POST', '/v1/users', body=sm.JSONRequestBody({'username': 'smithy'})))

        with pytest.raises(Exception) as e:
            requests.post('http://my-service.com/v1/users', data={'first_name': 'smithy'})

        expected_error_description = (
            "Received unexpected request 'POST http://my-service.com/v1/users, "
            "headers: {'User-Agent': 'python-requests/2.23.0', 'Accept-Encoding': 'gzip, deflate', "
            "'Accept': '*/*', 'Connection': 'keep-alive', 'Content-Length': '17', 'Content-Type': 'application/x-www-form-urlencoded'}', "
            "text: first_name=smithy.\n"
            "Expected requests are:\n"
            "  - POST http://my-service.com/v1/users, json: {'username': 'smithy'}"
        )
        assert expected_error_description == str(e.value)


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


def test_cookies_can_be_set_from_body_and_actual_response(servicemock: Any):
    with sm.Mocker() as m:
        (sm.expect('http://my-service.com', m)
            .to_receive(sm.Request('GET', '/v1/status-check'))
            .and_responds(sm.HTTP200Ok(
                sm.JSON({'status': 'ok'}, cookies=(sm.Cookie('session', 'deadbeef', path='/v1/status-check'),)),
                cookies=(sm.Cookie('value', '5'),))
            ))

        res = requests.get('http://my-service.com/v1/status-check')
        assert {'value': '5', 'session': 'deadbeef'} == res.cookies.get_dict()
