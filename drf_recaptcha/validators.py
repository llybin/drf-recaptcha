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

# Enough for the error documents these APIs answer with, and a bound on what a
# rejected request can write to the log.
ERROR_BODY_LOG_LIMIT = 2000


def read_error_body(error: HTTPError) -> str:
    """What the response to a refused verification request says.

    Worth the trouble because the status line alone rarely identifies the fault:
    the Enterprise API answers a mismatched project and API key with a 400 whose
    body carries `RESOURCE_PROJECT_INVALID`, and that distinction is the
    difference between a misconfigured deployment and an outage. `HTTPError` is
    itself a file object, so the body is readable here and nowhere later.
    """
    try:
        body = error.read(ERROR_BODY_LOG_LIMIT)
    except (OSError, ValueError):
        # A body that cannot be read is not worth failing over — the caller is
        # already on its way to rejecting the submission.
        return "<unreadable>"

    return body.decode("utf-8", errors="replace") if body else "<empty>"


def get_credential_from_settings(setting_name: str) -> str:
    # Unset and blank mean the same here: an environment variable nobody set
    # usually reaches settings as an empty string, and neither value can
    # authenticate a verification request.
    return getattr(settings, setting_name, "") or ""


class ReCaptchaValidator:
    requires_context = True

    messages = {
        "captcha_invalid": "Error verifying reCAPTCHA, please try again.",
        "captcha_error": "Error verifying reCAPTCHA, please try again.",
        "captcha_unconfigured": "Error verifying reCAPTCHA, please try again.",
    }
    default_recaptcha_secret_key = None

    def __call__(self, value, serializer_field):
        if self._is_testing():
            self._run_validation_as_testing()
            return

        client_ip = self._get_client_ip_from_context(serializer_field)
        recaptcha_secret_key = self._get_secret_key_from_context_or_default(
            serializer_field,
        )

        self._validate_is_configured(recaptcha_secret_key)

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
        return (
            serializer_field.context.get("recaptcha_secret_key")
            or self.default_recaptcha_secret_key
            or get_credential_from_settings("DRF_RECAPTCHA_SECRET_KEY")
        )

    def _get_missing_credentials(self, secret_key: str) -> list[str]:
        return [] if secret_key else ["DRF_RECAPTCHA_SECRET_KEY"]

    def _validate_is_configured(self, secret_key: str) -> None:
        # Rejected rather than accepted, because the alternative is taking
        # tokens nobody verified. Rejected rather than raised on, so a
        # deployment missing a credential loses the submissions its captcha
        # guards and keeps serving everything else.
        missing = self._get_missing_credentials(secret_key)
        if not missing:
            return

        logger.error(
            "reCAPTCHA is not configured: %s not set, so a token cannot be"
            " verified and the submission is rejected.",
            ", ".join(f"settings.{setting}" for setting in missing),
        )
        raise ValidationError(
            self.messages["captcha_unconfigured"],
            # The code of a failed verification, so a client that resets the
            # widget on it can retry once the credential is in place.
            code="captcha_error",
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
            check_captcha = self._submit(
                value=value,
                secret_key=secret_key,
                client_ip=client_ip,
            )
        except HTTPError as error:  # Catch timeouts, etc.
            body = read_error_body(error)
            logger.exception("Couldn't get response, HTTPError: %s", body)
            raise ValidationError(self.messages["captcha_error"], code="captcha_error")  # noqa: B904

        return check_captcha

    def _submit(
        self,
        value: str,
        secret_key: str,
        client_ip: str,
    ) -> "RecaptchaResponse":
        return client.submit(
            recaptcha_response=value,
            secret_key=secret_key,
            remoteip=client_ip,
        )

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
    score_missing_message = (
        "The response not contains score, reCAPTCHA v3 response must"
        " contains score, probably secret key for reCAPTCHA v2"
    )

    def __init__(self, action, required_score, secret_key):
        self.recaptcha_action = action
        self.recaptcha_required_score = required_score
        self.score = None
        self.default_recaptcha_secret_key = secret_key

    def _process_response(self, check_captcha_response):
        self._validate_score(check_captcha_response)
        self._validate_action(check_captcha_response)

    def _validate_score(self, check_captcha_response):
        self.score = check_captcha_response.extra_data.get("score", None)
        if self.score is None:
            logger.error(self.score_missing_message)
            raise ValidationError(self.messages["captcha_error"], code="captcha_error")

        if self.recaptcha_required_score > float(self.score):
            logger.info(
                "ReCAPTCHA validation failed due to score of %s"
                " being lower than the required amount for action '%s'.",
                self.score,
                check_captcha_response.extra_data.get("action", ""),
            )
            raise ValidationError(
                self.messages["captcha_invalid"],
                code="captcha_invalid",
            )

    def _validate_action(self, check_captcha_response):
        action = check_captcha_response.extra_data.get("action", "")

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


class ReCaptchaEnterpriseValidator(ReCaptchaV3Validator):
    score_missing_message = (
        "The assessment doesn't contain a risk analysis score, check that the"
        " site key is a reCAPTCHA Enterprise key of the given project"
    )

    def __init__(
        self,
        action,
        required_score,
        secret_key,
        project_id=None,
        site_key=None,
    ):
        super().__init__(
            action=action,
            required_score=required_score,
            secret_key=secret_key,
        )
        self.recaptcha_project_id = project_id
        self.recaptcha_site_key = site_key

    def _get_project_id(self) -> str:
        return self.recaptcha_project_id or get_credential_from_settings(
            "DRF_RECAPTCHA_ENTERPRISE_PROJECT_ID",
        )

    def _get_site_key(self) -> str:
        return self.recaptcha_site_key or get_credential_from_settings(
            "DRF_RECAPTCHA_ENTERPRISE_SITE_KEY",
        )

    def _get_missing_credentials(self, secret_key: str) -> list[str]:
        # An assessment needs all three, so one of them missing is as good as
        # none of them set.
        return super()._get_missing_credentials(secret_key) + [
            setting
            for setting, value in (
                ("DRF_RECAPTCHA_ENTERPRISE_PROJECT_ID", self._get_project_id()),
                ("DRF_RECAPTCHA_ENTERPRISE_SITE_KEY", self._get_site_key()),
            )
            if not value
        ]

    def _submit(
        self,
        value: str,
        secret_key: str,
        client_ip: str,
    ) -> "RecaptchaResponse":
        return client.submit_enterprise(
            recaptcha_response=value,
            api_key=secret_key,
            project_id=self._get_project_id(),
            site_key=self._get_site_key(),
            expected_action=self.recaptcha_action,
            remoteip=client_ip,
        )

    def _process_response(self, check_captcha_response):
        self._validate_score(check_captcha_response)

        # Checkbox site keys are not bound to an action.
        if self.recaptcha_action is not None:
            self._validate_action(check_captcha_response)
