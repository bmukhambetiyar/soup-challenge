import getpass
import locale
import os
import platform
import shutil
import site
import sys
import tempfile

sp = site.getsitepackages()[0]
print("python", platform.python_version())
print("os", sys.platform, platform.release())
print("arch", platform.machine())
print("user", getpass.getuser())
print("site-packages", sp)
print("site-packages writable", os.access(sp, os.W_OK))
print("tempdir", tempfile.gettempdir())
print("locale encoding", locale.getpreferredencoding(False))
print("stdout encoding", sys.stdout.encoding)
print("executable", sys.executable)
print("space in path", " " in sys.executable)
for tool in ("git", "curl", "gcc", "pip"):
    print("tool", tool, shutil.which(tool))
for var in ("HOME", "USER", "USERPROFILE", "LANG", "CI", "PYTHONUTF8"):
    print("env", var, os.environ.get(var))
