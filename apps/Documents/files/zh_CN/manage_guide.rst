manage.py 使用指南
=====================

:Author: Limodou <limodou@gmail.com>

.. contents:: 
.. sectnum::


``uliweb`` 是Uliweb提供的命令行工具，你可以用它做许多的事情。在使用它之前，你应该要先安装
Uliweb，如::

    python setup.py develop
    
or::

    python setup.py install
    
or::

    easy_install uliweb


runserver
-------------

启动开发服务器。

::

    Usage: uliweb runserver [options] 
    
    options:
    
    -h hostname
    
        开发服务器的地址，缺省为localhost
        
    -p port
    
        开发服务器端口，缺省为8000
        
    --no-reloader
    
        是否当修改代码后自动重新装载代码，缺省为自动重新装载
        
    --no-debugger
    
        是否当出现错误时可以显示Debug页面，缺省为显示
        
示例：

::

    uliweb runserver #启动缺省服务器
    
runadmin
--------------

功能同runserver，但是会自动包含admin这个App。

makeproject
-------------

生成一个project框架，它将自动按给定的名字生成一个project目录，同时包含有初始子目录和文件。

::

    Usage: uliweb makeproject projectname
  
示例：

::

    uliweb makeproject project 
    
创建project项目目录。

makeapp
-------------

生成一个app框架，它将自动按给定的名字生成一个app目录，同时包含有初始子目录和文件。

::

    Usage: uliweb makeapp appname
  
示例：

::

    uliweb makeapp Hello 
    
创建Hello应用，将在apps目录下创建一个Hello的目录，并带有初始的文件和结构。

makepkg
-------------

生成一个Python包结构目录，即带有__init__.py文件。

::

    Usage: uliweb makepkg pkgname

exportstatic
---------------

将所有已安装的app下的static文件和子目录复制到一个统一的目录下。注意，如果你在apps的
settings.py中设定了INSTALLED_APPS参数，则所有设定的app将被处理，如果没有设置，则
按缺省方式，将apps目录下的所有app都进行处理。对于存在同名的文件，此命令缺省将进行检
查，如果发现文件名相同，但内容不同的文件将会给出指示，并且放弃对此文件的拷贝。可以
在命令行使用-no-check来关闭检查。

::

    Usage: uliweb exportstatic [options] outputdir
    
    options:
    
    -v
    
        是否输出冗余信息。缺省为不输出。一旦设定将在执行时显示一些处理情况。
        
    -no-check
    
        是否在拷贝时进行检查。缺省为检查，一旦发现不符会在命令行进行指示。如果设定为
        不检查，则直接进行覆盖。
        
示例：

::

    uliweb exportstatic ../uliweb_test   
    #将所有已安装的app下的static文件拷贝到../uliweb_test目录下。
        
i18n
-------

i18n处理工具，用来从项目中提取_()形式的信息，并生成.pot文件。可以按app或全部app或整个
项目为单位进行处理。对于app或全部app方式，将在每个app下创建： ``app/locale/[zh]/LC_MESSAGES/uliweb.pot`` 
这样的文件。其中[zh]根据语言的不同而不同。并且它还会把.pot文件自动合并到uliweb.po文件上。

::

    Usage: uliweb i18n [options]
    
    options:
    
    -a appname
    
        指定要处理的appname。不能与--all, -w混用。
        
    --all
    
        处理全部的app，不能与-a, -w混用。
        
    -w
    
        整个项目处理，不能与-a, --all混用。
    
    -l locale
    
        如果没有指定则为en。否则按指定名字生成相应的目录。
        
    -m
    
        如果指定则自动与已经存在的.po文件进行合并，缺省不合并。
        
示例：

::

    uliweb i18n -a appname -l zh #单个app的处理
    uliweb i18n --all -l zh      #全部已安装app的处理
    uliweb i18n -w               #整个apps目录的处理，缺省locale为en
    
extracturls
-------------

从每个view模块中抽取URL定义，所以你需要首先使用expose()来定义它们。它将会把所有的URL
输出到apps/urls.py中。如果存在apps/urls.py文件，Uliweb在启动时将自动进行导入，并
禁止expose()。

::

    Usage: uliweb extracturls
    
如果已经在apps目录下存在urls.py文件，它将提示你是否你想要覆盖。

call
--------

::

    Usage: uliweb call name
    
执行所有安装的App下的<name>.py程序。