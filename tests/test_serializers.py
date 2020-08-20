import pytest
from django.core.exceptions import ImproperlyConfigured
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import Serializer
from rest_framework.test import APIRequestFactory

from drf_recaptcha.constants import TEST_V2_SECRET_KEY
from drf_recaptcha.fields import ReCaptchaV2Field, ReCaptchaV3Field


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


def test_serializer_v2(settings):
    settings.DRF_RECAPTCHA_SECRET_KEY = TEST_V2_SECRET_KEY

    class TestSerializer(Serializer):
        token = ReCaptchaV2Field()

    serializer = TestSerializer(
        data={"token": "test_token"},
        context={"request": APIRequestFactory().get("/recaptcha")},
    )
    assert serializer.is_valid() is True


def test_serializer_v3(settings):
    settings.DRF_RECAPTCHA_SECRET_KEY = TEST_V2_SECRET_KEY

    class TestSerializer(Serializer):
        token = ReCaptchaV3Field(action="test_action")

    serializer = TestSerializer(
        data={"token": "test_token"},
        context={"request": APIRequestFactory().get("/recaptcha")},
    )
    with pytest.raises(ValidationError) as exc_info:
        serializer.is_valid(raise_exception=True)

    assert (
        str(exc_info.value)
        == "{'token': [ErrorDetail(string='Error verifying reCAPTCHA, please try again.', code='captcha_error')]}"
    )
