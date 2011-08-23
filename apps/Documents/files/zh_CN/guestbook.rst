迷你留言板
=============

:Author: Limodou <limodou@gmail.com>

.. contents:: 
.. sectnum::

也许你已经学过了 `Hello, Uliweb <hello_uliweb>`_ 这篇教程，对Uliweb已经有了一个感性的
认识，那么好，现在让我们进入数据库的世界，看一看如何使用简单的数据库。

准备
------

在 uliweb-tests 项目中已经有完整的GuestBook的源代码，你可以从它里面检出:

::

    svn checkout http://uliweb-tests.googlecode.com/svn/trunk/guestbook guestbook
    cd guestbook
    uliweb runserver
    
然后在浏览器输入 http://localhost:8000/guestbook 这样就可以看到了。目前缺省是使用
sqlite3。如果你安装了python 2.5它已经是内置的。否则要安装相应的数据库和Python的绑定模
块。目前Uliweb使用 `SqlAlchemy <http://www.sqlalchemy.org>`_ 作为数据库底层驱动，
它支持多种数据库，如：mysql, sqlite, postgresql, 等。

好了，源码准备好了，下一步，准备开发环境。

创建工程
-----------

建议在一个空目录下开始你的工作，例如:

::

    uliweb makeproject guestbook

创建APP
-----------

进入前面创建的目录，然后使用 makeapp 建一个新的App。执行:

::

    cd guestbook
    uliweb makeapp GuestBook
    
这样就自动会在项目的apps目录下创建一个 ``GuestBook`` 的App。

配置数据库
------------

Uliweb中的数据库不是缺省生效的，因此你需要配置一下才可以使用。Uliweb虽然提供了自已的
ORM，但是你可以不使用它。Uliweb提供了插件机制，可以让你容易地在适当的时候执行初始化的工作。
打开 ``apps/GuestBook/settings.ini`` 文件，修改 ``INSTALLED_APPS`` 的内容为::

    INSTALLED_APPS = [
        'GuestBook',
        'uliweb.contrib.orm',
        ]

然后添加下面的内容::

    [ORM]
    CONNECTION = 'sqlite:///guestbook.db'

所以 ``settings.ini`` 将看上去象::

    [GLOBAL]
    DEBUG = True
    
    INSTALLED_APPS = [
        'GuestBook',
        'uliweb.contrib.orm',
        ]
    
    [ORM]
    CONNECTION = 'sqlite:///guestbook.db'
    
ORM.CONNECTION 是ORM的连联字符串，它和SQLAlchemy包使用的一样。通常的格式看上去象::

    provider://username:password@localhost:port/dbname?argu1=value1&argu2=value2

对于Sqlite，连接信息有些不同::
    
    sqlite_db = create_engine('sqlite:////absolute/path/to/database.txt')
    sqlite_db = create_engine('sqlite:///d:/absolute/path/to/database.txt')
    sqlite_db = create_engine('sqlite:///relative/path/to/database.txt')
    sqlite_db = create_engine('sqlite://')  # in-memory database
    sqlite_db = create_engine('sqlite://:memory:')  # the same
    
这里我们使用相对路径格式，所以 ``guestbook.db`` 将会在guestbook目录下被创建。

数据库初始化
~~~~~~~~~~~~

首先是设定一个参数 ``DEBUG_LOG = True`` ，注意全部是大写，它将用来控制是否要输出调试信息，这
里为底层的SQL语句。

然后：

.. code:: python

    @plugin('startup')
    def startup(sender):
        from uliweb import orm
        orm.set_debug_query(DEBUG_LOG)
        orm.set_auto_bind(True)
        orm.set_auto_migirate(True)
        orm.get_connection(**connection)

它将当Uliweb在执行到startup的位置时会调用相关的插件函数。startup是插件函数调用点的名字，
已经在SimpleFrame.py中定义了。每个调用点都有自已的名字和将要传递的参数。startup将传递
sender参数，这里sender就是框架实例。每一个插件函数的第一个参数都是调用者对象。

后面就是数据库初始化的工作了。因为Uliweb并不绑定一个数据库，因此初始化的工作需要由你来做，
这样就比较自由。同时因为Uliweb组织方式为APP模式，它在启动时会自动查找所有APP下的settings.py
并进行导入，进行配置参数的收集工作，因此你就可以在每个APP下的settings.py写自已需要的配
置处理。一旦在一个地方设定的，它相当于全局生效了。所以这种方式的使用，当你希望每个APP尽可
能独立时非常有用。因此在Uliweb中的APP，一方面它可以保持有自已的结构，甚至包含静态文件，
配置文件，但同时在需要时也可以直接分享其它APP的信息。

``set_debug_query(DEBUG_LOG)`` 用来设置显示底层的SQL，在开发服务器环境下，它将显示在命令行上。

``set_auto_bind(True)`` 自动绑定设置。这样当你导入一个Model时，它将自动与缺省的数据库连接
进行绑定，就可以直接使用了。不然，你需要手动绑定每个Model需要与哪个连接关联。在只有单数据
连接时可以打开，在使用多数据连接时可以关闭，然后进行手工绑定处理。

``set_auto_migrate(True)`` 这个作用很大。首先，如果在运行时表还不存在，则Uliweb可以自动创
建表结构。其次，如果你使用过web2py，你会知道当Model发生变化时可以自动更新表结构。那么
Uliorm也可以做到，不过目前比较简单，只能处理象：增加，删除，修改
的情况。对于修改，可能会造成数据丢失。现在无法判断字段的改名，所以一旦改名，其实就是删除旧
的，创建新的，所以数据会丢失。这里可以把这个开关关闭，手工修改数据库，同时做好数据的备份。
我认为采用数据备份，然后通过恢复程序来恢复是最安全的。不过现在Uliweb还没有这类的工具。

采用自动迁移在开发时用户不必考虑修改表结构的工作，只要改了就生效，会非常方便。

经过上两步的设定，就可以在Uliweb环境下非常方便的使用数据库了。只要定义好，使用它就行了。
象建表，修改表结构全部自动完成，非常方便。

``orm.get_connection(**connection)`` 将创建数据库连接对象，并根据上面相关的设定进行必要的
初始化工作。所以上面的设定需要在调用get_conection()前完成。在调用完get_connection()之
后，创建的连接将作为缺省连接供全局使用。

模板环境的扩展
----------------

在settings.py中还有一个东西：

.. code:: python

    @plugin('prepare_view_env')
    def prepare_view_env(sender, env, request):
        from uliweb.utils.textconvert import text2html
        env['text2html'] = text2html

这也是一个插件的使用示例，它将向模板的环境中注入一个新的函数 ``text2html``, 这样你就可以
在模板中直接使用text2html这个函数了。并且因为这个插入点是全局生效的，所以其它的App可以
复用它。

准备Model
-----------

在GuestBook目录下创建一个名为models.py的文件，内容为：

.. code:: python

    from uliweb.orm import *
    import datetime
    
    class Note(Model):
        username = Field(CHAR)
        message = Field(TEXT)
        homepage = Field(str, max_length=128)
        email = Field(str, max_length=128)
        datetime = Field(datetime.datetime, auto_now_add=True)
        
很简单。

首先要从 uliweb.orm 中导入一些东西，这是是全部导入。

然后是导入datetime模块。为什么会用到它，因为Uliorm在定义Model时支持两种定义方式：

* 使用内部的Python类型，如：int, float, unicode, datetime.datetime, datetime.date,
  datetime.time, decimal.Decimal, str, bool。另外还扩展了一些类型，如：BLOB, CHAR, TEXT, DECIMAL。
  所以你在定义时只要使用Python的类型就好了。
* 然后就是象GAE一样的使用各种Property类，如：StringProperty, UnicodeProperty,
  IntegerProperty, BlobProperty, BooleanProperty, DateProperty, DateTimeProperty,
  TimeProperty, DecimalProperty, FloatProperty, TextProperty。

一个Model需要从 ``Model`` 类派生。然后每个字段就是定义为类属性。Field()是一个函数，它将
会根据第一个参数来查找对应的属性类，因此：

.. code:: python

    class Note(Model):
        username = StringProperty()
        message = TextProperty()
        homepage = StringProperty()
        email = StringProperty()
        datetime = DateTimeProperty()
        
每个字段还可以有一些属性，如常用的：

* default 缺省值
* max_length 最大值
* verbose_name 提示信息

象CharProperty和StringProperty，需要有一个max_length属性，如果没有给出，缺省是30。

等。具体的回头我会详细在数据文档中进行说明。

.. note::

    在定义Model时，Uliorm会自动为你添加 ``id`` 字段的定义，它将是一个主键，这一点与Django一样。
    
静态文件处理
--------------

我们将在后面显示静态文件，现在只需要把 ``uliweb.contrib.staticfiles`` 添加到 ``INSTALLED_APPS``
中就可以了。使用这个App，所有有效的app的static目录将被处理为静态目录，并且URL链接将添加 
``/static/`` 。现在 ``settings.ini`` 看上去象::

    [GLOBAL]
    DEBUG = True
    
    INSTALLED_APPS = [
        'GuestBook',
        'uliweb.contrib.orm',
        'uliweb.contrib.staticfiles',
        ]
    
    [ORM]
    CONNECTION = 'sqlite:///guestbook.db'
    
显示留言
-----------------------

增加guestbook()的View方法
~~~~~~~~~~~~~~~~~~~~~~~~~~

打开GuestBook下的views.py文件，加入显示留言的处理代码：

.. code:: python

    @expose('/guestbook')
    def guestbook():
        from models import Note
        from sqlalchemy import desc
        
        notes = Note.filter(order_by=[desc(Note.c.datetime)])
        return locals()

先定义url为 ``/guestbook`` 。

然后是guestbook()函数的定义。我们先导入Note类，然后通过它的类方法filter进行数据库的查
询。为了按时间倒序显示，我在filter中对 ``order_by`` 定义了降序排序，这里是SqlAlchemy的查询
语法。这个条件的意思就是对 ``datetime`` 字段进行倒序处理。

以下是一些简单的用法：

.. code:: python

    notes = Note.filter()               #全部记录，不带条件
    note = Note.get(3)                  #获取id值为3的记录
    note = Note.get(Note.c.username=='limodou') #获取username为limodou的记录
    
然后我们返回locals()，让模板来使用它。

.. note::

    在Uliweb中每个访问的URL与View之间要通过定义来实现，如使用expose。它需要一个URL的
    参数，然后在运行时，会把这个URL与所修饰的View方法进行对应，View方法将转化为：
    
        appname.viewmodule.functioname
        
    的形式。它将是一个字符串。然后同时Uliweb还提供了一个反向函数url_for，它将用来根据
    View方法的字符串形式和对应的参数来反向生成URL，可以用来生成链接，在后面的模板中我
    们将看到。

定义guestbook.html模板
~~~~~~~~~~~~~~~~~~~~~~~~

在GuestBook/templates目录下创建与View方法同名的模板，后缀为.html。在guestbook.html中
添加如下内容：

.. code:: django+html

    {{extend "base.html"}}
    <h1>Uliweb Guest Book</h1>
    <h2><a href="{{=url_for('%s.views.new_comment' % request.appname)}}">New Comment</a></h2>
    {{for n in notes:}}
    <div class="message">
    <h3><a href="{{= url_for('%s.views.del_comment' % request.appname, id=n.id) }}">
    <img src="{{= url_for('%s.views.static' % request.appname, filename='delete.gif') }}"/>
    </a> {{=n.username}} at {{=n.datetime.strftime('%Y/%m/%d %H:%M:%S')}} say:</h3>
    <p>{{=text2html(n.message)}}</p>
    </div>
    {{pass}}
    
    
第一行将从base.html模板进行继承。这里不想多说，只是要注意在base.html中有一个{{include}}
的定义，它表示子模板要插入的位置。你可以从Uliweb的源码中将base.html拷贝到你的目录下。

h2 标签将显示一个链接，它将用来调用添加留言的view函数。注意模板没有将显示与添加的
Form代码写在一起，因为那样代码比较多，同且如果用户输入出错，将再次显示所有的留言(因为这里
没有考虑分页)，这样处理比较慢，所以分成不同的处理了。

``{{for}}`` 是一个循环。记住Uliweb使用的是web2py的模板，不过进行了改造。所有在{{}}中的代码
可以是任意的Python代码，所以要注意符合Python的语法。因此后面的':'是不能省的。Uliweb的模
板允许你将代码都写在{{}}中，但对于HTML代码因为不是Python代码，要使用 ``out.write(htmlcode)`` 
这种代码来输出。也可以将Python代码写在{{}}中，而HTML代码放在括号外面，就象上面所做的。

在循环中对notes变量进行处理，然后显示一个删除的图形链接，用户信息和用户留言。

看到 ``{{=text2html(n.message)}}`` 了吗？它使用了我们在settings.py中定义的text2html函
数对文本进行格式化处理。

``{{pass}}`` 是必须的。在Uliweb模板中，不需要考虑缩近，但是需要在块语句结束时添加pass，表示缩
近结果。这样相当于把Python对缩近的严格要求进行了转换，非常方便。

好，在经过上面的工作后，显示留言的工作就完成了。但是目前还不能添加留言，下一步就让我们看如
何添加留言。

.. note::

    因为在base.html中和guestbook.html用到了一些css和图形文件，因此你可以从Uliweb的
    GuestBook/static目录下将全部文件拷贝到你的目录下。
    
增加留言
----------

增加new_comment()的View方法
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

在前面的模板中我们定义了增加留言的链接：

.. code:: html

    <a href="{{=url_for('%s.views.new_comment' % request.appname)}}">New Comment</a>
    
可以看出，我们使用了url_for来生成反向的链接。关于url_for在前面已经讲了，这里要注意的就是
函数名为new_comment，因此我们需要在views.py中生成这样的一个方法。

打开views.py，加入以下代码：

.. code:: python

    @expose('/guestbook/new_comment')
    def new_comment():
        from models import Note
        from forms import NoteForm
        import datetime
        
        form = NoteForm()
        if request.method == 'GET':
            return {'form':form.html(), 'message':''}
        elif request.method == 'POST':
            flag, data = form.validate(request.params)
            if flag:
                n = Note(**data)
                n.put()
                return redirect(url_for('%s.views.guestbook' % request.appname))
            else:
                message = "There is something wrong! Please fix them."
                return {'form':form.html(request.params, data, py=False), 'message':message}

可以看到链接是 ``/guestbook/new_comment`` 。

首先我们导入了一些类，包括Note这个Model。那么NoteForm是什么呢？它是用来生成录入Form的
对象，并且可以用来对数据进行校验。一会儿会对它进行介绍。

然后创建form对象。

再根据request.method是GET还是POST来执行不同的操作。对于GET将显示一个空Form，对于POST
表示用户提交了数据，要进行处理。使用GET和POST可以在同一个链接下处理不同的动作，这是一种
约定，一般中读操作使用GET，写或修改操作使用POST。

在request.method为GET时，我们只是返回空的form对象和一个空的message变量。form.html()可
以返回一个空的HTML表单代码。而message将用来提示出错的信息。

在request.method为POST时， 首先调用 ``form.validate(request.params)`` 对数据进行校验。
它将返回一个二元的tuple。第一个参数表示成功还是出错，第二个为成功时将转换为Python格式后
的数据，失败时为出错信息。

当flag为True时，进行成功处理。一会我们可以看到在表单中并没有datetime字段，因此这里我们
手工添加一个值，表示留言提交的时间。然后通过 ``n = Note(**data)`` 来生成Note记录，但这里并没有提
交到数据库中，因此再执行一个 ``n.put()`` 来保存记录到数据库中。使用 ``n.save()`` 也可以。

然后执行完毕后，调用 ``return redirect`` 进行页面的跳转，跳回留言板的首页。这里又使用了url_for来反
向生成链接。
    
当flag为False时，进行出错处理。这里我们向message中填入了出错提示，然后通过
``form.html(request.params, data, py=False)`` 来生成带出错信息的表单。这里data为出错
信息。 ``py=False`` 是表示在使用数据时不进行Python数据转换。因为Form在校验数据之后会根据
你所定义的数据类型，将上传的数据转换为Python的内部数据，如：int, float之类的。但是当出错
时，不存在转换后的Python数据，因此不能做这种转换，这时要使用 ``py=False`` 参数。如果data
是校验成功的数据，你想通过表单显示出来，可以直接使用 ``form.html(data)`` 就可以了。

定义录入表单
~~~~~~~~~~~~~

为了与后台进行交互，让用户可以通过浏览器进行数据录入，需要使用HTML的form系列元素来定义
录入元素。对于有经验的Web开发者可以直接手写HTML代码，但是对于初学者很麻烦。并且你还要考虑
出错处理，数据格式转换的处理。因此许多框架都提供了生成表单的工具，Uliweb也不例外。Form模
块就是干这个用的。

在GuestBook目录下创建forms.py文件，然后添加以下代码：

.. code:: python

    from uliweb.core import Form
    
    Form.Form.layout_class = Form.CSSLayout
    
    class NoteForm(Form.Form):
        message = Form.TextAreaField(label='Message:', required=True)
        username = Form.TextField(label='Username:', required=True)
        homepage = Form.TextField(label='Homepage:')
        email = Form.TextField(label='Email:')

首先导入Form模块，然后设定Form类使用css布局。目前Uliweb的Form提供两种布局，一种是使用
table元素生成的，另一种是使用div元素生成的。table布局是缺省的。

接着就是创建NoteForm元素了。这里我定义了4个字段，每个字段对应一种类型。象TextAreaField
表示多行的文本编辑，TextField表示单行文本，你还可以使用象：HiddenField, SelectField,
FileField, IntField, PasswordField, RadioSelectField等字段类型。目前Form的定义方式
与Uliorm的不太一致，因为Form创建的时间更早，以后也可以考虑写一个统一的Field来进行一致性
的处理。

也许你看到了，这其中有一些是带有类型的，如IntField，那么它将会转换为对应的Python数据类
型，同时当生成HTML代码时再转换回字符串。

每个Field类型可以定义若干的参数，如：

* label 用来显示一个标签
* required 用来校验是否输入，即不允许为空
* default 缺省值
* validators 校验器

很象Model的定义，但有所不同。

编写new_comment.html模板文件
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

在GuestBook/templates下创建new_comment.html，然后添加以下内容：

.. code:: html

    {{extend "base.html"}}
    {{if message:}}
    <p class="message">{{=message}}</p>
    {{pass}}
    <h1>New Comment</h1>
    <div class="form">
    {{Xml(form)}}
    </div>

首先是 ``{{extend "base.html"}}`` 表示从base.html继承。

然后是一个 if 判断是否有message信息，如果有则显示。这里要注意if后面的':'号。

然后显示form元素，这里使用了 ``{{Xml(form)}}`` 。form是从View中传入的，而Xml()是模板中
的内置方法，它用来原样输出内容，对HTML的标签不会进行转换。而 {{=variable}} 将对variable
变量的HTML标签进行转换。因此，如果你想输出原始的HTML文本，要使用Xml()来输出。

现在可以在浏览器中试一下了。

删除留言
----------

在前面guestbook.html中，我们在每条留言前定义了一个删除的图形链接，形式为：

.. code::

    <a href="{{=url_for('%s.views.new_comment' % request.appname)}}">New Comment</a>
    
那么下面就让我们实现它。

打开GuestBook/views.py文件，然后添加：

.. code:: python

    @expose('/guestbook/delete/<id>')
    def del_comment(id):
        from models import Note
    
        n = Note.get(int(id))
        if n:
            n.delete()
            return redirect(url_for('%s.views.guestbook' % request.appname))
        else:
            error("No such record [%s] existed" % id)

删除很简单，导入Note，然后通过 ``Note.get(int(id))`` 来得到对象，然后再调用对象的delete()
方法来删除。

URL参数定义
~~~~~~~~~~~~

请注意，这里expose使用了一个参数，即 ``<id>`` 形式。一旦在expose中的url定义
中有 ``<type:para>`` 的形式，就表示定义了一个参数。其中type:可以省略，它可以是int等类型。而
int将自动转化为 ``\d+`` 这种形式的正则式。Uliweb内置了象: int, float, path, any, string等类型，你可以在 `URL Mapping <url_mapping>`_ 文档中了解更多的细节。如果你只定义了
``<name>`` 这种形式，它表示匹配 ``//`` 间的内容。一旦在URL中定义了参数，则需要
在View函数中也需要定义相应的参数，因此del_comment函数就写为了： ``del_comment(id)`` 。
这里的id与URL中的id是一样的。

好了，现在你可以试一试删除功能是否可用了。

出错页面
~~~~~~~~~~~~~~~~

当程序出错时，你可能需要向用户提示一个错误信息，因此可以使用error()方法来返回一个出错
的页面。它的前面不需要return。只需要一个出错信息就可以了。

那么出错信息的模板怎么定义呢？在你的templates目录下定义一个名为error.html的文件，并加
入一些内容即可。

创建error.html，然后，输入如下代码：

.. code:: html

    {{title="Error"}}
    {{extend "base.html"}}
    <h1>Error!</h1>
    <p>{{=message}}</p>


这个页面很简单，就是定义了一个title变量，然后是继承base.html，再接着是显示出错内容。

不过这里有一个很重要的技巧，那就是在 {{extend}} 前面定义的内容在渲染模板时，将出现在最
前面。这样，一旦父模板中有一些变量需要处理，但是你没有通过View方法来传入，而是在子模板
中来定义它，通过这种方法就可以将定义放在使用语句的前面，从而不会报未定义的错误。

.. note::

    这是我对web2py模板的一个扩展。以前web2py要求{{extend}}是第一行的，但现在可以不是。
    并且这种处理可以很好的处理：在子模板中定义在父模板中要使用的变量的情况。
    
运行
------

在前面的开发过程中你可以启动一个开发服务器进行调试。启动开发服务器的命令为：

::

    uliweb runserver
    
当启动后，在浏览器输入： ``http://localhost:8000/``

结论
-------

经过学习，我们了解了许多内容：

#. ORM的使用，包括：ORM的初始化配置，Model的定义，简单的增加，删除，查询
#. Form使用，包括：Form的定义，Form的布局，HTML代码生成，数据校验，出错处理
#. 模板的使用，包括： {{extend}} 的使用，在模板环境中增加自定义函数，子模板变量定义的
   技巧，错误模板的使用，Python代码的嵌入
#. View的使用，包括：redirect, error的使用, 静态文件处理
#. URL映射的使用，包括：expose的使用，参数定义，与View函数的对应
#. manage.py的使用，包括：export, makeapp的使用
#. 结构的了解，包括：Uliweb的app组织，settings.py文件的处理机制，view函数与模板文件
   的对应关系

内容很多，的确。而这些还远远不是一个框架的全部。随着应用的复杂，框架的功能也会越来越多。
而一个好的框架应该就是让有经验的人用来首先构建出一个更易于使用，易于管理的环境，然后
让团队中的人在这个环境下去开发，让对框架有经验的人对环境进行不断的调整和完善，使其越来
越方便和强大。Uliweb正在向着这个目标前进。