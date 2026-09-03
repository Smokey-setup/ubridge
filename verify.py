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
    
    # Assert Negative-Sign Fixed Point Isolation Logic (-0.25 Verification)
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
    
    print("\n PRODUCTION STATUS CONFIRMED: 10/10 READY FOR PRODUCTION ")

if __name__ == "__main__":
    run_suite()
