URL Mapping
=============

:Author: Limodou <limodou@gmail.com>

.. contents:: 
.. sectnum::

Uliweb uses Werkzeug's routing.py module to process URLs. When you use ``makeapp`` 
command to create a new app directory, it'll automatically create a ``views.py``,
and it'll automatically add some code for you, for example:

.. code:: python

    from uliweb.core.SimpleFrame import expose
    
So that you can directly use expose in view modules. ``expose`` is a decorator
function. Using it you can binding an URL with a view function, and create
reversed URL later by ``url_for`` function(It's another function provided by 
SimpleFrame).

expose Description
----------------------

For now, Uliweb doesn't support centralized URL management, so you need to add
expose in front of each view function. If there is no expose, the function will
not be visited by browser.

Basic usage is:

#. Default Mapping

   .. code:: python

        @expose
        def index(arg1, arg2):
            return {}
        
   When there is no arguments in expose(), it'll execute default mapping process.
   So the URL would be mapped to:

   ::

        /appname/view_function_name/<arg1>/<arg2>
    
   And if there is no arugments in view function, the URL would be mapped to:

   ::

        /appname/view_function_name
    
#. Specified Mapping

   .. code:: python

        @expose('/index')
        def index():
            return {}
            
   You can specify any URL you want to use in expose() function, this URL will
   be bound to below view function.
    
#. Argument Process

   If there are something can be changed in the URL, you can configure them as
   arguments. A basic argument format is like:

   .. code:: python

        <convertor(arguments):name>
    
   ``convertor`` and ``arguments`` can be omitted. convertor can be set as: int, float,
   any, string, unicode, path now. Different convertor can accept different
   arguments. More details please see below section about convertor Description.
   The simplest format is ``<name>``, it'll match the stuff between ``'/'`` and ``'/'``.

   For ``name``, it's the argument name, it needs to be matched with the arugments
   of view function it bounded.

#. Other arguments of expose

   ``expose`` function enable other arguments except for the first URL string, for example:

   defaults

        It can be used for defining the default arguments value of view function 
        argument, for example, you can do:
        
        .. code:: python
        
            @expose('/all', defaults={'page': 1})
            @expose('/all/page/<int:page>')
            def show(page):
                return {}
                
        You can see above two URLs will be bound to the same ``show()`` function, but because
        ``show()`` need a ``page`` argument, so for the first URL, you should define
        a default value of ``page`` argument.
        
    build_only
    
        If it be set as ``True``, then it means that this binding will only be used for 
        creating reversed URL, it'll not be used for matching URL. For now, Uliweb
        provide static files serving, just add static file serving view function
        to view modules, and bind static URL to this view function.
        But you may want to use web server(Like Apache) to serve static files.
        And you probablely have already used ``url_for`` to create reversed URL,
        then you can set this argument to ``True``, so that the ``url_for`` can be
        still enabled, but URL matching will be disabled.
        
    There are more arguments you can use in ``expose`` function, you can see the 
    routing.py of Werkzeug for more details.
    
.. note::

    In non-GAE environment, you don't need to import expose explicitly, because
    Uliweb has already put it in __builtin__, so you can use it directly. But in GAE,
    it'll disable this process, so you need to import it explicitly. But if you use
    makeapp to create a new app, Uliweb has already put this line in views.py.
    
url_for Description
-----------------------

url_for can be used for creating reversed URL, it need a string format view
function name, for example:

.. code:: python

    url_for('appname.views_module_name.function_name', **kwargs)
    
kwargs will match with the arguments of view function.

Let's see an example. Say you define an URL in ``Hello`` app:

.. code:: python

    @expose('/index')
    def index():
        pass
        
Then when you want to get reversed URL, you can do:

.. code:: python

    url_for('Hello.views.index') #Result will be '/index'
    
If you don't want to hard code app name here, you can do:

.. code:: python

    url_for('%s.views.index' % request.appname)
    
``request`` is request object, and it has a ``appname`` attribute, it's the current
app name.

.. note::

    For now, you can use url_for directory in both view functions and templates
    without import it explicitly.
    
convertor Description
------------------------

* int

  Basic format is:

  ::

    <int:name>                      #Simple format
    <int(fixed_digits=4):name>      #With arguments
    
  Supported arguments are:

  * fixed_digits Fixed length
  * min Minimum
  * max Maximum

* float

  Basic format is:

  ::

    <float:name>                    #Simple format
    <float(min=0.01):name>          #With arguments
    
  Supported arguments are:

  * min Minimum
  * max Maximum

* string and unicode

  They are the same actually

  Basic format is:

  ::

    <string:name>
    <unicode(length=2):name>
    
  Supported arguments are:

  * minlength Minimal length
  * maxlength Maximal length
  * length Fixed length

* path

  Just like ``string`` and ``unicode`` convertor, but has no arguments.
  Used to match stuff between ``'/'`` and next string or the end.

  Basic format is:

  ::

    <path:name>
    
  Example:

  ::

    '/static/<path:filename>'
  
  can match:

  ::

    '/static/a.css'         -> filename='a.css'
    '/static/css/a.css'     -> filename='css/a.css'
    '/static/image/a.gif'   -> filename='image/a.gif'

* any

  Basic format is:

  ::

    <any(about, help, imprint, u"class"):name>

  It'll match any of string listed.

