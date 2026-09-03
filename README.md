# ubridge

A zero-dependency, ultra-performance cross-language data serialization bridge solving IEEE 754 drift and structural engine bugs natively via raw C-ABI memory routing.

---

## 🛠️ How to Compile

Before your language can talk to the engine, compile the C source files into raw machine instructions.

### System Requirements
* **GCC compiler** installed.
* **Make tool** installed.

### Build Command
Run this command in your repository terminal:
```bash
make
```
This instantly builds your shared system binary code (`libubridge.so` on Linux, `libubridge.dylib` on macOS, or `libubridge.dll` on Windows).

---

## 🧬 Engine Core Blueprint

Your library exposes clear, simple doors to manage raw data structures directly inside system memory:

* **`ub_create`**: Spawns a brand-new data box on the system heap.
* **`ub_int`**: Safely packs a whole number into memory.
* **`ub_float`**: Corrects precision anomalies to keep decimals pure.
* **`ub_str`**: Converts text arrays into compressed byte blocks.
* **`ub_array`**: Links multiple memory data boxes together like a chain.
* **`ub_object`**: Creates alphabetized dictionary maps out of messy keys.
* **`ub_process`**: Finalizes data with anti-loop security and signatures.
* **`ub_free`**: Safely wipes memory blocks to avoid server RAM bloat.

---

## 💻 Language Blueprints

Choose your language engine below. Follow the human-friendly explanation to link your code directly to the hardware core.

### 1. Python (via `ctypes`)
**Human Explanation**: Python loads the binary, sets up voice channels using ctypes, builds a floating-point data box, fixes any decimal bugs, and safely clears the computer memory cache when finished.
```python
import ctypes

# Load the compiled machine binary
lib = ctypes.CDLL('./libubridge.so')
lib.ub_create.restype = ctypes.c_void_p
lib.ub_process.restype = ctypes.c_char_p

# Pass your dynamic calculations straight to the metal
node = lib.ub_create(2)  # 2 tells the engine to accept a float
lib.ub_float(ctypes.c_void_p(node), ctypes.c_double(0.1 + 0.2))

# Extract your tamper-proof text payload signature
print(lib.ub_process(ctypes.c_void_p(node)).decode())

# Clear your server memory spaces completely
lib.ub_free(ctypes.c_void_p(node))
```

### 2. Node.js / TypeScript (via `ffi-napi`)
**Human Explanation**: Node bridges your JavaScript calculations straight to the native library. It builds data packets on the fly and wipes the system heap afterwards to prevent slow performance loops.
```javascript
const ffi = require('ffi-napi');

// Declare function access channels
const lib = ffi.Library('./libubridge.so', {
  'ub_create': ['pointer', ['uint8']],
  'ub_float': ['void', ['pointer', 'double']],
  'ub_process': ['string', ['pointer']],
  'ub_free': ['void', ['pointer']]
});

// Build and process custom data tokens
const node = lib.ub_create(2);
lib.ub_float(node, 0.1 + 0.2);
console.log(lib.ub_process(node));

// Wipe memory allocations instantly
lib.ub_free(node);
```

### 3. Go (via Native Cgo Integration)
**Human Explanation**: Go uses its internal compiler rules to directly overlay parameters onto your C engine library header, processing records at hardware speeds with no web format overhead.
```go
package main
/*
#cgo LDFLAGS: -L. -lubridge
#include "ubridge.h"
*/
import "C"
import "fmt"

func main() {
// Call your core binary engine gates cleanly
node := C.ub_create(2)
C.ub_float(node, C.double(0.1+0.2))

// Convert machine memory pointers back to Go strings
fmt.Println(C.GoString(C.ub_process(node)))
C.ub_free(node)
}
```

### 4. Rust (via Foreign Function Interface)
**Human Explanation**: Rust leverages its unsafe memory block system to handshake with your C library symbols. It handles your low-level data structures with absolute performance safety.
```rust
use std::ffi::{c_char, c_void, CStr};

#[link(name = "ubridge")]
extern "C" {
    fn ub_create(t: u8) -> *mut c_void;
    fn ub_float(node: *mut c_void, val: f64);
    fn ub_process(node: *mut c_void) -> *const c_char;
    fn ub_free(node: *mut c_void);
}

fn main() {
    unsafe {
        // Run unthrottled hardware calls directly
        let node = ub_create(2);
        ub_float(node, 0.1 + 0.2);
        
        let res = CStr::from_ptr(ub_process(node)).to_str().unwrap();
        println!("{}", res);
        ub_free(node);
    }
}
```

### 5. C# (.NET via `DllImport` P/Invoke)
**Human Explanation**: C# triggers standard Windows and Linux internal system loaders to look up your engine files, map memory references, and read clean results with no cross-framework delay.
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

    public static void Main() {
        // Execute low-level library tasks via managed pointer windows
        IntPtr node = ub_create(2);
        ub_float(node, 0.1 + 0.2);
        
        string output = Marshal.PtrToStringAnsi(ub_process(node));
        Console.WriteLine(output);
        ub_free(node);
    }
}
```

### 6. Java (via Project Panama Foreign Function API)
**Human Explanation**: Java opens modern hardware avenues to directly lookup binary system addresses. It bypasses old sluggish legacy steps to read memory structures at native computer speeds.
```java
import java.lang.foreign.*;
import java.lang.invoke.MethodHandle;

public class UBridgeJava {
    public static void main(String[] args) throws Throwable {
        SymbolLookup lookup = SymbolLookup.libraryLookup("libubridge.so", Arena.global());
        Linker linker = Linker.nativeLinker();

        MethodHandle uCreate = linker.downcallHandle(lookup.find("ub_create").get(), FunctionDescriptor.of(ValueLayout.ADDRESS, ValueLayout.JAVA_BYTE));
        MethodHandle uFloat = linker.downcallHandle(lookup.find("ub_float").get(), FunctionDescriptor.ofVoid(ValueLayout.ADDRESS, ValueLayout.JAVA_DOUBLE));
        MethodHandle uProcess = linker.downcallHandle(lookup.find("ub_process").get(), FunctionDescriptor.of(ValueLayout.ADDRESS, ValueLayout.ADDRESS));
        MethodHandle uFree = linker.downcallHandle(lookup.find("ub_free").get(), FunctionDescriptor.ofVoid(ValueLayout.ADDRESS));

        // Create data box maps via hardware lookup structures
        MemorySegment node = (MemorySegment) uCreate.invokeExact((byte) 2);
        uFloat.invokeExact(node, 0.1 + 0.2);
        MemorySegment resPtr = (MemorySegment) uProcess.invokeExact(node);
        
        System.out.println(resPtr.reinterpret(Long.MAX_VALUE).getString(0));
        uFree.invokeExact(node);
    }
}
```

### 7. C++ (via Native Linkage)
**Human Explanation**: C++ imports your header file directly into its compilation cycle. It links straight to your functions without needing any interop translations or wrapper plugins.
```cpp
#include "ubridge.h"
#include <iostream>

int main() {
    // True native execution with absolute zero abstraction overhead
    UNode* node = ub_create(2);
    ub_float(node, 0.1 + 0.2);
    
    std::cout << ub_process(node) << std::endl;
    ub_free(node);
    return 0;
}
```
