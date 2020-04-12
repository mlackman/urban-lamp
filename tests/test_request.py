from .context import Request, JSONRequestBody


def test_converting_to_string_when_only_method_and_url():
    assert str(Request('GET', '/v1/users')) == 'GET /v1/users'


def test_converting_to_string_with_headers():
    r = Request('GET', '/v1/users', headers={'x-token': 'some', 'accept': 'application/json'})
    assert str(r) == "GET /v1/users, headers: {'x-token': 'some', 'accept': 'application/json'}"


def test_converting_to_string_with_json_body():
    r = Request('GET', '/v1/users', body=JSONRequestBody({'name': 'john'}))
    assert str(r) == "GET /v1/users, json: {'name': 'john'}"
