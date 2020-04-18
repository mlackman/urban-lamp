from servicemock import Request
from servicemock.servicemock import VerifyErrorMessage


def create_request() -> Request:
    return Request('method', 'someurl')


def test_error_message_when_one_request():
    assert "Expected request 'method someurl' was not made." == str(VerifyErrorMessage([create_request()]))


def test_error_message_when_multiple_requests():
    expected_msg = (
        "Following expected requests were not made:\n"
        "  - method someurl\n"
        "  - method someurl"
    )
    assert expected_msg == str(VerifyErrorMessage([create_request(), create_request()]))
