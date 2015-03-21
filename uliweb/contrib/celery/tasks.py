# common celery task
# It'll be used for any common function as celery task

from uliweb import functions
from uliweb.utils.common import import_attr

@functions.async_task
def common_celery_task(func, *args, **kwargs):
    f = import_attr(func)
    return f(*args, **kwargs)