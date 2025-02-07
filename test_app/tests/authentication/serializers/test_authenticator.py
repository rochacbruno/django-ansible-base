import uuid
from unittest import mock

import pytest
from django.utils.text import slugify
from rest_framework.serializers import ValidationError

from ansible_base.authentication.serializers import AuthenticatorSerializer


def test_validate_blank_authenticator_slug(shut_up_logging):
    serializer = AuthenticatorSerializer()
    try:
        assert uuid.UUID(serializer.validate_slug(""))
    except ValueError:
        pytest.fail("uuid not generated if a blank slug is provided")


def test_validate_new_authenticator_slug(shut_up_logging):
    slug = str(uuid.uuid4())

    serializer = AuthenticatorSerializer()
    assert serializer.validate_slug(slug) == slugify(slug)


@pytest.mark.django_db
def test_removed_authenticator_plugin(ldap_authenticator, shut_up_logging):
    serializer = AuthenticatorSerializer()
    item = serializer.to_representation(ldap_authenticator)
    assert 'error' not in item
    assert 'configuration' in item
    assert item['configuration'] != {}

    # Change the type of the LDAP authenticator
    ldap_authenticator.type = 'junk'
    item = serializer.to_representation(ldap_authenticator)
    assert 'error' in item
    assert 'configuration' in item
    assert item['configuration'] == {}


def test_authenticator_no_configuration(shut_up_logging):
    serializer = AuthenticatorSerializer()
    with pytest.raises(ValidationError):
        serializer.validate(
            {
                "name": "Local Test Authenticator",
                "enabled": True,
                "create_objects": True,
                "remove_users": False,
                "type": "ansible_base.authentication.authenticator_plugins.local",
                "order": 497,
            }
        )


def test_authenticator_validate_import_error(shut_up_logging):
    serializer = AuthenticatorSerializer()
    with (
        mock.patch(
            "ansible_base.authentication.serializers.authenticator.AuthenticatorSerializer.context",
            return_value={'request': {'method': 'PUT'}},
        ),
        mock.patch(
            "ansible_base.authentication.serializers.authenticator.get_authenticator_plugin",
            side_effect=ImportError(),
        ),
    ):
        with pytest.raises(ValidationError):
            serializer.validate(
                {
                    "name": "Local Test Authenticator",
                    "enabled": True,
                    "create_objects": True,
                    "remove_users": False,
                    "configuration": {},
                    "type": "ansible_base.authentication.authenticator_plugins.local",
                    "order": 497,
                }
            )


@pytest.mark.django_db
def test_disable_last_enabled_authenticator(system_user, local_authenticator):
    # NOTE: The serializer is only used for PUT/POST/PATCH. A DELETE
    # is only processed at the view and model level and would be tested
    # there instead.

    # Instantiate a serializer
    serializer = AuthenticatorSerializer()

    # the serializer won't have an object instance to check
    # for the current state of the enabled field unless we
    # manually set it here ...
    serializer.instance = local_authenticator

    # we have mock out the request method so that it doesn't bomb out on an empty config
    with mock.patch(
        "ansible_base.authentication.serializers.authenticator.AuthenticatorSerializer.context",
        return_value={'request': {'method': 'PATCH'}},
    ):
        # validation should fail ...
        with pytest.raises(ValidationError) as exc_info:
            serializer.validate(
                {
                    'id': local_authenticator.id,
                    'type': local_authenticator.type,
                    'name': local_authenticator.name,
                    'enabled': False,
                    'configuration': {},
                }
            )

    assert "At least one authenticator must be enabled" in str(exc_info.value)
