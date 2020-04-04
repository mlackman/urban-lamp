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
        self.http_code, self.http_reason = http_status.split(' ', 1)


class Ok(Response):

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

    def _match_request(self, request: requests.Request):
        self.requested = True

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

    def __init__(self, request: Request):
        self._request = request

    def and_responds(self, response: Response):
        ExpectedRequests.add(self._request)


class RequestDSL:

    def __init__(self, base_url: str, m: requests_mock.Mocker):
        self._base_url = base_url
        self._m = m

    def to_receive(self, request: Request) -> ResponseDSL:
        r = Request(request.method, f'{self._base_url}{request.url}')
        ExpectedRequests.add(r)
        return ResponseDSL(r)


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
