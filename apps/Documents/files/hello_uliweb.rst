Hello, Uliweb
================

:Author: Limodou <limodou@gmail.com>

.. contents:: 
.. sectnum::

This tutorial will get you started with the Uliweb framework. 
In the following simple demo, we're going to generate a plain page 
which displays "Hello, Uliweb." step by step.

Getting Started
-----------------

The first thing would be to read this article `Installation <installation>`_,
 a correct installation of Uliweb is a prerequisite.

Creating a new project
------------------------

Uliweb provides a command line tool named ``uliweb``, you can use
it to execute several commands. 

At the command line,  change to or create a directory in which you want to create new
Uliweb project,  then execute:

::

    uliweb makeproject project
    
If the command execution is successful, it'll output nothing and create a
directory named ``hello_project``. A clean workspace is created with relevant files
for the project in this directory.

The project folder will be::

    |-- app.yaml
    |-- apps/
    |   `-- settings.ini
    |-- gae_handler.py
    |-- runcgi.py
    `-- wsgi_handler.wsgi

Creating the 'Hello' app
---------------------------

.. code::

    cd project
    uliweb makeapp Hello
    
Go into ``project`` directory, create a new app following the command as
shown. You can substitute the name of the app, ``Hello`` with another name of your choice.

After the command above is executed successfully, 
you can find the following files in ``apps/Hello`` directory::

    |-- __init__.py
    |-- conf.py
    |-- info.ini
    |-- static/
    |   `-- readme.txt
    |-- templates/
    |   `-- readme.txt
    `-- views.py

Starting the server
-----------------------

After the above steps, you can start up your web project as follows:

::

    uliweb runserver
    
Following the instructions and information printout to the console, you can 
open a browser and enter the url http://localhost:8000.  You would see a rendered
page with the message "Hello, Uliweb" . Congratulations!

Modifying the "View" 
----------------------------

When user requests an URL, Uliweb tries to map the URL to a view function. So in 
the case of our example, the request for http://localhost:8000 would map to a function
thatmaps to the "/" location on our server. To see how this works, take a look in
the ``Hello/view.py`` file. All your view functions should be declared in this file.
Open it in your favourite editor, then you will see:

.. code:: python

    #coding=utf-8
    from uliweb import expose
    
    @expose('/')
    def index():
        return '<h1>Hello, Uliweb</h1>'

The above code was generated automatically when you executing ``makeapp``, 
and we even don't need write any code, the  !

``@expose('/')`` decorator is used for URL Mapping, which means map the url ``'/'`` to 
the view function below. So when visiting http://localhost:8000, function ``index()`` 
will be called. If a view function is not decorated by ``expose``, it will not 
be mapped to any url and is treated as a local function.

This function will return a line of HTML code that will be displayed directly in browser.

Adding templates
-------------------

If your view function returns a dict object, Uliweb will apply it to a template automatically.
It means that different return value will cause a different action.
The template is the same name as your view function with '.html' suffix.
For example, the template of ``index()`` is ``index.html``. 
Templates should be placed into the directory ``templates`` which will be automatically
created when creating a new app. Now let's add a new function to test template
process.

.. code:: python

    @expose('/template')
    def template():
        return {}

Then create a new file ``template.html`` in ``apps/Hello/templates`` with contents 
like below:

.. code:: html

    <h1>Hello, Uliweb</h1>
    
Visit http://localhost:8000/template in the browser, you will see the same thing as the previous one.

Using template variables
---------------------------

In above two examples, all data are outputed directly, we're going to use template
variables to change that. Add another view function with the following code:

.. code:: python

    @expose('/template1')
    def template1():
        return {'content':'Uliweb'}

The function ``template1()`` returns a dict object with ``content`` which representing 
the content to be displayed. If you feel uncomfortable with the ``{}``, try 
this alternative:

.. code:: python

    return dict(content='Uliweb')
    
or:

.. code:: python

    content = 'Uliweb'
    return locals()
    
The first one uses ``dict()`` to construct a dict object while 
the second one uses the builtin function ``locals()`` directly - as long as you 
define the corresponding variables in current scope. Although ``locals()`` may 
return some irrelevant variables, it is not harmful.

Then create ``template1.html`` in ``apps/Hello/templates`` with contents like below:

.. code:: html

    <h1>Hello, {{=content}}</h1>

``{{=content}}`` represents outputing value of ``content`` to template. Here you can use a 
variable or a function with return value between ``{{=`` and ``}}``.

.. note::

    The development server provided by Uliweb has the ability to reload apps, 
    you don't need to restart the server too often when making changes - 
    refreshing you browser is enough in most situations. However, when 
    you are struck with templates cache or something goes wrong seriously, 
    you do need to restart it. Pressing Ctrl + C in command line can shutdown 
    the server, and then you can restart it.

End
------

This tutorial only demonstrates some fundamental things like view and templates 
and lots of topics are not mentioned, such as:

* Organizing Apps
* Using Database
* Configurations
* etc.

You can find other documentation at http://uliwebproject.appspot.com.
