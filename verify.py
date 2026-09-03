import ctypes
import os
import subprocess
import sys
import tempfile

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
        outputs.append((value, result))

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
        outputs.append((value, result))

    return outputs

def test_base64_lengths():
    lib = load_library()

    outputs = []

    for length in range(64):
        data = bytes((i % 256 for i in range(length)))

        node = lib.ub_create(3)

        if data:
            lib.ub_str(node, data)
        else:
            lib.ub_str(node, b"")

        result = process(lib, node)
        lib.ub_free(node)

        assert result.startswith("P:")
        assert "#SIG:" in result

        outputs.append((length, result))

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
        outputs.append((value, result))

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

def test_fuzz():
    lib = load_library()

    for length in range(500):
        data = bytes(((i * 37 + length) % 256 for i in range(length % 128)))

        node = lib.ub_create(3)
        lib.ub_str(node, data)

        result = process(lib, node)
        lib.ub_free(node)

        assert "#SIG:" in result

    return "500 deterministic fuzz iterations completed"

TESTS = [
    ("basic", test_basic),
    ("integer_boundaries", test_integer_boundaries),
    ("float_values", test_float_values),
    ("base64_lengths_0_to_63", test_base64_lengths),
    ("string_edges", test_string_edges),
    ("utf8", test_utf8),
    ("boolean", test_boolean),
    ("null", test_null),
    ("array", test_array),
    ("object", test_object),
    ("nested", test_nested),
    ("determinism", test_determinism),
    ("cycle_detection", test_cycle),
    ("large_100000_byte_string", test_large_string),
    ("fuzz_500", test_fuzz),
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
        results.write("UBRIDGE BRUTAL STRUCTURAL TEST RESULTS\n")
        results.write("=" * 60 + "\n\n")

        passed = 0
        failed = 0
        crashed = 0

        for index, (name, _) in enumerate(TESTS, 1):
            print(f"[{index}/{len(TESTS)}] {name}")

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
            results.write("\nALL TESTS PASSED.\n")

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
