from django.conf import settings
from rest_framework.serializers import CharField

from drf_recaptcha.constants import DEFAULT_V3_SCORE
from drf_recaptcha.validators import ReCaptchaV2Validator, ReCaptchaV3Validator


class ReCaptchaV2Field(CharField):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.write_only = True

        validator = ReCaptchaV2Validator(secret_key=settings.DRF_RECAPTCHA_SECRET_KEY)
        self.validators.append(validator)


class ReCaptchaV3Field(CharField):
    def __init__(self, action: str, required_score: float = None, **kwargs):
        super().__init__(**kwargs)

        self.write_only = True

        scores_from_settings = getattr(settings, "DRF_RECAPTCHA_ACTION_V3_SCORES", {})

        required_score = (
            required_score
            or getattr(scores_from_settings, action, None)
            or getattr(settings, "DRF_RECAPTCHA_DEFAULT_V3_SCORE", DEFAULT_V3_SCORE)
        )

        validator = ReCaptchaV3Validator(
            action=action,
            required_score=required_score,
            secret_key=settings.DRF_RECAPTCHA_SECRET_KEY,
        )
        self.validators.append(validator)
