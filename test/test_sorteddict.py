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
    """

def test_init():
    """
    >>> d = SortedDict({'a':'b', 'c':'d'})
    >>> d[1] = 'e'
    >>> d[2] = 'f'
    >>> d.items()
    [('a', 'b'), ('c', 'd'), (1, 'e'), (2, 'f')]
    """

def test_kvio():
    """
    >>> d = SortedDict(kvio=True)
    >>> d[1] = 'e'
    >>> d[2] = 'f'
    >>> d.items()
    [(1, 'e'), (2, 'f')]
    >>> repr(d)
    "<SortedDict {1:'e', 2:'f'}>"
    >>> d[1] = 'c'
    >>> d.keys()
    [2, 1]
    """


def test_setitem_append():
    """
    >>> d = SortedDict()
    >>> d[1] = 'e'
    >>> d[2] = 'f'
    >>> d.items()
    [(1, 'e'), (2, 'f')]
    >>> d.__setitem__(1, 'c', append=True)
    >>> d.keys()
    [2, 1]
    """

def test_attr():
    """
    >>> d = SortedDict()
    >>> d.name = 1
    >>> d.keys()
    ['name']
    >>> d.name
    1
    >>> d._name = 2
    >>> d.keys()
    ['name']
    >>> d._name
    2
    >>> del d.name
    >>> d.keys()
    []
    >>> del d._name
    """
