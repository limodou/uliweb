#coding=utf-8
import uliweb.form as form
from uliweb.form import *
from uliweb.form.layout import QueryLayout
from uliweb.i18n import gettext_lazy as _

class QueryForm(form.Form):
    form_buttons = form.Button(value=_('Search'), _class="btn btn-primary", type='submit')
    layout_class = QueryLayout
    form_method = 'GET'
    
    def post_html(self):
        buf = """
<script>
$(document).ready(function(){
    $('#query_div').hide();
    $('#more_query').click(function(){
        $('#query_div').toggle();
    });
});
</script>
    """
        return buf
