import os, sys
import hotshot
import hotshot.stats
from cStringIO import StringIO

PROFILE_DATA_DIR = "./profile"
class ProfileApplication(object):
    def __init__(self, app):
        self.path = path = PROFILE_DATA_DIR
        if not os.path.exists(path):
            os.makedirs(path)
            os.chmod(path, 0755)
        self.app = app
        
    def __call__(self, environ, start_response):
        profname = "%s.prof" % (environ['PATH_INFO'].strip("/").replace('/', '.'))
        profname = os.path.join(self.path, profname)
        prof = hotshot.Profile(profname)
#        prof.start()
        ret = prof.runcall(self.app, environ, start_response)
        prof.close()
        
        out = StringIO()
        old_stdout = sys.stdout
        sys.stdout = out
        
        stats = hotshot.stats.load(profname)
        #stats.strip_dirs()
        stats.sort_stats('time', 'calls')
        stats.print_stats()
        
        sys.stdout = old_stdout
        stats_str = out.getvalue()
        
        from uliweb.utils.textconvert import text2html
        text = text2html(stats_str)
        outputfile = profname + '.html'
        file(outputfile, 'wb').write(text)
        
        return ret
        
