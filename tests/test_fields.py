import pytest
from django.core.exceptions import ImproperlyConfigured

from drf_recaptcha.fields import ReCaptchaV2Field, ReCaptchaV3Field
from drf_recaptcha.validators import ReCaptchaV2Validator, ReCaptchaV3Validator


@pytest.mark.parametrize(
    ("params", "expected"),
    [({}, True), ({"write_only": False}, True), ({"write_only": True}, True)],
)
def test_recaptcha_v2_field_write_only(params, expected):
    field = ReCaptchaV2Field(**params)
    assert field.write_only is expected


@pytest.mark.parametrize(
    ("params", "expected"),
    [({}, True), ({"write_only": False}, True), ({"write_only": True}, True)],
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
        ({"required_score": 0.8}, None, 0.6, 0.8),
        ({"required_score": 0.8}, {"test_action": 0.7}, 0.6, 0.7),
    ],
)
def test_recaptcha_v3_field_score_priority(
    params, from_settings, settings_default, expected, settings
):
    settings.DRF_RECAPTCHA_ACTION_V3_SCORES = from_settings
    settings.DRF_RECAPTCHA_DEFAULT_V3_SCORE = settings_default

    field = ReCaptchaV3Field(action="test_action", **params)
    assert field.required_score == expected


@pytest.mark.parametrize(
    ("field_class", "params", "validator_class"),
    [
        (ReCaptchaV2Field, {}, ReCaptchaV2Validator),
        (ReCaptchaV3Field, {"action": "test_action"}, ReCaptchaV3Validator),
    ],
)
def test_recaptcha_has_recaptcha_validator(field_class, params, validator_class):
    field = field_class(**params)

    cnt_validators = len(field.validators)
    assert cnt_validators > 0
    assert isinstance(field.validators[cnt_validators - 1], validator_class)


@pytest.mark.parametrize(
    ("params", "from_settings", "settings_default", "error"),
    [
        ({}, None, "0.6", "Default score value should be int or float"),
        ({}, None, -0.1, "Default score value should be between 0.0 - 1.0"),
        ({}, None, 1.1, "Default score value should be between 0.0 - 1.0"),
        (
            {},
            '{"test_action": 0.7}',
            None,
            "DRF_RECAPTCHA_ACTION_V3_SCORES should be a dict.",
        ),
        (
            {},
            {"test_action": "0.7"},
            None,
            "Score value for action 'test_action' should be int or float",
        ),
        (
            {},
            {"test_action": -1},
            None,
            "Score value for action 'test_action' should be between 0.0 - 1.0",
        ),
        (
            {},
            {"test_action": 2},
            None,
            "Score value for action 'test_action' should be between 0.0 - 1.0",
        ),
        (
            {"required_score": "0.8"},
            None,
            None,
            "Score value for action 'test_action' should be int or float",
        ),
        (
            {"required_score": -0.01},
            None,
            None,
            "Score value for action 'test_action' should be between 0.0 - 1.0",
        ),
        (
            {"required_score": 1.01},
            None,
            None,
            "Score value for action 'test_action' should be between 0.0 - 1.0",
        ),
    ],
)
def test_recaptcha_v3_field_score_improperly_configured(
    params, from_settings, settings_default, error, settings
):
    settings.DRF_RECAPTCHA_ACTION_V3_SCORES = from_settings
    settings.DRF_RECAPTCHA_DEFAULT_V3_SCORE = settings_default

    with pytest.raises(ImproperlyConfigured) as exc_info:
        ReCaptchaV3Field(action="test_action", **params)

    assert str(exc_info.value) == error
