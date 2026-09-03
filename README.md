# ubridge

A zero-dependency, ultra-performance cross-language data serialization bridge solving IEEE 754 drift and structural engine bugs natively via raw C-ABI memory routing.

## 🛠️ Prerequisites & Compilation

Before your high-level language runtime can call the `ubridge` interface core, you must compile the C source files into a shared machine binary native to your server operating system.

### Build Tool Requirements
* **GCC or Clang compiler** installed on your system path.
* **Make utility** installed.

### Execution Command
Open your terminal inside the repository root directory and run the compilation layer:
```bash
make
```
This instantly generates a high-speed library file (`libubridge.so` on Linux, `libubridge.dylib` on macOS, or `libubridge.dll` on Windows) which handles high-velocity data parsing across language runtimes.

---

## 🧬 Core API Engine Interface Mapping

Your library exposes raw memory doors via the standard C Binary Interface. Developers interact with the data node lifecycle using these core methods:

* **`u_create(uint8_t type)`**: Allocates an isolated, type-specific data node block straight onto the system heap.
* **`u_int(UNode* node, int64_t val)`**: Formats and locks a 64-bit integer into a protected system byte structure.
* **`u_float(UNode* node, double val)`**: Normalizes decimal fractions, neutralizing computer-level float inaccuracies down to deterministic parameters.
* **`u_str(UNode* node, const char* val)`**: Dynamically maps plain text layers into compressed byte buffers.
* **`u_array(UNode* arr_node, UNode* item_node)`**: Appends data nodes together to build deep collection arrays.
* **`u_object(UNode* obj_node, const char* key, UNode* val_node)`**: Lexicographically structures key-value dictionary bindings.
* **`u_process(UNode* root)`**: Encodes the structural object graph into an optimized format featuring tamper protection.
* **`u_free(UNode* root)`**: Reclaims memory blocks to eliminate RAM leaks and bloat.

---

## 💻 Language Execution Blueprints

Developers can seamlessly open the core engine gateway from any programming language environment using native interop frameworks:

### 1. Python (via `ctypes`)
```python
import ctypes

lib = ctypes.CDLL('./libubridge.so')
lib.u_create.restype = ctypes.c_void_p
lib.u_process.restype = ctypes.c_char_p

# Create float node and process payload safely
node = lib.u_create(2)  # Type U_FLOAT = 2
lib.u_float(ctypes.c_void_p(node), ctypes.c_double(0.1 + 0.2))
print(lib.u_process(ctypes.c_void_p(node)).decode())
lib.u_free(ctypes.c_void_p(node))
```

### 2. Node.js / TypeScript (via `ffi-napi`)
```javascript
const ffi = require('ffi-napi');

const lib = ffi.Library('./libubridge.so', {
  'u_create': ['pointer', ['uint8']],
  'u_float': ['void', ['pointer', 'double']],
  'u_process': ['string', ['pointer']],
  'u_free': ['void', ['pointer']]
});

const node = lib.u_create(2);
lib.u_float(node, 0.1 + 0.2);
console.log(lib.u_process(node));
lib.u_free(node);
```

### 3. Go (via Native Cgo Integration)
```go
package main
/*
#cgo LDFLAGS: -L. -lubridge
#include "ubridge.h"
*/
import "C"
import "fmt"

func main() {
node := C.u_create(2)
C.u_float(node, C.double(0.1+0.2))
fmt.Println(C.GoString(C.u_process(node)))
C.u_free(node)
}
```

### 4. Rust (via Foreign Function Interface)
```rust
use std::ffi::{c_char, c_void, CStr};

#[link(name = "ubridge")]
extern "C" {
    fn u_create(t: u8) -> *mut c_void;
    fn u_float(node: *mut c_void, val: f64);
    fn u_process(node: *mut c_void) -> *const c_char;
    fn u_free(node: *mut c_void);
}

fn main() {
    unsafe {
        let node = u_create(2);
        u_float(node, 0.1 + 0.2);
        let res = CStr::from_ptr(u_process(node)).to_str().unwrap();
        println!("{}", res);
        u_free(node);
    }
}
```

### 5. C# (.NET via `DllImport` P/Invoke)
```csharp
using System;
using System.Runtime.InteropServices;

public class Program {
    [DllImport("libubridge.so", CallingConvention = CallingConvention.Cdecl)]
    private static extern IntPtr u_create(byte type);

    [DllImport("libubridge.so", CallingConvention = CallingConvention.Cdecl)]
    private static extern void u_float(IntPtr node, double val);

    [DllImport("libubridge.so", CallingConvention = CallingConvention.Cdecl)]
    private static extern IntPtr u_process(IntPtr node);

    [DllImport("libubridge.so", CallingConvention = CallingConvention.Cdecl)]
    private static extern void u_free(IntPtr node);

    public static void Main() {
        IntPtr node = u_create(2);
        u_float(node, 0.1 + 0.2);
        string output = Marshal.PtrToStringAnsi(u_process(node));
        Console.WriteLine(output);
        u_free(node);
    }
}
```

### 6. Java (via Project Panama Foreign Function API)
```java
import java.lang.foreign.*;
import java.lang.invoke.MethodHandle;

public class UBridgeJava {
    public static void main(String[] args) throws Throwable {
        SymbolLookup lookup = SymbolLookup.libraryLookup("libubridge.so", Arena.global());
        Linker linker = Linker.nativeLinker();

        MethodHandle uCreate = linker.downcallHandle(lookup.find("u_create").get(), FunctionDescriptor.of(ValueLayout.ADDRESS, ValueLayout.JAVA_BYTE));
        MethodHandle uFloat = linker.downcallHandle(lookup.find("u_float").get(), FunctionDescriptor.ofVoid(ValueLayout.ADDRESS, ValueLayout.JAVA_DOUBLE));
        MethodHandle uProcess = linker.downcallHandle(lookup.find("u_process").get(), FunctionDescriptor.of(ValueLayout.ADDRESS, ValueLayout.ADDRESS));
        MethodHandle uFree = linker.downcallHandle(lookup.find("u_free").get(), FunctionDescriptor.ofVoid(ValueLayout.ADDRESS));

        MemorySegment node = (MemorySegment) uCreate.invokeExact((byte) 2);
        uFloat.invokeExact(node, 0.1 + 0.2);
        MemorySegment resPtr = (MemorySegment) uProcess.invokeExact(node);
        System.out.println(resPtr.reinterpret(Long.MAX_VALUE).getString(0));
        uFree.invokeExact(node);
    }
}
```

### 7. C++ (via Native Linkage)
```cpp
#include "ubridge.h"
#include <iostream>

int main() {
    UNode* node = u_create(2);
    u_float(node, 0.1 + 0.2);
    std::cout << u_process(node) << std::endl;
    u_free(node);
    return 0;
}
```
