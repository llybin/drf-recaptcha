from unittest.mock import Mock

import pytest


@pytest.fixture
def mocked_serializer_field():
    return Mock(context={})


@pytest.fixture
def mocked_serializer_field_with_request_context():
    return Mock(context={"request": Mock(META={"HTTP_X_FORWARDED_FOR": "4.3.2.1"})})


@pytest.fixture
def mocked_serializer_field_with_request_secret_key_context():
    return Mock(
        context={
            "request": Mock(META={"HTTP_X_FORWARDED_FOR": "4.3.2.1"}),
            "recaptcha_secret_key": "from-context",
        }
    )
