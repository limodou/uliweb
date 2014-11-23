from uliweb.orm import *
from Test.models import User

class User(User):
    age = Field(int)

class User1(User):
    __replace__ = True
    age = Field(int)