体系结构和机制
===============

:Author: Limodou <limodou@gmail.com>

.. contents:: 
.. sectnum::

组织结构
----------

如果你从svn中下载Uliweb源码，它不仅包括了Uliweb的核心组件，同时还包括了uliwebproject
网站的全部源码和一些示例程序。Uliweb采用与web2py类似的管理方式，即核心代码与应用放在一
起，到时会减少部署的一些麻烦。但是对于项目的组织是采用Django的管理方式，而不是web2py的
方式。一个完整的项目将由一个或若干个App组织，它们都统一放在apps目录下。但Uliweb的app的
组织更为完整，每个app有自已独立的：

* settings.py 它是配置文件
* templates目录用于存放模板
* static目录用于存放静态文件
* views文件，用于存放view代码

这种组织方式使得Uliweb的App重用更为方便。

在uliweb的下载目录下，基本结构为：

::

    apps/               #App的存放目录
    lib/
        sqlalchemy/     #缺省的数据库驱动包，使用sqlalchemy项目
        migrate/        #sqlalchemy的migrate包
        webob/          #用于Request, Response的处理，使用webob项目
        werkzeug/       #底层框架支撑库，使用werkzeug项目
    uliweb/             #Uliweb核心代码
    app.yaml            #供部署在GAE上使用
    gae_handler.py      #供部署在GAE上使用
    manage.py           #Uliweb的命令行管理程序
    wsgi_handler.wsgi   #供部署在apache+mod_wsgi上使用
    
其中uliweb又分为：

::

    uliweb/
        core/           #核心模块
        i18n/           #国际化处理模块
        middlewares/    #middleware汇总
        orm/            #缺省ORM库
        test/           #测试程序
        utils/          #输助模块
        
apps的结构为：

::

    apps/
        __init__.py
        settings.py
        app1/
            __init__.py
            settings.py
            templates/
            static/
        app2/
            __init__.py
            settings.py
            templates/
            static/
    
App管理
-----------

一个项目可以由一个App或多个App组成，而且每个App的结构不一定要求完整，但至少要求是一个
Python的包的结构，即目录下需要一个__init__.py文件。因此一个App可以：

* 只有一个settings.py 这样可以做一些初始化配置的工作，比如：数据库配置，i18n的配置等
* 只有templates，可以提供一些公共的模板
* 只有static，可以提供一些公共的静态文件
* 其它的内容

Uliweb在启动时对于apps下的App有两种处理策略：

#. 认为全部App都是生效的
#. 根据apps/settings.py中的配置项INSTALLED_APPS来决定哪些App要生效

Uliweb在启动时会根据生效的App来导入它们的settings.py文件，并将其中配置项进行合并最终
形成一个完整的 ``settings`` 变量供App来使用。同时在处理生效的App的同时，会自动查找所有views开头
的文件和views子目录并进行导入，这块工作主要是为了收集所有定义在views文件中的URL。

这样当Uliweb启动完毕，所有App下的settings.py和views文件将被导入。因此，你可以在settings.py
文件中做一些初始化的工作。

要注意，只有变量名全部为大写字母的才被认为是配置项，否则将被忽略掉。

在实际的项目中，你可能有一个主控的App，你可以在它的settings.py中进行象：数据库初始化等工作。
然后依赖于Uliweb的管理功能，让其它的App可以共享主控模块的信息。

对于象templates和static，Uliweb会首先在当前App下进行搜索，如果没有找到，则去其它生效的App
相应的目录下进行查找。因此，你可以把所有生效的App的templates和static看成一个整体。所以
你完全可以编写只包含templates或static的App，主要是提供一些公共信息。

URL处理
------------

目前Uliweb支持两种URL的定义方式。

一种是将URL定义在每个view模块中，通过expose来定义。

另一种是先用expose在每个模块中定义，然后通过extracturls来导出URL的定义到apps/urls.py文件
中，然后再启动Uliweb时，它会自动识别并导入，expose并自动失效。如果你喜欢这种方式，你可以
很容易地做到了。

URL的格式采用werkzeug的routing模块处理方式。可以定义参数，可以反向生成URL。在Uliweb
中定义了两个方便的函数：

* expose 用来将URL与view方法进行映射
* url_for 用来根据view方法反向生成URL

MVT框架
------------

Uliweb也采用MVT的框架。目前Model是基于SqlAlchemy封装的ORM。View则采函数。但当你在运行view
函数，你会运行在一个环境下，这一点有些象web2py。不过web2py是基于exec，而Uliweb是通过
向函数注入变量(func_globals)来实现的。这种在某种环境下运行的方式使得你减少了许多的导入，许
多对象可以在view函数中直接使用，非常方便。Template一般你不需要主动来调用，Uliweb采用自动
映射的做法，即当一个view函数返回一个dict变量时，会自动查找模板并进行处理。当返回值不是
dict对象时将不自动套用模板。如果在response中直接给response.template指定模板名，可以不使用缺
省的模板。缺省模板文件名是与view函数名一样，但扩展名为.html。

在使用模板时也有一个环境变量，你可以直接在模板中直接使用预置的对象。同时Uliweb还提供了对
view函数和模板环境的扩展能力。

扩展处理
---------

Uliweb提供了多种扩展的能力：

* plugin扩展。这是一种插件处理机制。Uliweb已经预设了一些调用点，这些调用点会在特殊的地方
  被执行。你可以针对这些调用点编写相应的处理，并且将其放在settings.py中，当Uliweb在启动
  时会自动对其进行采集，当程序运行到调用点位置时，自动调用对应的插件函数。
* middleware扩展。它与Django的机制完全类似。你可以在配置文件中配置middleware类。每个
  middleware可以处理请求和响应对象。
* views模块的初始化处理。在views模块中，如果你写了一个名为__begin__的函数，它将在执行
  要处理的view函数之前被处理，它相当于一个入口。因此你可以在这里面做一些模块级别的处理，
  比如检查用户的权限。因此建议你根据功能将view函数分到不同的模块中。

