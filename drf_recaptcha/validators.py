import logging
from typing import TYPE_CHECKING
from urllib.error import HTTPError

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from ipware import get_client_ip
from rest_framework.serializers import ValidationError

from drf_recaptcha import client

if TYPE_CHECKING:
    from drf_recaptcha.client import RecaptchaResponse

logger = logging.getLogger(__name__)


class ReCaptchaValidator:
    requires_context = True

    messages = {
        "captcha_invalid": "Error verifying reCAPTCHA, please try again.",
        "captcha_error": "Error verifying reCAPTCHA, please try again.",
    }
    default_recaptcha_secret_key = ""

    def __call__(self, value, serializer_field):
        if self._is_testing():
            self._run_validation_as_testing()
            return

        client_ip = self._get_client_ip_from_context(serializer_field)
        recaptcha_secret_key = self._get_secret_key_from_context_or_default(
            serializer_field,
        )

        check_captcha = self._get_captcha_response_with_payload(
            value=value,
            secret_key=recaptcha_secret_key,
            client_ip=client_ip,
        )

        self._pre_validate_response(check_captcha)
        self._process_response(check_captcha)

    @staticmethod
    def _is_testing() -> bool:
        return getattr(settings, "DRF_RECAPTCHA_TESTING", False)

    def _run_validation_as_testing(self):
        testing_result = getattr(settings, "DRF_RECAPTCHA_TESTING_PASS", True)
        if not testing_result:
            raise ValidationError(
                self.messages["captcha_invalid"],
                code="captcha_invalid",
            )

    def _get_secret_key_from_context_or_default(self, serializer_field) -> str:
        return serializer_field.context.get(
            "recaptcha_secret_key",
            self.default_recaptcha_secret_key,
        )

    @staticmethod
    def _get_client_ip_from_context(serializer_field):
        request = serializer_field.context.get("request")
        if not request:
            msg = (
                "Couldn't get client ip address. "
                "Check your serializer gets context with request."
            )
            raise ImproperlyConfigured(msg)

        recaptcha_client_ip, _ = get_client_ip(request)
        return recaptcha_client_ip

    def _get_captcha_response_with_payload(
        self,
        value: str,
        secret_key: str,
        client_ip: str,
    ) -> "RecaptchaResponse":
        try:
            check_captcha = client.submit(
                recaptcha_response=value,
                secret_key=secret_key,
                remoteip=client_ip,
            )
        except HTTPError:  # Catch timeouts, etc.
            logger.exception("Couldn't get response, HTTPError")
            raise ValidationError(self.messages["captcha_error"], code="captcha_error")  # noqa: B904

        return check_captcha

    def _pre_validate_response(self, check_captcha: "RecaptchaResponse") -> None:
        if check_captcha.is_valid:
            return

        logger.info(
            "ReCAPTCHA validation failed due to: %s",
            check_captcha.error_codes,
        )
        raise ValidationError(self.messages["captcha_invalid"], code="captcha_invalid")

    def _process_response(self, check_captcha_response): ...


class ReCaptchaV2Validator(ReCaptchaValidator):
    def __init__(self, secret_key):
        self.default_recaptcha_secret_key = secret_key

    def _process_response(self, check_captcha_response):
        score = check_captcha_response.extra_data.get("score", None)

        if score is not None:
            logger.error(
                "The response contains score, reCAPTCHA v2 response doesn't"
                " contains score, probably secret key for reCAPTCHA v3",
            )
            raise ValidationError(self.messages["captcha_error"], code="captcha_error")


class ReCaptchaV3Validator(ReCaptchaValidator):
    def __init__(self, action, required_score, secret_key):
        self.recaptcha_action = action
        self.recaptcha_required_score = required_score
        self.score = None
        self.default_recaptcha_secret_key = secret_key

    def _process_response(self, check_captcha_response):
        self.score = check_captcha_response.extra_data.get("score", None)
        if self.score is None:
            logger.error(
                "The response not contains score, reCAPTCHA v3 response must"
                " contains score, probably secret key for reCAPTCHA v2",
            )
            raise ValidationError(self.messages["captcha_error"], code="captcha_error")

        action = check_captcha_response.extra_data.get("action", "")

        if self.recaptcha_required_score > float(self.score):
            logger.info(
                "ReCAPTCHA validation failed due to score of %s"
                " being lower than the required amount for action '%s'.",
                self.score,
                action,
            )
            raise ValidationError(
                self.messages["captcha_invalid"],
                code="captcha_invalid",
            )

        if self.recaptcha_action != action:
            logger.warning(
                "ReCAPTCHA validation failed due to value of action '%s'"
                " is not equal with defined '%s'.",
                action,
                self.recaptcha_action,
            )
            raise ValidationError(
                self.messages["captcha_invalid"],
                code="captcha_invalid",
            )
