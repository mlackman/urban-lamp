from __future__ import annotations
from typing import List, Sequence, Optional, Mapping, Any, Callable
import json
import functools

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

    def __init__(self, http_status: str, body: Optional[str] = None):
        code, self.http_reason = http_status.split(' ', 1)
        self.http_code = int(code)
        self.body = body


class HTTP200Ok(Response):

    def __init__(self):
        super().__init__('200 OK')


class JSON(Response):

    def __init__(self, body: Mapping[str, Any], http_status: Optional[str] = None):
        status = http_status or '200 OK'
        super().__init__(status, json.dumps(body))


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

    def __init__(self, register_uri: Callable):
        self._register_uri = register_uri
        self._response = self.default_response
        self._register()

    def and_responds(self, response: Response):
        self._response = response
        self._register()

    def _register(self):
        self._register_uri(
            status_code=self._response.http_code,
            reason=self._response.http_reason,
            text=self._response.body
        )


class RequestDSL:

    def __init__(self, base_url: str, m: requests_mock.Mocker):
        self._base_url = base_url
        self._m = m

    def to_receive(self, request: Request) -> ResponseDSL:
        r = Request(request.method, f'{self._base_url}{request.url}')
        register_uri = functools.partial(self._m.register_uri, request.method, request.url, additional_matcher=r.match_request)
        ExpectedRequests.add(r)
        return ResponseDSL(register_uri)


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
