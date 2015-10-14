#coding=utf-8
import uliweb.form as form
from uliweb.form import *
from uliweb.form.layout import QueryLayout
from uliweb.i18n import gettext_lazy as _

class NewStyleQueryLayout(QueryLayout):
    def get_more_button(self):
        return ''

    def post_layout(self):
        return '<div class="more_query_bar"><div><a href="#" id="more_query" title="%s">%s</a></div></div>' % (_('more'), _('more'))

class QueryForm(form.Form):
    form_buttons = form.Button(value=_('Search'), _class="btn btn-primary", type='submit')
    layout_class = NewStyleQueryLayout
    form_method = 'GET'

    def pre_html(self):
        return '''<link rel="stylesheet" type="text/css" href="/static/uimultiselect/jquery.multiselect.css"/>
<script src='/static/uimultiselect/jquery.multiselect.min.js'></script>
<script src='/static/uimultiselect/jquery.multiselect.zh.js'></script>
'''

    def post_html(self):
        buf = """
<script>
$(document).ready(function(){
    $('#query_div').hide();
    $('#more_query').click(function(){
        $('#query_div').toggle();
        $('#more_query').toggleClass("foldup")
    });
});
</script>
    """
        return buf
