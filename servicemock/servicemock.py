from __future__ import annotations
from typing import List, Sequence, Optional, Mapping, Any, Dict
from abc import ABC, abstractmethod

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


class RequestUriBuilder:

    def __init__(self, m: requests_mock.Mocker):
        self._m = m
        self._headers: Dict[str, str] = {}
        self._cookiejar = requests_mock.CookieJar()

    def match_request(self, method: str, url: Any, **kwargs):
        self._method = method
        self._url = url
        self._kwargs = kwargs

    def set_response(self, headers: Optional[Dict[str, str]] = None, cookies: Optional[Sequence[Cookie]] = None,
                     **kwargs):
        if headers:
            self._headers.update(**headers)
        if cookies:
            for cookie in cookies:
                cookie.add_to(self._cookiejar)
        self._kwargs.update(**kwargs)

    def register(self):
        self._m.register_uri(self._method, self._url, headers=self._headers, cookies=self._cookiejar, **self._kwargs)


class Response:

    def __init__(self, http_status: str,
                 body: Optional[ResponseBody] = None, headers: Optional[Dict[str, str]] = None,
                 cookies: Optional[Sequence[Cookie]] = None):
        code, self.http_reason = http_status.split(' ', 1)
        self.http_code = int(code)
        self.body = body
        self.headers = headers
        self.cookies = cookies

    def register(self, builder: RequestUriBuilder):
        builder.set_response(
            status_code=self.http_code,
            reason=self.http_reason,
            headers=self.headers,
            cookies=self.cookies,
        )
        if self.body:
            self.body.register(builder)


class HTTP200Ok(Response):

    def __init__(self, *args, **kwargs):
        super().__init__('200 OK', *args, **kwargs)


class ResponseBody(ABC):

    @abstractmethod
    def register(self, builder: RequestUriBuilder):
        pass


class JSON(ResponseBody):

    def __init__(self, body: Mapping[str, Any], headers: Optional[Dict[str, str]] = None,
                 cookies: Optional[Sequence[Cookie]] = None):
        self._body = body
        self._headers = headers
        self._cookies = cookies

    def register(self, builder: RequestUriBuilder):
        builder.set_response(json=self._body, headers=self._headers, cookies=self._cookies)


class Cookie:

    def __init__(self, name: str, value: str, **kwargs):
        self._name = name
        self._value = value
        self._kwargs = kwargs

    def add_to(self, cookiejar: requests_mock.CookieJar):
        cookiejar.set(self._name, self._value, **self._kwargs)


class Request:
    """
    Request, which is expected to receive
    """

    def __init__(self, method: str, url: str):
        self.method = method
        self.url = url
        self.requested = False

    def register(self, builder: RequestUriBuilder):
        builder.match_request(self.method, self.url, additional_matcher=self._match_request)

    def _match_request(self, request: requests.Request):
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

    def __init__(self, builder: RequestUriBuilder):
        self._builder = builder
        self._response = self.default_response
        self._register()

    def and_responds(self, response: Response):
        self._response = response
        self._register()

    def _register(self):
        self._response.register(self._builder)
        self._builder.register()


class RequestDSL:

    def __init__(self, base_url: str, builder: RequestUriBuilder):
        self._base_url = base_url
        self._builder = builder

    def to_receive(self, request: Request) -> ResponseDSL:
        r = Request(request.method, f'{self._base_url}{request.url}')
        r.register(self._builder)
        ExpectedRequests.add(r)
        return ResponseDSL(self._builder)


def expect(base_url: str, m: Optional[requests_mock.Mocker] = None) -> RequestDSL:
    # TODO: if requests_mock not provide make add it to the Context objec (where ExpectedRequests should be also)
    return RequestDSL(base_url, RequestUriBuilder(m))


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
