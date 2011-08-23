uliweb Command Guide
=====================

:Author: Limodou <limodou@gmail.com>

.. contents:: 
.. sectnum::


``uliweb`` is a command line tool provided by Uliweb, you can use it to do
many works. When you install Uliweb from::

    python setup.py develop
    
or::

    python setup.py install
    
or::

    easy_install uliweb
    
it'll create a script named ``uliweb`` in Python/Scripts folder. So if you
want to use it directly in command line, you should setup Python installation
path and Python/Scripts path to ``PATH`` environment variable. When you finish
it, then you can run ``python`` and ``uliweb`` directly in command line.

``uliweb`` tool supports many action, I'll explain them one by one below.

runserver
-------------

Startup development server.

::

    Usage: uliweb runserver [options] 
    
    options:
    
    -h hostname
    
        Development server host name, default is ``localhost``.
        
    -p port
    
        Development server host port, defalt is ``8000``.
        
    --no-reloader
    
        If automatically reload changed modules when you made some changes, default
        is ``True``.
        
    --no-debugger
    
        If automatically show debug page when there is exception throwed, default
        is ``True``.
        
Example:

::

    uliweb runserver
    
runadmin
-------------

Start developing server with admin app.

::

    Usage: uliweb runadmin
    
It's very like ``runserver`` command, but the difference is it'll automatically
add admin app to your project.
    
makeproject
--------------

Create a new project directory according the given project name. If there is already
a same name project exists, it'll prompt that if you want to overwrite it, you can 
choice 'y' or 'n'.

::

    Usage: uliweb makeproject projectname

Example:

::

    uliweb makeproject test

makeapp
-------------

Create a new app directory structure according the given app name, it'll include
initial sub-directories and files. After you created project, you should change
current path to the project folder first. Say the project folder is ``./test``, 
after you created the project, there should be a ``apps`` sub-folder in ``./test``, so
``./test/apps`` is the exactly apps directory. And if you execute ``makeapp`` command,
it'll find the ``apps`` folder in current directory, and create app folder in ``apps``
folder. If there is no ``apps`` foder in current directory, it'll create a ``apps`` 
folder in current directory, then create app folder in ``apps`` folder.

::

    Usage: uliweb makeapp appname
  
Example:

::

    uliweb makeproject test
    cd test
    uliweb makeapp Hello 
    
It'll create a Hello app in ``./test/apps`` directory of ``test`` project folder, 
the app folder name is ``Hello``.

makepkg
----------

::

    Usage: uliweb makepkg pkgname

Creating a directory according Python package structure, that's including a 
__init__.py in it.

exportstatic
---------------

Export all files from availabe apps static directory to target directory.
You can set availabe apps name in apps/settings.py via INSTALLED_APPS option, for
example: INSTALLED_APPS=['Hello', 'Documents']. If you didn't set it, all folders
in apps will be treated as an available app. When exporting static files, if there
are some files with same name, it'll be checked if the content is the same by 
default, and give you some messages in the console, and skip this file. But you
can disable this check of cause.

::

    Usage: uliweb exportstatic [options] outputdir
    
    options:
    
    -v
    
        Output verbose information, default is not output.
        
    -no-check
    
        If check the same named files content, default is enabled, if found,
        it'll output some message and skip the file. 
        
Example:

::

    uliweb exportstatic ../uliweb_test   
    #Export all available apps static to ../uliweb_test directory.
        
i18n
-------

I18n process tool, you can use it to extract translation catalog from
python source files and template files, the translation function is _(). 
You can process a single app or all apps by in separately or whole project.
It'll create .pot file. For app mode, the .pot file will be saved in
``yourproject/apps/appname/locale/lang/LC_MESSAGE/uliweb.pot``. For whole project mode, the 
.pot file will be saved in ``yourproject/local/lang/LC_MESSAGE/uliweb.pot``.
And lang should be different according the language which you want to deal with.
You can also use it to automatically merge .pot to existed .po file.

::

    Usage: uliweb i18n [options]
    
    options:
    
    -a appname
    
        Process a single appname, can't be used with --all, -w together.
        
    --all
    
        Process all available apps, can't be used with -a, -w together.
        
    -w
    
        Process whole project, can't be used with -a, --all together.
    
    -l locale
    
        If not provided, it'll be ``en``. If Provided, it'll be used as language 
        name. I suggest that you should use ``en_US`` format(language_locale).
        
    -m
    
        If automatically merge .pot with existed .po file, default is not automatically 
        merge.
    
Example:

::

    uliweb i18n -a appname -l zh #Single app process
    uliweb i18n --all -l zh      #All of available apps process
    uliweb i18n -w               #Whole apps process, and using default locale ``en``.
    
extracturls
-------------

Extract URL definition from each view modules, so you should define URL via
expose() first. It'll output the urls to apps/urls.py file. And if there is
apps/urls.py, Uliweb will automatically import it then disable expose(). 

::

    Usage: uliweb extracturls
    
If there is already a urls.py file in apps directory, it'll prompte you
to confirm you want to overwrite it.

call
-------

::

    Usage: uliweb call name
    
Executing all <name>.py from every installed App.
