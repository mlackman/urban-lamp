from __future__ import annotations
from typing import List, Sequence, Optional, Mapping, Any, Dict
from abc import ABC, abstractmethod
import copy
import json

import requests
import requests_mock  # type: ignore

# Types
Headers = Dict[str, str]

_ctx: Context = None


class Context:
    def __init__(self):
        self._nullify_requests_mocks()

    def start(self):
        if self._implicit_requests_mock:
            self._implicit_requests_mock.stop()

        self._nullify_requests_mocks()
        ExpectedRequests.reset()

    def _nullify_requests_mocks(self):
        self._explicit_requests_mock = None
        self._implicit_requests_mock = None

    def init_request_mock(self, m: Optional[requests_mock.Mocker] = None) -> requests_mock.Mocker:
        initializing_request_mock_first_time = self._explicit_requests_mock is None and self._implicit_requests_mock is None

        if initializing_request_mock_first_time:
            implicit_requests_mock_usage = not m
            if implicit_requests_mock_usage:
                self._implicit_requests_mock = requests_mock.Mocker()
                self._implicit_requests_mock.start()
                mocker = self._implicit_requests_mock
            else:
                self._explicit_requests_mock = m
                mocker = self._explicit_requests_mock

        mocker = self._implicit_requests_mock or self._explicit_requests_mock

        started_implicit_requests_mock_usage = self._implicit_requests_mock is not None
        if m is not None and started_implicit_requests_mock_usage:
            raise AssertionError("Implicit requests_mock use started. Add or remove requests_mock.Mocker from/to all 'expect' calls")

        started_explicit_requests_mock_usage = self._explicit_requests_mock is not None
        if m is None and started_explicit_requests_mock_usage:
            raise AssertionError("Explicit requests_mock usage started. Add or remove requests_mock.Mocker from/to all 'expect' calls")
        return mocker


# TODO: Make normal class
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

    def __init__(self, method: str, url: str, body: Optional[RequestBody] = None, headers: Optional[Headers] = None):
        self.method = method
        self.url = url
        self.requested = False
        self.headers = headers or {}
        self.body = body or NullRequestBody()

    def register(self, builder: RequestUriBuilder):
        builder.match_request(self.method, self.url, request_headers=self.headers, additional_matcher=self._match_request)

    def _match_request(self, request: requests.Request):
        self.requested = self.body.match(request)
        return self.requested

    def __str__(self) -> str:
        description = f'{self.method} {self.url}'

        if self.headers:
            description = description + f', headers: {self.headers}'

        body_description = str(self.body)
        if body_description:
            description = description + f', {body_description}'

        return description


class RequestBody(ABC):

    @abstractmethod
    def match(self, request: requests.Request) -> bool:
        pass

    @abstractmethod
    def __str__(self) -> str:
        pass


class NullRequestBody(RequestBody):

    def match(self, *args, **kwargs) -> bool:
        return True

    def __str__(self):
        return ''


class JSONRequestBody(RequestBody):

    def __init__(self, body: Dict[str, Any]):
        self.body = body

    def match(self, request: requests.Request) -> bool:
        try:
            received_json = request.json()
        except json.JSONDecodeError:
            received_json = None
        return received_json == self.body

    def __str__(self):
        return f'json: {self.body}'


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
        r = copy.deepcopy(request)
        r.url = f'{self._base_url}{request.url}'
        r.register(self._builder)
        ExpectedRequests.add(r)
        return ResponseDSL(self._builder)


def expect(base_url: str, m: Optional[requests_mock.Mocker] = None) -> RequestDSL:
    global _ctx
    mocker = _ctx.init_request_mock(m)
    return RequestDSL(base_url, RequestUriBuilder(mocker))


def verify():
    """
    Verify all expected requests were made.
    """
    requests = ExpectedRequests.get_requests_not_made()
    assert requests == [], str(VerifyErrorMessage(requests))


def start():
    """
    Inits service mock, can be called between tests
    """
    global _ctx
    _ctx = Context()
    _ctx.start()
