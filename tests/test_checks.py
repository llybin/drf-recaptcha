import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from drf_recaptcha.checks import recaptcha_system_check
from drf_recaptcha.constants import TEST_V2_SECRET_KEY


@override_settings(DRF_RECAPTCHA_SECRET_KEY=None)
def test_warning_no_secret_key():
    with pytest.raises(ImproperlyConfigured) as exc_info:
        recaptcha_system_check(None)

    assert str(exc_info.value) == "settings.DRF_RECAPTCHA_SECRET_KEY must be set."


@override_settings(DRF_RECAPTCHA_TESTING=True, DRF_RECAPTCHA_SECRET_KEY=None)
def test_silent_testing():
    assert recaptcha_system_check(None) == []


@override_settings(DRF_RECAPTCHA_SECRET_KEY=TEST_V2_SECRET_KEY)
def test_warning_test_secret_key():
    errors = recaptcha_system_check(None)
    assert len(errors) == 1
    assert errors[0].hint == "Update settings.DRF_RECAPTCHA_SECRET_KEY"
