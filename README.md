```bash
cat << 'EOF' > README.md
# ubridge

> A low-level, cross-language data serialization and precision bridge designed to eliminate floating-point drift and standardize data exchange between Node.js, Python, Rust, Go, Java, C#, and native environments via a unified C-ABI.

---

## The Story: The Floating-Point Nightmare

Every backend engineer, financial developer, or systems architect eventually hits the same quiet wall: **floating-point math**.

You perform a precise calculation in a Node.js microservice—handling transaction fees, crypto balances, or telemetry coordinates—serialize it to JSON, and pass it to a Python data analytics pipeline or a Go background worker. Suddenly, `0.3` becomes `0.30000000000000004`. 

Standard IEEE 754 double-precision floating-point arithmetic is a marvel of hardware optimization, but it is fundamentally unsuited for deterministic business logic, financial ledgers, or cross-language data parity. Rounding errors accumulate silently across different language runtimes, leading to desynced states, audit failures, and silent data corruption.

Existing solutions usually mean dragging massive, heavy serialization frameworks into your stack, writing custom parsers for every microservice boundary, or accepting subtle cross-language discrepancies.

**I built `ubridge` to solve this once and for all.**

Instead of relying on fragile standard floats, `ubridge` treats numbers under the hood as **scaled 64-bit fixed-point integers** (`U_SCALE_FACTOR = 100,000,000`). It packs data into a unified, lightweight Abstract Syntax Tree (AST) implemented in bare-metal C, and exposes it natively to *any* programming language through a stable C-ABI. What you encode on one side is precisely what you decode on the other—across any operating system, compiler, or runtime.

---

## Why Use Ubridge?

* **Zero Floating-Point Drift:** By shifting decimals into predictable integer multipliers internally (`145.75` becomes `14575000000`), calculations and serializations remain completely deterministic.
* **Universal Language Interoperability:** Written in strict ISO C11. Because it compiles down to a clean shared library (`.so`, `.dylib`, or `.dll`), any language with a Foreign Function Interface (FFI) can bind to it directly.
* **Zero-Leak Memory Architecture:** Native bindings implement advanced lifecycle safeguards (V8 `FinalizationRegistry`, Python `Context Managers`), ensuring that C-heap allocations are automatically cleaned up.
* **Automatic Object Translation:** You don't have to build C-nodes manually. Pass any complex, nested dictionary, list, or JSON object directly into the wrappers, and it recursively maps everything into native structures.

---

## How Other Languages Communicate with Ubridge

Because `ubridge` exposes a pure C Application Binary Interface (C-ABI) wrapped by `ubridge.h`, **any modern programming language** can load the shared library and execute its functions directly. 

Here is how different ecosystems hook into `ubridge`:

### 1. Python (via `ctypes`)
Python loads the library using `ctypes`, mapping function signatures directly to memory pointers. The high-level `ubridge` package wraps this with context managers for automated cleanup:
```python
from ubridge import UBridge

with UBridge.from_py({"user": "Alice", "balance": 1450.75}) as root:
    print(root.process())

```
### 2. JavaScript / TypeScript (via ffi-napi)
Node.js interacts with the shared library through FFI bindings. The @set-up/ubridge wrapper maps JavaScript objects into native C memory trees safely:
```javascript
const { UBridge } = require('@set-up/ubridge');

const root = UBridge.fromJS({ user: "Alice", balance: 1450.75 });
console.log(root.process());
root.free();

```
### 3. Rust (via std::ffi or libloading)
Rust can bind directly to the shared library by declaring external C functions:
```rust
use std.os.raw::{c_char, c_void};

#[link(name = "ubridge")]
extern "C" {
    fn ub_create(node_type: u8) -> *mut c_void;
    fn ub_free(root: *mut c_void);
}

fn main() {
    unsafe {
        let node = ub_create(1); // U_INT
        ub_free(node);
    }
}

```
### 4. Go / Golang (via cgo)
Go can consume ubridge natively by importing C and including the header file directly in comments:
```go
package main

/*
#cgo LDFLAGS: -L. -lubridge
#include "ubridge.h"
*/
import "C"

func main() {
    node := C.ub_create(C.U_INT)
    C.ub_free(node)
}

```
### 5. C# / .NET (via DllImport)
C# handles native interop seamlessly using Platform Invoke (P/Invoke):
```csharp
using System;
using System.Runtime.InteropServices;

class Program {
    [DllImport("ubridge.dll", CallingConvention = CallingConvention.Cdecl)]
    static extern IntPtr ub_create(byte type);

    [DllImport("ubridge.dll", CallingConvention = CallingConvention.Cdecl)]
    static extern void ub_free(IntPtr root);

    static void Main() {
        IntPtr node = ub_create(1);
        ub_free(node);
    }
}

```
### 6. Java (via JNA - Java Native Access)
Java can load the library without writing custom JNI boilerplate by using JNA interface mapping:
```java
import com.sun.jna.Library;
import com.sun.jna.Native;
import com.sun.jna.Pointer;

public interface UBridgeLib extends Library {
    UBridgeLib INSTANCE = (UBridgeLib) Native.load("ubridge", UBridgeLib.class);

    Pointer ub_create(byte type);
    void ub_free(Pointer root);
}

```
## Data Types (TYPES)
| ID | Identifier | Description |
|---|---|---|
| 0 | U_NULL | Represents a null or unassigned value. |
| 1 | U_INT | 64-bit signed integer. |
| 2 | U_FLOAT | Fixed-point scaled floating-point value. |
| 3 | U_STRING | Base64-packed safe string payload. |
| 4 | U_BOOL | Boolean value (1 for true, 0 for false). |
| 5 | U_ARRAY | Ordered list of child nodes. |
| 6 | U_OBJECT | Key-value dictionary with deterministic sorting. |
## Core C Function Reference
 * ub_create(uint8_t type)
   * **What it does:** Allocates and initializes a new UNode on the C heap of the specified type. Returns a raw memory pointer.
 * ub_int(UNode* node, int64_t val)
   * **What it does:** Assigns a 64-bit integer value to the node with network/host byte order safety.
 * ub_float(UNode* node, double val)
   * **What it does:** Captures a double precision float, validates against NaN/Infinity, scales it against U_SCALE_FACTOR, and stores it as a fixed-point integer.
 * ub_str(UNode* node, const char* val)
   * **What it does:** Duplicates a string safely into the node's internal memory buffer.
 * ub_array(UNode* arr_node, UNode* item_node)
   * **What it does:** Dynamically resizes the parent array's buffer and appends the child node pointer.
 * ub_object(UNode* obj_node, const char* key, UNode* val_node)
   * **What it does:** Binds a string key and a value node to a parent object with dynamic memory allocation.
 * ub_process(UNode* root)
   * **What it does:** Recursively serializes the AST into the ubridge string protocol, appends an FNV-1a cryptographic integrity tag (SIG:...), and returns a newly allocated string pointer.
 * ub_free(UNode* root)
   * **What it does:** Safely walks the entire node graph (handling circular references and loops) and deallocates all memory blocks from the C heap.
 * ub_string_free(char* ptr)
   * **What it does:** Deallocates string pointers returned by ub_process to prevent cross-language memory leaks.
## Building from Source
To compile the shared library for your current host architecture:
```bash

# Compile the shared library (libubridge.so, .dylib, or ubridge.dll)
make

```
