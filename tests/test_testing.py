import pytest
from rest_framework.exceptions import ValidationError

from drf_recaptcha.validators import ReCaptchaV2Validator, ReCaptchaV3Validator


@pytest.mark.parametrize(
    ("validator_class", "params"),
    [
        (ReCaptchaV2Validator, {}),
        (ReCaptchaV3Validator, {"action": "test_action", "required_score": 0.4}),
    ],
)
def test_recaptcha_validator_testing_success(validator_class, params, settings):
    settings.DRF_RECAPTCHA_TESTING = True

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
def test_recaptcha_validator_testing_fail(validator_class, params, settings):
    settings.DRF_RECAPTCHA_TESTING = True
    settings.DRF_RECAPTCHA_TESTING_PASS = False

    validator = validator_class(secret_key="TEST_SECRET_KEY", **params)

    with pytest.raises(ValidationError) as exc_info:
        validator("test_token")

    assert (
        str(exc_info.value)
        == "[ErrorDetail(string='Error verifying reCAPTCHA, please try again.', code='captcha_invalid')]"
    )
