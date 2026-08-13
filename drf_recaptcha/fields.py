from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from rest_framework.serializers import CharField

from drf_recaptcha.constants import DEFAULT_V3_SCORE
from drf_recaptcha.validators import (
    ReCaptchaEnterpriseValidator,
    ReCaptchaV2Validator,
    ReCaptchaV3Validator,
)

# The fields below leave the credentials they are not given as arguments to the
# validator, which reads them from settings when it runs. Building a field
# touches no setting, so what a missing credential costs is decided per request,
# in `ReCaptchaValidator._validate_is_configured`.


class ReCaptchaV2Field(CharField):
    def __init__(self, secret_key: str | None = None, **kwargs):
        super().__init__(**kwargs)

        self.write_only = True

        validator = ReCaptchaV2Validator(secret_key=secret_key)
        self.validators.append(validator)


def validate_v3_settings_score_value(
    value: int or float or None,
    action: str | None = None,
):
    if value is None:
        return

    if not isinstance(value, int | float):
        if action:
            message = f"Score value for action '{action}' should be int or float"
        else:
            message = "Default score value should be int or float"

        raise ImproperlyConfigured(message)

    if value < 0.0 or value > 1.0:
        if action:
            message = f"Score value for action '{action}' should be between 0.0 - 1.0"
        else:
            message = "Default score value should be between 0.0 - 1.0"

        raise ImproperlyConfigured(message)


def get_v3_action_score_from_settings(action: str) -> int or float or None:
    scores_from_settings = getattr(settings, "DRF_RECAPTCHA_ACTION_V3_SCORES", None)

    if scores_from_settings is None:
        return None

    if not isinstance(scores_from_settings, dict):
        msg = "DRF_RECAPTCHA_ACTION_V3_SCORES should be a dict."
        raise ImproperlyConfigured(msg)

    action_score_from_settings = scores_from_settings.get(action, None)
    validate_v3_settings_score_value(action_score_from_settings, action)
    return action_score_from_settings


def get_v3_default_score_from_settings() -> int or float or None:
    default_score_from_settings = getattr(
        settings,
        "DRF_RECAPTCHA_DEFAULT_V3_SCORE",
        None,
    )
    validate_v3_settings_score_value(default_score_from_settings)
    return default_score_from_settings


def get_required_score(
    action: str | None,
    required_score: int or float or None,
) -> int or float:
    action_score_from_settings = get_v3_action_score_from_settings(action)
    default_score_from_settings = get_v3_default_score_from_settings()
    validate_v3_settings_score_value(required_score, action)

    return (
        action_score_from_settings
        if action_score_from_settings is not None
        else (
            required_score
            if required_score is not None
            else (
                default_score_from_settings
                if default_score_from_settings is not None
                else DEFAULT_V3_SCORE
            )
        )
    )


class ScoreFieldMixin:
    _validator: ReCaptchaV3Validator

    @property
    def score(self):
        score = self._validator.score
        if score is None:
            msg = (
                "You must call the serializer `.is_valid()` method before "
                "attempting to access the `.score` property of this field."
            )
            raise AssertionError(msg)
        return score


class ReCaptchaV3Field(ScoreFieldMixin, CharField):
    def __init__(
        self,
        action: str,
        required_score: float | None = None,
        secret_key: str | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.write_only = True

        self.required_score = get_required_score(action, required_score)

        self._validator = ReCaptchaV3Validator(
            action=action,
            required_score=self.required_score,
            secret_key=secret_key,
        )
        self.validators.append(self._validator)


class ReCaptchaEnterpriseField(ScoreFieldMixin, CharField):
    # `secret_key` is the Google Cloud API key of the assessment request,
    # `action` is unset for checkbox site keys, they are not bound to an action.
    def __init__(
        self,
        action: str | None = None,
        required_score: float | None = None,
        secret_key: str | None = None,
        project_id: str | None = None,
        site_key: str | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.write_only = True

        self.required_score = get_required_score(action, required_score)

        self._validator = ReCaptchaEnterpriseValidator(
            action=action,
            required_score=self.required_score,
            secret_key=secret_key,
            project_id=project_id,
            site_key=site_key,
        )
        self.validators.append(self._validator)
