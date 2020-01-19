import pytest

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
