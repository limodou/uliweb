import uliweb
from uliweb.utils.setup import setup
import apps

__doc__ = """doc"""

setup(name='test_extorm',
    version=apps.__version__,
    description="Description of your project",
    package_dir = {'test_extorm':'apps'},
    packages = ['test_extorm'],
    include_package_data=True,
    zip_safe=False,
)
