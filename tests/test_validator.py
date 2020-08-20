from unittest import mock

import pytest
from rest_framework.serializers import ValidationError

from drf_recaptcha.client import RecaptchaResponse
from drf_recaptcha.validators import ReCaptchaV2Validator, ReCaptchaV3Validator


@pytest.mark.parametrize(
    ("validator_class", "params"),
    [
        (ReCaptchaV2Validator, {}),
        (ReCaptchaV3Validator, {"action": "test_action", "required_score": 0.4}),
    ],
)
def test_recaptcha_validator_get_response_success(validator_class, params):
    validator = validator_class(secret_key="TEST_SECRET_KEY", **params)
    assert isinstance(validator.get_response("test_token"), RecaptchaResponse)


@pytest.mark.parametrize(
    ("validator_class", "params"),
    [
        (ReCaptchaV2Validator, {}),
        (ReCaptchaV3Validator, {"action": "test_action", "required_score": 0.4}),
    ],
)
def test_recaptcha_validator_get_response_fail(validator_class, params):
    validator = validator_class(secret_key="TEST_SECRET_KEY", **params)
    assert isinstance(validator.get_response("test_token"), RecaptchaResponse)


@pytest.mark.parametrize(
    ("validator_class", "params", "response"),
    [
        (ReCaptchaV2Validator, {}, RecaptchaResponse(is_valid=True)),
        (
            ReCaptchaV3Validator,
            {"action": "test_action", "required_score": 0.4},
            RecaptchaResponse(
                is_valid=True, extra_data={"score": 0.6, "action": "test_action"}
            ),
        ),
    ],
)
def test_recaptcha_validator_call_success(validator_class, params, response):
    validator = validator_class(secret_key="TEST_SECRET_KEY", **params)
    validator.get_response = mock.Mock(return_value=response)
    try:
        validator("test_token")
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
def test_recaptcha_validator_call_fail(validator_class, params, response, error):
    validator = validator_class(secret_key="TEST_SECRET_KEY", **params)
    validator.get_response = mock.Mock(return_value=response)

    with pytest.raises(ValidationError) as exc_info:
        validator("test_token")

    assert str(exc_info.value) == error


@pytest.mark.parametrize(
    ("validator_class", "params"),
    [
        (ReCaptchaV2Validator, {}),
        (ReCaptchaV3Validator, {"action": "test_action", "required_score": 0.4}),
    ],
)
def test_recaptcha_validator_set_context(validator_class, params, settings):
    settings.DRF_RECAPTCHA_TESTING = True

    validator = validator_class(secret_key="TEST_SECRET_KEY", **params)

    assert validator.recaptcha_client_ip == ""

    serializer_field = mock.Mock(
        context={"request": mock.Mock(META={"HTTP_X_FORWARDED_FOR": "4.3.2.1"})}
    )

    validator("test_token", serializer_field)

    assert validator.recaptcha_client_ip == "4.3.2.1"
