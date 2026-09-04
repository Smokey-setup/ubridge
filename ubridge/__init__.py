import ctypes
import math
import os
import sys
from typing import Any, Optional


__version__ = "2.0.0"


# ==========================
# NATIVE LIBRARY RESOLUTION
# ==========================

if sys.platform == "darwin":
    _library_name = "libubridge.dylib"
elif sys.platform == "win32":
    _library_name = "ubridge.dll"
else:
    _library_name = "libubridge.so"


_library_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    _library_name,
)


if not os.path.isfile(_library_path):
    raise FileNotFoundError(
        "[@set-up/ubridge] FATAL: Native library not found at "
        f"{_library_path}. "
        f"Platform={sys.platform}, architecture={os.uname().machine if hasattr(os, 'uname') else 'unknown'}."
    )


# ==========
# NATIVE ABI
# ==========

lib = ctypes.CDLL(_library_path)


lib.ub_create.argtypes = [
    ctypes.c_uint8,
]
lib.ub_create.restype = ctypes.c_void_p


lib.ub_int.argtypes = [
    ctypes.c_void_p,
    ctypes.c_int64,
]
lib.ub_int.restype = None


lib.ub_float.argtypes = [
    ctypes.c_void_p,
    ctypes.c_double,
]
lib.ub_float.restype = None


lib.ub_str.argtypes = [
    ctypes.c_void_p,
    ctypes.c_char_p,
]
lib.ub_str.restype = None


lib.ub_scientific.argtypes = [
    ctypes.c_void_p,
    ctypes.c_int64,
    ctypes.c_int32,
]
lib.ub_scientific.restype = None


lib.ub_array.argtypes = [
    ctypes.c_void_p,
    ctypes.c_void_p,
]
lib.ub_array.restype = None


lib.ub_object.argtypes = [
    ctypes.c_void_p,
    ctypes.c_char_p,
    ctypes.c_void_p,
]
lib.ub_object.restype = None


# ub_process returns an allocated char*.
# Ownership belongs to the caller and MUST be released
# with ub_string_free().
lib.ub_process.argtypes = [
    ctypes.c_void_p,
]
lib.ub_process.restype = ctypes.c_void_p


lib.ub_free.argtypes = [
    ctypes.c_void_p,
]
lib.ub_free.restype = None


lib.ub_string_free.argtypes = [
    ctypes.c_void_p,
]
lib.ub_string_free.restype = None


# ==============
# TYPE CONSTANTS
# ==============

class Types:
    NULL = 0
    INT = 1
    FLOAT = 2
    STRING = 3
    BOOL = 4
    ARRAY = 5
    OBJECT = 6


# ==============
# ABI VALIDATION
# ==============

_VALID_TYPES = frozenset(
    {
        Types.NULL,
        Types.INT,
        Types.FLOAT,
        Types.STRING,
        Types.BOOL,
        Types.ARRAY,
        Types.OBJECT,
    }
)


_INT64_MIN = -(1 << 63)
_INT64_MAX = (1 << 63) - 1

_INT32_MIN = -(1 << 31)
_INT32_MAX = (1 << 31) - 1


# =======
# UBRIDGE
# =======

class UBridge:
    """
    High-level Python wrapper around the native UBridge C ABI.

    Native ownership is graph-based.

    Only a root UBridge object owns the native graph. Child
    wrappers never independently free native memory.
    """

    def __init__(
        self,
        node_type: int,
        _owner: Optional["UBridge"] = None,
    ):
        if node_type not in _VALID_TYPES:
            raise ValueError(
                f"[@set-up/ubridge] Invalid UNode type: {node_type}"
            )

        ptr = lib.ub_create(node_type)

        if not ptr:
            raise MemoryError(
                "[@set-up/ubridge] Native ub_create() failed."
            )

        self.ptr = ctypes.c_void_p(ptr)
        self._type = node_type
        self._freed = False

        if _owner is None:
            self._owner = self
            self._children = set()
        else:
            self._owner = _owner
            self._children = set()

    # ==============
    # INTERNAL STATE
    # ==============

    @property
    def type(self) -> int:
        return self._type

    @property
    def _root(self) -> "UBridge":
        return self._owner

    def _check_alive(self):
        if (
            self._freed
            or not self.ptr
            or not self.ptr.value
        ):
            raise RuntimeError(
                "[@set-up/ubridge] Attempted to operate on "
                "a freed native UNode."
            )

    def _retain_child(self, child: "UBridge"):
        if not isinstance(child, UBridge):
            raise TypeError(
                "[@set-up/ubridge] Child must be a UBridge node."
            )

        child._check_alive()

        parent_root = self._root
        child_root = child._root

        if child_root is parent_root:
            self._children.add(child)
            return

        # A standalone native subtree may be transferred into
        # another graph exactly once.
        if child_root is not child:
            raise RuntimeError(
                "[@set-up/ubridge] Cannot attach a node that "
                "already belongs to another native graph."
            )

        old_root = child_root

        self._transfer_root(
            old_root,
            parent_root,
        )

        self._children.add(child)

    def _transfer_root(
        self,
        old_root: "UBridge",
        new_root: "UBridge",
    ):
        """
        Transfer ownership of a standalone native subtree.

        The native pointers themselves do not move. Only the
        Python ownership boundary changes.
        """

        stack = [old_root]
        visited = set()

        while stack:
            node = stack.pop()

            marker = id(node)

            if marker in visited:
                continue

            visited.add(marker)

            node._owner = new_root

            for child in node._children:
                stack.append(child)

    # =======
    # INTEGER
    # =======

    def set_int(self, val: int):
        self._check_alive()

        if isinstance(val, bool) or not isinstance(val, int):
            raise TypeError(
                "[@set-up/ubridge] set_int() requires an int."
            )

        if val < _INT64_MIN or val > _INT64_MAX:
            raise OverflowError(
                "[@set-up/ubridge] Integer exceeds int64 range."
            )

        lib.ub_int(
            self.ptr,
            ctypes.c_int64(val),
        )

        return self

    # ======
    # FLOAT
    # ======

    def set_float(self, val: float):
        self._check_alive()

        if isinstance(val, bool):
            raise TypeError(
                "[@set-up/ubridge] set_float() requires a number."
            )

        try:
            number = float(val)
        except (TypeError, ValueError) as exc:
            raise TypeError(
                "[@set-up/ubridge] Invalid floating-point value."
            ) from exc

        if not math.isfinite(number):
            raise ValueError(
                "[@set-up/ubridge] Float must be finite."
            )

        lib.ub_float(
            self.ptr,
            ctypes.c_double(number),
        )

        return self

    # =======
    # STRING
    # =======

    def set_str(self, val: str):
        self._check_alive()

        if not isinstance(val, str):
            val = str(val)

        if "\x00" in val:
            raise ValueError(
                "[@set-up/ubridge] Strings containing NUL "
                "characters cannot cross the C string ABI."
            )

        encoded = val.encode(
            "utf-8",
            "strict",
        )

        lib.ub_str(
            self.ptr,
            encoded,
        )

        return self

    # =======
    # BOOLEAN
    # =======

    def set_bool(self, val: bool):
        self._check_alive()

        lib.ub_int(
            self.ptr,
            ctypes.c_int64(
                1 if bool(val) else 0
            ),
        )

        return self

    # ==========
    # SCIENTIFIC
    # ==========

    def set_scientific(
        self,
        coefficient: int,
        exponent: int,
    ):
        self._check_alive()

        if (
            isinstance(coefficient, bool)
            or not isinstance(coefficient, int)
        ):
            raise TypeError(
                "[@set-up/ubridge] Scientific coefficient "
                "must be an int."
            )

        if (
            coefficient < _INT64_MIN
            or coefficient > _INT64_MAX
        ):
            raise OverflowError(
                "[@set-up/ubridge] Scientific coefficient "
                "exceeds int64 range."
            )

        if (
            isinstance(exponent, bool)
            or not isinstance(exponent, int)
        ):
            raise TypeError(
                "[@set-up/ubridge] Scientific exponent "
                "must be an int."
            )

        if (
            exponent < _INT32_MIN
            or exponent > _INT32_MAX
        ):
            raise OverflowError(
                "[@set-up/ubridge] Scientific exponent "
                "exceeds int32 range."
            )

        lib.ub_scientific(
            self.ptr,
            ctypes.c_int64(coefficient),
            ctypes.c_int32(exponent),
        )

        return self

    # =====
    # ARRAY
    # =====

    def push(self, item_node: "UBridge"):
        self._check_alive()

        if self._type != Types.ARRAY:
            raise TypeError(
                "[@set-up/ubridge] push() requires "
                "an ARRAY node."
            )

        if not isinstance(item_node, UBridge):
            raise TypeError(
                "[@set-up/ubridge] Array item must "
                "be a UBridge node."
            )

        item_node._check_alive()

        self._retain_child(item_node)

        lib.ub_array(
            self.ptr,
            item_node.ptr,
        )

        return self

    # =====
    # OBJECT
    # =====

    def set_key(
        self,
        key: str,
        val_node: "UBridge",
    ):
        self._check_alive()

        if self._type != Types.OBJECT:
            raise TypeError(
                "[@set-up/ubridge] set_key() requires "
                "an OBJECT node."
            )

        if not isinstance(val_node, UBridge):
            raise TypeError(
                "[@set-up/ubridge] Object value must "
                "be a UBridge node."
            )

        val_node._check_alive()

        key = str(key)

        if "\x00" in key:
            raise ValueError(
                "[@set-up/ubridge] Object keys cannot "
                "contain NUL characters."
            )

        encoded_key = key.encode(
            "utf-8",
            "strict",
        )

        self._retain_child(val_node)

        lib.ub_object(
            self.ptr,
            encoded_key,
            val_node.ptr,
        )

        return self

    # =============
    # SERIALIZATION
    # =============

    def process(self) -> Optional[str]:
        self._check_alive()

        res_ptr = lib.ub_process(
            self.ptr
        )

        if not res_ptr:
            return None

        try:
            raw = ctypes.cast(
                res_ptr,
                ctypes.c_char_p,
            ).value

            if raw is None:
                return None

            return raw.decode(
                "utf-8",
                "strict",
            )

        finally:
            lib.ub_string_free(
                res_ptr
            )

    # =====
    # FREE
    # =====

    def free(self):
        """
        Free the entire native graph exactly once.

        Calling free() on a child delegates to its root.
        """

        root = self._root

        if root is not self:
            root.free()
            return

        if self._freed:
            return

        root_ptr = root.ptr

        try:
            if root_ptr and root_ptr.value:
                lib.ub_free(root_ptr)
        finally:
            self._invalidate_graph()

    def _invalidate_graph(self):
        stack = [self]
        visited = set()

        while stack:
            node = stack.pop()

            marker = id(node)

            if marker in visited:
                continue

            visited.add(marker)

            children = tuple(
                node._children
            )

            node._freed = True
            node.ptr = None

            for child in children:
                stack.append(child)

            node._children.clear()

    # ===============
    # CONTEXT MANAGER
    # ===============

    def __enter__(self):
        self._check_alive()
        return self

    def __exit__(
        self,
        exc_type,
        exc_val,
        exc_tb,
    ):
        self.free()

    # =========
    # DESTRUCTOR
    # =========

    def __del__(self):
        """
        Only the root graph owner is allowed to release
        native memory.

        Destructors are intentionally defensive because Python
        interpreter shutdown can partially tear down modules.
        """

        try:
            if (
                getattr(self, "_owner", self) is self
                and not getattr(self, "_freed", True)
            ):
                self.free()
        except Exception:
            pass

    # ======================
    # PYTHON → NATIVE GRAPH
    # ======================

    @staticmethod
    def from_py(
        data: Any,
        seen=None,
    ):
        """
        Convert Python primitives, lists, tuples and dictionaries
        into a native UBridge graph.

        Cycles and shared Python references are preserved.
        """

        if seen is None:
            seen = {}

        root = None

        try:
            root = UBridge._from_py(
                data,
                seen,
                depth=0,
                root=None,
            )

            return root

        except Exception:
            if root is not None:
                try:
                    root.free()
                except Exception:
                    pass

            raise

    @staticmethod
    def _from_py(
        data: Any,
        seen: dict,
        depth: int,
        root: Optional["UBridge"],
    ):
        if depth > 1024:
            raise RecursionError(
                "[@set-up/ubridge] Python graph exceeds "
                "the maximum serialization depth of 1024."
            )

        # -----
        # NONE
        # -----

        if data is None:
            return UBridge(
                Types.NULL,
                _owner=root,
            )

        # --------
        # BOOLEAN
        # --------

        if isinstance(data, bool):
            return UBridge(
                Types.BOOL,
                _owner=root,
            ).set_bool(data)

        # -------
        # INTEGER
        # -------

        if isinstance(data, int):
            return UBridge(
                Types.INT,
                _owner=root,
            ).set_int(data)

        # -----
        # FLOAT
        # -----

        if isinstance(data, float):
            if not math.isfinite(data):
                raise ValueError(
                    "[@set-up/ubridge] Non-finite Python "
                    "float cannot be represented."
                )

            return UBridge(
                Types.FLOAT,
                _owner=root,
            ).set_float(data)

        # -------
        # STRING
        # -------

        if isinstance(data, str):
            return UBridge(
                Types.STRING,
                _owner=root,
            ).set_str(data)

        # -----------
        # LIST / TUPLE
        # -----------

        if isinstance(data, (list, tuple)):

            obj_id = id(data)

            if obj_id in seen:
                return seen[obj_id]

            arr_node = UBridge(
                Types.ARRAY,
                _owner=root,
            )

            if root is None:
                root = arr_node

            seen[obj_id] = arr_node

            for item in data:
                child = UBridge._from_py(
                    item,
                    seen,
                    depth + 1,
                    root,
                )

                arr_node.push(child)

            return arr_node

        # -----------
        # DICTIONARY
        # -----------

        if isinstance(data, dict):

            obj_id = id(data)

            if obj_id in seen:
                return seen[obj_id]

            obj_node = UBridge(
                Types.OBJECT,
                _owner=root,
            )

            if root is None:
                root = obj_node

            seen[obj_id] = obj_node

            for key, value in data.items():

                child = UBridge._from_py(
                    value,
                    seen,
                    depth + 1,
                    root,
                )

                obj_node.set_key(
                    str(key),
                    child,
                )

            return obj_node

        # ----------------
        # UNSUPPORTED TYPE
        # ----------------

        raise TypeError(
            "[@set-up/ubridge] Unsupported Python type: "
            f"{type(data).__name__}"
        )


__all__ = [
    "UBridge",
    "Types",
    "lib",
    "__version__",
]
