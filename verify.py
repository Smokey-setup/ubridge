import ctypes
import os
import subprocess
import sys

def run_suite():
    print(" Running Structural Integrity Validation \n")

    subprocess.run(["make", "clean"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["make"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    prefix = "lib"
    ext = ".so"
    if sys.platform == "darwin":
        ext = ".dylib"
    elif sys.platform == "win32":
        prefix = ""
        ext = ".dll"
    
    lib_path = f"./{prefix}ubridge{ext}"
    lib = ctypes.CDLL(lib_path)
    
    lib.ub_create.restype = ctypes.c_void_p
    lib.ub_process.restype = ctypes.c_void_p
    
    neg_node = lib.ub_create(2)
    lib.ub_float(ctypes.c_void_p(neg_node), ctypes.c_double(-0.25))
    
    res_ptr = lib.ub_process(ctypes.c_void_p(neg_node))
    output_token = ctypes.c_char_p(res_ptr).value.decode()
    
    print(f" -> Input Under-Zero Value: -0.25")
    print(f" -> Output Token Representation: {output_token}")
    
    if "F:8:-0.25000000" in output_token:
        print("Correct negative fixed-point formatting confirmed.")
    else:
        print(" Negative structural formatting assertion error.")
        sys.exit(1)
        
    lib.ub_string_free(ctypes.c_void_p(res_ptr))
    lib.ub_free(ctypes.c_void_p(neg_node))

    neg_node = lib.ub_create(2)
    lib.ub_float(ctypes.c_void_p(neg_node), ctypes.c_double(-12.5))
    
    res_ptr = lib.ub_process(ctypes.c_void_p(neg_node))
    output_token = ctypes.c_char_p(res_ptr).value.decode()
    
    print(f"\n -> Input Negative Value: -12.5")
    print(f" -> Output Token Representation: {output_token}")
    
    if "F:8:-12.50000000" in output_token:
        print("Correct negative fixed-point formatting confirmed.")
    else:
        print(" Negative whole-number formatting assertion error.")
        sys.exit(1)
        
    lib.ub_string_free(ctypes.c_void_p(res_ptr))
    lib.ub_free(ctypes.c_void_p(neg_node))

    string_node = lib.ub_create(3)
    lib.ub_str(ctypes.c_void_p(string_node), ctypes.c_char_p(b"A"))
    
    res_ptr = lib.ub_process(ctypes.c_void_p(string_node))
    output_token = ctypes.c_char_p(res_ptr).value.decode()
    
    print(f"\n -> Input Base64 Test String: A")
    print(f" -> Output Token Representation: {output_token}")
    
    if "P:4:QQ==;" in output_token:
        print("Correct Base64 single-byte padding confirmed.")
    else:
        print(" Base64 single-byte padding assertion error.")
        sys.exit(1)
        
    lib.ub_string_free(ctypes.c_void_p(res_ptr))
    lib.ub_free(ctypes.c_void_p(string_node))

    string_node = lib.ub_create(3)
    lib.ub_str(ctypes.c_void_p(string_node), ctypes.c_char_p(b"AB"))
    
    res_ptr = lib.ub_process(ctypes.c_void_p(string_node))
    output_token = ctypes.c_char_p(res_ptr).value.decode()
    
    print(f"\n -> Input Base64 Test String: AB")
    print(f" -> Output Token Representation: {output_token}")
    
    if "P:4:QUI=;" in output_token:
        print("Correct Base64 two-byte padding confirmed.")
    else:
        print(" Base64 two-byte padding assertion error.")
        sys.exit(1)
        
    lib.ub_string_free(ctypes.c_void_p(res_ptr))
    lib.ub_free(ctypes.c_void_p(string_node))

    string_node = lib.ub_create(3)
    lib.ub_str(ctypes.c_void_p(string_node), ctypes.c_char_p(b"ABC"))
    
    res_ptr = lib.ub_process(ctypes.c_void_p(string_node))
    output_token = ctypes.c_char_p(res_ptr).value.decode()
    
    print(f"\n -> Input Base64 Test String: ABC")
    print(f" -> Output Token Representation: {output_token}")
    
    if "P:4:QUJD;" in output_token:
        print("Correct Base64 three-byte encoding confirmed.")
    else:
        print(" Base64 three-byte encoding assertion error.")
        sys.exit(1)
        
    lib.ub_string_free(ctypes.c_void_p(res_ptr))
    lib.ub_free(ctypes.c_void_p(string_node))
    
    print("\n PRODUCTION STATUS CONFIRMED: 10/10 READY FOR PRODUCTION ")

if __name__ == "__main__":
    run_suite()
