import pytest
from drf_recaptcha.validators import ReCaptchaV2Validator, ReCaptchaV3Validator
from rest_framework.exceptions import ValidationError


@pytest.mark.parametrize(
    ("validator_class", "params"),
    [
        (ReCaptchaV2Validator, {}),
        (ReCaptchaV3Validator, {"action": "test_action", "required_score": 0.4}),
    ],
)
def test_recaptcha_validator_testing_success(
    validator_class,
    params,
    settings,
    mocked_serializer_field,
):
    settings.DRF_RECAPTCHA_TESTING = True

    validator = validator_class(secret_key="TEST_SECRET_KEY", **params)  # noqa: S106
    try:
        validator("test_token", mocked_serializer_field)
    except ValidationError:
        pytest.fail("Validation is not passed")


@pytest.mark.parametrize(
    ("validator_class", "params"),
    [
        (ReCaptchaV2Validator, {}),
        (ReCaptchaV3Validator, {"action": "test_action", "required_score": 0.4}),
    ],
)
def test_recaptcha_validator_testing_fail(
    validator_class,
    params,
    settings,
    mocked_serializer_field,
):
    settings.DRF_RECAPTCHA_TESTING = True
    settings.DRF_RECAPTCHA_TESTING_PASS = False

    validator = validator_class(secret_key="TEST_SECRET_KEY", **params)  # noqa: S106

    with pytest.raises(ValidationError) as exc_info:
        validator("test_token", mocked_serializer_field)

    assert (
        str(exc_info.value) == "[ErrorDetail(string='Error verifying reCAPTCHA, "
        "please try again.', code='captcha_invalid')]"
    )
