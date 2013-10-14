import time
from contextlib import contextmanager

@contextmanager
def timeit(output):
    """
    If output is string, then print the string and also time used
    """
    b = time.time()
    yield
    print output, 'time used: %.3fs' % (time.time()-b)