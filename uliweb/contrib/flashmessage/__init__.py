def prepare_default_env(sender, env):
    env['get_flashed_messages'] = get_flashed_messages
    env['flash'] = flash

def flash(message, category='success'):
    from uliweb import request
    
    request.session.setdefault('_flashed_messages', []).append((category, message))
    
def get_flashed_messages():
    from uliweb import request
    if hasattr(request, 'session'):
        return request.session.pop('_flashed_messages', [])
    else:
        return []