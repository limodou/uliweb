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

