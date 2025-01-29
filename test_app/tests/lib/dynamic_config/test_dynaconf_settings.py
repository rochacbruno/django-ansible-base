from ansible_base.lib.dynamic_config import factory


def test_swagger_disabled():
    settings = factory("TEST", INSTALLED_APPS=[])
    assert 'drf_spectacular' not in settings['INSTALLED_APPS']


def test_swagger_enabled():
    settings = factory("TEST", INSTALLED_APPS=['ansible_base.api_documentation'])
    assert 'drf_spectacular' in settings['INSTALLED_APPS']
    assert "DEFAULT_SCHEMA_CLASS" in settings['REST_FRAMEWORK']

    assert "TITLE" in settings['SPECTACULAR_SETTINGS']
    assert "DESCRIPTION" in settings['SPECTACULAR_SETTINGS']
    assert "VERSION" in settings['SPECTACULAR_SETTINGS']
    assert "SCHEMA_PATH_PREFIX" in settings['SPECTACULAR_SETTINGS']


def test_authentication_with_backends():
    settings = factory(
        "TEST",
        AUTHENTICATION_BACKENDS=['something'],
        INSTALLED_APPS=['ansible_base.authentication'],
    )
    assert "social_django" in settings['INSTALLED_APPS']
    assert 'ansible_base.authentication.backend.AnsibleBaseAuth' in settings['AUTHENTICATION_BACKENDS']
    assert 'ansible_base.authentication.middleware.AuthenticatorBackendMiddleware' in settings['MIDDLEWARE']
    assert 'ansible_base.authentication.session.SessionAuthentication' in settings['REST_FRAMEWORK']['DEFAULT_AUTHENTICATION_CLASSES']
    assert 'ansible_base.authentication.authenticator_plugins' in settings['ANSIBLE_BASE_AUTHENTICATOR_CLASS_PREFIXES']
    assert 'SOCIAL_AUTH_LOGIN_REDIRECT_URL' in settings
    assert "SOCIAL_AUTH_PIPELINE" in settings
    assert "SOCIAL_AUTH_STORAGE" in settings
    assert "SOCIAL_AUTH_STRATEGY" in settings
    assert "SOCIAL_AUTH_LOGIN_REDIRECT_URL" in settings


def test_authentication_no_backends():
    settings = factory("TEST", INSTALLED_APPS=['ansible_base.authentication'])
    assert 'ansible_base.authentication.backend.AnsibleBaseAuth' in settings['AUTHENTICATION_BACKENDS']


def test_append_middleware():
    settings = factory("TEST", INSTALLED_APPS=['ansible_base.authentication'], REST_FRAMEWORK={}, MIDDLEWARE=['something'])
    assert 'ansible_base.authentication.middleware.AuthenticatorBackendMiddleware' == settings['MIDDLEWARE'][-1]


def test_insert_middleware():
    settings = factory(
        "TEST", INSTALLED_APPS=['ansible_base.authentication'], MIDDLEWARE=['something', 'django.contrib.auth.middleware.AuthenticationMiddleware', 'else']
    )
    assert 'ansible_base.authentication.middleware.AuthenticatorBackendMiddleware' == settings['MIDDLEWARE'][2]


def test_dont_update_class_prefixes():
    settings = factory("TEST", INSTALLED_APPS=['ansible_base.authentication'], ANSIBLE_BASE_AUTHENTICATOR_CLASS_PREFIXES=['other.things'])
    assert 'ansible_base.authentication.authenticator_plugins' not in settings['ANSIBLE_BASE_AUTHENTICATOR_CLASS_PREFIXES']


def test_filtering():
    settings = factory("TEST", INSTALLED_APPS=['ansible_base.rest_filters'], REST_FRAMEWORK={'something': 'else'})
    assert 'ansible_base.rest_filters.rest_framework.type_filter_backend.TypeFilterBackend' in settings['REST_FRAMEWORK']['DEFAULT_FILTER_BACKENDS']
    assert 'something' in settings['REST_FRAMEWORK']


def test_rbac_required_settings():
    settings = factory("TEST", INSTALLED_APPS=['ansible_base.rbac'])
    rbac_expected_settings = [
        'ANSIBLE_BASE_MANAGED_ROLE_REGISTRY',
        'ANSIBLE_BASE_CREATOR_DEFAULTS',
        'ANSIBLE_BASE_CHECK_RELATED_PERMISSIONS',
        'ANSIBLE_BASE_ROLE_CREATOR_NAME',
        'ANSIBLE_BASE_ROLES_REQUIRE_VIEW',
        'ANSIBLE_BASE_DELETE_REQUIRE_CHANGE',
        'ANSIBLE_BASE_ALLOW_TEAM_PARENTS',
        'ANSIBLE_BASE_ALLOW_TEAM_ORG_PERMS',
        'ANSIBLE_BASE_ALLOW_TEAM_ORG_MEMBER',
        'ANSIBLE_BASE_ALLOW_TEAM_ORG_ADMIN',
        'ANSIBLE_BASE_ALLOW_CUSTOM_ROLES',
        'ANSIBLE_BASE_ALLOW_CUSTOM_TEAM_ROLES',
        'ANSIBLE_BASE_ALLOW_SINGLETON_USER_ROLES',
        'ANSIBLE_BASE_ALLOW_SINGLETON_TEAM_ROLES',
        'ANSIBLE_BASE_ALLOW_SINGLETON_ROLES_API',
        'ANSIBLE_BASE_EVALUATIONS_IGNORE_CONFLICTS',
        'ANSIBLE_BASE_BYPASS_SUPERUSER_FLAGS',
        'ANSIBLE_BASE_BYPASS_ACTION_FLAGS',
        'ANSIBLE_BASE_CACHE_PARENT_PERMISSIONS',
        'ALLOW_LOCAL_RESOURCE_MANAGEMENT',
        'ALLOW_LOCAL_ASSIGNING_JWT_ROLES',
        'ALLOW_SHARED_RESOURCE_CUSTOM_ROLES',
        'MANAGE_ORGANIZATION_AUTH',
        'ANSIBLE_BASE_RBAC_MODEL_REGISTRY',
        'ORG_ADMINS_CAN_SEE_ALL_USERS',
    ]
    assert set(rbac_expected_settings) == set(settings.keys() & rbac_expected_settings)


def test_resource_registry_required_settings():
    settings = factory("TEST", INSTALLED_APPS=['ansible_base.resource_registry'])
    resource_registry_expected_settings = [
        'RESOURCE_SERVER_SYNC_ENABLED',
        'RESOURCE_SERVICE_PATH',
        'ENABLE_SERVICE_BACKED_SSO',
    ]
    assert set(resource_registry_expected_settings) == set(settings.keys() & resource_registry_expected_settings)
