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


def test_when_request_is_made_to_not_expected_end_point_informative_exception_is_raised(servicemock):
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
