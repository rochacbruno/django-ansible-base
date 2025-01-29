"""
Instantiate the DYNACONF instance and export the settings to Django settings.
Any variable is overridable by environment variables prefixed with TESTAPP_.
Application current mode can be configured with TESTAPP_MODE environment variable.
by default it will be development.
"""

import sys

from ansible_base.lib.dynamic_config import export, factory, load_envvars, load_standard_settings_files, validate

if "pytest" in sys.modules:
    # https://github.com/agronholm/typeguard/issues/260
    # Enable runtime type checking only for running tests
    # must be done here because python hooks will not reliably call the
    # typguard plugin setup before other plugins which setup Django, which loads settings.
    # Lower in this settings file, the dynamic config imports ansible_base
    from typeguard import install_import_hook

    install_import_hook(packages=["ansible_base"])

# Create a the standard DYNACONF instance which will come with DAB defaults
# This loads defaults.py and environment specific file e.g: development_defaults.py
DYNACONF = factory(
    "TESTAPP",
    environments=("development", "sqlite"),
    settings_files=["defaults.py"],
)

# Load new standard settings files from
#  /etc/ansible-automation-platform/ and /etc/ansible-automation-platform/testapp/
load_standard_settings_files(DYNACONF)

# Set overrides that must be set after DAB and file settings are loaded
DYNACONF.set(
    "ANSIBLE_BASE_JWT_MANAGED_ROLES",
    "@merge System Auditor",
    loader_identifier="add_system_auditor",
)

# Load envvars at the end to allow them to override everything loaded so far
load_envvars(DYNACONF)

# Update django.conf.settings with DYNACONF keys.
export(DYNACONF)

# Validate the settings according to the validators registered
validate(DYNACONF)
