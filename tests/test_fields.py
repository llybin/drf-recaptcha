import pytest
from django.test import override_settings

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
