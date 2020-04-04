from __future__ import annotations
from typing import List, Sequence, Optional
import requests
import requests_mock  # type: ignore


class ExpectedRequests:
    _expected_requests: List[Request] = []

    @classmethod
    def add(cls, request: Request):
        cls._expected_requests.append(request)

    @classmethod
    def get_requests_not_made(cls) -> List[Request]:
        return [r for r in cls._expected_requests if r.requested is False]

    @classmethod
    def reset(cls):
        cls._expected_requests = []


class Response:

    def __init__(self, http_status: str):
        code, self.http_reason = http_status.split(' ', 1)
        self.http_code = int(code)


class HTTP200Ok(Response):

    def __init__(self):
        super().__init__('200 OK')


class Request:
    """
    Request, which is expected to receive
    """

    def __init__(self, method: str, url: str):
        self.method = method
        self.url = url
        self.requested = False

    def match_request(self, request: requests.Request):
        self.requested = True
        return self.requested

    def __str__(self) -> str:
        return f'{self.method} {self.url}'


class VerifyErrorMessage:

    def __init__(self, requests: Sequence[Request]):
        self._requests = requests

    def __str__(self) -> str:
        if len(self._requests) == 1:
            return f"Expected request '{self._requests[0]}' was not made."
        else:
            msg = "Following expected requests were not made:\n  - "
            msg += "\n  - ".join([str(r) for r in self._requests])
            return msg


class ResponseDSL:
    default_response: Response = HTTP200Ok()

    def __init__(self, m: requests_mock.Mocker, request: Request):
        self._m = m
        self._request = request
        self._response = self.default_response
        self._register_uri()

    def and_responds(self, response: Response):
        pass

    def _register_uri(self):
        self._m.register_uri(
            self._request.method,
            self._request.url,
            additional_matcher=self._request.match_request,
            status_code=self._response.http_code,
            reason=self._response.http_reason
        )


class RequestDSL:

    def __init__(self, base_url: str, m: requests_mock.Mocker):
        self._base_url = base_url
        self._m = m

    def to_receive(self, request: Request) -> ResponseDSL:
        r = Request(request.method, f'{self._base_url}{request.url}')
        ExpectedRequests.add(r)
        return ResponseDSL(self._m, r)


def expect(base_url: str, m: Optional[requests_mock.Mocker] = None) -> RequestDSL:
    return RequestDSL(base_url, m)


def verify():
    """
    Verify all expected requests were made.
    """
    requests = ExpectedRequests.get_requests_not_made()
    assert requests == [], str(VerifyErrorMessage(requests))


def clean():
    """
    Clears all expectations.
    Should be called between tests
    """
    ExpectedRequests.reset()
