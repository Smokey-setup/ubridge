import ctypes
import math
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
RESULT_FILE = os.path.join(ROOT, "brutal_test_results.txt")

def library_path():
    if sys.platform == "darwin":
        return os.path.join(ROOT, "libubridge.dylib")
    if sys.platform == "win32":
        return os.path.join(ROOT, "ubridge.dll")
    return os.path.join(ROOT, "libubridge.so")

def load_library():
    lib = ctypes.CDLL(library_path())

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

    return lib

def process(lib, node):
    ptr = lib.ub_process(node)

    if not ptr:
        raise RuntimeError("ub_process returned NULL")

    try:
        return ctypes.string_at(ptr).decode("utf-8")
    finally:
        lib.ub_string_free(ptr)

def test_basic():
    lib = load_library()

    node = lib.ub_create(1)
    lib.ub_int(node, 123456789)

    result = process(lib, node)

    lib.ub_free(node)

    assert result.startswith("I:")
    assert "#SIG:" in result

    return result

def test_integer_boundaries():
    lib = load_library()

    values = [
        0,
        1,
        -1,
        127,
        -128,
        255,
        -255,
        2147483647,
        -2147483648,
        9223372036854775807,
        -9223372036854775807 - 1
    ]

    outputs = []

    for value in values:
        node = lib.ub_create(1)
        lib.ub_int(node, value)

        result = process(lib, node)

        lib.ub_free(node)

        assert "#SIG:" in result
        outputs.append(result)

    return outputs

def test_float_values():
    lib = load_library()

    values = [
        0.0,
        1.0,
        -1.0,
        0.25,
        -0.25,
        12.5,
        -12.5,
        123456.789,
        -123456.789
    ]

    outputs = []

    for value in values:
        node = lib.ub_create(2)
        lib.ub_float(node, value)

        result = process(lib, node)

        lib.ub_free(node)

        assert "#SIG:" in result
        outputs.append(result)

    return outputs

def test_extreme_float_values():
    lib = load_library()

    values = [
        1e-12,
        -1e-12,
        1e-9,
        -1e-9,
        999999.999999,
        -999999.999999,
        1e10,
        -1e10,
        1e15,
        -1e15,
        1e18,
        -1e18
    ]

    outputs = []

    for value in values:
        node = lib.ub_create(2)
        lib.ub_float(node, value)

        result = process(lib, node)

        lib.ub_free(node)

        assert "#SIG:" in result
        outputs.append(result)

    return outputs

def test_nan_and_infinity():
    lib = load_library()

    values = [
        float("nan"),
        float("inf"),
        float("-inf")
    ]

    outputs = []

    for value in values:
        node = lib.ub_create(2)

        lib.ub_float(node, value)

        result = process(lib, node)

        lib.ub_free(node)

        assert "#SIG:" in result
        outputs.append(result)

    return outputs

def test_base64_lengths():
    lib = load_library()

    outputs = []

    for length in range(64):
        data = bytes((i % 256 for i in range(length)))

        node = lib.ub_create(3)
        lib.ub_str(node, data)

        result = process(lib, node)

        lib.ub_free(node)

        assert result.startswith("P:")
        assert "#SIG:" in result

        outputs.append(result)

    return outputs

def test_string_edges():
    lib = load_library()

    values = [
        b"",
        b"A",
        b"AB",
        b"ABC",
        b"hello",
        b"hello world",
        b"0123456789",
        b"!@#$%^&*()_+-=[]{}|;:',.<>/?",
        b"\x00"
    ]

    outputs = []

    for value in values:
        node = lib.ub_create(3)
        lib.ub_str(node, value)

        result = process(lib, node)

        lib.ub_free(node)

        assert "#SIG:" in result
        outputs.append(result)

    return outputs

def test_utf8():
    lib = load_library()

    values = [
        "hello".encode(),
        "café".encode(),
        "日本語".encode(),
        "🚀🔥".encode(),
        "Привет".encode(),
        "مرحبا".encode()
    ]

    outputs = []

    for value in values:
        node = lib.ub_create(3)
        lib.ub_str(node, value)

        result = process(lib, node)

        lib.ub_free(node)

        assert "#SIG:" in result
        outputs.append(result)

    return outputs

def test_boolean():
    lib = load_library()

    outputs = []

    for value in [0, 1, 2, -1, 999999]:
        node = lib.ub_create(4)
        lib.ub_int(node, value)

        result = process(lib, node)

        lib.ub_free(node)

        assert result.startswith("B:")
        outputs.append(result)

    return outputs

def test_null():
    lib = load_library()

    node = lib.ub_create(0)

    result = process(lib, node)

    lib.ub_free(node)

    assert result.startswith("NIL;")

    return result

def test_empty_array():
    lib = load_library()

    arr = lib.ub_create(5)

    result = process(lib, arr)

    lib.ub_free(arr)

    assert result.startswith("A:0[")
    assert "#SIG:" in result

    return result

def test_empty_object():
    lib = load_library()

    obj = lib.ub_create(6)

    result = process(lib, obj)

    lib.ub_free(obj)

    assert result.startswith("O:0{")
    assert "#SIG:" in result

    return result

def test_array():
    lib = load_library()

    arr = lib.ub_create(5)

    for value in [1, 2, 3, 4, 5]:
        item = lib.ub_create(1)
        lib.ub_int(item, value)
        lib.ub_array(arr, item)

    result = process(lib, arr)

    lib.ub_free(arr)

    assert result.startswith("A:5[")

    return result

def test_large_array():
    lib = load_library()

    arr = lib.ub_create(5)

    for value in range(5000):
        item = lib.ub_create(1)
        lib.ub_int(item, value)
        lib.ub_array(arr, item)

    result = process(lib, arr)

    lib.ub_free(arr)

    assert result.startswith("A:5000[")
    assert "#SIG:" in result

    return f"serialized_length={len(result)}"

def test_object():
    lib = load_library()

    obj = lib.ub_create(6)

    entries = [
        (b"zeta", 3),
        (b"alpha", 1),
        (b"middle", 2)
    ]

    for key, value in entries:
        item = lib.ub_create(1)
        lib.ub_int(item, value)
        lib.ub_object(obj, key, item)

    result = process(lib, obj)

    lib.ub_free(obj)

    assert result.startswith("O:3{")
    assert "#SIG:" in result

    return result

def test_large_object():
    lib = load_library()

    obj = lib.ub_create(6)

    for value in range(1000):
        key = f"key_{value:05d}".encode()

        item = lib.ub_create(1)
        lib.ub_int(item, value)

        lib.ub_object(obj, key, item)

    result = process(lib, obj)

    lib.ub_free(obj)

    assert result.startswith("O:1000{")
    assert "#SIG:" in result

    return f"serialized_length={len(result)}"

def test_long_object_key():
    lib = load_library()

    obj = lib.ub_create(6)

    key = b"K" * 10000

    item = lib.ub_create(1)
    lib.ub_int(item, 42)

    lib.ub_object(obj, key, item)

    result = process(lib, obj)

    lib.ub_free(obj)

    assert "#SIG:" in result
    assert "K:10000:" in result

    return f"serialized_length={len(result)}"

def test_nested():
    lib = load_library()

    obj = lib.ub_create(6)
    arr = lib.ub_create(5)

    item1 = lib.ub_create(1)
    lib.ub_int(item1, 42)

    item2 = lib.ub_create(3)
    lib.ub_str(item2, b"nested")

    lib.ub_array(arr, item1)
    lib.ub_array(arr, item2)

    lib.ub_object(obj, b"data", arr)

    result = process(lib, obj)

    lib.ub_free(obj)

    assert "#SIG:" in result

    return result

def test_deep_nesting():
    lib = load_library()

    root = lib.ub_create(5)
    current = root

    for _ in range(100):
        child = lib.ub_create(5)
        lib.ub_array(current, child)
        current = child

    value = lib.ub_create(1)
    lib.ub_int(value, 123)

    lib.ub_array(current, value)

    result = process(lib, root)

    lib.ub_free(root)

    assert "#SIG:" in result

    return f"serialized_length={len(result)}"

def test_determinism():
    lib = load_library()

    obj = lib.ub_create(6)

    a = lib.ub_create(1)
    b = lib.ub_create(1)

    lib.ub_int(a, 100)
    lib.ub_int(b, 200)

    lib.ub_object(obj, b"z", a)
    lib.ub_object(obj, b"a", b)

    first = process(lib, obj)
    second = process(lib, obj)

    lib.ub_free(obj)

    assert first == second

    return first

def test_duplicate_object_keys():
    lib = load_library()

    obj = lib.ub_create(6)

    first = lib.ub_create(1)
    second = lib.ub_create(1)

    lib.ub_int(first, 100)
    lib.ub_int(second, 200)

    lib.ub_object(obj, b"duplicate", first)
    lib.ub_object(obj, b"duplicate", second)

    result = process(lib, obj)

    lib.ub_free(obj)

    assert result.startswith("O:2{")
    assert "#SIG:" in result

    return result

def test_cycle():
    lib = load_library()

    arr = lib.ub_create(5)

    lib.ub_array(arr, arr)

    result = process(lib, arr)

    lib.ub_free(arr)

    assert "LOOP:" in result

    return result

def test_large_string():
    lib = load_library()

    data = b"A" * 100000

    node = lib.ub_create(3)
    lib.ub_str(node, data)

    result = process(lib, node)

    lib.ub_free(node)

    assert result.startswith("P:")
    assert "#SIG:" in result

    return f"serialized_length={len(result)}"

def test_1mb_string():
    lib = load_library()

    data = b"B" * (1024 * 1024)

    node = lib.ub_create(3)
    lib.ub_str(node, data)

    result = process(lib, node)

    lib.ub_free(node)

    assert result.startswith("P:")
    assert "#SIG:" in result

    return f"serialized_length={len(result)}"

def test_repeated_serialization():
    lib = load_library()

    node = lib.ub_create(3)
    lib.ub_str(node, b"repeated serialization test")

    previous = None

    for _ in range(1000):
        result = process(lib, node)

        if previous is not None:
            assert result == previous

        previous = result

    lib.ub_free(node)

    return "1000 repeated serializations completed"

def test_repeated_create_free():
    lib = load_library()

    for i in range(10000):
        node = lib.ub_create(1)
        lib.ub_int(node, i)
        result = process(lib, node)
        lib.ub_free(node)

        assert "#SIG:" in result

    return "10000 create/process/free cycles completed"

def test_fuzz():
    lib = load_library()

    for length in range(500):
        data = bytes(
            ((i * 37 + length) % 256 for i in range(length % 128))
        )

        node = lib.ub_create(3)
        lib.ub_str(node, data)

        result = process(lib, node)

        lib.ub_free(node)

        assert "#SIG:" in result

    return "500 deterministic fuzz iterations completed"

def test_extended_fuzz():
    lib = load_library()

    for iteration in range(5000):
        length = (iteration * 7919) % 2048

        data = bytes(
            ((iteration * 31 + i * 17) % 256 for i in range(length))
        )

        node = lib.ub_create(3)
        lib.ub_str(node, data)

        result = process(lib, node)

        lib.ub_free(node)

        assert "#SIG:" in result

    return "5000 extended fuzz iterations completed"

def test_mixed_array():
    lib = load_library()

    arr = lib.ub_create(5)

    null_node = lib.ub_create(0)

    int_node = lib.ub_create(1)
    lib.ub_int(int_node, -999)

    float_node = lib.ub_create(2)
    lib.ub_float(float_node, -12.5)

    string_node = lib.ub_create(3)
    lib.ub_str(string_node, b"mixed")

    bool_node = lib.ub_create(4)
    lib.ub_int(bool_node, 1)

    nested_obj = lib.ub_create(6)
    nested_value = lib.ub_create(1)
    lib.ub_int(nested_value, 42)
    lib.ub_object(nested_obj, b"value", nested_value)

    lib.ub_array(arr, null_node)
    lib.ub_array(arr, int_node)
    lib.ub_array(arr, float_node)
    lib.ub_array(arr, string_node)
    lib.ub_array(arr, bool_node)
    lib.ub_array(arr, nested_obj)

    result = process(lib, arr)

    lib.ub_free(arr)

    assert "#SIG:" in result

    return result

TESTS = [
    ("basic", test_basic),
    ("integer_boundaries", test_integer_boundaries),
    ("float_values", test_float_values),
    ("extreme_float_values", test_extreme_float_values),
    ("nan_and_infinity", test_nan_and_infinity),
    ("base64_lengths_0_to_63", test_base64_lengths),
    ("string_edges", test_string_edges),
    ("utf8", test_utf8),
    ("boolean", test_boolean),
    ("null", test_null),
    ("empty_array", test_empty_array),
    ("empty_object", test_empty_object),
    ("array", test_array),
    ("large_array_5000", test_large_array),
    ("object", test_object),
    ("large_object_1000", test_large_object),
    ("long_object_key_10000", test_long_object_key),
    ("nested", test_nested),
    ("deep_nesting_100", test_deep_nesting),
    ("determinism", test_determinism),
    ("duplicate_object_keys", test_duplicate_object_keys),
    ("cycle_detection", test_cycle),
    ("large_100000_byte_string", test_large_string),
    ("large_1mb_string", test_1mb_string),
    ("repeated_serialization_1000", test_repeated_serialization),
    ("repeated_create_free_10000", test_repeated_create_free),
    ("fuzz_500", test_fuzz),
    ("extended_fuzz_5000", test_extended_fuzz),
    ("mixed_array", test_mixed_array),
]

def child_mode(case_name):
    for name, func in TESTS:
        if name == case_name:
            func()
            print("PASS")
            return 0

    print(f"Unknown test: {case_name}", file=sys.stderr)
    return 2

def run_parent():
    with open(RESULT_FILE, "w", encoding="utf-8") as results:
        results.write("UBRIDGE EXTENDED BRUTAL STRUCTURAL TEST RESULTS\n")
        results.write("=" * 60 + "\n\n")

        passed = 0
        failed = 0
        crashed = 0

        for index, (name, _) in enumerate(TESTS, 1):
            print(f"[{index}/{len(TESTS)}] {name}", flush=True)

            completed = subprocess.run(
                [sys.executable, os.path.abspath(__file__), "--case", name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            if completed.returncode == 0:
                status = "PASS"
                passed += 1
            elif completed.returncode < 0:
                signal_number = -completed.returncode
                status = f"CRASH (signal {signal_number})"
                crashed += 1
            elif completed.returncode == 139:
                status = "CRASH (exit code 139 / SIGSEGV)"
                crashed += 1
            else:
                status = f"FAIL (exit code {completed.returncode})"
                failed += 1

            results.write(f"[{index}] {name}: {status}\n")

            if completed.stdout.strip():
                results.write("stdout:\n")
                results.write(completed.stdout)
                results.write("\n")

            if completed.stderr.strip():
                results.write("stderr:\n")
                results.write(completed.stderr)
                results.write("\n")

            results.write("-" * 60 + "\n")

        total = len(TESTS)

        results.write("\nSUMMARY\n")
        results.write("=" * 60 + "\n")
        results.write(f"TOTAL:   {total}\n")
        results.write(f"PASSED:  {passed}\n")
        results.write(f"FAILED:  {failed}\n")
        results.write(f"CRASHED: {crashed}\n")

        if crashed:
            results.write("\nCRITICAL: Native C library crash detected.\n")
        elif failed:
            results.write("\nFAILURE: One or more structural tests failed.\n")
        else:
            results.write("\nALL EXTENDED TESTS PASSED.\n")

    print()
    print(f"Results written to: {RESULT_FILE}")
    print(f"Passed:  {passed}")
    print(f"Failed:  {failed}")
    print(f"Crashed: {crashed}")

    return 1 if failed or crashed else 0

if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--case":
        sys.exit(child_mode(sys.argv[2]))

    sys.exit(run_parent())
