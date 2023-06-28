from unittest.mock import ANY, Mock, patch

import pytest
from rest_framework.serializers import Serializer

from drf_recaptcha.fields import ReCaptchaV2Field, ReCaptchaV3Field


@pytest.fixture(autouse=True)
def _default_recaptcha_settings(settings):
    settings.DRF_RECAPTCHA_SECRET_KEY = "from-default-settings"


@pytest.fixture
def patched_v2_validator():
    with patch(
        "drf_recaptcha.fields.ReCaptchaV2Validator.get_captcha_response_with_payload"
    ) as validator:
        yield validator


@pytest.fixture
def patched_v3_validator():
    with patch(
        "drf_recaptcha.fields.ReCaptchaV3Validator.get_captcha_response_with_payload"
    ) as validator:
        yield validator


TEST_CASES = [
    (
        {},
        {},
        "from-default-settings",
    ),
    (
        {"secret_key": "from-field-secret-key"},
        {},
        "from-field-secret-key",
    ),
    (
        {},
        {"recaptcha_secret_key": "from-context"},
        "from-context",
    ),
    (
        {"secret_key": "from-field-secret-key"},
        {"recaptcha_secret_key": "from-context"},
        "from-context",
    ),
]


@pytest.mark.parametrize(
    ("field_params", "field_context", "expected_secret_key"), TEST_CASES
)
def test_secret_key_priority_for_v2(
    field_params, field_context, expected_secret_key, patched_v2_validator
):
    field_context["request"] = Mock(META={"HTTP_X_FORWARDED_FOR": "4.3.2.1"})

    class _Serializer(Serializer):
        recaptcha = ReCaptchaV2Field(**field_params, required=True)

    serializer = _Serializer(data={"recaptcha": "foo"}, context=field_context)
    serializer.is_valid(raise_exception=False)

    patched_v2_validator.assert_called_once_with(
        value=ANY,
        secret_key=expected_secret_key,
        client_ip=ANY,
    )


@pytest.mark.parametrize(
    ("field_params", "field_context", "expected_secret_key"), TEST_CASES
)
def test_secret_key_priority_for_v3(
    field_params, field_context, expected_secret_key, patched_v3_validator
):
    field_context["request"] = Mock(META={"HTTP_X_FORWARDED_FOR": "4.3.2.1"})
    field_params.update(
        {
            "action": "some",
            "required_score": 1,
        }
    )

    class _Serializer(Serializer):
        recaptcha = ReCaptchaV3Field(**field_params, required=True)

    serializer = _Serializer(data={"recaptcha": "foo"}, context=field_context)
    serializer.is_valid(raise_exception=False)

    patched_v3_validator.assert_called_once_with(
        value=ANY,
        secret_key=expected_secret_key,
        client_ip=ANY,
    )
