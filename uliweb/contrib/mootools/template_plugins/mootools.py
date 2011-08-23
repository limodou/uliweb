def call(app, var, env, version=None, more=True):
    a = []
    if version:
        version = '-%s' % version
    else:
        version = ''
    a.append('mootools/mootools%s-core.js' % version)
    if more:
        a.append('mootools/mootools%s-more.js' % version)
    return {'toplinks':a}
