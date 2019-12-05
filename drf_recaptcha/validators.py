import logging
from urllib.error import HTTPError

from django.conf import settings
from ipware import get_client_ip
from rest_framework.serializers import ValidationError

from drf_recaptcha import client

logger = logging.getLogger(__name__)


class ReCaptchaValidator:
    messages = {
        "captcha_invalid": "Error verifying reCAPTCHA, please try again.",
        "captcha_error": "Error verifying reCAPTCHA, please try again.",
    }
    recaptcha_client_ip = ""
    recaptcha_secret_key = ""

    def is_testing_and_pass(self) -> bool:
        is_testing = getattr(settings, "DRF_RECAPTCHA_TESTING", False)
        if is_testing:
            testing_result = getattr(settings, "DRF_RECAPTCHA_TESTING_PASS", True)
            if not testing_result:
                raise ValidationError(
                    self.messages["captcha_invalid"], code="captcha_invalid"
                )
            else:
                return True

        return False

    def set_context(self, serializer_field):
        request = serializer_field.context.get("request")

        try:
            self.recaptcha_client_ip = get_client_ip(request)
        except AttributeError:
            logger.exception(
                "Couldn't get client ip address. Check your serializer gets context with request."
            )

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

        if not check_captcha.is_valid:
            logger.error(
                "ReCAPTCHA validation failed due to: %s", check_captcha.error_codes
            )
            raise ValidationError(
                self.messages["captcha_invalid"], code="captcha_invalid"
            )

        return check_captcha


class ReCaptchaV2Validator(ReCaptchaValidator):
    def __init__(self, secret_key):
        self.recaptcha_secret_key = secret_key

    def __call__(self, value):
        if self.is_testing_and_pass():
            return

        check_captcha = self.get_response(value)

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

    def __call__(self, value):
        if self.is_testing_and_pass():
            return

        check_captcha = self.get_response(value)

        score = check_captcha.extra_data.get("score", None)
        if score is None:
            logger.error(
                "The response not contains score, reCAPTCHA v3 response must"
                " contains score, probably secret key for reCAPTCHA v2"
            )
            raise ValidationError(self.messages["captcha_error"], code="captcha_error")

        action = check_captcha.extra_data.get("action", "")

        if self.recaptcha_required_score > float(score):
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
