from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


@pytest.fixture
def mocked_serializer_field(mocker: "MockerFixture"):
    return mocker.Mock(context={})


@pytest.fixture
def mocked_serializer_field_with_request_context(mocker: "MockerFixture"):
    return mocker.Mock(
        context={"request": mocker.Mock(META={"HTTP_X_FORWARDED_FOR": "4.3.2.1"})},
    )


@pytest.fixture
def mocked_serializer_field_with_request_secret_key_context(mocker):
    return mocker.Mock(
        context={
            "request": mocker.Mock(META={"HTTP_X_FORWARDED_FOR": "4.3.2.1"}),
            "recaptcha_secret_key": "from-context",
        },
    )
