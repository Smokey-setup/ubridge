import ctypes
import os
import subprocess
import sys
import base64
import random
import string
import math
import hashlib

RESULT_FILE = "brutal_test_results.txt"

def load_library():
    prefix = "lib"
    ext = ".so"

    if sys.platform == "darwin":
        ext = ".dylib"
    elif sys.platform == "win32":
        prefix = ""
        ext = ".dll"

    lib_path = f"./{prefix}ubridge{ext}"
    lib = ctypes.CDLL(lib_path)

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
        return None

    raw = ctypes.string_at(ptr)
    lib.ub_string_free(ptr)

    return raw.decode("utf-8", errors="replace")


def make_int(lib, value):
    node = lib.ub_create(1)
    lib.ub_int(node, value)
    return node


def make_float(lib, value):
    node = lib.ub_create(2)
    lib.ub_float(node, value)
    return node


def make_string(lib, value):
    node = lib.ub_create(3)
    lib.ub_str(node, value)
    return node


def make_bool(lib, value):
    node = lib.ub_create(4)
    lib.ub_int(node, 1 if value else 0)
    return node


def make_null(lib):
    return lib.ub_create(0)


def run_test(results, name, passed, detail):
    status = "PASS" if passed else "FAIL"
    results.append(f"[{status}] {name}")
    results.append(f"       {detail}")
    return passed


def main():
    results = []
    failures = 0

    results.append("UBRIDGE BRUTAL SYSTEM AUDIT")
    results.append("=" * 80)
    results.append("")
    results.append(f"Python: {sys.version}")
    results.append(f"Platform: {sys.platform}")
    results.append(f"Working Directory: {os.getcwd()}")
    results.append("")

    try:
        lib = load_library()
        run_test(results, "Library loading", True, "Native library loaded successfully.")
    except Exception as exc:
        results.append("[FAIL] Library loading")
        results.append(f"       {type(exc).__name__}: {exc}")
        failures += 1
        write_results(results)
        return

    results.append("")
    results.append("1. INTEGER BOUNDARY TESTS")
    results.append("-" * 80)

    integer_values = [
        0,
        1,
        -1,
        2,
        -2,
        127,
        -127,
        128,
        -128,
        255,
        -255,
        256,
        -256,
        32767,
        -32768,
        65535,
        -65535,
        2147483647,
        -2147483648,
        4294967295,
        -4294967295,
        9223372036854775807,
        -9223372036854775807,
    ]

    for value in integer_values:
        try:
            node = make_int(lib, value)
            output = process(lib, node)
            lib.ub_free(node)

            expected = f"I:{value};"

            passed = output is not None and expected in output

            if not run_test(
                results,
                f"Integer {value}",
                passed,
                f"Output: {output}"
            ):
                failures += 1
        except Exception as exc:
            failures += 1
            run_test(
                results,
                f"Integer {value}",
                False,
                f"{type(exc).__name__}: {exc}"
            )

    results.append("")
    results.append("2. FLOATING-POINT TESTS")
    results.append("-" * 80)

    float_values = [
        0.0,
        1.0,
        -1.0,
        0.1,
        -0.1,
        0.25,
        -0.25,
        0.5,
        -0.5,
        1.5,
        -1.5,
        12.5,
        -12.5,
        123456.789,
        -123456.789,
        0.00000001,
        -0.00000001,
        0.000000001,
        -0.000000001,
        999999999.9999999,
        -999999999.9999999,
    ]

    for value in float_values:
        try:
            node = make_float(lib, value)
            output = process(lib, node)
            lib.ub_free(node)

            passed = output is not None and output.startswith("F:8:")

            if not run_test(
                results,
                f"Float {value}",
                passed,
                f"Output: {output}"
            ):
                failures += 1
        except Exception as exc:
            failures += 1
            run_test(
                results,
                f"Float {value}",
                False,
                f"{type(exc).__name__}: {exc}"
            )

    results.append("")
    results.append("3. BASE64 EXHAUSTIVE LENGTH TEST")
    results.append("-" * 80)

    for length in range(0, 64):
        data = bytes((i * 37 + length) % 256 for i in range(length))

        try:
            node = make_string(lib, data)
            output = process(lib, node)
            lib.ub_free(node)

            encoded = base64.b64encode(data).decode()
            expected = f"P:{len(encoded)}:{encoded};"

            passed = output is not None and expected in output

            if not run_test(
                results,
                f"Base64 length {length}",
                passed,
                f"Expected: {expected} | Output: {output}"
            ):
                failures += 1
        except Exception as exc:
            failures += 1
            run_test(
                results,
                f"Base64 length {length}",
                False,
                f"{type(exc).__name__}: {exc}"
            )

    results.append("")
    results.append("4. STRING EDGE CASES")
    results.append("-" * 80)

    string_cases = [
        b"",
        b"A",
        b"AB",
        b"ABC",
        b"hello",
        b"hello world",
        b"1234567890",
        b"\x00",
        b"\x01\x02\x03\x04",
        bytes(range(32)),
        bytes(range(128)),
        bytes(range(256)),
        b"A" * 1000,
        b"B" * 10000,
    ]

    for data in string_cases:
        try:
            node = make_string(lib, data)
            output = process(lib, node)
            lib.ub_free(node)

            encoded = base64.b64encode(data).decode()
            expected = f"P:{len(encoded)}:{encoded};"

            passed = output is not None and expected in output

            if not run_test(
                results,
                f"String byte length {len(data)}",
                passed,
                f"Encoded length: {len(encoded)} | Output length: {len(output) if output else 0}"
            ):
                failures += 1
        except Exception as exc:
            failures += 1
            run_test(
                results,
                f"String byte length {len(data)}",
                False,
                f"{type(exc).__name__}: {exc}"
            )

    results.append("")
    results.append("5. UTF-8 STRING TESTS")
    results.append("-" * 80)

    unicode_cases = [
        "",
        "hello",
        "café",
        "naïve",
        "こんにちは",
        "你好",
        "안녕하세요",
        "Привет",
        "مرحبا",
        "🚀",
        "🔥💻🌍",
        "𐍈",
    ]

    for text in unicode_cases:
        data = text.encode("utf-8")

        try:
            node = make_string(lib, data)
            output = process(lib, node)
            lib.ub_free(node)

            encoded = base64.b64encode(data).decode()
            expected = f"P:{len(encoded)}:{encoded};"

            passed = output is not None and expected in output

            if not run_test(
                results,
                f"UTF-8 {repr(text)}",
                passed,
                f"Output: {output}"
            ):
                failures += 1
        except Exception as exc:
            failures += 1
            run_test(
                results,
                f"UTF-8 {repr(text)}",
                False,
                f"{type(exc).__name__}: {exc}"
            )

    results.append("")
    results.append("6. BOOLEAN TESTS")
    results.append("-" * 80)

    for value in [False, True]:
        try:
            node = make_bool(lib, value)
            output = process(lib, node)
            lib.ub_free(node)

            expected = "B:1;" if value else "B:0;"
            passed = output is not None and expected in output

            if not run_test(
                results,
                f"Boolean {value}",
                passed,
                f"Output: {output}"
            ):
                failures += 1
        except Exception as exc:
            failures += 1
            run_test(
                results,
                f"Boolean {value}",
                False,
                f"{type(exc).__name__}: {exc}"
            )

    results.append("")
    results.append("7. NULL TEST")
    results.append("-" * 80)

    try:
        node = make_null(lib)
        output = process(lib, node)
        lib.ub_free(node)

        passed = output is not None and output.startswith("NIL;")

        if not run_test(
            results,
            "NULL serialization",
            passed,
            f"Output: {output}"
        ):
            failures += 1
    except Exception as exc:
        failures += 1
        run_test(
            results,
            "NULL serialization",
            False,
            f"{type(exc).__name__}: {exc}"
        )

    results.append("")
    results.append("8. SIGNATURE DETERMINISM")
    results.append("-" * 80)

    try:
        outputs = []

        for _ in range(20):
            node = make_string(lib, b"determinism-test")
            outputs.append(process(lib, node))
            lib.ub_free(node)

        passed = len(set(outputs)) == 1

        if not run_test(
            results,
            "Repeated serialization determinism",
            passed,
            f"Unique outputs: {len(set(outputs))}"
        ):
            failures += 1
    except Exception as exc:
        failures += 1
        run_test(
            results,
            "Repeated serialization determinism",
            False,
            f"{type(exc).__name__}: {exc}"
        )

    results.append("")
    results.append("9. RANDOMIZED STRING FUZZ TEST")
    results.append("-" * 80)

    random.seed(1337)

    for test_number in range(1, 501):
        length = random.randint(0, 512)
        data = bytes(random.randint(0, 255) for _ in range(length))

        try:
            node = make_string(lib, data)
            output = process(lib, node)
            lib.ub_free(node)

            encoded = base64.b64encode(data).decode()
            expected = f"P:{len(encoded)}:{encoded};"

            passed = output is not None and expected in output

            if not passed:
                failures += 1
                results.append(f"[FAIL] Random fuzz test #{test_number}")
                results.append(f"       Input length: {length}")
                results.append(f"       Expected: {expected}")
                results.append(f"       Output: {output}")
                break
        except Exception as exc:
            failures += 1
            results.append(f"[FAIL] Random fuzz test #{test_number}")
            results.append(f"       {type(exc).__name__}: {exc}")
            break
    else:
        results.append("[PASS] 500 randomized string fuzz tests")
        results.append("       No serialization mismatch detected.")

    results.append("")
    results.append("10. OBJECT KEY ORDER DETERMINISM")
    results.append("-" * 80)

    try:
        obj1 = lib.ub_create(6)
        obj2 = lib.ub_create(6)

        values1 = [
            (b"zeta", make_int(lib, 1)),
            (b"alpha", make_int(lib, 2)),
            (b"middle", make_int(lib, 3)),
        ]

        values2 = [
            (b"middle", make_int(lib, 3)),
            (b"zeta", make_int(lib, 1)),
            (b"alpha", make_int(lib, 2)),
        ]

        for key, value in values1:
            lib.ub_object(obj1, key, value)

        for key, value in values2:
            lib.ub_object(obj2, key, value)

        output1 = process(lib, obj1)
        output2 = process(lib, obj2)

        passed = output1 == output2

        if not run_test(
            results,
            "Object ordering determinism",
            passed,
            f"Outputs identical: {passed}"
        ):
            failures += 1

        lib.ub_free(obj1)
        lib.ub_free(obj2)

    except Exception as exc:
        failures += 1
        run_test(
            results,
            "Object ordering determinism",
            False,
            f"{type(exc).__name__}: {exc}"
        )

    results.append("")
    results.append("11. ARRAY SERIALIZATION")
    results.append("-" * 80)

    try:
        arr = lib.ub_create(5)

        children = [
            make_int(lib, 1),
            make_int(lib, -2),
            make_float(lib, 3.5),
            make_string(lib, b"test"),
            make_bool(lib, True),
        ]

        for child in children:
            lib.ub_array(arr, child)

        output = process(lib, arr)

        passed = output is not None and output.startswith("A:5[")

        if not run_test(
            results,
            "Mixed array serialization",
            passed,
            f"Output: {output}"
        ):
            failures += 1

        lib.ub_free(arr)

    except Exception as exc:
        failures += 1
        run_test(
            results,
            "Mixed array serialization",
            False,
            f"{type(exc).__name__}: {exc}"
        )

    results.append("")
    results.append("12. NESTED STRUCTURE")
    results.append("-" * 80)

    try:
        outer = lib.ub_create(6)
        inner = lib.ub_create(5)

        lib.ub_array(inner, make_string(lib, b"nested"))
        lib.ub_array(inner, make_int(lib, 42))

        lib.ub_object(outer, b"array", inner)
        lib.ub_object(outer, b"name", make_string(lib, b"uBridge"))

        output = process(lib, outer)

        passed = output is not None and output.startswith("O:2{")

        if not run_test(
            results,
            "Nested object/array serialization",
            passed,
            f"Output: {output}"
        ):
            failures += 1

        lib.ub_free(outer)

    except Exception as exc:
        failures += 1
        run_test(
            results,
            "Nested object/array serialization",
            False,
            f"{type(exc).__name__}: {exc}"
        )

    results.append("")
    results.append("13. CYCLE DETECTION")
    results.append("-" * 80)

    try:
        arr = lib.ub_create(5)
        lib.ub_array(arr, arr)

        output = process(lib, arr)

        passed = output is not None and "LOOP:" in output

        if not run_test(
            results,
            "Self-referencing array cycle detection",
            passed,
            f"Output: {output}"
        ):
            failures += 1

        lib.ub_free(arr)

    except Exception as exc:
        failures += 1
        run_test(
            results,
            "Self-referencing array cycle detection",
            False,
            f"{type(exc).__name__}: {exc}"
        )

    results.append("")
    results.append("14. LARGE SERIALIZATION")
    results.append("-" * 80)

    try:
        data = b"X" * 100000
        node = make_string(lib, data)

        output = process(lib, node)
        lib.ub_free(node)

        encoded_length = len(base64.b64encode(data))

        passed = output is not None and f"P:{encoded_length}:" in output

        if not run_test(
            results,
            "100,000-byte string serialization",
            passed,
            f"Input: 100000 bytes | Expected encoded length: {encoded_length} | Output length: {len(output) if output else 0}"
        ):
            failures += 1

    except Exception as exc:
        failures += 1
        run_test(
            results,
            "100,000-byte string serialization",
            False,
            f"{type(exc).__name__}: {exc}"
        )

    results.append("")
    results.append("=" * 80)
    results.append("BRUTAL AUDIT SUMMARY")
    results.append("=" * 80)
    results.append(f"FAILURES DETECTED: {failures}")

    if failures == 0:
        results.append("RESULT: ALL TESTS PASSED")
    else:
        results.append("RESULT: SYSTEM FAILED ONE OR MORE TESTS")

    results.append("")
    results.append("IMPORTANT:")
    results.append("Passing this audit does not mathematically prove absence of all bugs.")
    results.append("It means the tested behaviors survived the current stress suite.")

    write_results(results)


def write_results(results):
    with open(RESULT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(results))
        f.write("\n")

    print(f"Brutal audit complete.")
    print(f"Results written to: {RESULT_FILE}")


if __name__ == "__main__":
    main()
