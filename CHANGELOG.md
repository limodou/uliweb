Uliweb Change Log
=====================

0.5 Version
-----------------

* Fix OneToOne result object not be cached bug
* When access reversed OneToOne property, if OneToOne record not existed, it'll auto create
  a blank object automatically. And if delete one record, it'll delete reversed onetoone
  record also.
* Add lock protect when creating request and response local instance in `_open()` function
* Add ORM Model migrate support
* Refactor SortedDict with dict base class
* Add model_config app, to support dynamic create model
* Add model ipython notebook support
* Refact sqldot
* Add environ variables passing in uliweb shell command
* Change app_url syntax to {'suffix':} to {'prefix':} only for dict data type
* Add URL route option in settings, it is [URL_ROUTE], format is

    ```
    [URL_ROUTE]
    any_key_1 = ('mapping_str', 'replacement')
    any_key_2 = ('mapping_str', 'replacement')
    ```
* Change uliweb jupyter extension load mechanism from automatically to `%load_ext uliweb`

0.4.1 Version
-----------------

* Add new app sequence, you can use it to create sequence value.
* Fix generic version parameter passing to obj.save() bug, only when version is not False will be passed
* Improve nginx and supervisor config content for deployment
* Fix multi expose `expose('/')` and `expose('')` for the same URL bug
* Add `strict_slashes=False` to Map instance.
* Add `Reference()` with `reference_class` is `None`, it can replace `SelfReference`
* Add `ManyToMany()` with `reference_class` is `None`, it can implements self manytomany relationship.
* Fix `ManyToMany()` with through model references to the same model bug

0.4 Version
-----------------
* Refactor template with tornado
* Fix Pickle default value process bug, will not convert empty value to ''
* Add staticize command
* Resume DEBUG_TEMPLATE option for template
* Fix count implement when there is group_by, limit, join, it'll use select count(*) from (select * from table)
* Add __debug__ parameter for tracing i18n language
* ORM add duplication support, so you can set it in CONNECTIONS options, it'll make definition of
  Model engine simple
* Add `set_session()` function to orm
* Add `fieldname` parameter to Property, and fix column mapping process between property and table field
* Add `-z` paramter to `load` and `loadtable` command, thanks for linuxr
* Fix `tmp/templates_temp` creation

0.3.1 Version
-----------------

* Add qqmail mail server backend support, thanks to Yubin Wang <harry198344 AT gmail.com>
* Add `yes` option, remove `--force` of makeapp,makeproject command
* Remove `has_options` attribute in Command class
* Fix `include` bug in ini
* Fix condition test bug of orm.get()
* Add `sqlshell` command
* Add `having` and `join` support to ORM
* Add whole database dump and load support #33
* Add NotFound to __all__ of orm
* Fix recorder bug
* Add `validatetemplate` command to validate syntax for template files

0.3 Version
-----------------

* Fix pyini "key=" for raw output bug
* Fix objcache for Lazy field bug, it'll refresh first if found Lazy field
* Fix executing orm command raise Exception not be thrown bug
* Refact multidb support
* Change UserWarn to DeprecationWarning
* Fix syncdb for different table name between `Model.__tablename__` and settings bug
* Remove `get_cached()` and add `cache` parameter to `Model.get()`
* Add `get_local_cache()` and `clear_local_cache()` in order to compatiable
  with SimpleFrame implementation
* ORM `Property.to_str()` will return string but not unicode for CHAR and VARCHAR.
* Simplify server_default, if integer given, it'll be convert to `text(n)`
* `ManyResult.all()` can receive a `cache` parameter
* Improve `dump()` and `load()`, add PickleType , ManyToMany support
* Refact objcache app implementation and add `exclude` config option
* Remove primary_key detect, because multi primary_key columns can make composite primary key,
  add partition support for mysql

  you can define:

    ```
    __table_args__ = {
        'mysql_partition_by':'HASH(YEAR(create_time))',
        'mysql_partitions': '6'
    }
    ```
* add None patch process, you can set '', 'empty, 'exception'.
* move uliweb/orm/middle*.py to uliweb/contrib/orm
* move uliweb/i18n/middle_i18n.py to uliweb/contrib/i18n
* move storage from core to utils directory
* improve count process
* Fix Reference and ManyToMany dump and load bug
* Add `is_in_web()` funciton, so you can test if current frame is in web executation
* Add `--gevent` support to call command
* Add `any` to Model, Result, ManyResult
* Add `clear_prefix()` to redis_cli APP, this feature need redis 2.6+ version
* Add version check to redis_cli APP, default is disabled
* Add `clear_table()` to objcache APP
* Add 'id' parameter to `get()` and `get_object()` and `get_cached_object()` functions,
  so that if the ID can't be found in cache, condition (old parameter) will be used.
  And when id and condition given both, only when id is not integer or valid expression
  condition will be used. So in most cases, you don't need pass condition.
* If not set url option for session of database type, it'll automatically use ORM settings if exists
* Add settings and local_settings env variables support
* Fix count bug
* Change orm requirement.txt, add uliweb-alembic package
* generic app add avalon and mmgrid support
* Model.put() not is deprecated, you should use save
* `generic.py` add version support when saving, and add `save` callback parameter.

0.2.6 Version
-----------------

* Add warning output for Reference class parameter of relation properties definition.
* Fix manual and total process bug in ListView and SelectListView
* Fix rawsql bug
* Add `get_object()` support in Generic ListView
* Fix `get_cached()` bug
* Fix process_files in generic add and edit functions bug
* Add `import readline` before enter shell environment
* change occ name to version
* Improve autocomplete in shell command
* Fix manytomany cached value is not used when do the save, because of not stored
  in `_old_values`
* If you've already define primary key in Model, then it'll not create id property
  for you, just like:

    ```
    user_id = Field(int, primary_key=True, autoincrement=True)
    ```
* Fix sqldot bug and improve sqlhtml generation
* Eanble colored log output by default.
* Add recorder app, you can use it to record the visit url, and test it later

0.2.5 Version
-----------------

* Fix config template and add `uwsgi` shell support
* Add environment variables support in `settings.ini`. For example, there is a 
  `MYSQL_PORT` defined in environment, so you can defined something in settings.ini:

    ```
    [DEFAULT]
    port = $MYSQL_PORT
    port_str = '${MYSQL_PORT}'
    ```
    
    `$MYSQL_PORT` is the same as `${MYSQL_PORT}`. Just when the variable follows
    identifier, so `${}` can easily separate between them.
* Add `STATIC_COMBINE_CONFIG` configuration, you can toggle static combination with it.
  Default is False. The configuration is:

    ```
    [STATIC_COMBINE_CONFIG]
    enabled = False
    ```
* Fix objcache app bug, if not fields defined in settings, it'll use all columns of table
* Add `get_table` function to `functions`, you can use it to get table object. Used
  in `uliweb.contrib.tables` app.
* Add `local_cache` to local in SimpleFrame, and it can be used to store require relative
  cache values, and it'll be empty after each require process.
* Improve `get_object()` function in ORM, add `use_local` parameter, so the cached
  value will be checked in `local_cache` first, and also save it in local_cache when 
  get a value from cache or database.
* Improve objcache config format, you can also define table like this:

    ```
    user = {'fields':['username'], 'expire':expire_time, 'key':callable(instance)|key_field}
    #or
    user = ['username', 'nickname']
    #or
    user = 
    ```
    
    If no fields defined, it'll use all fields of Model. And if expire is 0 or
    not defined, it'll not expired at all.
    
    `key` will be used to replace `id`, if you want another key value, and it
    can be also a callable object, it'll receive an instance of Model parameter,
    so you can create any key value as you want.
* Add Optimistic Concurrency Control support for ORM, so you should defined `version`
  Field first in Model, then when you save the object, you should use:

    ```
    obj.save(occ=True)
    ```
    
    If there is already other operation saved the record, it'll raise an `SaveError`
    Exception by default, because the version has been changed. You can also pass:
    
    * `occ_fieldname` used to defined the version fieldname, default is `version`
    * `occ_exception` used to enabled Exception raised, default is `True`, if you 
      set it `False` it'll return False, but not raise an Exception.

0.2.4 Version
-----------------

* Fix ORM is not compatible with SQLAlchemy 0.9.1. Old style:

    ```
    cond = None
    cond = (Blog.c.id==5) & None
    ```
    
    will not right in 0.9.1, because None will not be skipped, so you can change
    above code `cond = None` to :
    
    ```
    from sqlalchemy.sql import true
    cond = true()
    ``` 
    
    or
    
    ```
    from uliweb.orm import true
    cond = true()
    ```
    
* add `__contains__` to functions, so you can test if an API is already defined, just
  use:

    ```
    'flash' in functions
    ```
* Refact generic.py, remove `functions.flash` and `functions.get_fileserving` dependencies by default. 

* Fix `yield` support in view function, you can also used in gevent environment, for example:

    ```
    @expose('/test')
    def test():
        yield "<ul>"
        for i in range(10):
            yield "<li>%d</li>" % (i + 1)
            sleep(1)
        yield "</ul>"
    ```

* Fix `rawsql()` bug for different database engine
* Fix `jsonp()` dumps Chinese characters bug
* Add `trim_path()` function to `utils/common.py`, it can trim a file path to 
  limited length, for example:

    ```
    >>> a = '/project/apps/default/settings.ini'
    >>> trim_path(a, 30)
    '.../apps/default/settings.ini'
    ```
    
    Default limited length is 30.
* Add ORM connection information output when given `-v` option in command line. And
  the password will be replace with `'*'`. For example:

    ```
    $>uliweb syncdb -v
    Connection : mysql://blog:***@localhost/blog?charset=utf8
    
    [default] Creating [1/1, blog] blog...EXISTED
    ```
* Add multiple apps support for `makeapp` command, so you can use :

    ```
    uliweb makeapp a b c
    ```
    
    to create `a`, `b`, `c` apps at once time.
* Refactor `save_file()` process, add `headers` and `convertors` parameter.

    `headers` used to create csv header instead of using column name, but you can
    create alias name like this:
    
    ```
    User.c.username.label(u"Name")
    ```
    
    and `convertors` used to convert column value, for example:
    
    ```
    def name(value, data):
        """
        value is the column value
        data is the current record object
        """
        return value + 'test'
    save_file(do_(select([User.c.name])), 'test.csv', convertors={'name':name})
    ```
* Fix `call_view()` invoke `wrap_result` bug. Missing pass `handler` parameter to wrap_result.
    
0.2.3 Version
-----------------

* Update nginx support output, add proxy_set_header
* Add `save_file()` function to orm, so you can save select result to a csv file
* Add `save_file()` method to Result.
* Fix missing `clear()` function of SortedDict.
* Fix i18n process, for project and apps extraction, it'll create application first, so that
  user defined tag will be registered correctly. But user defined tag will be limited later. 
* Add `walk_dirs()` to utils/common.py. This function can ignore some files and file ext, 
  and supports fnmatch pattern.

0.2.2 Version
-----------------

* Add `clear()` to SortedDict
* Add protect for form to generic AddView and EditView, default is enabled, so
  user can't submit a form multiple times.
* Add `--blocks` parameter to `uliweb find -t templatefile --blocks`, it'll display
  all blocks defined in template. With `--with-filename` will display template filename
  also.
* ini replace variable will be moved to the end of section
* Add content-range support for filedown thanks to zhangchunlin
* Improve `import_attr()`, support pkg_resource entry point string format, 'module:object.attr'
* Add requirements.txt to uliweb.contrib.orm, install: SQLAlchemy, MySQL-python, alembic first
* Add logo files
* Fix find -t --blocks bug
* Add `DEBUG_TEMPLATE` option to settings/GLOBAL, if it's `True`, then all blocks in a template
  will be surrounded by comment code just like:

    ```
    <!-- BLOCK title (apps/theme/templates/theme/skeleton.html) -->
    <!-- END title -->
    ```
    
  But this output may breaks template output, so make sure you just use it in debug mode.
* Add `--color` option to runserver, default is False. The log output will be colored by default.
  And you can change it in `[LOG.COLORS]`. Color supported is: BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE.
* Add `config` command support. It'll create config file to console. You can also
  define your own config file structure to support this command in apps. Just set `template_files/config`, 
  and write `xxxxx.conf` and even `xxxxx.ini`, in `xxxxx.ini` you can set variables
  and default values which used in `xxxxx.conf`. So `xxxxx.conf` can have template
  variables.
* Improve `support` command, also support file structure defined under apps.
* Fix template normcase bug, changed to normpath.
* Refactor ORM Reference, OneToOne, ManyToMany init process, it'll be lazy initialized, and
  you should use get_model to get the Model. Because of lazy process, when two
  Models are in same models.py, and they have relationship with them, the reversed
  properties will not assigned to reference class like before, you should use
  get_model to get those models.
* Make get_model() set_model() don't distinquish case
* Fix expose for two different view functions but with the same URL does not keep the last one bug
* Fix rabc init not using functions.has_role and functions.has_permission.
* Fix rules.py bug
* Fix rule process, add expose(replace, template) support
* Revert ORM.NULLABLE = True

0.2.1 Version
-----------------

* Add `uliweb.utils.timeit` module, use can use @timeit(prompt) to calcalate the
  time used about a code block
* change default file_serving action parameter value to `None`
* Fix Reference validate bug

0.2 Version
-----------------

* Fix auth.models `get_href` bug
* Change ORM `save()` process, it'll keep the manytomany data, before will
  remove them from data
* Add changed, saved and send_disptach to save() function.
* Improve `set_echo()`, add time, explain, caller parameters.
* Add `get_caller()` to utils.common module.
* Add `CheckboxSelectField` to form.
* Add `jsonp` function, just like json.
* Fix rule merge bug
* Improve `get_redis(**options)` enable pass parameters to it.
* Improve `jsonp()` only alphabetic and number available in `callback` parameter
* Improve pyini, support cross section variable referer and lazy process support
* Improve load command, add total records and used time display, and also use bulk
  insert
* add `test_image` function in `uliweb/utils/image.py`
* add xhr_redirect_json support. When you start uliweb application, you can pass
  xhr_redirect_json(boolean) to it, and default value is True. It means if the request
  is ajax, so the redirect will be returned as a json result with 500 status code.
  So the frontend can use it to redirect as what it wants.
* ORM remove/clear empty condition will delete all records
* Add `classonlymethod()` to uliweb.utils.common, it just likes classmethod, but
  it'll limit only class object can invoke the method rather than instance object.
* Refactor upload app, add `download` to functions
* Improve secretkey app, add `-o` to specify output file. Add `keyfile` to most functions.
* Add `MIME_TYPES` section to upload app, but it'll only effect with uliweb application, but not web server
* Improve call command, enable call modules ouside apps directory, and add project path to sys.path
* Fix orm PICKLE update bug, use deepcopy to save old_value.
* Add tornado server support.
* Add gevent and gevent-socketio server support.
* Add install command support, you can write requirements.txt in project directory or app directory.
* Add create setup.py while makeproject
* `make_application()` can reenter
* Add `ORM/MODELS_CONFIG` support

0.1.7 Version
-----------------

* Fix `uliweb.contrib.tables` dbinit.py bug
* Improve generic command can process `camel_view` to `CamelView`
* Add `pretty_dict` function to common
* Fix xmlrpc not compatiable with `prepare_request`
* Convert unknown object with `str()` in json_dumps
* Add `encrypt` and `decrypt` function to functions
* Fix pyini list value process bug for set can't process un-hashed object
* Change find tempalte result, also will list the parent template file with the same name
* Improve find template with `--tree` parameter, and it'll show a tree view of
  tmplate extend or include.
* Improve alembic init, it will remove alembic path first.
* Remove orm derived duplication check, so that user can overwrite the property of parent
* Add Decimal default precision to 10, and scale to 2
* Add functions.request_url() this can be replace request.url.
* Add count number to orm command when process multiple tables and also display appname of the model
* Add `post_commit` to transcation middleware. So you can bind a callback to it.
* Add `sequence` to Property.
* Remove LoginForm validate process, because authenticate already done this.
* Add `authenticate` to functions
* Add functions to uliweb shell
* Add ORM Lazy and cache support
* Refactor manage.py get_commands process
* Add flat_list and remove cach_get in common.py
* Refactor objcache app
* Add redis_cli app
* Fix upload app bug
* Add CHECK_MAX_LENGTH to orm app. So if it's True, and if max_length is not passed
  a value, it'll raise an Exception. Or if CHECK_MAX_LENGTH is False, max_length will
  be 255 by default.
* Add `post_do` and `rawsql` function to orm.
* Change `generic/template_files/common/views.py` to `views.py.tmpl`
* Add GenericReference value `(Model, object_id)` support
* Fix pyini save process
* Fix `_create_kwargs` quote characters bug, and change the function to `to_attrs`
* Refactor multiple db support, only one engine supported for each class.
* Add static combine functionality, so you can combine some js or css files into
  one file.
* Improve `sql` command, add index output, and also add `sqltable` command.
* Add SQLMonitor
* Fix unbind bug
* Improve ORM `auto` and `auto_add` process. If `auto` and `auto_add` are both `False` or `None`,
  default will be used. And if one of `auto` or `auto_add` is `True`, then only
  add or update will use default value.
* improve do_ process, and add set_echo() function, so you can use it to debug sql executation
* improve shell command, add filename support
* mail add sendmail support
* fix zip mode bug in dump and add zip support for dumptable command
* remove kwargs['default'] = self.default process
* add expiry_time support for session key
* Fix checkbox label delimeter bug
* add cache parameter to ids()
* add mapping_only support and add not remove table in alembic diff support, you should add --remove
* add --force for alembic diff and add server_default compare support
* Add colorloged.py, so you can use it to output colored log
* fix now() for date and time
* Upgrade werkzeug to 0.9.1
* Improve ssl options

0.1.6 Version
-----------------

* Add CSRF support thanks for Damon
* Add multiple lines comment tag `{{## ##}}` support to template
* Improve makeproject project template, add .gitignore and local_settings.ini
* Refactor `call_view()` so that fix the soap view function will invoke
  `__begin__` or `__end__` twice bug.
* Refactor Functions, and Decorators, add parent class Finder. Also you can import
  from `uliweb`
* Replace class type judgement with `inspect.isclass()`
* Fix `--version` command argument process bug.
* Improve `import_mod_attr`, and make it can receive object parameter
* Add `handler()` function to Dispatcher, and it'll return an instance of `DispatcherHandler`
  and it provide `get`, `post`, `delete`, .etc, restful api, and you can invoke
  them to execute an url, for example:

    ```
    from uliweb import application

    handler = application.handler()
    r = handler.get('/index')
    #r is response object
    ```
* Add `client_from_application()` to uliweb/utils/test.py
* Add `dispatcher_cls` and `dispatcher_kwargs` to `make_application` and
  `make_simple_applicatin`, so you can pass difference Disptacher class
  which provided by `uliweb/core/SimpleFrame.py`.
* Add `PUT` and `PATCH` judgement to csrf middleware.
* Fix template.py for multiple times extending the same template file bug
* Expose `filename_convert()` function from upload app
* Add `get_uuid()` function to utils/common.py
* Fix `get_collection_name()` bug
* Fix json bug, when dealing with `0x00-0x1f`
* Add generic app, so user can use `functions.ListView`
* Add fieldset support for BootstrapLayout
* Change generic.py `json_body` to `json_result`, add `.f` attributes to DetailView object
* Change IntField build class to Number, so the html code will be `<input type="number"/>`
* Change DateTimeField html creation with UTC to no UTC.
* Fix `GET` and `POST` bind to same url but with different method will be replaced bug
* Fix `u"""` and `u'''` bug in pyini process
* Skip empty templates directories when startup
* Module of template_plugins can be configured in settings.ini
* Add `df` parameter to common.copy_dir processor callback function
* Remove `return`, `continue`, `break` unindent process, so only `pass` will unindent used
* Add `generic` command, you can use it to create scafold of List, Add, View, Edit, Delete,
  it support angularjs, html, easyui theme.
* Add `Builder` class to html.py, then refactor `generic.DetailView` , so you can use
  `{{<< view.body}}` to get the body result but not the whole paragraph.
* Add `kwargs` to ORM get, filter, and also add `for_update` method to Result, so.
  you can do select with for update lock, for example:

    ```
    Model.get(Model.c.id==id, for_update=True)
    Model.filter(condition).for_update().filter(condition)
    ```

* generic ListView and SimpleListView can get value of page and rows from request,
  so if you pass these variables in the GET or POST, you don't need to parse them
  and then pass them to ListView or SimpleListView, you can just skip them, ListView
  and SimpleListView will parse them automatically
* `Result.for_update` can receive an argument, default it `True`, and string also
  can be accpeted, please see the sqlalchemy doc http://docs.sqlalchemy.org/en/latest/core/expression_api.html for details.
* Add secretkey app, when you installed this app, you can execute cmd:

    ```
    uliweb makekey
    ```

  to create a secretkey file, which will be locate in current directory by default. Then:

    ```
    from uliweb import functions
    des = functions.get_cipher()
    d = des.encrypt('hello')
    des.descrypt(d)
    ```

* Remove pagecache app
* Add `safe_unicode` and `safe_str` support i18n LazyString class
* Refactor generic.ListView and generic.SimpleListView output, the table will be
  and Builder object, so you can:

    ```
    table.begine
    table.colgroup
    table.head
    table.body
    table.end
    ```

* Add `get_input()` to command.py, you can use it to get a value from command line
  if an option is not given
* Remove APP_LAYOUT functionality, and it can be replaced with

    ```
    settings.APP_LAYOUTS.get('messages', 'layout.html')
    ```

  so you can still config app's layout template in settings.ini. Another way is
  to replace app's layout template in a new app with the same filename, and then
  install it after the original app in `INSTALLED_APPS`.

0.1.5 Version
-----------------

* Change cache settings, remove file_dir and lock_dir as 0.1.3 before
* Add more info about dispatch call exception output
* Add uliweb.contrib.form app, and add get_form() function.
* Make auth support get_form() appoach
* Improve file_storage process.
* Fix RedirectException still display bug.
* Add TablenameConvert support to uliweb.orm, you can pass an converter function
  via orm.set_tablename_converter(converter) function, or defined it in settings.ini
  if you are in a project, for example:

    ```
    [ORM]
    TABLENAME_CONVERTER = 'uliweb.utils.common.camel_to_'
    ```

  Then if the Model name is CamelCase then it'll be converted to `camel_case`.
* Add Reference, OneToOne, ManyToMany relation definition in Model level
* If collection_name is None, and if there is already `tablename_set` existed,
  then it'll create new collection_name automatically, so that the collection_name
  will not be duplication at all. But if the user pass the collection_name, and
  if there is `tablename_set` already, then raise the Exception always. Please note
  the difference about it.
* Change default max_length of CHAR, str, unicode as 255. The original default value
  is 30.
* Add IS_LENGTH_LESSTHAN and IS_LENGTH_BETWEEN to validators.py.
* Add [GLOBAL_OBJECTS] mechanism, objects config in here will be injected into uliweb.
* Add validators to uliweb, but this appoach is using [VALIDAOTRS] mechanism.
* Add IS_LENGTH_LESSTHAN validator to generic.py if there is max_length exists.
* Add newline and attrs to core/html.py/Tag, for example:

    ```
    >>> print Tag('p', 'Hello', attrs={'data-link':'ok'}, newline=False)
    <p data-link="ok">Hello</p>
    ```

  so you can pass `data-link` to `attrs`. For `newline=False` will not create `\n`.
* Remove `Script` of core/html.py.
* Add AUTHORS.md doc.
* Fix BootstrapTableLayout HiddenField creation bug.
* Add serial_cls support, so you can config session serial class yourself. Default is Cache.Serial.
* If the url prefix '!' then don't parse it with appname URL prefix. For example:

    ```
    @expose('!/hello')
    ```
* Improve url expose for '!' process, and make class view also support it. Add test_url.py.
* Change form validate_xxx in the front of the original validator functions, move BaseField
  validate error mssage to module level, e.g. ERR_REQUIRED
* Fix i18n bug for LazyString
* Add chmod after mkdirs in extract_dir function
* Add alembic init command will drop `alembic_version` table
* Add DEBUG_CONSOLE config to seperate DebugApplication evalex parameter from DEBUG

0.1.4 Version
-----------------

* Fix utils/date.to_datetime() support %f(misrosecond) format
* Add microsecond format support in utils/date.py
* Improve DateField, TimeField, DatetimeField process with date module
* Remove doc test from uliform.py to test_form.py
* Fix rules.py can't parse Class View function directly, such as defined in
   settings.ini, also fix app URL definition for relative expose bug.
* Add test_sorteddict.py and add sort() method to sorteddict class
* Add common set_var and get_var and configure them in default_settings.ini
* improve soap app, add multiple soap support, details you should see soap doc
* Refactor form, add build propert and function to Form class, and the result
   should be: pre_html, begin, body, buttons, end, post_html
* Add default parameter to uliweb/utils/common.py get_choice()
* Improve template extend and include process, if you extend the same filename
   with current filename, then it'll find the parent same named filename. This
   way can make new same named filename but extended from parent. Also support
   include tag.
* Add APP_LAYOUT support in uliweb.contrib.template, so in your template you can
   use: `{{use layout_template}}` in your tmplate, and config the app layout template
   as:

        [APP_LAYOUTS]
        appname = 'layout.html'

   so when render the template, the `layout_template` will be replaced with `layout.html`
* Add QueryString and query_string support in common.py
* Fix dispatch signal process bug
* Set werkzeug log level to 'info', #issue 2
* Improve template_layout.py checkbox creation
* Change wsgi_staticfiles apps order, later defined app will be processed earlier
* Refactor manage.py add call() function, add -f option to makeproject and makeapp
* Add test_cache.py test file.
* Add creator parameter to cache.get() and also support callable for value
* Add memcache storage support, and add inc(), dec() to cache
* Refactor require_login, remove has_login, require_login will raise Redirect Exception
   so you don't need to just return value
* Change Redirect to RedirectException, and redefine Redirect as function
* Fix soap configure reading bug
* Fix log format bug
* Fix pysimplesoap bool type bug http://code.google.com/p/pysimplesoap/issues/attachmentText?id=69&aid=690001000&name=simplexml.py.patch&token=F8TXcyAoCDS5vScp5MiFEccN6J4%3A1345507177742

0.1.3 Version
-----------------

* Fix loadtable bug for PickleType type, using inspecttable instead, so
   PickleyType will be BLOB type.
* Improve template process:

    * Add `#uliweb-template-tag:<begin_tag>,<end_tag><newline>` process to template
       file, and you can also pass `begin_tag` and `end_tag` to Template, and
       `template_file()` or `template()`
    * Add `[TEMPLATE_PROCESSOR]` section to `default_settings.ini`, so that user
       can setup his own template processor, the option will look like:

            angularjs_template = {'file_exts':['.ahtml'],
                'processor':'uliweb.core.template.template_file',
                'args':{}}

       * the key is not very important, but you should keep it unique
       * `file_exts` will be the file extensions, it's a list, so the
         processor can match multiple filenames
       * `processor` will be the path of template function, uliweb will
         import it when needed
       * `args` will be a dict, and it will be passed to template function
    * Add `BEGIN_TAG` and `END_TAG` to settings.ini, so user can change
       default tag name from `{{` and `}}` to other strings. But this
       appoach will effect globally, so if you are using other apps with
       templates which using old tag strings, will cause errors. So using
       `#uliweb-template-tag` or `TEMPLATE_PROCESSOR` maybe the good way,
       but you still need to set it in template file or set `response.template`
       with other template extension, because the defult template file extension
       is `.html`. For example:

            def index():
                response.template = 'index.ahtml'
                return {}

       Above code will override the default template filename from `index.html`
       to `index.ahtml`.
* Add Redirect support. Redirect is an exception, and also add Redirect support
   in middle_session. Because Redirect is an exception, so it'll implement process_exception
   and save the session also.
* Fix generic.py fields_convert_map initialization bug
* Fix template get_text() bug, add inherit_tags parameter to it, and if it's False,
   will use default begin and end tag string.
* Fix file_serving.download() for Chinese characters bug.
* Change the order of creating table colums according the definition of Model
* Fix pyini/uni_prt bug. And change _uni_prt to uni_prt.
* Add object() to ListView
* Upgrade pysimplesoap to 1.05a

0.1.2 Version
-----------------

* Fix permission tag, and change PERMISSION definitions in settings.ini, now the
   PERMISSION definition can use dict datatype, just like:

    ```
    [PERMISSION]
    PERM = {'name':'PERM', 'roles':['a', 'b'], 'description':'PERM}
    ```

   and with this method, you don't need to define ROLES_PERMISSIONS section
* Add TransactionMiddle as default settings in ORM settings.ini. By default, if
   you add 'uliweb.contrib.orm', the transaction middleware will automatically
   enabled. In the previous version, you should add this middleware yourself.
* Add app arguments to exportstatic command
* Remove --with-static option of export command, so default behavior is export
   static folder
* Fix default file_serving process, add x_filename process, in order to make
   alt filename support processing correctly.
* Add -m option to find command, so you can use:

    ```
    uliweb find -m model_name
    ```

   to find the model is defined in which model
* Add manytomany parameter to Model.delete() function, so it'll automatically
   delete manytomany relationships.
* Add tables app to uliweb.
* Add GenericReference and GenericRalation support
* Add BigIntegerProperty support, the shorthand is Field(BIGINT)
* Add `__pk_type__` variable, current is 'int', others will be 'biginteger',
   you can use set_pk_type(name) to switch it, also add PKTYPE() function, you
   can use Field(PKTYPE()) to create ForeignKey Property according the option,
   in web project, you can swith it via ORM/PK_TYPE
* Add delete_fieldname parameter to Model.delete(), so if you pass True, it'll
   assume the delete_fieldname is 'deleted', and if you pass real field_name it'll
   use it directly. This way will not delete the record at all, just change the
   delete_fieldname value from False to True.
* Fix RemoteField default datatype as int and default value is None.
* Refactor the ReferenceProperty datatype process.
* Add _class and id parameter to Form, and fix form_class process
* Refactor template, add BaseBlockNode class, and add end() process for block type node.

0.1.1 Version
-----------------

* Add BAE(Baidu Application Engine) and Heroku support

0.0.1 Version
-----------------

* Support i18n language setting key in query_string, and you can also configure
   keyword in settings.ini.