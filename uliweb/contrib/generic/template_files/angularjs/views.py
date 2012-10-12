from uliweb import expose, functions, settings

@expose('{{=url}}')
class {{=classname}}(object):
    def __begin__(self):
        #return functions.require_login()
        #
        pass
        
    def __init__(self):
        self.model = functions.get_model('{{=tablename}}')
        
    def _get_view(self):
        """
        Return a ListView object
        """
        #################################################################
        # you may change `pageno` to other variable means page no
        #################################################################
        page = int(request.values.get('pageno', 1)) - 1
        
        #################################################################
        # you may set `rows` to settings default value, just like
        # rows = request.values.get('rows', settings.PARA.get('rows', 10))
        #################################################################
        rows = request.values.get('rows', 10)
        
        #################################################################
        #filter condition
        #################################################################
        condition = None
        
        #################################################################
        #field convert map
        #################################################################
        fields_convert_map = {}
        
        view = functions.ListView(self.model, 
            pageno=page, 
            rows_per_page=rows,
            pagination=True,
            condition=condition,
            fields_convert_map=fields_convert_map,
        )
        return view
        
    def _get_fields(self):
        """
        Return list fields info, and it'll be used in angularjs template
        """
        view = functions.ListView(self.model)
        return view.table_info()['fields_list']
        
    @expose('')
    def index(self):
        return {'fields':self._get_fields()}
    
    def query(self):
        view = self._get_view()
        return json(view.json())
        
    def add(self):
        def pre_save(data):
            pass
            
        def post_created_form(fcls, model):
            pass
            
        def post_save(obj, data):
            pass
    
        def success_data(obj, data):
            d = obj.to_dict()
            return d
        
        view = functions.AddView(self.model,
#            pre_save=pre_save,
#            post_save=post_save,
#            post_created_form=post_created_form,
#            template_data={},
            success_data=True,
            )
        response.template = 'GenericAjaxView/add.html'
        return view.run(json_result=True)
        
    def view(self, id):
        """
        Show the detail of object. Template will receive an `object` variable 
        """
        obj = self.model.get_or_notfound(int(id))
        fields_convert_map = {}
        view = functions.DetailView(self.model, 
            obj=obj,
#            fields_convert_map=fields_convert_map,
        )
        return view.run()
        
    def edit(self, id):
        def success_data(obj, data):
            d = obj.to_dict()
            return d
           
        def post_created_form(fcls, model, obj):
            pass
        
        obj = self.model.get_or_notfound(int(id))
        view = functions.EditView(self.model, 
            obj=obj, 
#            template_data={'class_id':self.class_id},
#            post_created_form=post_created_form,
            success_data=True,
            )
        response.template = 'GenericAjaxView/edit.html'
        return view.run(json_result=True)
        
    def delete(self, id):
        def pre_delete(obj):
            pass
            
        obj = self.model.get_or_notfound(int(id))
        view = functions.DeleteView(self.model, 
            obj=obj,
#            pre_delete=pre_delete,
        )
        return view.run(json_result=True)
    