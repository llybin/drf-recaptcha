import json
from urllib.parse import quote, urlencode
from urllib.request import ProxyHandler, Request, build_opener

from django.conf import settings

from drf_recaptcha.constants import (
    DEFAULT_RECAPTCHA_DOMAIN,
    DEFAULT_RECAPTCHA_ENTERPRISE_DOMAIN,
)


class RecaptchaResponse:
    def __init__(self, is_valid, error_codes=None, extra_data=None):
        self.is_valid = is_valid
        self.error_codes = error_codes or []
        self.extra_data = extra_data or {}


def open_request(request_object):
    # Add proxy values to opener if needed.
    opener_args = []
    proxies = getattr(settings, "DRF_RECAPTCHA_PROXY", {})
    if proxies:
        opener_args = [ProxyHandler(proxies)]
    opener = build_opener(*opener_args)

    # Get response from POST to Google endpoint.
    return opener.open(
        request_object,
        timeout=getattr(settings, "DRF_RECAPTCHA_VERIFY_REQUEST_TIMEOUT", 10),
    )


def recaptcha_request(params):
    request_object = Request(
        url="https://{}/recaptcha/api/siteverify".format(
            getattr(settings, "DRF_RECAPTCHA_DOMAIN", DEFAULT_RECAPTCHA_DOMAIN)
        ),
        data=params,
        headers={
            "Content-type": "application/x-www-form-urlencoded",
            "User-agent": "DRF reCAPTCHA",
        },
    )

    return open_request(request_object)


def recaptcha_enterprise_request(params, project_id, api_key):
    domain = getattr(
        settings,
        "DRF_RECAPTCHA_ENTERPRISE_DOMAIN",
        DEFAULT_RECAPTCHA_ENTERPRISE_DOMAIN,
    )
    query = urlencode({"key": api_key})
    request_object = Request(
        url=f"https://{domain}/v1/projects/{quote(project_id)}/assessments?{query}",
        data=params,
        headers={
            "Content-type": "application/json",
            "User-agent": "DRF reCAPTCHA",
        },
    )

    return open_request(request_object)


def submit(recaptcha_response, secret_key, remoteip):
    params = urlencode(
        {
            "secret": secret_key,
            "response": recaptcha_response,
            "remoteip": remoteip,
        }
    )

    params = params.encode("utf-8")

    response = recaptcha_request(params)
    data = json.loads(response.read().decode("utf-8"))
    response.close()
    return RecaptchaResponse(
        is_valid=data.pop("success"),
        error_codes=data.pop("error-codes", None),
        extra_data=data,
    )


def submit_enterprise(  # noqa: PLR0913
    *,
    recaptcha_response,
    api_key,
    project_id,
    site_key,
    expected_action,
    remoteip,
):
    event = {"token": recaptcha_response, "siteKey": site_key}

    if expected_action:
        event["expectedAction"] = expected_action

    if remoteip:
        event["userIpAddress"] = remoteip

    params = json.dumps({"event": event}).encode("utf-8")

    response = recaptcha_enterprise_request(
        params,
        project_id=project_id,
        api_key=api_key,
    )
    data = json.loads(response.read().decode("utf-8"))
    response.close()

    token_properties = data.get("tokenProperties") or {}
    risk_analysis = data.get("riskAnalysis") or {}

    is_valid = token_properties.get("valid", False)

    return RecaptchaResponse(
        is_valid=is_valid,
        error_codes=(
            []
            if is_valid
            # `invalidReason` is an enum, `UNKNOWN_INVALID_REASON` is its
            # member for a reason Google didn't account for.
            else [token_properties.get("invalidReason") or "UNKNOWN_INVALID_REASON"]
        ),
        extra_data={
            "score": risk_analysis.get("score"),
            "action": token_properties.get("action", ""),
        },
    )
