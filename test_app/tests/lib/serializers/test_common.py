import pytest
from crum import impersonate

from ansible_base.authentication.models import AuthenticatorMap
from ansible_base.lib.serializers.common import CommonModelSerializer
from ansible_base.lib.utils.encryption import ENCRYPTED_STRING
from test_app.models import EncryptionModel
from test_app.serializers import EncryptionTestSerializer


@pytest.mark.django_db
def test_representation_of_encrypted_fields():
    model = EncryptionModel.objects.create()
    serializer = EncryptionTestSerializer()
    response = serializer.to_representation(model)
    assert response['testing1'] == ENCRYPTED_STRING
    assert response['testing2'] == ENCRYPTED_STRING


@pytest.mark.django_db
def test_update_of_encrypted_fields():
    model = EncryptionModel.objects.create()
    updated_data = {'testing1': 'c', 'testing2': ENCRYPTED_STRING}
    serializer = EncryptionTestSerializer()
    serializer.update(model, updated_data)
    updated_model = EncryptionModel.objects.first()
    assert updated_model.testing1 == 'c'
    assert updated_model.testing2 == EncryptionModel.testing2.field.default


def test_related_of_none():
    serializer = CommonModelSerializer()
    assert serializer._get_related(None) == {}


@pytest.mark.django_db
def test_related_of_model_with_related(ldap_authenticator):
    model = AuthenticatorMap.objects.create(
        authenticator=ldap_authenticator,
        map_type='always',
    )
    serializer = CommonModelSerializer()
    assert serializer._get_related(model) == {'authenticator': f'/api/v1/authenticators/{ldap_authenticator.id}/'}


@pytest.mark.django_db
def test_related_of_model_with_no_related(ldap_authenticator):
    model = EncryptionModel()
    serializer = CommonModelSerializer()
    assert serializer._get_related(model) == {}


@pytest.mark.django_db
def test_no_reverse_url_name():
    model = EncryptionModel.objects.create()
    serializer = EncryptionTestSerializer()
    assert serializer.get_url(model) == ''


def test_summary_of_none():
    serializer = CommonModelSerializer()
    assert serializer._get_summary_fields(None) == {}


@pytest.mark.django_db
def test_summary_of_model_with_no_summary(ldap_authenticator):
    model = EncryptionModel()
    serializer = CommonModelSerializer()
    assert serializer._get_summary_fields(model) == {}


@pytest.mark.django_db
def test_summary_of_model_with_summary(ldap_authenticator):
    model = AuthenticatorMap.objects.create(
        authenticator=ldap_authenticator,
        map_type='always',
    )
    serializer = CommonModelSerializer()
    assert serializer._get_summary_fields(model) == {'authenticator': {'id': ldap_authenticator.id, 'name': ldap_authenticator.name}}


@pytest.mark.django_db
def test_summary_of_model_with_created_user(user, ldap_authenticator):
    with impersonate(user):
        model = AuthenticatorMap.objects.create(
            authenticator=ldap_authenticator,
            map_type='always',
        )
    assert model.created_by == user
    serializer = CommonModelSerializer()

    summary_fields = serializer._get_summary_fields(model)
    expected_summary = {'username': user.username, 'first_name': user.first_name, 'last_name': user.last_name, 'id': user.id}
    assert summary_fields['created_by'] == expected_summary
    assert summary_fields['modified_by'] == expected_summary

    assert serializer._get_related(model) == {
        'authenticator': f'/api/v1/authenticators/{ldap_authenticator.pk}/',
        'created_by': f'/api/v1/users/{user.pk}/',
        'modified_by': f'/api/v1/users/{user.pk}/',
    }
