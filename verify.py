import ctypes
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
RESULT_FILE = os.path.join(ROOT, "asan_test_results.txt")

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

def test_string_memory():
    lib = load_library()

    sizes = [
        0,
        1,
        2,
        3,
        127,
        128,
        255,
        256,
        1023,
        1024,
        4095,
        4096,
        10000,
        100000,
        1048576
    ]

    for size in sizes:
        node = lib.ub_create(3)
        data = b"A" * size

        lib.ub_str(node, data)

        result = process(lib, node)

        lib.ub_free(node)

        assert "#SIG:" in result

def test_string_replace_free():
    lib = load_library()

    node = lib.ub_create(3)

    for size in range(0, 10000, 137):
        data = bytes((i % 256 for i in range(size)))
        lib.ub_str(node, data)

        result = process(lib, node)

        assert "#SIG:" in result

    lib.ub_free(node)

def test_array_memory():
    lib = load_library()

    arr = lib.ub_create(5)

    for i in range(10000):
        node = lib.ub_create(1)
        lib.ub_int(node, i)
        lib.ub_array(arr, node)

    result = process(lib, arr)

    lib.ub_free(arr)

    assert "#SIG:" in result

def test_object_memory():
    lib = load_library()

    obj = lib.ub_create(6)

    for i in range(5000):
        key = f"key_{i}".encode()

        node = lib.ub_create(1)
        lib.ub_int(node, i)

        lib.ub_object(obj, key, node)

    result = process(lib, obj)

    lib.ub_free(obj)

    assert "#SIG:" in result

def test_nested_memory():
    lib = load_library()

    root = lib.ub_create(6)
    current = root

    for i in range(100):
        child = lib.ub_create(6)
        value = lib.ub_create(1)

        lib.ub_int(value, i)
        lib.ub_object(current, f"level_{i}".encode(), value)
        lib.ub_object(current, b"child", child)

        current = child

    result = process(lib, root)

    lib.ub_free(root)

    assert "#SIG:" in result

def test_cycle_memory():
    lib = load_library()

    root = lib.ub_create(5)
    child = lib.ub_create(5)

    lib.ub_array(root, child)
    lib.ub_array(child, root)

    result = process(lib, root)

    lib.ub_free(root)

    assert "LOOP:" in result

def test_mixed_memory():
    lib = load_library()

    root = lib.ub_create(6)

    null_node = lib.ub_create(0)

    int_node = lib.ub_create(1)
    lib.ub_int(int_node, -9223372036854775807 - 1)

    float_node = lib.ub_create(2)
    lib.ub_float(float_node, -123456.789)

    string_node = lib.ub_create(3)
    lib.ub_str(string_node, b"A" * 100000)

    bool_node = lib.ub_create(4)
    lib.ub_int(bool_node, 1)

    array_node = lib.ub_create(5)

    for i in range(1000):
        item = lib.ub_create(1)
        lib.ub_int(item, i)
        lib.ub_array(array_node, item)

    lib.ub_object(root, b"null", null_node)
    lib.ub_object(root, b"integer", int_node)
    lib.ub_object(root, b"float", float_node)
    lib.ub_object(root, b"string", string_node)
    lib.ub_object(root, b"boolean", bool_node)
    lib.ub_object(root, b"array", array_node)

    result = process(lib, root)

    lib.ub_free(root)

    assert "#SIG:" in result

def test_repeated_lifecycle():
    lib = load_library()

    for cycle in range(20000):
        node = lib.ub_create(3)

        data = bytes(
            ((cycle * 31 + i * 17) % 256 for i in range(cycle % 512))
        )

        lib.ub_str(node, data)

        result = process(lib, node)

        lib.ub_free(node)

        assert "#SIG:" in result

def test_large_nested():
    lib = load_library()

    root = lib.ub_create(5)
    current = root

    for _ in range(250):
        child = lib.ub_create(5)
        lib.ub_array(current, child)
        current = child

    value = lib.ub_create(3)
    lib.ub_str(value, b"B" * 50000)
    lib.ub_array(current, value)

    result = process(lib, root)

    lib.ub_free(root)

    assert "#SIG:" in result

def test_fuzz_memory():
    lib = load_library()

    for iteration in range(10000):
        node_type = iteration % 7

        if node_type == 0:
            node = lib.ub_create(0)

        elif node_type == 1:
            node = lib.ub_create(1)
            lib.ub_int(
                node,
                ((iteration * 1103515245) & 0xFFFFFFFF) - 2147483648
            )

        elif node_type == 2:
            node = lib.ub_create(2)
            lib.ub_float(
                node,
                ((iteration % 100000) - 50000) / 37.0
            )

        elif node_type == 3:
            node = lib.ub_create(3)
            size = (iteration * 97) % 4096
            data = bytes(
                ((iteration + i * 13) % 256 for i in range(size))
            )
            lib.ub_str(node, data)

        elif node_type == 4:
            node = lib.ub_create(4)
            lib.ub_int(node, iteration % 2)

        elif node_type == 5:
            node = lib.ub_create(5)

            for i in range(iteration % 25):
                item = lib.ub_create(1)
                lib.ub_int(item, i)
                lib.ub_array(node, item)

        else:
            node = lib.ub_create(6)

            for i in range(iteration % 10):
                item = lib.ub_create(1)
                lib.ub_int(item, i)
                lib.ub_object(node, f"k{i}".encode(), item)

        result = process(lib, node)

        lib.ub_free(node)

        assert "#SIG:" in result

def test_signature_stability():
    lib = load_library()

    values = [
        b"",
        b"A",
        b"AB",
        b"ABC",
        b"A" * 127,
        b"B" * 1024,
        b"C" * 100000
    ]

    for data in values:
        node = lib.ub_create(3)
        lib.ub_str(node, data)

        first = process(lib, node)
        second = process(lib, node)
        third = process(lib, node)

        lib.ub_free(node)

        assert first == second
        assert second == third

def test_free_graph():
    lib = load_library()

    root = lib.ub_create(5)

    shared = lib.ub_create(6)

    value1 = lib.ub_create(1)
    value2 = lib.ub_create(3)

    lib.ub_int(value1, 123)
    lib.ub_str(value2, b"shared")

    lib.ub_object(shared, b"number", value1)
    lib.ub_object(shared, b"text", value2)

    lib.ub_array(root, shared)
    lib.ub_array(root, shared)

    result = process(lib, root)

    lib.ub_free(root)

    assert "#SIG:" in result

TESTS = [
    ("string_memory", test_string_memory),
    ("string_replace_free", test_string_replace_free),
    ("array_memory", test_array_memory),
    ("object_memory", test_object_memory),
    ("nested_memory", test_nested_memory),
    ("cycle_memory", test_cycle_memory),
    ("mixed_memory", test_mixed_memory),
    ("repeated_lifecycle", test_repeated_lifecycle),
    ("large_nested", test_large_nested),
    ("fuzz_memory", test_fuzz_memory),
    ("signature_stability", test_signature_stability),
    ("free_graph", test_free_graph),
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
        results.write("UBRIDGE ADDRESSSANITIZER MEMORY SAFETY TEST RESULTS\n")
        results.write("=" * 64 + "\n\n")

        passed = 0
        failed = 0
        crashed = 0
        sanitizer_errors = 0

        for index, (name, _) in enumerate(TESTS, 1):
            print(f"[{index}/{len(TESTS)}] {name}", flush=True)

            env = os.environ.copy()
            env["ASAN_OPTIONS"] = "detect_leaks=0:abort_on_error=1:halt_on_error=1"

            completed = subprocess.run(
                [sys.executable, os.path.abspath(__file__), "--case", name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env
            )

            combined = (
                completed.stdout + "\n" + completed.stderr
            ).lower()

            if completed.returncode == 0:
                status = "PASS"
                passed += 1
            elif (
                "addresssanitizer" in combined
                or "heap-buffer-overflow" in combined
                or "heap-use-after-free" in combined
                or "double-free" in combined
                or "stack-buffer-overflow" in combined
                or "memory leak" in combined
            ):
                status = "SANITIZER ERROR"
                sanitizer_errors += 1
            elif completed.returncode < 0:
                status = f"CRASH (signal {-completed.returncode})"
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

            results.write("-" * 64 + "\n")

        total = len(TESTS)

        results.write("\nSUMMARY\n")
        results.write("=" * 64 + "\n")
        results.write(f"TOTAL:             {total}\n")
        results.write(f"PASSED:            {passed}\n")
        results.write(f"FAILED:            {failed}\n")
        results.write(f"CRASHED:           {crashed}\n")
        results.write(f"SANITIZER ERRORS:  {sanitizer_errors}\n")

        if sanitizer_errors:
            results.write("\nCRITICAL: AddressSanitizer detected a memory-safety violation.\n")
        elif crashed:
            results.write("\nCRITICAL: Native crash detected.\n")
        elif failed:
            results.write("\nFAILURE: One or more memory-safety tests failed.\n")
        else:
            results.write("\nALL ADDRESSSANITIZER TESTS PASSED.\n")

    print()
    print(f"Results written to: {RESULT_FILE}")
    print(f"Passed:  {passed}")
    print(f"Failed:  {failed}")
    print(f"Crashed: {crashed}")
    print(f"ASan errors: {sanitizer_errors}")

    return 1 if failed or crashed or sanitizer_errors else 0

if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--case":
        sys.exit(child_mode(sys.argv[2]))

    sys.exit(run_parent())
