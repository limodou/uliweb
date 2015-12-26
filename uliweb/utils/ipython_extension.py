def make_shell_env(**kwargs):
    import os
    import sys
    from uliweb import functions, settings
    from uliweb.core.SimpleFrame import Dispatcher
    from uliweb.manage import make_simple_application

    project_dir = '.'
    application = make_simple_application(project_dir=project_dir)

    if project_dir not in sys.path:
        sys.path.insert(0, project_dir)

    app = application
    while app:
        if isinstance(app, Dispatcher):
            break
        else:
            app = app.app

    env = {'application':app, 'settings':settings, 'functions':functions}
    return env

def patch_ipython():
    from IPython.lib import pretty
    import IPython.core.formatters as formatters

    def _safe_get_formatter_method(obj, name):
        """Safely get a formatter method

        Enable classes formatter method
        """
        method = pretty._safe_getattr(obj, name, None)
        if callable(method):
            # obj claims to have repr method...
            if callable(pretty._safe_getattr(obj, '_ipython_canary_method_should_not_exist_', None)):
                # ...but don't trust proxy objects that claim to have everything
                return None
            return method
    formatters._safe_get_formatter_method = _safe_get_formatter_method
