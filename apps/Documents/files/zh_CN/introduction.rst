============
Uliweb 简介
============

:作者: Limodou <limodou@gmail.com>

.. contents:: 

它是什么
----------

Uliweb是一个新的Python Web Framework，它之所以会产生是因为现有的框架多少有些令人
不满意的地方，而且许多情况下这些不满意的地方或多或少对我开发Web有影响，因此在经过对
不少框架的学习之后，我决定开发一个新的框架，希望可以综合我认为其它框架中尽可能多的
优点，同时使这个新的框架尽可能的简单，易于上手和使用。

这个项目是由Limodou <limodou@gmail.com>发起并创建的。其中得到了许多人的帮助。

License
------------

Uliweb按照GPL v2进行发布。

基础组件
------------

它并不完全是从头写的一个东西，我目前使用了一些库，如：

* `Werkzeug <http://werkzeug.pocoo.org/>`_ 用它来进行框架的核心处理，比如：命令行，
  URL Mapping，Debug等。
* `webob <http://pythonpaste.org/webob/>`_  用它来生成Request, Response对象的生
  成和处理。
* `SqlAlchemy <http://www.sqlalchemy.org>`_ 基于它封装了Uliorm，可以使用ORM对
  数据库进行处理。

还有一些比较小的引用，如：

* template 是从 `web2py <http://mdp.cti.depaul.edu/>`_ 改造来的
* 部分处理代码从 `Django <http://www.djangoproject.com/>`_ 中借鉴

另外还有一些是自已新造的，如：

* Form处理，可以用来生成HTML代码和对上传的数据进行校验
* i18n处理，包括对模板的处理
* Uliorm，是在SqlAlchemy基础之上进行的封装，同时参考了GAE中的datastore的代码
* 框架的处理代码，这块不可能不自已造了
* 插件机制，从Ulipad中移植并进行了改造

功能特点
-----------

* 组织管理

  * 采用MVT模型开发。
  * 分散开发统一管理。采用App方式的项目组织。每个App有自已的配置文件，templates目录，
    static目录。使得Uliweb的App重用非常方便。同时在使用上却可以将所有App看成一个整体，
    可以相互引用静态文件和模板。缺省是所有App都是生效的，也可以指定哪些App是生效的。
    所有生效App的配置文件在启动时会统一进行处理，最终合成一个完整的配置视图。
    
* URL处理

  * 灵活强大的URL映射。采用Werkzeug的Routing模块，可以非常方便地定义URL，并与View函数
    进行绑定。同时可以根据view函数反向生成URL。支持URL参数定义，支持缺省URL定义，如：
 
    ::
 
      appname/view_module/function_name
    
* View与Template

  * View模板的自动套用。当view返回dict对象时，自动根据view函数的名字查找对应的模板。
  * 环境方式运行。每个view函数在运行时会处于一个环境下，因此你不必写许多的import，许多
    对象可以直接使用，比如request, response等。可以大大减少代码量。
  * 模板中可以直接嵌入Python代码，不需要考虑缩近，只要在块结束时使用pass。支持模板的
    include和继承。
    
* ORM

  * 支持Model与数据库的简单自动迁移，包括自动建表和表结构的修改。

* i18n

  * 支持代码和模板中的i18n处理
  * 支持浏览器语言和cookie的自动选择，动态切换语言
  * 提供命令行工具可以自动提取po文件，可以以App为单位或整个项目为单位。并在处理时自动将
    所有语言文件进行合并处理。当发生修改时，再次提取可以自动进行合并。
    
* 扩展

  * plugin扩展。这是一种插件处理机制。Uliweb已经预设了一些调用点，这些调用点会在特殊的地方
    被执行。你可以针对这些调用点编写相应的处理，并且将其放在settings.py中，当Uliweb在启动
    时会自动对其进行采集，当程序运行到调用点位置时，自动调用对应的插件函数。
  * middleware扩展。它与Django的机制完全类似。你可以在配置文件中配置middleware类。每个
    middleware可以处理请求和响应对象。
  * views模块的初始化处理。在views模块中，如果你写了一个名为__begin__的函数，它将在执行
    要处理的view函数之前被处理，它相当于一个入口。因此你可以在这里面做一些模块级别的处理，
    比如检查用户的权限。因此建议你根据功能将view函数分到不同的模块中。
    
* 命令行工具

  * 可以导出一个干净的工作环境
  * App的创建，会自动包含必要的目录结构，文件和代码
  * 静态文件导出，可以将所有生效的App下的static导出到一个统一的目录
  * 启动开发服务器

* 部署

  * 支持GAE部署
  * 支持Apache下的mod_wsgi部署

* 开发

  * 提供开发服务器，并当代码修改时自动装载修改的模块
  * 提供debug功能，可以查看出错的代码，包括模板中的错误

* 其它

  * Uliweb是一个Demo与源码合二为一的项目。它不仅包括所有核心代码，还同时包括了
    `uliwebproject <http://uliwebproject.appspot.com>`_ 网站的源码，同时还有其它
    的一些Demo，所以你可以直接使用这些代码。
  * 对于静态文件的支持可以处理HTTP_IF_MODIFIED_SINCE和trunk方式的静态文件处理。
    
项目目标
----------

* 开发一个简单易用的框架
* 框架要足够灵活，并易于扩展
* 包含足够的示例代码
* 编写清晰易懂的文档
* 能够在多种环境下使用