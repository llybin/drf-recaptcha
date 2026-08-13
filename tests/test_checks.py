import pytest
from drf_recaptcha.checks import (
    ENTERPRISE_SETTINGS,
    SECRET_KEY_SETTING,
    recaptcha_system_check,
)
from drf_recaptcha.constants import TEST_V2_SECRET_KEY


@pytest.fixture
def _enterprise_settings(settings):
    settings.DRF_RECAPTCHA_ENTERPRISE_PROJECT_ID = "test-project"
    settings.DRF_RECAPTCHA_ENTERPRISE_SITE_KEY = "TEST_SITE_KEY"


@pytest.mark.parametrize("value", [None, ""])
def test_warning_no_secret_key(value, settings):
    settings.DRF_RECAPTCHA_SECRET_KEY = value

    warnings = recaptcha_system_check(None)

    assert len(warnings) == 1
    assert warnings[0].id == "drf_recaptcha.W001"
    assert warnings[0].msg.startswith("settings.DRF_RECAPTCHA_SECRET_KEY not set")


def test_no_warning_when_secret_key_is_set():
    assert recaptcha_system_check(None) == []


def test_silent_testing(settings):
    settings.DRF_RECAPTCHA_TESTING = True
    settings.DRF_RECAPTCHA_SECRET_KEY = None

    assert recaptcha_system_check(None) == []


def test_warning_test_secret_key(settings):
    settings.DRF_RECAPTCHA_SECRET_KEY = TEST_V2_SECRET_KEY

    warnings = recaptcha_system_check(None)

    assert len(warnings) == 1
    assert warnings[0].id == "drf_recaptcha.recaptcha_test_key_error"
    assert warnings[0].hint == "Update settings.DRF_RECAPTCHA_SECRET_KEY"


@pytest.mark.usefixtures("_enterprise_settings")
def test_no_warning_when_enterprise_is_configured():
    assert recaptcha_system_check(None) == []


@pytest.mark.usefixtures("_enterprise_settings")
@pytest.mark.parametrize("setting_name", [SECRET_KEY_SETTING, *ENTERPRISE_SETTINGS])
def test_warning_names_the_missing_enterprise_setting(setting_name, settings):
    setattr(settings, setting_name, "")

    warnings = recaptcha_system_check(None)

    assert len(warnings) == 1
    assert warnings[0].msg.startswith(f"settings.{setting_name} not set")


def test_enterprise_settings_are_not_required_without_them(settings):
    """A project on v2 or v3 alone is not asked for a project id and a site key."""
    settings.DRF_RECAPTCHA_SECRET_KEY = ""

    warnings = recaptcha_system_check(None)

    assert len(warnings) == 1
    assert "ENTERPRISE" not in warnings[0].msg
