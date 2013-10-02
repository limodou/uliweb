import uliweb
from uliweb.utils.setup import setup
import apps

__doc__ = """doc"""

setup(name='{{=project_name}}',
    version=apps.__version__,
    description="Description of your project",
    package_dir = {'{{=project_name}}':'apps'},
    packages = ['{{=project_name}}'],
    include_package_data=True,
    zip_safe=False,
)
