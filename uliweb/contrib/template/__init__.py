def startup_installed(sender):
    from uliweb.core import template
    from tags import LinkNode, UseNode
    
    template.register_node('link', LinkNode)
    template.register_node('use', UseNode)

def init_static_combine():
    """
    Process static combine, create md5 key according each static filename
    """
    from uliweb import settings
    from hashlib import md5
    import os
    
    d = {}
    if settings.get_var('STATIC_COMBINE_CONFIG/enable', False):
        for k, v in settings.get('STATIC_COMBINE', {}).items():
            key = '_cmb_'+md5(''.join(v)).hexdigest()+os.path.splitext(v[0])[1]
            d[key] = v
        
    return d