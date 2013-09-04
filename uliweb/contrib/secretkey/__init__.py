from uliweb import settings, functions
from uliweb.utils.common import import_attr, application_path
from hashlib import md5

def get_cipher(key=None, keyfile=None):
    """
    Get cipher object, and then you can invoke:
        des = get_cipher()
        d = des.encrpy('Hello')
        print des.descrpy(d)
    """
    des_func = import_attr(settings.SECRETKEY.CIPHER_CLS)
    kwargs = settings.SECRETKEY.CIPHER_ARGS
    
    if not key:
        key = functions.get_cipher_key(keyfile)
    cipher = des_func(key, **kwargs)
    return cipher

def encrypt(v, key=None, keyfile=None):
    """
    Encrypt an string
    """
    cipher = functions.get_cipher(key, keyfile)
    return cipher.encrypt(v)

def decrypt(v, key=None, keyfile=None):
    """
    Encrypt an string
    """
    cipher = functions.get_cipher(key, keyfile)
    return cipher.decrypt(v)

def get_key(keyfile=None):
    """
    Read the key content from secret_file
    """
    keyfile = keyfile or application_path(settings.SECRETKEY.SECRET_FILE)
    with file(keyfile, 'rb') as f:
        return f.read()
    
def get_cipher_key(keyfile=None):
    """
    Create key which will be used in des, because des need 8bytes chars
    """
    _key = get_key(keyfile)
    _k = md5(_key).hexdigest()
    key = xor(_k[:8], _k[8:16], _k[16:24], _k[24:])
    return key
    
def xor(*args):
    arg1 = args[0]
    for arg in args[1:]:
        s = []
        for i, ch in enumerate(arg):
            s.append(chr(ord(arg1[i]) ^ ord(ch)))
        arg1 = ''.join(s)
    return arg1
