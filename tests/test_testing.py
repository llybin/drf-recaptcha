import pytest
from django.test import override_settings
from rest_framework.exceptions import ValidationError

from drf_recaptcha.validators import ReCaptchaV2Validator, ReCaptchaV3Validator


@pytest.mark.parametrize(
    ("validator_class", "params"),
    [
        (ReCaptchaV2Validator, {}),
        (ReCaptchaV3Validator, {"action": "test_action", "required_score": 0.4}),
    ],
)
@override_settings(DRF_RECAPTCHA_TESTING=True)
def test_recaptcha_validator_testing_success(validator_class, params):
    validator = validator_class(secret_key="TEST_SECRET_KEY", **params)
    try:
        validator("test_token")
    except ValidationError:
        pytest.fail("Validation is not passed")


@pytest.mark.parametrize(
    ("validator_class", "params"),
    [
        (ReCaptchaV2Validator, {}),
        (ReCaptchaV3Validator, {"action": "test_action", "required_score": 0.4}),
    ],
)
@override_settings(DRF_RECAPTCHA_TESTING=True, DRF_RECAPTCHA_TESTING_PASS=False)
def test_recaptcha_validator_testing_fail(validator_class, params):
    validator = validator_class(secret_key="TEST_SECRET_KEY", **params)

    with pytest.raises(ValidationError) as exc_info:
        validator("test_token")

    assert (
        str(exc_info.value)
        == "[ErrorDetail(string='Error verifying reCAPTCHA, please try again.', code='captcha_invalid')]"
    )
