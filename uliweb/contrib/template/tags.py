import os
import re
from uliweb.utils.common import log
from uliweb.core.template import *

r_links = re.compile('<link\s.*?\s+href\s*=\s*"?(.*?)["\s>]|<script\s.*?\s+src\s*=\s*"?(.*?)["\s>]', re.I)
r_head = re.compile('(?i)<head>(.*?)</head>', re.DOTALL)
r_top = re.compile('<!--\s*toplinks\s*-->')
r_bottom = re.compile('<!--\s*bottomlinks\s*-->')

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
        
    def render(self):
        return 'link(_env, %s)\n' % self.value
    
    def __repr__(self):
        return '{{link %s}}' % self.value
    
    @staticmethod
    def link(env, links, media=None, toplinks=True):
        if not isinstance(links, (tuple, list)):
            links = [links]
        if media:
            new_links = []
            for x in links:
                new_links.append({'value':x, 'media':media})
            links = new_links
        if toplinks:
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

    def render(self):
        return 'use(_vars, _env, %s)\n' % self.value
    
    def __repr__(self):
        return '{{use %s}}' % self.value
    
    @staticmethod
    def use(vars, env, plugin, *args, **kwargs):
        from uliweb.core.SimpleFrame import get_app_dir
        from uliweb import application as app

        if plugin in UseNode.__saved_template_plugins_modules__:
            mod = UseNode.__saved_template_plugins_modules__[plugin]
        else:
            from uliweb.utils.common import is_pyfile_exist
            mod = None
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
                log.debug("Can't found the [%s] html plugins, please check if you've installed special app already" % plugin)
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
    
class HtmlMerge(object):
    def __init__(self, text, links, vars, env):
        self.text = text
        self.links = links
        self.env = env
        self.vars = vars
        
    def __call__(self):
        b = r_head.search(self.text)
        if b:
            start, end = b.span()
            head = b.group()
            p = self.cal_position(head, start)
            links = []
            for v in r_links.findall(head):
                link = v[0] or v[1]
                links.append(link)
            result = self.assemble(self._clean_collection(links))
            if result['toplinks'] or result['bottomlinks']:
                top = result['toplinks'] or ''
                bottom = result['bottomlinks'] or ''
                return (self.text[:p[0]] + top + self.text[p[1]:p[2]] + bottom +
                    self.text[p[3]:])
        else:
            result = self.assemble(self._clean_collection([]))
            if result['toplinks'] or result['bottomlinks']:
                top = result['toplinks'] or ''
                bottom = (result['bottomlinks'] or '')
                return top + bottom + self.text
            
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
                if not link in r[_type] and not link in existlinks:
                    r[_type].append(link)
        return r

    def cal_position(self, head, start=0):
        length = len(head)
        t = r_top.search(head)
        if t:
            top_start, top_end = t.span()
        else:
            top_start = top_end = 6
        t = r_bottom.search(head)
        if t:
            bottom_start, bottom_end = t.span()
        else:
            bottom_start = bottom_end = length-7
        r = [start+i for i in [top_start, top_end, bottom_start, bottom_end]]
        return r

    def assemble(self, links):
        from uliweb.contrib.staticfiles import url_for_static
        
        toplinks = ['']
        bottomlinks = ['']
        for _type, result in [('toplinks', toplinks), ('bottomlinks', bottomlinks)]:
            for x in links[_type]:
                if isinstance(x, dict):
                    link, media = x['value'], x['media']
                else:
                    link, media = x, None
                if link.endswith('.js'):
                    link = url_for_static(link)
                    result.append('<script type="text/javascript" src="%s"></script>' % link)
                elif link.endswith('.css'):
                    link = url_for_static(link)
                    if media:
                        result.append('<link rel="stylesheet" type="text/css" href="%s" media="%s"/>' % (link, media))
                    else:
                        result.append('<link rel="stylesheet" type="text/css" href="%s"/>' % link)
                else:
                    result.append(link)
        return {'toplinks':'\n'.join(toplinks), 'bottomlinks':'\n'.join(bottomlinks)}

