"""What a field does when the deployment has no credential to verify a token."""

import pytest
from drf_recaptcha.fields import (
    ReCaptchaEnterpriseField,
    ReCaptchaV2Field,
    ReCaptchaV3Field,
)
from rest_framework.serializers import Serializer

FIELDS = [
    (ReCaptchaV2Field, {}),
    (ReCaptchaV3Field, {"action": "test_action"}),
    (ReCaptchaEnterpriseField, {"action": "test_action"}),
]


@pytest.fixture(autouse=True)
def _no_credentials(settings):
    """A deployment reading its credentials from unset environment variables."""
    settings.DRF_RECAPTCHA_SECRET_KEY = ""
    settings.DRF_RECAPTCHA_ENTERPRISE_PROJECT_ID = ""
    settings.DRF_RECAPTCHA_ENTERPRISE_SITE_KEY = ""


def validate(field_class, field_params, mocker):
    class _Serializer(Serializer):
        recaptcha = field_class(**field_params)

    serializer = _Serializer(
        data={"recaptcha": "test_token"},
        context={"request": mocker.Mock(META={"HTTP_X_FORWARDED_FOR": "4.3.2.1"})},
    )
    serializer.is_valid(raise_exception=False)
    return serializer


@pytest.mark.parametrize(("field_class", "field_params"), FIELDS)
def test_token_is_rejected_without_asking_google(field_class, field_params, mocker):
    opener = mocker.patch("drf_recaptcha.client.build_opener")

    serializer = validate(field_class, field_params, mocker)

    assert serializer.errors["recaptcha"][0].code == "captcha_error"
    # The submitter is not told which setting is missing, only that their token
    # was not checked.
    assert serializer.errors["recaptcha"] == [
        "Error verifying reCAPTCHA, please try again.",
    ]
    # Nothing to authenticate the request with, so nothing is sent: it would earn
    # an error from Google and a slower rejection.
    opener.assert_not_called()


@pytest.mark.parametrize(("field_class", "field_params"), FIELDS)
def test_testing_mode_still_passes_every_token(
    field_class,
    field_params,
    mocker,
    settings,
):
    """Environments without credentials on purpose must not fail closed."""
    settings.DRF_RECAPTCHA_TESTING = True

    assert validate(field_class, field_params, mocker).errors == {}


def test_every_missing_setting_is_logged(mocker, caplog):
    """An assessment needs all three, so all three are worth naming."""
    validate(ReCaptchaEnterpriseField, {"action": "test_action"}, mocker)

    assert "settings.DRF_RECAPTCHA_SECRET_KEY" in caplog.text
    assert "settings.DRF_RECAPTCHA_ENTERPRISE_PROJECT_ID" in caplog.text
    assert "settings.DRF_RECAPTCHA_ENTERPRISE_SITE_KEY" in caplog.text
