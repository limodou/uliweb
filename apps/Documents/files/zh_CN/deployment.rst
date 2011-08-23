部署指南
=============

:Author: Limodou <limodou@gmail.com>

.. contents:: 
.. sectnum::

GAE(Google Application Engine)
--------------------------------

GAE是Google提供的一个web运行环境，因此你首先要申请到一个可用的帐号。然后使用这个帐号创建
你的项目。

你应该在GAE的SDK下进行测试。

#. 通过export命令将Uliweb导出到GAE的开发环境下，目标路径与你的项目的名字相同。比如你的项
   目起名为myproject，而你的GAE环境安装在 "C:\Program Files\Google\google_appengine", 
   可以在命令行执行：

   ::

        python manage.py export "C:\Program Files\Google\google_appengine\myproject"
        
   注意目标目录名使用了双引号，因为目录中有空格。这样完整的Uliweb开发环境就安装好了。

#. 修改app.yaml文件，其中application对应的名字应该与你申请的名字相同，如myproject。
#. 进行你的开发。可以先使用Uliweb的开发服务器，然后再最后切换到GAE的开发服务器下进行测试。
#. 使用GAE的上传工具上传项目：

   ::

        python appcfg.py update myproject
        
.. note::

    目前Uliweb可以对静态文件进行统一的处理，因此你完全可以使用Uliweb的静态文件处理机制。
    如果你不需要，希望由GAE来做，那么可以考虑GAE的文档增加静态文件处理的配置。你需要：
    
    * 使用manage.py exportstatic命令将静态文件收集到一个统一的目录下
    * 修改app.yaml配置文件增加对这些静态文件的支持，并将其置于 ``- url: /.*`` 之前。
    
Apache
---------

mod_wsgi
~~~~~~~~~~~

#. 按 `mod_wsgi <http://code.google.com/p/modwsgi/>`_ 的说明安装mod_wsgi到apache下。

   * 拷贝mod_wsgi.so到apache的modules目录下

   Window环境可以看：

    http://code.google.com/p/modwsgi/wiki/InstallationOnWindows

   Linux环境可以看：

    http://code.google.com/p/modwsgi/wiki/InstallationOnLinux


#. 配置 apache 的httpd.conf文件

   * 增加：

     ::
    
        LoadModule wsgi_module modules/mod_wsgi.so
        WSGIScriptAlias / /path/to/uliweb/wsgi_handler.wsgi
        
        <Directory /path/to/youruliwebproject>
        Order deny,allow
        Allow from all
        </Directory>
        
     上面是将起始的URL设为/，你可以根据需要换为其它的起始URL，如/myproj。
    
     如果在windows下，示例为：
    
     ::
     
        WSGIScriptAlias / d:/project/svn/uliweb/wsgi_handler.wsgi
        
        <Directory d:/project/svn/uliweb>
        Order deny,allow
        Allow from all
        </Directory>

#. 重启apache
#. 测试。启动浏览器输入： http://localhost/YOURURL 来检测你的网站可否可以正常访问。 

Lighttpd + SCGI
-----------------
#. 配置lighttpd.conf：
   ::
     
     scgi.server=(
	"/uliweb.scgi"=> (
			 "main" => (
			 	"socket" => "/tmp/uliweb.sock",
				"check-local" => "disable",
				),
			),
	)
	url.rewrite-once = (
			 "^(/.*)$" => "/uliweb.scgi$1",
	)

#. 运行：
   ::
     
     python runcgi.py protocol=scgi socket=/tmp/uliweb.sck method=threaded daemonize=true

.. note::
	runcgi.py需要使用flup,下地址：http://trac.saddi.com/flup


IIS + SCGI
--------------

#. 下载安装pyISAPI_SCGI 地址: http://code.google.com/p/pyisapi-scgi/
#. pyISAPI_SCGI配置方法 http://code.google.com/p/pyisapi-scgi/wiki/PyISAPI_SCGI_0_6_17
#. 编辑scgi.conf:
   ::
     
     port=3033 #设置一个空闲的端口号


#. 运行:
   ::
     
     python runcgi.py protocol=scgi host=127.0.0.1 port=3033 method=threaded

.. note::
	runcgi.py需要使用flup,下地址：http://trac.saddi.com/flup


虚拟主机(DreamHost,BlueHost,HostMonsger等)
--------------------------------------------

FastCGI
~~~~~~~~~

#. 安装python, 参考http://wiki.dreamhost.com/Python
#. 新建dispatch.fcgi,内容：
   ::
   
     #!/home/yourname/bin/python (你安装的python的路径)
     import sys
     from runcgi import run
     run(method='threaded',protocol='fcgi')

#. 编辑.htaccess，内容：
   ::
   
     Options +FollowSymLinks +ExecCGI
     RewriteEngine On
     RewriteBase /
     RewriteRule ^(dispatch\.fcgi/.*)$ - [L]
     RewriteRule ^(.*)$ dispatch.fcgi/$1 [L]
     AddHandler fastcgi-script .fcgi #或者是AddHandler fcgid-script .fcgi

CGI
~~~~
#. 安装python, 参考http://wiki.dreamhost.com/Python
#. 修改runcgi.py,将第一行内容修改为：
   ::
     
     #!/home/yourname/bin/python (你安装的python的路径)


#. 修改.htaccess,内容：
   ::
     
     Options +FollowSymLinks +ExecCGI
     RewriteEngine On
     RewriteBase /
     RewriteRule ^(runcgi\.py/.*)$ - [L]
     RewriteRule ^(.*)$ runcgi.py/$! [L]
     AddHandler cgi-script .py
.. note::
	
	以CGI方式运行，需flup 1.0以上版本。