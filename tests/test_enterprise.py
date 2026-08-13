import json

import pytest
from drf_recaptcha import client
from drf_recaptcha.client import RecaptchaResponse, submit_enterprise
from drf_recaptcha.fields import ReCaptchaEnterpriseField
from drf_recaptcha.validators import ReCaptchaEnterpriseValidator
from rest_framework.serializers import Serializer, ValidationError


@pytest.fixture(autouse=True)
def _enterprise_settings(settings):
    settings.DRF_RECAPTCHA_SECRET_KEY = "TEST_API_KEY"  # noqa: S105
    settings.DRF_RECAPTCHA_ENTERPRISE_PROJECT_ID = "test-project"
    settings.DRF_RECAPTCHA_ENTERPRISE_SITE_KEY = "TEST_SITE_KEY"


def mocked_enterprise_request(mocker, payload):
    response = mocker.Mock()
    response.read.return_value = json.dumps(payload).encode("utf-8")
    return mocker.patch(
        "drf_recaptcha.client.recaptcha_enterprise_request",
        return_value=response,
    )


def test_submit_enterprise_sends_assessment(mocker):
    request = mocked_enterprise_request(
        mocker,
        {
            "tokenProperties": {"valid": True, "action": "test_action"},
            "riskAnalysis": {"score": 0.9},
        },
    )

    submit_enterprise(
        recaptcha_response="test_token",
        api_key="TEST_API_KEY",
        project_id="test-project",
        site_key="TEST_SITE_KEY",
        expected_action="test_action",
        remoteip="4.3.2.1",
    )

    params, kwargs = request.call_args
    assert kwargs == {"project_id": "test-project", "api_key": "TEST_API_KEY"}
    assert json.loads(params[0].decode("utf-8")) == {
        "event": {
            "token": "test_token",
            "siteKey": "TEST_SITE_KEY",
            "expectedAction": "test_action",
            "userIpAddress": "4.3.2.1",
        },
    }


def test_submit_enterprise_omits_empty_event_values(mocker):
    request = mocked_enterprise_request(
        mocker,
        {"tokenProperties": {"valid": True}, "riskAnalysis": {"score": 0.9}},
    )

    submit_enterprise(
        recaptcha_response="test_token",
        api_key="TEST_API_KEY",
        project_id="test-project",
        site_key="TEST_SITE_KEY",
        expected_action=None,
        remoteip=None,
    )

    params, _ = request.call_args
    assert json.loads(params[0].decode("utf-8")) == {
        "event": {"token": "test_token", "siteKey": "TEST_SITE_KEY"},
    }


@pytest.mark.parametrize(
    ("payload", "is_valid", "error_codes", "score", "action"),
    [
        (
            {
                "tokenProperties": {
                    "valid": True,
                    "action": "test_action",
                    "hostname": "example.com",
                },
                "riskAnalysis": {"score": 0.9, "reasons": ["LOW_CONFIDENCE_SCORE"]},
            },
            True,
            [],
            0.9,
            "test_action",
        ),
        (
            {
                "tokenProperties": {"valid": False, "invalidReason": "EXPIRED"},
                "riskAnalysis": {},
            },
            False,
            ["EXPIRED"],
            None,
            "",
        ),
        ({}, False, ["UNKNOWN_INVALID_REASON"], None, ""),
    ],
)
def test_submit_enterprise_parses_assessment(
    payload,
    is_valid,
    error_codes,
    score,
    action,
    mocker,
):
    mocked_enterprise_request(mocker, payload)

    response = submit_enterprise(
        recaptcha_response="test_token",
        api_key="TEST_API_KEY",
        project_id="test-project",
        site_key="TEST_SITE_KEY",
        expected_action="test_action",
        remoteip="4.3.2.1",
    )

    assert response.is_valid is is_valid
    assert response.error_codes == error_codes
    assert response.extra_data["score"] == score
    assert response.extra_data["action"] == action


def test_recaptcha_enterprise_request_url(mocker, settings):
    settings.DRF_RECAPTCHA_ENTERPRISE_DOMAIN = "recaptchaenterprise.example.com"
    opener = mocker.patch("drf_recaptcha.client.build_opener")

    client.recaptcha_enterprise_request(
        b"{}",
        project_id="test-project",
        api_key="TEST API KEY",
    )

    request_object = opener.return_value.open.call_args[0][0]
    assert request_object.full_url == (
        "https://recaptchaenterprise.example.com/v1/projects/test-project"
        "/assessments?key=TEST+API+KEY"
    )
    assert request_object.get_header("Content-type") == "application/json"


@pytest.mark.parametrize(
    ("params", "response"),
    [
        (
            {"action": "test_action", "required_score": 0.4},
            RecaptchaResponse(
                is_valid=True,
                extra_data={"score": 0.6, "action": "test_action"},
            ),
        ),
        (
            {"action": None, "required_score": 0.4},
            RecaptchaResponse(is_valid=True, extra_data={"score": 0.6, "action": ""}),
        ),
    ],
)
def test_enterprise_validator_call_success(
    params,
    response,
    mocked_serializer_field_with_request_context,
    mocker,
):
    validator = ReCaptchaEnterpriseValidator(
        secret_key="TEST_API_KEY",  # noqa: S106
        project_id="test-project",
        site_key="TEST_SITE_KEY",
        **params,
    )
    validator._get_captcha_response_with_payload = mocker.Mock(return_value=response)

    try:
        validator("test_token", mocked_serializer_field_with_request_context)
    except ValidationError:
        pytest.fail("Validation is not passed")


@pytest.mark.parametrize(
    ("params", "response", "error"),
    [
        (
            {"action": "test_action", "required_score": 0.4},
            RecaptchaResponse(is_valid=False, error_codes=["EXPIRED"]),
            "[ErrorDetail(string='Error verifying reCAPTCHA, please try again.',"
            " code='captcha_invalid')]",
        ),
        (
            {"action": "test_action", "required_score": 0.4},
            RecaptchaResponse(is_valid=True, extra_data={"score": None}),
            "[ErrorDetail(string='Error verifying reCAPTCHA, please try again.',"
            " code='captcha_error')]",
        ),
        (
            {"action": "test_action", "required_score": 0.4},
            RecaptchaResponse(
                is_valid=True,
                extra_data={"score": 0.3, "action": "test_action"},
            ),
            "[ErrorDetail(string='Error verifying reCAPTCHA, please try again.',"
            " code='captcha_invalid')]",
        ),
        (
            {"action": "test_action", "required_score": 0.4},
            RecaptchaResponse(
                is_valid=True,
                extra_data={"score": 0.6, "action": "other_action"},
            ),
            "[ErrorDetail(string='Error verifying reCAPTCHA, please try again.',"
            " code='captcha_invalid')]",
        ),
    ],
)
def test_enterprise_validator_call_fail(
    params,
    response,
    error,
    mocked_serializer_field_with_request_context,
    mocker,
):
    validator = ReCaptchaEnterpriseValidator(
        secret_key="TEST_API_KEY",  # noqa: S106
        project_id="test-project",
        site_key="TEST_SITE_KEY",
        **params,
    )
    validator._get_captcha_response_with_payload = mocker.Mock(return_value=response)

    with pytest.raises(ValidationError) as exc_info:
        validator("test_token", mocked_serializer_field_with_request_context)

    assert str(exc_info.value) == error


def test_enterprise_validator_submits_assessment(mocker):
    submit = mocker.patch("drf_recaptcha.client.submit_enterprise")
    validator = ReCaptchaEnterpriseValidator(
        action="test_action",
        required_score=0.4,
        secret_key="TEST_API_KEY",  # noqa: S106
        project_id="test-project",
        site_key="TEST_SITE_KEY",
    )

    validator._submit(
        value="test_token",
        secret_key="from-context",  # noqa: S106
        client_ip="4.3.2.1",
    )

    submit.assert_called_once_with(
        recaptcha_response="test_token",
        api_key="from-context",
        project_id="test-project",
        site_key="TEST_SITE_KEY",
        expected_action="test_action",
        remoteip="4.3.2.1",
    )


@pytest.mark.parametrize(
    "params",
    [{}, {"write_only": False}, {"write_only": True}],
)
def test_enterprise_field_write_only(params):
    field = ReCaptchaEnterpriseField(action="test_action", **params)
    assert field.write_only is True


def test_enterprise_field_has_validator():
    field = ReCaptchaEnterpriseField(action="test_action")

    cnt_validators = len(field.validators)
    assert cnt_validators > 0
    assert isinstance(
        field.validators[cnt_validators - 1], ReCaptchaEnterpriseValidator
    )


# The priority itself is covered for `get_required_score` in test_fields.py,
# this only checks the field is wired to it.
@pytest.mark.parametrize(
    ("params", "from_settings", "expected"),
    [
        ({}, None, 0.5),
        ({"required_score": 0.8}, {"test_action": 0.7}, 0.7),
    ],
)
def test_enterprise_field_score_priority(params, from_settings, expected, settings):
    settings.DRF_RECAPTCHA_ACTION_V3_SCORES = from_settings

    field = ReCaptchaEnterpriseField(action="test_action", **params)
    assert field.required_score == expected


@pytest.mark.parametrize(
    "setting_name",
    [
        "DRF_RECAPTCHA_SECRET_KEY",
        "DRF_RECAPTCHA_ENTERPRISE_PROJECT_ID",
        "DRF_RECAPTCHA_ENTERPRISE_SITE_KEY",
    ],
)
def test_enterprise_field_is_built_without_settings(setting_name, settings):
    """A serializer declaring the field still imports, see test_unconfigured.py."""
    setattr(settings, setting_name, None)

    field = ReCaptchaEnterpriseField(action="test_action")

    assert isinstance(field.validators[-1], ReCaptchaEnterpriseValidator)


def test_enterprise_field_arguments_take_priority_over_settings():
    field = ReCaptchaEnterpriseField(
        action="test_action",
        secret_key="from-field-secret-key",  # noqa: S106
        project_id="from-field-project",
        site_key="from-field-site-key",
    )
    validator = field.validators[-1]

    assert validator.default_recaptcha_secret_key == "from-field-secret-key"  # noqa: S105
    assert validator.recaptcha_project_id == "from-field-project"
    assert validator.recaptcha_site_key == "from-field-site-key"


def test_enterprise_credentials_from_the_field_need_no_settings(mocker, settings):
    """The unconfigured guard reads what the field resolves, not the settings."""
    settings.DRF_RECAPTCHA_SECRET_KEY = ""
    settings.DRF_RECAPTCHA_ENTERPRISE_PROJECT_ID = ""
    settings.DRF_RECAPTCHA_ENTERPRISE_SITE_KEY = ""
    mocked_enterprise_request(
        mocker,
        {"tokenProperties": {"valid": True}, "riskAnalysis": {"score": 0.9}},
    )

    class _Serializer(Serializer):
        recaptcha = ReCaptchaEnterpriseField(
            secret_key="from-field-secret-key",  # noqa: S106
            project_id="from-field-project",
            site_key="from-field-site-key",
        )

    serializer = _Serializer(
        data={"recaptcha": "test_token"},
        context={"request": mocker.Mock(META={"HTTP_X_FORWARDED_FOR": "4.3.2.1"})},
    )

    assert serializer.is_valid() is True


@pytest.mark.parametrize(
    ("field_params", "field_context", "expected_api_key"),
    [
        ({}, {}, "TEST_API_KEY"),
        ({"secret_key": "from-field-secret-key"}, {}, "from-field-secret-key"),
        ({}, {"recaptcha_secret_key": "from-context"}, "from-context"),
        (
            {"secret_key": "from-field-secret-key"},
            {"recaptcha_secret_key": "from-context"},
            "from-context",
        ),
    ],
)
def test_enterprise_api_key_priority(
    field_params,
    field_context,
    expected_api_key,
    mocker,
):
    validator = mocker.patch(
        "drf_recaptcha.fields.ReCaptchaEnterpriseValidator"
        "._get_captcha_response_with_payload",
    )
    field_context["request"] = mocker.Mock(META={"HTTP_X_FORWARDED_FOR": "4.3.2.1"})

    class _Serializer(Serializer):
        recaptcha = ReCaptchaEnterpriseField(
            action="test_action",
            **field_params,
            required=True,
        )

    serializer = _Serializer(data={"recaptcha": "foo"}, context=field_context)
    serializer.is_valid(raise_exception=False)

    validator.assert_called_once_with(
        value=mocker.ANY,
        secret_key=expected_api_key,
        client_ip=mocker.ANY,
    )


def test_enterprise_field_score(mocker):
    mocker.patch(
        "drf_recaptcha.fields.ReCaptchaEnterpriseValidator"
        "._get_captcha_response_with_payload",
        return_value=RecaptchaResponse(
            is_valid=True,
            extra_data={"score": 0.6, "action": "test_action"},
        ),
    )

    class _Serializer(Serializer):
        recaptcha = ReCaptchaEnterpriseField(action="test_action")

    serializer = _Serializer(
        data={"recaptcha": "test_token"},
        context={"request": mocker.Mock(META={"HTTP_X_FORWARDED_FOR": "4.3.2.1"})},
    )

    assert serializer.is_valid() is True
    assert serializer.fields["recaptcha"].score == 0.6


@pytest.mark.parametrize(
    ("assessment", "is_valid"),
    [
        (
            {
                "tokenProperties": {"valid": True, "action": "test_action"},
                "riskAnalysis": {"score": 0.9},
            },
            True,
        ),
        (
            {
                "tokenProperties": {"valid": False, "invalidReason": "EXPIRED"},
                "riskAnalysis": {},
            },
            False,
        ),
    ],
)
def test_enterprise_serializer(assessment, is_valid, mocker):
    opener = mocker.patch("drf_recaptcha.client.build_opener")
    opener.return_value.open.return_value.read.return_value = json.dumps(
        assessment,
    ).encode("utf-8")

    class _Serializer(Serializer):
        recaptcha = ReCaptchaEnterpriseField(action="test_action")

    serializer = _Serializer(
        data={"recaptcha": "test_token"},
        context={"request": mocker.Mock(META={"HTTP_X_FORWARDED_FOR": "4.3.2.1"})},
    )

    assert serializer.is_valid() is is_valid

    request_object = opener.return_value.open.call_args[0][0]
    assert request_object.full_url == (
        "https://recaptchaenterprise.googleapis.com/v1/projects/test-project"
        "/assessments?key=TEST_API_KEY"
    )
    assert json.loads(request_object.data.decode("utf-8")) == {
        "event": {
            "token": "test_token",
            "siteKey": "TEST_SITE_KEY",
            "expectedAction": "test_action",
            "userIpAddress": "4.3.2.1",
        },
    }


def test_enterprise_field_score_not_validated():
    field = ReCaptchaEnterpriseField(action="test_action")

    with pytest.raises(AssertionError) as exc_info:
        _ = field.score

    assert str(exc_info.value) == (
        "You must call the serializer `.is_valid()` method before "
        "attempting to access the `.score` property of this field."
    )
