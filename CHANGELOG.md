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
