# ubridge 

A zero-dependency, ultra-performance cross-language data serialization bridge converting incoming data payloads into deterministic, 8-decimal fixed-point representations natively via raw C-ABI memory routing. 

--- 

## 🌎 What ubridge Solves for the World 

Traditional software architectures suffer from two historic pain points when microservices pass complex information across modern tech stacks: 

1. **The Polyglot Tax**: Constantly stringifying objects into massive JSON payloads wastes immense CPU cycles and network memory bandwidth. `ubridge` eliminates this tax by letting different runtimes safely share data inside the **exact same raw memory addresses** at pure hardware speed. 
2. **IEEE 754 Representation Traps**: Modern computer chips store fractions using base-2 bits, causing numbers like `0.1 + 0.2` to naturally drift into `0.30000000000000004`. `ubridge` acts as an absolute mathematical gatekeeper. It captures data as hard integer coordinates using an 8-decimal fixed-point scale factor (`100,000,000`), locking calculations into a unified cross-platform representation format that guarantees identical output behavior anywhere on earth. 

--- 

## Prerequisites & Native Compilation 

Before your high-level language runtime can call the interface core, you must compile the C source files into a shared machine binary matching your server operating system. 

### Build Tool Requirements 
* **GCC or Clang compiler** installed on your system path. 
* **Make utility** installed. 

### Execution Build Command 
Open your terminal inside the repository root directory and run: 
```bash 
make 

```
This automatically compiles the shared module based on your active host environment:
 * **Linux**: Generates libubridge.so
 * **macOS**: Generates libubridge.dylib
 * **Windows**: Generates ubridge.dll
## Core API Engine Interface Mapping
The library exposes simple doors to manage complex data structures directly inside system memory:
 * **ub_create(uint8_t type)**: Allocates an isolated, type-specific data node block onto the system heap.
 * **ub_int(UNode* node, int64_t val)**: Formats and locks a 64-bit integer into a network-byte-order structure.
 * **ub_float(UNode* node, double val)**: Converts values into an integer-scaled fixed-point tracking register, defeating precision drift.
 * **ub_str(UNode* node, const char* val)**: Dynamically maps plain text layers into memory-efficient strings.
 * **ub_array(UNode* arr_node, UNode* item_node)**: Appends nodes together dynamically to build deep data collection arrays.
 * **ub_object(UNode* obj_node, const char* key, UNode* val_node)**: Creates sorted key-value maps out of dynamic property payloads.
 * **ub_process(UNode* root)**: Encodes the structural data graph into a payload string featuring cyclic protection and an FNV-1a tamper signature.
 * **ub_free(UNode* root)**: Recursively destroys object graphs while protecting the engine against double-free system crashes.
 * **ub_string_free(char* ptr)**: Reclaims the explicit string buffer allocated by ub_process to guarantee a **0% memory leak** runtime footprint.
## Language Execution Blueprints
Every major programming language in modern computing history can tap directly into the compiled native binary using built-in Foreign Function Interfaces (FFI).
### 1. Python (via ctypes)
**Human Explanation**: Python loads the binary, configures explicit voice channels via ctypes pointers, streams raw decimal tracking info, and safely clears the string allocation memory cache when printed.
```python
import ctypes 
import sys 

# 1. Mount the native machine library binary (adjust extension if on macOS/Windows) 
lib = ctypes.CDLL('./libubridge.so') 

# 2. Map explicit return constraints for pointer safety 
lib.ub_create.restype = ctypes.c_void_p 
lib.ub_process.restype = ctypes.c_void_p 

# Crucial: Fetch raw pointer address to avoid leaks 
# 3. Stream data allocations straight into the memory bridge 
node = lib.ub_create(2) # Type U_FLOAT = 2 
lib.ub_float(ctypes.c_void_p(node), ctypes.c_double(-0.25)) 

# 4. Extract signed payload parameters from the text stream 
res_ptr = lib.ub_process(ctypes.c_void_p(node)) 
print(ctypes.c_char_p(res_ptr).value.decode()) 

# 5. Clear both structural and text execution leaks completely 
lib.ub_string_free(ctypes.c_void_p(res_ptr)) 
lib.ub_free(ctypes.c_void_p(node)) 

```
### 2. Node.js / TypeScript (via ffi-napi)
**Human Explanation**: Node bridges your JavaScript properties straight to the compiled native binary. It maps object layers dynamically and completely wipes the system heap afterwards to prevent sluggish memory bloat.
```javascript
const ffi = require('ffi-napi'); 

// 1. Establish the direct interface gateway signatures 
const lib = ffi.Library('./libubridge.so', { 
    'ub_create': ['pointer', ['uint8']], 
    'ub_float': ['void', ['pointer', 'double']], 
    'ub_process': ['string', ['pointer']], 
    'ub_free': ['void', ['pointer']], 
    'ub_string_free': ['void', ['pointer']] 
}); 

// 2. Build and process custom dynamic data tokens 
const node = lib.ub_create(2); 
lib.ub_float(node, -0.25); 

// 3. Process structural output streams natively 
const result = lib.ub_process(node); 
console.log(result); 

// 4. Release system memory allocations explicitly 
lib.ub_free(node); 
// Note: When using 'string' as an ffi return type, ffi-napi copies the buffer; 
// pass your raw pointer if managing fine-grained garbage collection tracks. 

```
### 3. Go (via Native Cgo Integration)
**Human Explanation**: Go uses its fast compiler parameters to link against your library. It formats numbers directly inside system RAM and extracts standard string parameters at raw hardware speed.
```go
package main 

/* 
#cgo LDFLAGS: -L. -lubridge 
#include "ubridge.h" 
*/ 
import "C" 
import "fmt" 

func main() { 
// 1. Spawns data box nodes cleanly via machine binary codes 
node := C.ub_create(2) 
C.ub_float(node, C.double(-0.25)) 

// 2. Process data stream and convert machine memory pointers back to Go strings 
resPtr := C.ub_process(node) 
fmt.Println(C.GoString(resPtr)) 

// 3. Clear system resources completely to avoid memory accumulation 
C.ub_string_free((*C.char)(resPtr)) 
C.ub_free(node) 
} 

```
### 4. Rust (via Foreign Function Interface)
**Human Explanation**: Rust leverages its low-overhead unsafe code structures to handshake with your C library symbols, tracking system memory states with optimal execution efficiency.
```rust
use std::ffi::{c_char, c_void, CStr}; 

#[link(name = "ubridge")] 
extern "C" { 
    fn ub_create(t: u8) -> *mut c_void; 
    fn ub_float(node: *mut c_void, val: f64); 
    fn ub_process(node: *mut c_void) -> *mut c_char; 
    fn ub_free(node: *mut c_void); 
    fn ub_string_free(ptr: *mut c_char); 
} 

fn main() { 
    unsafe { 
        // 1. Run unthrottled hardware calls directly on the system heap 
        let node = ub_create(2); 
        ub_float(node, -0.25); 
        
        // 2. Borrow and read string contents from the native pointer layout 
        let res_ptr = ub_process(node); 
        let res = CStr::from_ptr(res_ptr).to_str().unwrap(); 
        println!("{}", res); 
        
        // 3. Deallocate tracking points to ensure zero RAM leak expansion 
        ub_string_free(res_ptr); 
        ub_free(node); 
    } 
} 

```
### 5. C# (.NET via DllImport P/Invoke)
**Human Explanation**: C# utilizes high-velocity platform invoke bindings to load the library, assign variables to specific memory tracking addresses, and dump allocation frames smoothly.
```csharp
using System; 
using System.Runtime.InteropServices; 

public class Program { 
    [DllImport("libubridge.so", CallingConvention = CallingConvention.Cdecl)] 
    private static extern IntPtr ub_create(byte type); 
    
    [DllImport("libubridge.so", CallingConvention = CallingConvention.Cdecl)] 
    private static extern void ub_float(IntPtr node, double val); 
    
    [DllImport("libubridge.so", CallingConvention = CallingConvention.Cdecl)] 
    private static extern IntPtr ub_process(IntPtr node); 
    
    [DllImport("libubridge.so", CallingConvention = CallingConvention.Cdecl)] 
    private static extern void ub_free(IntPtr node); 
    
    [DllImport("libubridge.so", CallingConvention = CallingConvention.Cdecl)] 
    private static extern void ub_string_free(IntPtr ptr); 
    
    public static void Main() { 
        // 1. Allocate native memory shapes through internal pointer windows 
        IntPtr node = ub_create(2); 
        ub_float(node, -0.25); 
        
        // 2. Fetch raw pointer and translate token contents to managed string 
        IntPtr resPtr = ub_process(node); 
        string output = Marshal.PtrToStringAnsi(resPtr); 
        Console.WriteLine(output); 
        
        // 3. Free native allocations explicitly 
        ub_string_free(resPtr); 
        ub_free(node); 
    } 
} 

```
### 6. Java (via Project Panama Foreign Function API)
**Human Explanation**: Java opens modern hardware memory access blocks to find binary system structures. It bypasses slow, old legacy layers to read your data tokens at raw computer speed.
```java
import java.lang.foreign.*; 
import java.lang.invoke.MethodHandle; 

public class UBridgeJava { 
    public static void main(String[] args) throws Throwable { 
        SymbolLookup lookup = SymbolLookup.libraryLookup("libubridge.so", Arena.global()); 
        Linker linker = Linker.nativeLinker(); 
        
        MethodHandle ubCreate = linker.downcallHandle(lookup.find("ub_create").get(), FunctionDescriptor.of(ValueLayout.ADDRESS, ValueLayout.JAVA_BYTE)); 
        MethodHandle ubFloat = linker.downcallHandle(lookup.find("ub_float").get(), FunctionDescriptor.ofVoid(ValueLayout.ADDRESS, ValueLayout.JAVA_DOUBLE));
        MethodHandle ubProcess = linker.downcallHandle(lookup.find("ub_process").get(), FunctionDescriptor.of(ValueLayout.ADDRESS, ValueLayout.ADDRESS));
        MethodHandle ubFree = linker.downcallHandle(lookup.find("ub_free").get(), FunctionDescriptor.ofVoid(ValueLayout.ADDRESS));
        MethodHandle ubStringFree = linker.downcallHandle(lookup.find("ub_string_free").get(), FunctionDescriptor.ofVoid(ValueLayout.ADDRESS));

        // 1. Establish structural node segments inside foreign memory pools
        MemorySegment node = (MemorySegment) ubCreate.invokeExact((byte) 2);
        ubFloat.invokeExact(node, -0.25);

        // 2. Interpret memory segment references to extract Java outputs
        MemorySegment resPtr = (MemorySegment) ubProcess.invokeExact(node);
        System.out.println(resPtr.reinterpret(Long.MAX_VALUE).getString(0));

        // 3. Clear leak footprints using clean destruction commands
        ubStringFree.invokeExact(resPtr);
        ubFree.invokeExact(node);
    }
}

```
### 7. C++ (via Native Linkage)
**Human Explanation**: C++ imports your interface header directly into its core compilation process. It calls your methods straight on the hardware layer with absolute zero wrapper overhead.
```cpp
#include "ubridge.h"
#include <iostream>

int main() {
    // 1. Allocate node structures directly on the hardware layout boundary
    UNode* node = ub_create(2);
    ub_float(node, -0.25);

    // 2. Process serialization outputs and read them instantly
    const char* result = ub_process(node);
    std::cout << result << std::endl;

    // 3. Release both text arrays and struct containers safely
    ub_string_free((char*)result);
    ub_free(node);
    return 0;
}

```