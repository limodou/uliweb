Global Environment
======================

:Author: Limodou <limodou@gmail.com>

.. contents:: 
.. sectnum::

Uliweb provides essential runtime environment and objects, that's I call them
global environment.

Objects
--------

Some globally objects can be easily imported from ``uliweb``, for example:

.. code:: python

    from uliweb import application, request, response, settings, Request, Response

application
~~~~~~~~~~~~~

It's a unique object which is used as Uliweb project instance object. It's
the instance of ``uliweb.core.SimpleFrame.Dispatcher``, and there are several
attributes and properties you can use, for example:

apps
    It'll enumerate all available Apps name of current application instance. It's
    a list, for example: ``['Hello', 'uliweb.contrib.staticfiles']``
    
apps_dir
    It's apps directory of current application instance.
    
template_dirs
    It's the collection of all available Apps template searching directory of 
    current application.
    
get_file(filename, dir='static')
    Searching a file from all available Apps relative directory, default is ``static``
    directory. And it'll begin to search from current request App, if not found,
    it'll search from other apps.
    
template(filename, vars=None, env=None)
    Renderring a template, and it'll begin to search from current request App for
    the template file. ``vars`` is a dict object. If you don't provide an ``env`` object, 
    it'll use the default environment. If you want to inject other objects but
    not provided in vars, you don't need to change env directly, but via dispatch
    machenism to bind ``prepare_view_env`` topic, it'll be ok.
        
    This function will return the renderred string object.
    
render(filename, vars, env=None)
    It's very like template, but it'll return a Response instance directly, but 
    not a string object.
    
Request
~~~~~~~~~~~~

This Request class is inherit from Request of werkzeug, the different between them
is:

    I add some compatibilities to it. The original Request class of werkzeug
    has not GET, POST, params, FILES such properties, instead of: args, form,
    values, files, and in order to compatibily with other Request class,
    I add GET, POST, params, FILES to it.
    
Response
~~~~~~~~~~~~

This Response is also inherit from Response class of werkzeug, the different is:

    add a ``write`` method. There is no such method of original Response class
    of werkzeug, but there is a ``stream`` property, and there is ``write`` method on
    it. So after extending, you can use write method directly, it'll be handy more I 
    think.
    
request
~~~~~~~~~~~~

request is a proxy object about the instance of Request class, so it's not a 
real Request object, response is also like that. But you can treat them as real
Request and Response instances to use. So why do that, the important reason is
handy. You may run your application in multiple threaded circumstance, so in order
to keep thread safe, request and response will be created in thread local environment.
And use these proxy objects, user don't need to care about the thread environment,
just use request and response is ok, they will do the work for you. The real
Request and Response objects will be saved in local.request and local.response.

.. note::

    request and response have life cycle, they are created when the request is 
    received, and invalided after the response is returned. So when you use them,
    please ensure they are in the life cycle.

When we talk about the environment of View, we said that: when writing view function,
there are some objects which can be treated as global objects. request and 
response are just in them. And one different between them and others are the life
cycle, request and response are thread relative and have temporary life cycle, but
others have whole life cycle along with the project instance.

If we want to use request and response in non-view functions, one way is passing
request and response to them, but it's ugly. The other way to use them is to import
them from uliweb, it'll be very handy.
    
response
~~~~~~~~~~~~

It's just like request, it's a proxy object of the Response instance too.
    
settings
~~~~~~~~~~~

Settings configure object.

Methods
--------

For example:

.. code:: python

    from uliweb import (redirect, json, POST, GET, post_view, 
        pre_view, url_for, expose, get_app_dir, get_apps
        )

redirect
~~~~~~~~~~

.. code:: python

    def redirect(location, code=302):
    
Return a Response object, cause browser redirect to a new ULR.

json
~~~~~~~~

.. code:: python

    def json(data):
    
Convert the data to json format, and return it as a Response object.

expose
~~~~~~~~~

See details in `URL映射 <url_mapping>`_

POST
~~~~~

Just like expose, but only matched when the request method is ``POST``.

GET
~~~~~

Just like expose, but only matched when the request method is ``GET``.

url_for
~~~~~~~~~

.. code:: python

    def url_for(endpoint, **values):

It'll return reversed URL according the endpoint argument. endpoint can be 
string format, just like: ``Hello.view.index``, and you can also pass it a 
real function object.

get_app_dir
~~~~~~~~~~~~~~

.. code:: python

    def get_app_dir(app):

It'll return the directory of the app.

get_apps
~~~~~~~~~~~

.. code:: python

    def get_apps(apps_dir, include_apps=None):
    
It'll return a list of all available app's name according the apps argument. apps
is the project/apps directory.