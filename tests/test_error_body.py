"""What a refused verification request leaves behind for whoever has to fix it.

Google answers a request it will not verify with an error document, and the
status line on its own rarely says which fault it was. Enterprise in particular
answers both a wrong project and an API key belonging to another project with
`400 Bad Request`, and names the difference only in the body.
"""

import io
from email.message import Message
from urllib.error import HTTPError

import pytest
from drf_recaptcha.validators import ReCaptchaEnterpriseValidator, read_error_body
from rest_framework.serializers import ValidationError

RESOURCE_PROJECT_INVALID = (
    b'{"error": {"code": 400, "message": "Invalid resource field value in the'
    b' request.", "status": "INVALID_ARGUMENT", "details": [{"reason":'
    b' "RESOURCE_PROJECT_INVALID"}]}}'
)


class UnreadableBody(io.BytesIO):
    def read(self, *_args, **_kwargs):
        msg = "connection reset"
        raise OSError(msg)


def build_http_error(body) -> HTTPError:
    return HTTPError(
        url="https://recaptchaenterprise.googleapis.com/v1/projects/p/assessments",
        code=400,
        msg="Bad Request",
        hdrs=Message(),
        fp=body,
    )


def test_the_reason_reaches_the_log_with_the_rejection(
    mocked_serializer_field_with_request_context,
    mocker,
    caplog,
):
    mocker.patch(
        "drf_recaptcha.client.submit_enterprise",
        side_effect=build_http_error(io.BytesIO(RESOURCE_PROJECT_INVALID)),
    )
    validator = ReCaptchaEnterpriseValidator(
        action="test_action",
        required_score=0.5,
        secret_key="TEST_API_KEY",  # noqa: S106
        project_id="test-project",
        site_key="TEST_SITE_KEY",
    )

    with pytest.raises(ValidationError) as exc_info:
        validator("test_token", mocked_serializer_field_with_request_context)

    # The submitter is told no more than before: whose configuration is wrong is
    # none of their business, and a retry may well work.
    assert exc_info.value.detail[0].code == "captcha_error"
    assert "RESOURCE_PROJECT_INVALID" in caplog.text


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        (io.BytesIO(RESOURCE_PROJECT_INVALID), "RESOURCE_PROJECT_INVALID"),
        (io.BytesIO(b""), "<empty>"),
        # A body that cannot be read is not worth an exception of its own: the
        # caller is already on its way to rejecting the submission.
        (UnreadableBody(), "<unreadable>"),
        (io.BytesIO(b"\xff not utf-8"), "not utf-8"),
    ],
)
def test_a_body_is_described_whatever_it_holds(body, expected):
    assert expected in read_error_body(build_http_error(body))


def test_a_long_body_is_bounded():
    error = build_http_error(io.BytesIO(b"x" * 10_000))

    assert len(read_error_body(error)) == 2000
