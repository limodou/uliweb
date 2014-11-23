from uliweb.orm import *

class User(Model):
    username = Field(str)

    def print_name(self):
        return 'print_name'