import sys, os

path = os.path.dirname(os.path.abspath(__file__))
project_path = path
sys.path.insert(0, project_path)
sys.path.insert(0, os.path.join(path, 'lib'))

from uliweb.manage import make_application
from werkzeug.serving import run_simple
application = make_application(project_dir=project_path)

run_simple('0.0.0.0',  int(os.environ.get('PORT', 5000)), application)
