import os
import sys
import inspect
from ansible_base.lib.dynamic_config.settings_logic import get_dab_settings
from dynaconf import Dynaconf


def factory(name: str, **options) -> Dynaconf:
    # Get the path of the module that called this function
    frame = inspect.currentframe().f_back
    caller_path = os.path.dirname(inspect.getfile(frame))

    settings = Dynaconf(
        env_switcher=f"{name}_MODE",
        envvar=f"{name}_SETTINGS",
        envvar_prefix=name,
        root_path=caller_path,
        **options
    )
    # settings.update(get_dab_settings(...))
    return settings
    
    
def export(settings: Dynaconf):
    frame = inspect.currentframe().f_back
    caller_module_name = frame.f_globals["__name__"]
    settings.populate_obj(sys.modules[caller_module_name], internal=False)
    