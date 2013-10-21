import os
import re
from uliweb.utils.common import log
from uliweb.core.template import *
from uliweb import functions

r_links = re.compile('<link\s+.*?\s*href\s*=\s*"?(.*?)["\s>]|<script\s+.*?\s*src\s*=\s*"?(.*?)["\s>]', re.I)
r_head = re.compile('(?i)<head>(.*?)</head>', re.DOTALL)
r_top = re.compile('<!--\s*toplinks\s*-->')
r_bottom = re.compile('<!--\s*bottomlinks\s*-->')

#used to remember static files combine infos
__static_combine__ = None
__static_mapping__ = {}

class UseModuleNotFound(Exception): pass
class TemplateDefineError(Exception): pass

class LinkNode(Node):
    
    def __init__(self, value=None, content=None, template=None):
        self.value = value
        self.content = content
        self.template = template
        
    @staticmethod
    def init(template):
        template.add_callback(LinkNode.htmlmerge)
        template.add_exec_env('link', LinkNode.link)
        template.add_exec_env('__links__', {'toplinks':[], 'bottomlinks':[]})
        
    def __str__(self):
        return 'link(_env, %s)\n' % self.value
    
    def __repr__(self):
        return '{{link %s}}' % self.value
    
    @staticmethod
    def link(env, links, media=None, to='toplinks'):
        if not isinstance(links, (tuple, list)):
            links = [links]
        if media:
            new_links = []
            for x in links:
                new_links.append({'value':x, 'media':media})
            links = new_links
        if to == 'toplinks':
            env['__links__']['toplinks'].extend(links)
        else:
            env['__links__']['bottomlinks'].extend(links)
        
    @staticmethod
    def htmlmerge(text, template, vars, env):
        m = HtmlMerge(text, env['__links__'], vars, env)
        return  m()
    
class UseNode(LinkNode):
    __saved_template_plugins_modules__ = {}
    
    @staticmethod
    def init(template):
        template.add_callback(UseNode.htmlmerge)
        template.add_exec_env('use', UseNode.use)
        template.add_exec_env('__links__', {'toplinks':[], 'bottomlinks':[]})

    def __str__(self):
        return 'use(_vars, _env, %s)\n' % self.value
    
    def __repr__(self):
        return '{{use %s}}' % self.value
    
    @staticmethod
    def use(vars, env, plugin, *args, **kwargs):
        from uliweb.core.SimpleFrame import get_app_dir
        from uliweb import application as app, settings
        from uliweb.utils.common import is_pyfile_exist

        if plugin in UseNode.__saved_template_plugins_modules__:
            mod = UseNode.__saved_template_plugins_modules__[plugin]
        else:
            #add settings support, only support simple situation
            #so for complex cases you should still write module
            #format just like:
            #
            #[TEMPLATE_USE]
            #name = {
            #   'toplinks':[
            #       'myapp/jquery.myapp.{version}.min.js',
            #   ], 
            #   'depends':[xxxx], 
            #   'config':{'version':'UI_CONFIG/test'},
            #   'default':{'version':'1.2.0'},
            #}
            #
            mod = None
            c = settings.get_var('TEMPLATE_USE/'+plugin)
            if c:
                config = c.pop('config', {})
                default = c.pop('default', {})
                #evaluate config value
                config = dict([(k, settings.get_var(v, default.get(k, ''))) for k, v in config.items()])
                #merge passed arguments
                config.update(kwargs)
                for t in ['toplinks', 'bottomlinks']:
                    if t in c:
                        c[t] = [x.format(**config) for x in c[t]]
                mod = c
            else:
                for p in app.apps:
                    if not is_pyfile_exist(os.path.join(get_app_dir(p), 'template_plugins'), plugin):
                        continue
                    module = '.'.join([p, 'template_plugins', plugin])
                    try:
                        mod = __import__(module, {}, {}, [''])
                    except ImportError, e:
                        log.exception(e)
                        mod = None
            if mod:
                UseNode.__saved_template_plugins_modules__[plugin] = mod
            else:
                log.error("Can't find the [%s] template plugin, please check if you've installed special app already" % plugin)
                if settings.get_var('TEMPLATE/RAISE_USE_EXCEPTION'):
                    raise UseModuleNotFound("Can't find the %s template plugin, check if you've installed special app already" % plugin)
                
        #mod maybe an dict
        if isinstance(mod, dict):
            v = mod
        else:
            v = None
            call = getattr(mod, 'call', None)
            if call:
                v = call(app, vars, env, *args, **kwargs)
        if v:
            if 'depends' in v:
                for _t in v['depends']:
                    if isinstance(_t, str):
                        UseNode.use(vars, env, _t)
                    else:
                        d, kw = _t
                        UseNode.use(vars, env, d, **kw)
            for _type in ['toplinks', 'bottomlinks']:
                if _type in v:
                    links = v[_type]
                    if not isinstance(links, (tuple, list)):
                        links = [links]
                    env['__links__'][_type].extend(links)
            if 'depends_after' in v:
                for _t in v['depends_after']:
                    if isinstance(_t, str):
                        UseNode.use(vars, env, _t)
                    else:
                        d, kw = _t
                        UseNode.use(vars, env, d, **kw)
                
    
class HtmlMerge(object):
    def __init__(self, text, links, vars, env):
        self.text = text
        self.links = links
        self.env = env
        self.vars = vars
        self.init()
        
    def init(self):
        global __static_combine__, __static_mapping__
        from . import init_static_combine
        
        if __static_combine__ is None:
            __static_combine__ = init_static_combine()
            for k, v in __static_combine__.items():
                for x in v:
                    __static_mapping__[x] = k
        
    def __call__(self):
#        b = r_head.search(self.text)
#        if b:
#            start, end = b.span()
#            head = b.group()
#            p = self.cal_position(head, start)
#            links = []
#            for v in r_links.findall(head):
#                link = v[0] or v[1]
#                links.append(link)
#            result = self.assemble(self._clean_collection(links))
#            if result['toplinks'] or result['bottomlinks']:
#                top = result['toplinks'] or ''
#                bottom = result['bottomlinks'] or ''
#                return (self.text[:p[0]] + top + self.text[p[1]:p[2]] + bottom +
#                    self.text[p[3]:])
#        else:
#            result = self.assemble(self._clean_collection([]))
#            if result['toplinks'] or result['bottomlinks']:
#                top = result['toplinks'] or ''
#                bottom = (result['bottomlinks'] or '')
#                return top + bottom + self.text

        result = self.assemble(self._clean_collection([]))
        #cal links first, if no toplinks or bottomlinks be found, then
        #do nothing, otherwise find the head, and calculate the position
        #of toplinks and bottomlinks
        if result['toplinks'] or result['bottomlinks']:
            links = []
            b = r_head.search(self.text)
            if b:
                start, end = b.span()
                head = b.group()
                for v in r_links.findall(head):
                    link = v[0] or v[1]
                    links.append(link)
            else:
                head = ''
                start, end = 0, 0
            result = self.assemble(self._clean_collection(links))
            if result['toplinks'] or result['bottomlinks']:
                top = result['toplinks'] or ''
                bottom = result['bottomlinks'] or ''
                top_start, bottom_start = self.cal_position(self.text, top, bottom,
                    len(head), start)
                
                if top and bottom:
                    if bottom_start < top_start:
                        raise TemplateDefineError, "Template <!-- bottomlinks --> shouldn't be defined before <!-- toplinks -->"
                    return self.text[:top_start] + top + self.text[top_start:bottom_start] + bottom + self.text[bottom_start:]
                elif top:
                    return self.text[:top_start] + top + self.text[top_start:]
                elif bottom:
                    return self.text[:bottom_start] + bottom + self.text[bottom_start:]
        
        return self.text
    
    def _clean_collection(self, existlinks):
        r = {'toplinks':[], 'bottomlinks':[]}
        links = {}
        #process links, link could be (order, link) or link
        for _type in ['toplinks', 'bottomlinks']:
            t = self.links.get(_type, [])
            for link in t:
                #link will also be template string
                if '{{' in link and '}}' in link:
                    link = template(link, self.env)
                    
                #process static combine
                new_link = __static_mapping__.get(link, link)
                if new_link.endswith('.js') or new_link.endswith('.css'):
                    _link = functions.url_for_static(new_link)
                else:
                    _link = new_link
                if not new_link in r[_type] and not _link in existlinks:
                    r[_type].append(new_link)
        return r

    def cal_position(self, text, has_toplinks, has_bottomlinks, head_len, head_start):
        """
        Calculate the position of toplinks and bottomlinks, if there is not
        toplinks and bottomlinks then toplinks position will be the position after <head>
        and if there is no bottomlinks, the bottomlinks position will be the
        position before </head>.
        """
        if head_len == 0:
            top_start = top_end = bottom_start = bottom_end = 0
        else:
            top_start = top_end = head_start + 6
            bottom_start = bottom_end = head_start + head_len - 7
            
        if has_toplinks:
            t = r_top.search(text)
            if t:
                top_start, top_end = t.span()
        
        if has_bottomlinks:
            t = r_bottom.search(text)
            if t:
                bottom_start, bottom_end = t.span()

        return top_end, bottom_end

    def assemble(self, links):
        toplinks = ['']
        bottomlinks = ['']
        for _type, result in [('toplinks', toplinks), ('bottomlinks', bottomlinks)]:
            for x in links[_type]:
                if isinstance(x, dict):
                    link, media = x['value'], x['media']
                else:
                    link, media = x, None
                if link.endswith('.js'):
                    link = functions.url_for_static(link)
                    result.append('<script type="text/javascript" src="%s"></script>' % link)
                elif link.endswith('.css'):
                    link = functions.url_for_static(link)
                    if media:
                        result.append('<link rel="stylesheet" type="text/css" href="%s" media="%s"/>' % (link, media))
                    else:
                        result.append('<link rel="stylesheet" type="text/css" href="%s"/>' % link)
                elif link.endswith('.less'):
                    link = functions.url_for_static(link)
                    result.append('<link rel="stylesheet/less" href="%s"/>' % link)
                else:
                    result.append(link)
        return {'toplinks':'\n'.join(toplinks), 'bottomlinks':'\n'.join(bottomlinks)}

