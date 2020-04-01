import requests_mock  # type: ignore
import pytest  # type: ignore

from .context import servicemock as sm


def test_when_service_is_not_called_informative_exception_is_raised(requests_mock: requests_mock.Mocker):
    sm.expect(sm.Request(requests_mock, 'GET', '/v1/status-check')).responds(sm.Ok())

    with pytest.raises(AssertionError) as e:
        sm.verify()
    assert "Expected request 'GET /v1/status-check' but never received the request" in str(e.value)
