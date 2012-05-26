import sys, os

path = os.path.dirname(os.path.abspath(__file__))
project_path = os.path.join(path, 'project')
sys.path.insert(0, project_path)
sys.path.insert(0, os.path.join(path, 'lib'))

from uliweb.manage import make_application
application = make_application(project_dir=project_path)
