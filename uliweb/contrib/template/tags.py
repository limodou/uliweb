import os
import re
from uliweb.utils.common import log
from uliweb.core.template import *
from uliweb import functions
import warnings
import inspect

r_links = re.compile('<link\s+.*?\s*href\s*=\s*"?(.*?)["\s>]|<script\s+.*?\s*src\s*=\s*"?(.*?)["\s>]', re.I)
r_head = re.compile('(?i)<head>(.*?)</head>', re.DOTALL)
r_top = re.compile('<!--\s*toplinks\s*-->')
r_bottom = re.compile('<!--\s*bottomlinks\s*-->')

#used to remember static files combine infos
__static_combine__ = None
__static_mapping__ = {}
__saved_template_plugins_modules__ = {}
__use_cached__ = {}

class UseModuleNotFound(Exception): pass
class TemplateDefineError(Exception): pass

def link(env, links, to='toplinks', **kwargs):
    if not isinstance(links, (tuple, list)):
        links = [links]
    if kwargs:
        new_links = []
        for x in links:
            kw = {'value':x}
            kw.update(kwargs)
            new_links.append(kw)
        links = new_links
    if to == 'toplinks':
        env['toplinks'].extend(links)
    else:
        env['bottomlinks'].extend(links)

def htmlmerge(text, env):
    m = HtmlMerge(text, env)
    return  m()
    
def use(env, plugin, *args, **kwargs):
    toplinks, bottomlinks = find(plugin, *args, **kwargs)
    env['toplinks'].extend(toplinks)
    env['bottomlinks'].extend(bottomlinks)

def find(plugin, *args, **kwargs):
    from uliweb.core.SimpleFrame import get_app_dir
    from uliweb import application as app, settings
    from uliweb.utils.common import is_pyfile_exist

    key = (plugin, repr(args) + repr(sorted(kwargs.items())))
    if key in __use_cached__:
        return __use_cached__[key]

    if plugin in __saved_template_plugins_modules__:
        mod = __saved_template_plugins_modules__[plugin]
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
            for p in reversed(app.apps):
                if not is_pyfile_exist(os.path.join(get_app_dir(p), 'template_plugins'), plugin):
                    continue
                module = '.'.join([p, 'template_plugins', plugin])
                try:
                    mod = __import__(module, fromlist=['*'])
                    break
                except ImportError as e:
                    log.info('Module path is {}'.format(os.path.join(get_app_dir(p), 'template_plugins', plugin)))
                    log.exception(e)
                    mod = None
        if mod:
            __saved_template_plugins_modules__[plugin] = mod
        else:
            log.error("Can't find the [%s] template plugin, please check if you've installed special app already" % plugin)
            raise UseModuleNotFound("Can't find the %s template plugin, check if you've installed special app already" % plugin)

    #mod maybe an dict
    if isinstance(mod, dict):
        v = mod
    else:
        v = None
        call = getattr(mod, 'call', None)
        call.__name__ = call.__module__
        if call:
            para = inspect.getargspec(call)[0]
            #test if the funtion is defined as old style
            if ['app', 'var', 'env'] == para[:3]:
                warnings.simplefilter('default')
                warnings.warn("Tmplate plugs call function(%s) should be defined"
                              " as call(*args, **kwargs) not need (app, var, env) any more" % call.__module__,
                              DeprecationWarning)
                v = call(app, {}, {}, *args, **kwargs)

            else:
                v = call(*args, **kwargs)

    toplinks = []
    bottomlinks = []
    if v:
        if 'depends' in v:
            for _t in v['depends']:
                if isinstance(_t, str):
                    t, b = find(_t)
                else:
                    d, kw = _t
                    t, b = find(d, **kw)
                toplinks.extend(t)
                bottomlinks.extend(b)
        if 'toplinks' in v:
            links = v['toplinks']
            if not isinstance(links, (tuple, list)):
                links = [links]
            toplinks.extend(links)
        if 'bottomlinks' in v:
            links = v['bottomlinks']
            if not isinstance(links, (tuple, list)):
                links = [links]
            bottomlinks.extend(links)
        if 'depends_after' in v:
            for _t in v['depends_after']:
                if isinstance(_t, str):
                    t, b = use(env, _t)
                else:
                    d, kw = _t
                    t, b = use(env, d, **kw)
                toplinks.extend(t)
                bottomlinks.extend(b)

    __use_cached__[key] = toplinks, bottomlinks
    return toplinks, bottomlinks
    
class HtmlMerge(object):
    def __init__(self, text, links):
        self.text = text
        self.links = links
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
        result = self.assemble(self._clean_collection([]))
        #cal links first, if no toplinks or bottomlinks be found, then
        #do nothing, otherwise find the head, and calculate the position
        #of toplinks and bottomlinks
        if result['toplinks'] or result['bottomlinks'] or result['headlinks']:
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
                        raise TemplateDefineError("Template <!-- bottomlinks --> shouldn't be defined before <!-- toplinks -->")
                    return self.text[:top_start] + top + self.text[top_start:bottom_start] + bottom + self.text[bottom_start:]
                elif top:
                    return self.text[:top_start] + top + self.text[top_start:]
                elif bottom:
                    return self.text[:bottom_start] + bottom + self.text[bottom_start:]

        return self.text
    
    def _clean_collection(self, existlinks):
        from uliweb.utils.sorteddict import SortedDict

        r = {'toplinks':SortedDict(), 'bottomlinks':SortedDict(), 'headlinks':SortedDict()}
        #process links, link could be (order, link) or link
        for _type in ['toplinks', 'bottomlinks', 'headlinks']:
            t = self.links.get(_type, [])
            for link in t:
                #link will also be template string
                if '{{' in link and '}}' in link:
                    #link = template(link, self.env)
                    raise TemplateDefineError("Can't support tag {{}} in links")
                    
                #process static combine
                if isinstance(link, dict):
                    link_key = link.get('value')
                    link_value = link.copy()
                    link_value.pop('value')
                else:
                    link_key = link
                    link_value = {}
                new_link = __static_mapping__.get(link_key, link_key)
                if new_link.endswith('.js') or new_link.endswith('.css'):
                    _link = functions.url_for_static(new_link)
                else:
                    _link = new_link
                if not new_link in r[_type] and not _link in existlinks:
                    link_value['link'] = _link
                    r[_type][new_link] = link_value
                    existlinks.append(_link)
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
        from uliweb.core.html import to_attrs

        toplinks = ['']
        bottomlinks = ['']
        for _type, result in [('toplinks', toplinks), ('bottomlinks', bottomlinks)]:
            for link, kw in links[_type].items():
                _link = kw.pop('link', link)
                if kw:
                    attrs = to_attrs(kw)
                else:
                    attrs = ''
                if link.endswith('.js'):
                    result.append('<script type="text/javascript" src="%s"%s></script>' % (_link, attrs))
                elif link.endswith('.css'):
                    result.append('<link rel="stylesheet" type="text/css" href="%s"%s/>' % (_link, attrs))
                else:
                    result.append(link)

        return {'toplinks':'\n'.join(toplinks), 'bottomlinks':'\n'.join(bottomlinks)}

