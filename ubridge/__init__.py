import ctypes
import os
import sys

__version__ = "1.1.0"

# 1. Fail-Safe Library Path Resolution
if sys.platform == "darwin":
    _library_name = "libubridge.dylib"
elif sys.platform == "win32":
    _library_name = "ubridge.dll"
else:
    _library_name = "libubridge.so"

_library_path = os.path.join(os.path.dirname(__file__), _library_name)

if not os.path.exists(_library_path):
    raise FileNotFoundError(f"[@set-up/ubridge] FATAL: Native library not found at {_library_path}.")

lib = ctypes.CDLL(_library_path)

# 2. Precise FFI Binding Signatures
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

# CRITICAL FIX: Return void_p so we can intercept the string pointer and free it safely
lib.ub_process.argtypes = [ctypes.c_void_p]
lib.ub_process.restype = ctypes.c_void_p

lib.ub_free.argtypes = [ctypes.c_void_p]
lib.ub_free.restype = None

lib.ub_string_free.argtypes = [ctypes.c_void_p]
lib.ub_string_free.restype = None


class Types:
    NULL = 0
    INT = 1
    FLOAT = 2
    STRING = 3
    BOOL = 4
    ARRAY = 5
    OBJECT = 6


class UBridge:
    """High-level Python wrapper for UBridge with automatic context management and builder patterns."""
    
    def __init__(self, node_type: int):
        self.ptr = lib.ub_create(node_type)
        if not self.ptr:
            raise MemoryError("[@set-up/ubridge] Failed to allocate native UNode pointer.")
        self._freed = False

    def set_int(self, val: int):
        self._check_alive()
        lib.ub_int(self.ptr, int(val))
        return self

    def set_float(self, val: float):
        self._check_alive()
        lib.ub_float(self.ptr, float(val))
        return self

    def set_str(self, val: str):
        self._check_alive()
        if val is not None:
            encoded = str(val).encode('utf-8')
            lib.ub_str(self.ptr, encoded)
        return self

    def set_bool(self, val: bool):
        self._check_alive()
        lib.ub_int(self.ptr, 1 if val else 0)
        return self

    def push(self, item_node):
        self._check_alive()
        lib.ub_array(self.ptr, item_node.ptr)
        return self

    def set_key(self, key: str, val_node):
        self._check_alive()
        encoded_key = str(key).encode('utf-8')
        lib.ub_object(self.ptr, encoded_key, val_node.ptr)
        return self

    def process(self) -> str:
        self._check_alive()
        res_ptr = lib.ub_process(self.ptr)
        if not res_ptr:
            return None
        
        # Safely extract the string and free the C allocation to prevent memory leaks
        c_str = ctypes.cast(res_ptr, ctypes.c_char_p).value
        result = c_str.decode('utf-8') if c_str else None
        lib.ub_string_free(res_ptr)
        return result

    def free(self):
        if not self._freed and self.ptr:
            lib.ub_free(self.ptr)
            self.ptr = None
            self._freed = True

    def _check_alive(self):
        if self._freed or not self.ptr:
            raise RuntimeError("[@set-up/ubridge] Segmentation Fault Prevented: Attempted to operate on a freed native node.")

    # Context Manager Support (`with UBridge(...) as node:`)
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.free()

    def __del__(self):
        try:
            self.free()
        except Exception:
            pass

    @staticmethod
    def from_py(data, seen=None):
        """Recursively translates ANY complex Python structure (lists, dicts, primitives) into a native C graph."""
        if seen is None:
            seen = {}

        if data is None:
            return UBridge(Types.NULL)
        if isinstance(data, bool):
            return UBridge(Types.BOOL).set_bool(data)
        if isinstance(data, int):
            return UBridge(Types.INT).set_int(data)
        if isinstance(data, float):
            return UBridge(Types.FLOAT).set_float(data)
        if isinstance(data, str):
            return UBridge(Types.STRING).set_str(data)

        # Cyclic reference detection using Python object IDs
        obj_id = id(data)
        if obj_id in seen:
            return seen[obj_id]

        if isinstance(data, (list, tuple)):
            arr_node = UBridge(Types.ARRAY)
            seen[obj_id] = arr_node
            for item in data:
                arr_node.push(UBridge.from_py(item, seen))
            return arr_node

        if isinstance(data, dict):
            obj_node = UBridge(Types.OBJECT)
            seen[obj_id] = obj_node
            for k, v in data.items():
                obj_node.set_key(str(k), UBridge.from_py(v, seen))
            return obj_node

        return UBridge(Types.NULL)
