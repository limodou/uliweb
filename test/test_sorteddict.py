from uliweb.utils.sorteddict import SortedDict

def test_1():
    """
    >>> d = SortedDict()
    >>> d[2] = {'id':'a', 'name':'a2'}
    >>> d[4] = {'id':'d', 'name':'a4'}
    >>> d[3] = {'id':'c', 'name':'a3'}
    >>> d[1] = {'id':'b', 'name':'a1'}
    >>> d.items()
    [(2, {'id': 'a', 'name': 'a2'}), (4, {'id': 'd', 'name': 'a4'}), (3, {'id': 'c', 'name': 'a3'}), (1, {'id': 'b', 'name': 'a1'})]
    >>> d.sort()
    >>> d.items()
    [(1, {'id': 'b', 'name': 'a1'}), (2, {'id': 'a', 'name': 'a2'}), (3, {'id': 'c', 'name': 'a3'}), (4, {'id': 'd', 'name': 'a4'})]
    """