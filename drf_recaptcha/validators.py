import logging
from urllib.error import HTTPError

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from ipware import get_client_ip
from rest_framework.serializers import ValidationError

from drf_recaptcha import client

logger = logging.getLogger(__name__)


class ReCaptchaValidator:
    requires_context = True

    messages = {
        "captcha_invalid": "Error verifying reCAPTCHA, please try again.",
        "captcha_error": "Error verifying reCAPTCHA, please try again.",
    }
    recaptcha_client_ip = ""
    recaptcha_secret_key = ""

    @staticmethod
    def is_testing() -> bool:
        return getattr(settings, "DRF_RECAPTCHA_TESTING", False)

    def testing_validation(self):
        testing_result = getattr(settings, "DRF_RECAPTCHA_TESTING_PASS", True)
        if not testing_result:
            raise ValidationError(
                self.messages["captcha_invalid"], code="captcha_invalid"
            )

    def set_context(self, serializer_field):
        request = serializer_field.context.get("request")
        if not request:
            raise ImproperlyConfigured(
                "Couldn't get client ip address. Check your serializer gets context with request."
            )

        self.recaptcha_client_ip, _ = get_client_ip(request)

    def get_response(self, value: str) -> client.RecaptchaResponse:
        try:
            check_captcha = client.submit(
                recaptcha_response=value,
                secret_key=self.recaptcha_secret_key,
                remoteip=self.recaptcha_client_ip,
            )
        except HTTPError:  # Catch timeouts, etc
            logger.exception("Couldn't get response, HTTPError")
            raise ValidationError(self.messages["captcha_error"], code="captcha_error")

        return check_captcha

    def pre_validate_response(self, check_captcha: client.RecaptchaResponse):
        if not check_captcha.is_valid:
            logger.error(
                "ReCAPTCHA validation failed due to: %s", check_captcha.error_codes
            )
            raise ValidationError(
                self.messages["captcha_invalid"], code="captcha_invalid"
            )


class ReCaptchaV2Validator(ReCaptchaValidator):
    def __init__(self, secret_key):
        self.recaptcha_secret_key = secret_key

    def __call__(self, value, serializer_field=None):
        # compatibility with drf < 3.11
        if serializer_field and not self.recaptcha_client_ip:
            self.set_context(serializer_field)

        if self.is_testing():
            self.testing_validation()
            return

        check_captcha = self.get_response(value)

        self.pre_validate_response(check_captcha)

        score = check_captcha.extra_data.get("score", None)
        if score is not None:
            logger.error(
                "The response contains score, reCAPTCHA v2 response doesn't"
                " contains score, probably secret key for reCAPTCHA v3"
            )
            raise ValidationError(self.messages["captcha_error"], code="captcha_error")


class ReCaptchaV3Validator(ReCaptchaValidator):
    def __init__(self, action, required_score, secret_key):
        self.recaptcha_action = action
        self.recaptcha_required_score = required_score
        self.recaptcha_secret_key = secret_key

    def __call__(self, value, serializer_field=None):
        # compatibility with drf < 3.11
        if serializer_field and not self.recaptcha_client_ip:
            self.set_context(serializer_field)

        if self.is_testing():
            self.testing_validation()
            return

        check_captcha = self.get_response(value)

        self.pre_validate_response(check_captcha)

        score = check_captcha.extra_data.get("score", None)
        if score is None:
            logger.error(
                "The response not contains score, reCAPTCHA v3 response must"
                " contains score, probably secret key for reCAPTCHA v2"
            )
            raise ValidationError(self.messages["captcha_error"], code="captcha_error")

        action = check_captcha.extra_data.get("action", "")

        if self.recaptcha_required_score >= float(score):
            logger.error(
                "ReCAPTCHA validation failed due to score of %s"
                " being lower than the required amount for action '%s'.",
                score,
                action,
            )
            raise ValidationError(
                self.messages["captcha_invalid"], code="captcha_invalid"
            )

        if self.recaptcha_action != action:
            logger.error(
                "ReCAPTCHA validation failed due to value of action '%s'"
                " is not equal with defined '%s'.",
                action,
                self.recaptcha_action,
            )
            raise ValidationError(
                self.messages["captcha_invalid"], code="captcha_invalid"
            )
