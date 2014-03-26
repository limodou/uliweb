from uliweb import functions, expose, is_in_web

@expose('/test_web')
def test_web():
    return is_in_web()

@expose('/test_add')
def test_add():
    Blog = functions.get_model('blog')
    b = Blog(title='test_add', content='test_add')
    b.save()
    return 'ok'

@expose('/test_rollback')
def test_rollback():
    Blog = functions.get_model('blog')
    b = Blog(title='test_add', content='test_add')
    b.save()
    raise Exception('fail')
    return 'ok'

@expose('/test_manual_commit')
def test_manual_commit():
    from uliweb.orm import Begin, Commit, Rollback
    
    Begin()
    Blog = functions.get_model('blog')
    b = Blog(title='test_add', content='test_add')
    b.save()
    Commit()
    return 'ok'

@expose('/test_manual_rollback')
def test_manual_rollback():
    from uliweb.orm import Begin, Commit, Rollback
    
    Begin()
    Blog = functions.get_model('blog')
    b = Blog(title='test_add', content='test_add')
    b.save()
    Rollback()
    return 'ok'
