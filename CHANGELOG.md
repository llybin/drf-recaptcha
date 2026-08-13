# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

At the moment, the changelog is located [in releases](https://github.com/llybin/drf-recaptcha/releases).
In the future, it will be updated to follow the standard described above.

## [Unreleased]

### Added

- Support for reCAPTCHA Enterprise ([#11](https://github.com/llybin/drf-recaptcha/issues/11)).
  `ReCaptchaEnterpriseField` verifies a token by creating an assessment with the Google Cloud API,
  authenticated with an API key, so no additional dependency is required.
- Settings `DRF_RECAPTCHA_ENTERPRISE_PROJECT_ID`, `DRF_RECAPTCHA_ENTERPRISE_SITE_KEY`
  and `DRF_RECAPTCHA_ENTERPRISE_DOMAIN`.
- The system check reports every credential setting a token cannot be verified without,
  the Enterprise project id and site key included.

### Changed

- Credentials taken from settings are read when a field validates rather than when it is
  built, so a deployment missing one starts and serves everything the captcha does not
  guard. The fields reject the submissions they protect instead, with the code
  `captcha_error` and the new `captcha_unconfigured` message, and log which setting is
  missing.
- A missing `DRF_RECAPTCHA_SECRET_KEY` is a system check warning rather than an error, so
  it no longer fails every management command that runs checks, `migrate` included. The
  check messages carry ids, `drf_recaptcha.W001` for missing credentials, so
  `SILENCED_SYSTEM_CHECKS` can reach them.
- An `HTTPError` from a verification request is logged with the response body, bounded to
  2000 characters, rather than the status line alone. The Enterprise API distinguishes a
  site key from another project, a project the API key cannot use, and a disabled API only
  in that body, so without it every one of them reports as `HTTP Error 400: Bad Request`.

### Removed

- `ImproperlyConfigured` from `ReCaptchaEnterpriseField` for a missing project id or site
  key, and `get_enterprise_setting`. Building the field no longer touches settings.
