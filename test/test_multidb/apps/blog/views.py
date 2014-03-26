from uliweb import functions, expose, is_in_web

@expose('/test_web')
def test_web():
    return is_in_web()