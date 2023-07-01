import pytest
from rest_framework.serializers import ValidationError

from drf_recaptcha.client import RecaptchaResponse
from drf_recaptcha.validators import ReCaptchaV2Validator, ReCaptchaV3Validator


@pytest.fixture
def _drf_recaptcha_testing(settings):
    settings.DRF_RECAPTCHA_TESTING = True


@pytest.fixture(
    params=[
        (ReCaptchaV2Validator, {}, RecaptchaResponse(is_valid=True)),
        (
            ReCaptchaV3Validator,
            {"action": "test_action", "required_score": 0.4},
            RecaptchaResponse(
                is_valid=True, extra_data={"score": 0.6, "action": "test_action"}
            ),
        ),
    ]
)
def validator_with_mocked_captcha_valid_response(request, mocker):
    validator_class = request.param[0]
    params = request.param[1]
    response = request.param[2]

    validator_with_mocked_get_response = validator_class(
        secret_key="TEST_SECRET_KEY", **params
    )
    validator_with_mocked_get_response._get_captcha_response_with_payload = mocker.Mock(
        return_value=response
    )

    return validator_with_mocked_get_response


def test_recaptcha_validator_call_success(
    validator_with_mocked_captcha_valid_response,
    mocked_serializer_field_with_request_context,
):
    try:
        validator_with_mocked_captcha_valid_response(
            "test_token", mocked_serializer_field_with_request_context
        )
    except ValidationError:
        pytest.fail("Validation is not passed")


@pytest.mark.parametrize(
    ("validator_class", "params", "response", "error"),
    [
        (
            ReCaptchaV2Validator,
            {},
            RecaptchaResponse(is_valid=False),
            "[ErrorDetail(string='Error verifying reCAPTCHA, please try again.', code='captcha_invalid')]",
        ),
        (
            ReCaptchaV2Validator,
            {},
            RecaptchaResponse(
                is_valid=True, extra_data={"score": 0.6, "action": "test_action"}
            ),
            "[ErrorDetail(string='Error verifying reCAPTCHA, please try again.', code='captcha_error')]",
        ),
        (
            ReCaptchaV3Validator,
            {"action": "test_action", "required_score": 0.4},
            RecaptchaResponse(is_valid=False),
            "[ErrorDetail(string='Error verifying reCAPTCHA, please try again.', code='captcha_invalid')]",
        ),
        (
            ReCaptchaV3Validator,
            {"action": "test_action", "required_score": 0.4},
            RecaptchaResponse(is_valid=True),
            "[ErrorDetail(string='Error verifying reCAPTCHA, please try again.', code='captcha_error')]",
        ),
        (
            ReCaptchaV3Validator,
            {"action": "test_action", "required_score": 0.4},
            RecaptchaResponse(is_valid=True, extra_data={"score": 0.3}),
            "[ErrorDetail(string='Error verifying reCAPTCHA, please try again.', code='captcha_invalid')]",
        ),
        (
            ReCaptchaV3Validator,
            {"action": "test_action", "required_score": 0.4},
            RecaptchaResponse(is_valid=True, extra_data={"score": 0.5}),
            "[ErrorDetail(string='Error verifying reCAPTCHA, please try again.', code='captcha_invalid')]",
        ),
        (
            ReCaptchaV3Validator,
            {"action": "test_action", "required_score": 0.4},
            RecaptchaResponse(
                is_valid=True, extra_data={"score": 0.5, "action": "other_action"}
            ),
            "[ErrorDetail(string='Error verifying reCAPTCHA, please try again.', code='captcha_invalid')]",
        ),
    ],
)
def test_recaptcha_validator_call_fail(
    validator_class,
    params,
    response,
    error,
    mocked_serializer_field_with_request_context,
    mocker,
):
    validator = validator_class(secret_key="TEST_SECRET_KEY", **params)
    validator._get_captcha_response_with_payload = mocker.Mock(return_value=response)

    with pytest.raises(ValidationError) as exc_info:
        validator("test_token", mocked_serializer_field_with_request_context)

    assert str(exc_info.value) == error


def test_recaptcha_validator_get_response_called_with_correct_ip(
    validator_with_mocked_captcha_valid_response,
    mocked_serializer_field_with_request_context,
):
    validator_with_mocked_captcha_valid_response(
        "test_token", mocked_serializer_field_with_request_context
    )

    validator_with_mocked_captcha_valid_response._get_captcha_response_with_payload.assert_called_once_with(
        secret_key="TEST_SECRET_KEY",
        client_ip="4.3.2.1",
        value="test_token",
    )


def test_recaptcha_validator_takes_secret_key_from_context(
    validator_with_mocked_captcha_valid_response,
    mocked_serializer_field_with_request_secret_key_context,
    mocker,
):
    validator_with_mocked_captcha_valid_response(
        "test_token", mocked_serializer_field_with_request_secret_key_context
    )

    validator_with_mocked_captcha_valid_response._get_captcha_response_with_payload.assert_called_once_with(
        secret_key="from-context",
        client_ip=mocker.ANY,
        value="test_token",
    )
