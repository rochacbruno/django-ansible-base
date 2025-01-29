from __future__ import annotations

import inspect
import os
import sys
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dynaconf import Dynaconf
from dynaconf.constants import YAML_EXTENSIONS
from dynaconf.loaders import env_loader
from dynaconf.loaders.base import BaseLoader
from dynaconf.loaders.yaml_loader import yaml

from ansible_base.lib.dynamic_config.settings_logic import get_mergeable_dab_settings


def factory(
    name: str,  # main app name to be used to name env_switcher and envvar_prefix
    extra_envvar_prefixes: list[str] | None = None,  # extra prefixes to be used in envvar loader
    **options,  # options to be passed to Dynaconf
) -> Dynaconf:
    """Create a Dynaconf instance for a specific service.

    This function creates a Dynaconf instance with the following options:
    - env_switcher: based on the app name
    - envvar_prefix: based on the app name
    - root_path: based on the caller module path
    - loaders: empty list (to be loaded manually)
    - options: any other options passed to the function (e.g. settings_files)
      some options are not allowed and will raise an error if passed.

    The Dynaconf instance returned will do the following:
    - Define its mode based on the env_switcher e.g. "AWX_MODE"
    - Define its envvar prefix based on the envvar_prefix e.g. "AWX"
    - Consider multiple envvar_prefixes if extra_envvar_prefixes is passed (e.g. "AWX,FOO,BAR")
    - Define STANDARD_SETTINGS_FILES for /etc/ansible-automation-platform/config/
      first load yaml files from the base path, then from the app specific path.
    - Pass all the options to the Dynaconf instance (except the invalid ones)
      e.g:
        - settings_files=["defaults.py"] (this is mainly for default static settings)
        - environments=("development", "production", "quiet", "kube") (this is for modes)
          and allow the load of additional settings files such as `development_defaults.py`

    Once the Dynaconf is instantiated (and settings are loaded), the function will
    add the DAB settings to the Dynaconf instance, and set the `is_development_mode`
    flag based on the current mode.

    Dynaconf object is returned and the caller can perform additional operations
    such as read settings, set additional settings, load more settings files,
    and finally export the settings to the caller module using the `export` function.
    """

    _check_options(options)
    prefix = name.upper()
    name = name.lower()
    frame = inspect.currentframe().f_back
    caller_path = os.path.dirname(inspect.getfile(frame))

    if extra_envvar_prefixes is not None:
        envvar_prefix = ",".join([prefix, *extra_envvar_prefixes])
    else:
        envvar_prefix = prefix

    std_base_path = Path("/etc/ansible-automation-platform/")
    options.setdefault(
        "ANSIBLE_STANDARD_SETTINGS_FILES",
        [
            std_base_path / "settings.yaml",
            std_base_path / "flags.yaml",
            std_base_path / ".secrets.yaml",
            std_base_path / name / "settings.yaml",
            std_base_path / name / "flags.yaml",
            std_base_path / name / ".secrets.yaml",
        ],
    )

    # Set DAB default variables
    options.setdefault(
        "ANSIBLE_BASE_OVERRIDABLE_SETTINGS",
        [
            'INSTALLED_APPS',
            'REST_FRAMEWORK',
            'AUTHENTICATION_BACKENDS',
            'SPECTACULAR_SETTINGS',
            'MIDDLEWARE',
            'OAUTH2_PROVIDER',
            'CACHES',
            'TEMPLATES',
        ],
    )
    options.setdefault("ANSIBLE_BASE_OVERRIDDEN_SETTINGS", [])
    options.setdefault("INSTALLED_APPS", [])
    options.setdefault("MIDDLEWARE", [])
    options.setdefault("REST_FRAMEWORK", {})

    # Create Dynaconf instance with the given options as defaults
    settings = Dynaconf(
        env_switcher=f"{prefix}_MODE",
        envvar_prefix=envvar_prefix,
        root_path=caller_path,
        # Disable default loaders because each file/env will be loaded individually
        loaders=[],
        **options,
    )

    # Add DAB settings
    dab_settings = get_mergeable_dab_settings(settings.to_dict())
    # get all keys from dab_settings set ANSIBLE_BASE_OVERRIDEN_SETTINGS to the keys
    # that are in ANSIBLE_BASE_OVERRIDABLE_SETTINGS
    settings.set(
        "ANSIBLE_BASE_OVERRIDDEN_SETTINGS",
        list(dab_settings.keys() & settings.ANSIBLE_BASE_OVERRIDABLE_SETTINGS),
        loader_identifier="overridden_dab_settings",
    )
    settings.update(dab_settings, loader_identifier="merge_dab_settings")

    # Dynaconf allows composed modes
    # so current_env can be a comma separated string of modes (e.g. "development,quiet")
    settings.set(
        "is_development_mode",
        "development" in settings.current_env.lower(),
        loader_identifier="is_development_mode_check",
    )
    return settings


def export(settings: Dynaconf):
    """Export the settings to the module that called this function.

    In a djangoapp/settings.py this will take all variables from the Dynaconf
    instance and set them as attributes in the settings module
    so they can be accessed as `settings.VARIABLE_NAME` from django.conf.settings.
    """
    frame = inspect.currentframe().f_back
    caller_module_name = frame.f_globals["__name__"]
    settings.populate_obj(
        sys.modules[caller_module_name],
        internal=False,
        ignore=["IS_DEVELOPMENT_MODE"],
    )


def load_standard_settings_files(settings: Dynaconf):
    """Load the standard settings files for Ansible Automation Platform.

    This function loops the `ANSIBLE_STANDARD_SETTINGS_FILES` list in the settings
    and loads each file into the settings object without considering the current env,
    as these files are meant to be environment agnostic.

    NOTE: this function must be replaced by future implementation
    of Dynaconf's `settings.load_file` that will support envless loading.
    """
    loader = BaseLoader(
        obj=settings,
        env=settings.current_env,
        identifier="standard_settings_loader",
        extensions=YAML_EXTENSIONS,
        file_reader=yaml.safe_load,
        string_reader=yaml.safe_load,
        validate=False,
    )
    for path in settings.ANSIBLE_STANDARD_SETTINGS_FILES:
        if not path.exists():
            continue
        data = loader.get_source_data([str(path)])
        loader._envless_load(data)


def load_envvars(settings: Dynaconf):
    """Loads environment variables into the settings object.

    This function exists to be called on-demand after all settings are loaded
    """
    env_loader.load(settings, identifier="dab.dynamic_config")


def _check_options(options):
    """Raise Error if invalid options are passed.

    Invalid options are those that are not allowed in the factory function,
    and must be defined here by Django Ansible Base.
    """
    invalid_options = {
        "envvar_prefix",  # defined based on app name
        "env_switcher",  # defined based on app name
        "root_path",  # defined dynamically by factory
        "validators",  # Cannot be defined because would trigger eager validation
    }
    if invalid_options & set(options.keys()):
        raise ImproperlyConfigured(f"Invalid Dynaconf options: {invalid_options}")


def validate(settings: Dynaconf):
    """Validate the settings according to the validators registered.
    This function operates on a clone of the settings object to avoid
    validation to write to the inspection data.
    """
    settings.dynaconf_clone().validators.validate()
