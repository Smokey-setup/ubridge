import ctypes
import os
import sys

if sys.platform == "darwin":
    _library_name = "libubridge.dylib"
elif sys.platform == "win32":
    _library_name = "ubridge.dll"
else:
    _library_name = "libubridge.so"

_library_path = os.path.join(os.path.dirname(__file__), _library_name)

lib = ctypes.CDLL(_library_path)

lib.ub_create.argtypes = [ctypes.c_uint8]
lib.ub_create.restype = ctypes.c_void_p

lib.ub_int.argtypes = [ctypes.c_void_p, ctypes.c_int64]
lib.ub_int.restype = None

lib.ub_float.argtypes = [ctypes.c_void_p, ctypes.c_double]
lib.ub_float.restype = None

lib.ub_str.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
lib.ub_str.restype = None

lib.ub_array.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
lib.ub_array.restype = None

lib.ub_object.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_void_p]
lib.ub_object.restype = None

lib.ub_process.argtypes = [ctypes.c_void_p]
lib.ub_process.restype = ctypes.c_void_p

lib.ub_free.argtypes = [ctypes.c_void_p]
lib.ub_free.restype = None

lib.ub_string_free.argtypes = [ctypes.c_void_p]
lib.ub_string_free.restype = None
