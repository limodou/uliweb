`英文版 <{{= url_for('%s.views.documents' % request.appname)+'?lang=en' }}>`_

基本信息
---------------------
{{ 
def index(filename, lang=''):
    return url_for('%s.views.show_document' % request.appname, filename=filename, lang=lang)
pass
}}
* `Uliweb简介 <{{= index('introduction') }}>`_
* `许可协议 <{{= index('license') }}>`_
* 更新说明
* `鸣谢 <{{= index('credits') }}>`_
* `使用Uliweb的网站 <{{= index('sites') }}>`_

安装
-------------------------

* `系统需求 <{{= index('requirements') }}>`_
* `安装Uliweb <{{= index('installation') }}>`_
* 配置Uliweb

教程
-------------------------------

* `Hello, Uliweb(易) <{{= index('hello_uliweb') }}>`_
* `迷你留言薄(难) <{{= index('guestbook') }}>`_
* 模板和视图
* 快速构建博客
* 用CSS美化你的博客
* 深入了解Uliweb
* 参考资料

参考
-----------------------------

* `体系统结构和机制 <{{= index('architecture') }}>`_
* `URL映射 <{{= index('url_mapping') }}>`_
* `视图 <{{= index('views') }}>`_
* `模板 <{{= index('template') }}>`_
* `数据库和ORM <{{= index('orm') }}>`_
* `部署指南 <{{= index('deployment') }}>`_
* `manage.py使用指南 <{{= index('manage_guide') }}>`_
* `I18n <{{= index('i18n') }}>`_
* `全局环境 <{{= index('globals') }}>`_

高级话题
-----------------------------

* 扩展Uliweb
* 详解配置文件
* 安全机制
* 容错机制
* 在Uliweb中使用Ajax
* 与其他框架结合()

系统类参考
------------------------------

扩展主题
-------------------------------

* 快速参考图


