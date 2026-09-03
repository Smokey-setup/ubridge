# ubridge
A zero-dependency, ultra-performance cross-language data serialization bridge solving IEEE 754 drift and structural engine bugs natively via raw C-ABI memory routing.


# u-bridge: The Universal Data Engine Doorway

An open-source, zero-dependency cross-language processing core. This framework resolves the historical IEEE 754 float drift bugs and structural processing disparities by leveraging pure shared-memory pointers.

## Quick-Start Build Execution
```bash
make
```

## Universal Language Integration Formats

### 1. Python Gateway Integration
```python
import ctypes

lib = ctypes.CDLL('./libubridge.so')
lib.u_create.restype = ctypes.c_void_p
lib.u_process.restype = ctypes.c_char_p

# Access core door using clean pointer streaming layers
node = lib.u_create(2) # Type U_FLOAT
lib.u_float(ctypes.c_void_p(node), ctypes.c_double(0.1 + 0.2))
print(lib.u_process(ctypes.c_void_p(node)).decode())
```

### 2. Node.js Gateway Integration
```javascript
const ffi = require('ffi-napi');

const lib = ffi.Library('./libubridge.so', {
  'u_create': ['pointer', ['uint8']],
  'u_float': ['void', ['pointer', 'double']],
  'u_process': ['string', ['pointer']]
});

const node = lib.u_create(2);
lib.u_float(node, 0.1 + 0.2);
console.log(lib.u_process(node));
```
