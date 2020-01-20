import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import RequestFactory, override_settings
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import Serializer

from drf_recaptcha.constants import TEST_V2_SECRET_KEY
from drf_recaptcha.fields import ReCaptchaV2Field, ReCaptchaV3Field


@pytest.mark.parametrize(
    ("params", "expected"),
    [({}, True), ({"write_only": False}, True,), ({"write_only": True}, True,)],
)
def test_recaptcha_v2_field_write_only(params, expected):
    field = ReCaptchaV2Field(**params)
    assert field.write_only is expected


@pytest.mark.parametrize(
    ("params", "expected"),
    [({}, True), ({"write_only": False}, True,), ({"write_only": True}, True,)],
)
def test_recaptcha_v3_field_write_only(params, expected):
    field = ReCaptchaV3Field(action="test_action", **params)
    assert field.write_only is expected


@pytest.mark.parametrize(
    ("params", "from_settings", "settings_default", "expected"),
    [
        ({}, None, None, 0.5),
        ({}, None, 0.6, 0.6),
        ({}, {"test_action": 0.7}, 0.6, 0.7),
        ({"required_score": 0.8}, {"test_action": 0.7}, 0.6, 0.8),
    ],
)
def test_recaptcha_v3_field_score_priority(
    params, from_settings, settings_default, expected
):
    with override_settings(
        DRF_RECAPTCHA_ACTION_V3_SCORES=from_settings,
        DRF_RECAPTCHA_DEFAULT_V3_SCORE=settings_default,
    ):
        field = ReCaptchaV3Field(action="test_action", **params)
        assert field.required_score == expected


@pytest.mark.parametrize(
    ("field_class", "params"),
    [(ReCaptchaV2Field, {}), (ReCaptchaV3Field, {"action": "test_action"})],
)
def test_serializer_requires_context(field_class, params):
    class TestSerializer(Serializer):
        token = field_class(**params)

    serializer = TestSerializer(data={"token": "test_token"})

    with pytest.raises(ImproperlyConfigured) as exc_info:
        serializer.is_valid(raise_exception=True)

    assert (
        str(exc_info.value)
        == "Couldn't get client ip address. Check your serializer gets context with request."
    )


@override_settings(DRF_RECAPTCHA_SECRET_KEY=TEST_V2_SECRET_KEY)
def test_functional_v2():
    class TestSerializer(Serializer):
        token = ReCaptchaV2Field()

    serializer = TestSerializer(
        data={"token": "test_token"},
        context={"request": RequestFactory().get("/recaptcha")},
    )
    assert serializer.is_valid() is True


@override_settings(DRF_RECAPTCHA_SECRET_KEY=TEST_V2_SECRET_KEY)
def test_functional_v3():
    class TestSerializer(Serializer):
        token = ReCaptchaV3Field(action="test_action")

    serializer = TestSerializer(
        data={"token": "test_token"},
        context={"request": RequestFactory().get("/recaptcha")},
    )
    with pytest.raises(ValidationError) as exc_info:
        serializer.is_valid(raise_exception=True)

    assert (
        str(exc_info.value)
        == "{'token': [ErrorDetail(string='Error verifying reCAPTCHA, please try again.', code='captcha_error')]}"
    )
