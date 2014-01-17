def startup_installed(sender):
    from uliweb.core import template
    from tags import LinkNode, UseNode
    
    if sender.settings.TEMPLATE.USE_TEMPLATE_TEMP_DIR:
        template.use_tempdir(sender.settings.TEMPLATE.TEMPLATE_TEMP_DIR)
        
    template.DEBUG = sender.settings.GLOBAL.get('DEBUG_TEMPLATE', False)
    template.register_node('link', LinkNode)
    template.register_node('use', UseNode)
    
    template.BEGIN_TAG = sender.settings.TEMPLATE.BEGIN_TAG
    template.END_TAG = sender.settings.TEMPLATE.END_TAG

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