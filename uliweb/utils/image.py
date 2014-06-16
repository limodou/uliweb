import os

QUALITY = 95

def fix_filename(filename, suffix=''):
    """
    e.g.
        fix_filename('icon.png', '_40x40')
        
        return
    
            icon_40x40.png
    """
    if suffix:
        f, ext = os.path.splitext(filename)
        return f+suffix+ext
    else:
        return filename

def resize_image(fobj, size=(50, 50), quality=None):
    from PIL import Image
    from StringIO import StringIO
    
    image = Image.open(fobj)
    if image.mode not in ('L', 'RGB'):
        image = image.convert('RGB')
    image = image.resize(size, Image.ANTIALIAS)
    o = StringIO()
    image.save(o, "JPEG", quality=quality or QUALITY)
    o.seek(0)
    return o

def thumbnail_image(realfile, filename, size=(200, 75), suffix=True, quality=None):
    """
    :param: real input filename (string)
    :filename: relative input filename (string)
    :param: suffix if True, then add '.thumbnail' to the end of filename
    
    return value should be a tuple, (saved_real_filename, saved_filename)
    """
    from PIL import Image

    im = Image.open(realfile)
    file, ext = os.path.splitext(realfile)
    if im.size[0]<=size[0] and im.size[1]<=size[1]:
        #the image size is smaller than thumbnail size, so we don't need to 
        #thumbnail the image
        return filename, filename
    im.thumbnail(size, Image.ANTIALIAS)
    format = ext[1:].upper()
    if format == 'JPG':
        format = 'JPEG'
    if suffix:
        ofile = file + ".thumbnail" + ext
    else:
        ofile = realfile
    im.save(ofile, format, quality=quality or QUALITY)
    file1, ext1 = os.path.splitext(filename)
    if suffix:
        ofile1 = file1 + ".thumbnail" + ext
    else:
        ofile1 = filename
    return ofile, ofile1

def resize_image_string(buf, size=(50, 50)):
    from StringIO import StringIO
    f = StringIO(buf)
    return resize_image(f, size).getvalue()
    
def image_size(filename):
    from PIL import Image

    image = Image.open(filename)
    return image.size

def test_image(filename, strong=False):
    """
    If strong is true, it'll really open the file, but with strong is false,
    it'll only test the file suffix
    """
    if strong:
        from PIL import Image
        if not os.path.exists(filename):
            return False
        try:
            image = Image.open(filename)
            return True
        except:
            return False
    else:
        ext = os.path.splitext(filename)[1]
        if ext.lower() in ['.jpg', '.bmp', '.png', '.ico', 'jpeg', 'gif']:
            return True
    
def crop_resize(fobj, outfile, x, y, w, h, size=(50, 50), quality=None):
    from PIL import Image

    image = Image.open(fobj)
    if image.mode not in ('L', 'RGB'):
        image = image.convert('RGB')
    r = image.crop((x, y, x+w, y+h))
    if size:
        rm = r.resize(size, Image.ANTIALIAS)
    else:
        rm = r
    rm.save(outfile, "JPEG", quality=quality or QUALITY)
    