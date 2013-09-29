import sys, os
import getopt
from gevent import monkey
from socketio.server import SocketIOServer

monkey.patch_all()

hostname = '127.0.0.1'
port = 80

opts, args = getopt.getopt(sys.argv[1:], "h:p:", [])
for o, a in opts:
    if o == '-h':
        hostname = a
    elif o == '-p':
        port = int(a)

path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.insert(0, path)

from uliweb.manage import make_simple_application
application = make_simple_application(project_dir=path)

SocketIOServer((hostname, port), application, resource="socket.io").serve_forever()
