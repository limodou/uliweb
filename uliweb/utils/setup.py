from setuptools import setup
from setuptools.command import build_py as b
import os,sys
import glob

#remove build and dist directory
import shutil
#if os.path.exists('build'):
#    shutil.rmtree('build')
#if os.path.exists('dist'):
#    shutil.rmtree('dist')

def copy_dir(self, package, src, dst):
    self.mkpath(dst)
    for r in os.listdir(src):
        if r in ['.svn', '_svn']:
            continue
        fpath = os.path.join(src, r)
        if os.path.isdir(fpath):
            copy_dir(self, package + '.' + r, fpath, os.path.join(dst, r))
        else:
            ext = os.path.splitext(fpath)[1]
            if ext in ['.pyc', '.pyo', '.bak', '.tmp']:
                continue
            target = os.path.join(dst, r)
            self.copy_file(fpath, target)

def find_dir(self, package, src):
    for r in os.listdir(src):
        if r in ['.svn', '_svn']:
            continue
        fpath = os.path.join(src, r)
        if os.path.isdir(fpath):
            for f in find_dir(self, package + '.' + r, fpath):
                yield f
        else:
            ext = os.path.splitext(fpath)[1]
            if ext in ['.pyc', '.pyo', '.bak', '.tmp']:
                continue
            yield fpath

def build_package_data(self):
    for package in self.packages or ():
        src_dir = self.get_package_dir(package)
        build_dir = os.path.join(*([self.build_lib] + package.split('.')))
        copy_dir(self, package, src_dir, build_dir)
setattr(b.build_py, 'build_package_data', build_package_data)

def get_source_files(self):
    filenames = []
    for package in self.packages or ():
        src_dir = self.get_package_dir(package)
        filenames.extend(list(find_dir(self, package, src_dir)))
    return filenames
setattr(b.build_py, 'get_source_files', get_source_files)

from setuptools.command.develop import develop
from distutils import sysconfig

unlink = os.unlink

def rm(obj):
    import shutil
    if os.path.exists(obj):
        try:
            
            if os.path.isdir(obj):
                if os.path.islink(obj):
                    unlink(obj)
                else:
                    shutil.rmtree(obj)
            else:
                if os.path.islink(obj):
                    unlink(obj)
                else:
                    os.remove(obj)
        except:
            import traceback
            traceback.print_exc()
            raise

__CSL = None
def symlink(source, link_name):
    '''symlink(source, link_name)
       Creates a symbolic link pointing to source named link_name
    
    copys from http://stackoverflow.com/questions/1447575/symlinks-on-windows/7924557
    '''
    global __CSL
    if __CSL is None:
        import ctypes
        csl = ctypes.windll.kernel32.CreateSymbolicLinkW
        csl.argtypes = (ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint32)
        csl.restype = ctypes.c_ubyte
        __CSL = csl
    flags = 0
    if source is not None and os.path.isdir(source):
        flags = 1
    if __CSL(link_name, source, flags) == 0:
        raise ctypes.WinError()

def pre_run(func):
    def _f(self):
        global unlink
        
        if self.distribution.package_dir and sys.platform == 'win32':
            try:
                import ntfslink
            except:
                print 'You need to install ntfslink package first in windows platform.'
                print 'You can find it at https://github.com/juntalis/ntfslink-python'
                sys.exit(1)
            if not hasattr(os, 'symlink'):
                os.symlink = symlink
                os.path.islink = ntfslink.symlink.check
                unlink = ntfslink.symlink.unlink
        func(self)
    return _f          
develop.run = pre_run(develop.run)

def post_install_for_development(func):
    def _f(self):
        func(self)
        packages = self.distribution.packages
        package_dir = self.distribution.package_dir
        libpath = sysconfig.get_python_lib()
        
        if not package_dir: return
    
        for p in sorted(packages):
            #if the package is something like 'x.y.z'
            #then create site-packages/x/y
            #then create symlink to z to src directory
            ps = p.split('.')
            if len(ps)>1:
                path = libpath
                for x in ps[:-1]:
                    path = os.path.join(path, x)
                    if not os.path.exists(path):
                        os.makedirs(path)
                    inifile = os.path.join(path, '__init__.py')
                    if not os.path.exists(inifile):
                        with open(inifile, 'w') as f:
                            f.write('\n')
                    
            pkg = os.path.join(libpath, *ps)
            d = package_dir.get(p, None)
            if d is None:
                print "Error: the package %s directory can't be found in package_dir, please config it first" % p
                sys.exit(1)
                
            src = os.path.abspath(os.path.join(os.getcwd(), d))
            print 'Linking ', src, 'to', pkg
            rm(pkg)
            os.symlink(src, pkg)
            
    return _f
develop.install_for_development = post_install_for_development(develop.install_for_development)

def post_uninstall_link(func):
    def _f(self):
        func(self)
        packages = self.distribution.packages
        package_dir = self.distribution.package_dir
        
        if not package_dir: return
    
        libpath = sysconfig.get_python_lib()
        for p in sorted(packages, reverse=True):
            print 'Unlink... %s' % p
            pkg = os.path.join(libpath, p.replace('.', '/'))
            rm(pkg)
    return _f
develop.uninstall_link = post_uninstall_link(develop.uninstall_link)
