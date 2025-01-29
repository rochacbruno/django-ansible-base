import os
import sys
import inspect
from ansible_base.lib.dynamic_config.settings_logic import get_dab_settings
from dynaconf import Dynaconf
from django.core.exceptions import ImproperlyConfigured
from pathlib import Path

def factory(
    name: str,  # main app name to be used to name env_switcher and envvar_prefix
    extra_envvar_prefixes: list[str] | None = None,  # extra prefixes to be used in envvar loader
    **options,  # options to be passed to Dynaconf
) -> Dynaconf:
    """Create a Dynaconf instance for a specific app."""
    # Get the path of the module that called this function
    check_options(options)
    prefix = name.upper()
    name = name.lower()
    frame = inspect.currentframe().f_back
    caller_path = os.path.dirname(inspect.getfile(frame))

    if extra_envvar_prefixes is not None:
        envvar_prefix = ",".join([prefix, *extra_envvar_prefixes])
    else:
        envvar_prefix = prefix

    std_base_path = Path(f"/etc/ansible-automation-platform/config/{name}/")
    options.setdefault(
        "ANSIBLE_STANDARD_SETTINGS_FILES", 
        [
            std_base_path / "settings.yaml",
            std_base_path / "flags.yaml",
            std_base_path / ".secrets.yaml",
        ]
    )

    settings = Dynaconf(
        env_switcher=f"{prefix}_MODE",
        envvar_prefix=envvar_prefix,
        root_path=caller_path,
        **options
    )

    # Add DAB settings
    dab_settings = get_dab_settings(
        installed_apps=settings.INSTALLED_APPS,
        rest_framework=settings.get("REST_FRAMEWORK", {}),
        spectacular_settings=settings.get("SPECTACULAR_SETTINGS", {}),
        authentication_backends=settings.get("AUTHENTICATION_BACKENDS", []),
        middleware=settings.get("MIDDLEWARE", []),
        oauth2_provider=settings.get("OAUTH2_PROVIDER", {}),
        caches=settings.get("CACHES", {}),
    )
    # NOTE: DAB completely overrides the settings and performs its own merging strategy
    # once get_dab_settings starts returning a dict with dynaconf merging logic,
    # such as `NESTED__dunder` or explicit `@merge` , or `dynaconf_merge` keys,
    # then the merge can be set to True
    settings.update(dab_settings, loader_identifier="get_dab_settings", merge=False)

    # Dynaconf allows composed modes 
    # so current_env can be a comma separated string of modes (e.g. "development,quiet")
    settings.set("is_development_mode", "development" in settings.current_env.lower())
    
    return settings
    
    
def export(settings: Dynaconf):
    """Export the settings to the module that called this function."""
    frame = inspect.currentframe().f_back
    caller_module_name = frame.f_globals["__name__"]
    settings.populate_obj(
        sys.modules[caller_module_name], 
        internal=False,
        ignore=["IS_DEVELOPMENT_MODE"],
    )


def load_standard_settings_files(settings: Dynaconf):
    for path in settings.ANSIBLE_STANDARD_SETTINGS_FILES:
        settings.load_file(path)


def check_options(options):
    """Raise Error if invalid options are passed."""
    invalid_options = {
        "envvar_prefix",
        "env_switcher",
        "root_path",
    }
    if invalid_options & set(options.keys()):
        raise ImproperlyConfigured(f"Invalid Dynaconf options: {invalid_options}")