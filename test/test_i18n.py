from uliweb.i18n import ugettext_lazy as _

def test_1():
    """
    >>> x = _('Hello')
    >>> print repr(x)
    ugettext_lazy('Hello')
    """

def test_1():
    """
    >>> x = _('Hello {0}')
    >>> print x.format('name')
    Hello name
    """