const ffi = require('@napi-ffi/ffi-napi');
const path = require('path');
const os = require('os');
const fs = require('fs');

// 1. Fail-Safe Path Resolution
const prefix = os.platform() === 'win32' ? '' : 'lib';
const ext = os.platform() === 'win32' ? '.dll' : os.platform() === 'darwin' ? '.dylib' : '.so';
const libPath = path.join(__dirname, `${prefix}ubridge${ext}`);

if (!fs.existsSync(libPath)) {
  throw new Error(`[@set-up/ubridge] FATAL: Native library not found at ${libPath}. Ensure it is compiled for ${os.platform()}-${os.arch()}.`);
}

// 2. Bound FFI Native Library
const native = ffi.Library(libPath, {
  'ub_create': ['pointer', ['uint8']],
  'ub_int': ['void', ['pointer', 'int64']],
  'ub_float': ['void', ['pointer', 'double']],
  'ub_str': ['void', ['pointer', 'string']],
  'ub_array': ['void', ['pointer', 'pointer']],
  'ub_object': ['void', ['pointer', 'string', 'pointer']],
  // CRITICAL FIX: Return pointer, not string, to prevent malloc leaks
  'ub_process': ['pointer', ['pointer']], 
  'ub_free': ['void', ['pointer']],
  'ub_string_free': ['void', ['pointer']]
});

const TYPES = { NULL: 0, INT: 1, FLOAT: 2, STRING: 3, BOOL: 4, ARRAY: 5, OBJECT: 6 };

// 3. V8 Garbage Collection Registry
// This guarantees C-memory is freed even if the developer forgets to call .free()
const gcRegistry = new FinalizationRegistry((ptr) => {
  if (ptr && !ptr.isNull()) {
    native.ub_free(ptr);
  }
});

// 4. The Bulletproof Wrapper Class
class UBridge {
  constructor(type) {
    this.ptr = native.ub_create(type);
    this.isFreed = false;
    gcRegistry.register(this, this.ptr, this);
  }

  setInt(val) { this._checkAlive(); native.ub_int(this.ptr, Math.trunc(val)); return this; }
  setFloat(val) { this._checkAlive(); native.ub_float(this.ptr, Number(val)); return this; }
  setStr(val) { this._checkAlive(); native.ub_str(this.ptr, String(val)); return this; }
  setBool(val) { this._checkAlive(); native.ub_int(this.ptr, val ? 1 : 0); return this; }
  
  push(itemNode) { 
    this._checkAlive(); 
    native.ub_array(this.ptr, itemNode.ptr); 
    return this; 
  }
  
  setKey(key, valNode) { 
    this._checkAlive(); 
    native.ub_object(this.ptr, String(key), valNode.ptr); 
    return this; 
  }

  process() {
    this._checkAlive();
    const resPtr = native.ub_process(this.ptr);
    if (resPtr.isNull()) return null;
    
    // Safely extract the string and free the C allocation
    const resultString = resPtr.readCString();
    native.ub_string_free(resPtr);
    
    return resultString;
  }

  free() {
    if (!this.isFreed && this.ptr && !this.ptr.isNull()) {
      gcRegistry.unregister(this); // Remove from GC tracking
      native.ub_free(this.ptr);
      this.ptr = null;
      this.isFreed = true;
    }
  }

  _checkAlive() {
    if (this.isFreed || !this.ptr) {
      throw new Error("[@set-up/ubridge] Segmentation Fault Prevented: Attempted to operate on a freed native C pointer.");
    }
  }

  /**
   * Translates ANY chaotic JavaScript value (including cyclic references) 
   * into a C-native UBridge tree automatically.
   */
  static fromJS(data, seen = new WeakMap()) {
    if (data === null || data === undefined) return new UBridge(TYPES.NULL);
    
    // Handle Primitive Types
    if (typeof data === 'boolean') return new UBridge(TYPES.BOOL).setBool(data);
    if (typeof data === 'string') return new UBridge(TYPES.STRING).setStr(data);
    if (typeof data === 'number') {
      return Number.isInteger(data) 
        ? new UBridge(TYPES.INT).setInt(data) 
        : new UBridge(TYPES.FLOAT).setFloat(data);
    }

    // Cycle Detection Map for JS Objects
    if (typeof data === 'object') {
      if (seen.has(data)) return seen.get(data); // Circular reference hit!

      if (Array.isArray(data)) {
        const arrNode = new UBridge(TYPES.ARRAY);
        seen.set(data, arrNode);
        for (let i = 0; i < data.length; i++) {
          arrNode.push(UBridge.fromJS(data[i], seen));
        }
        return arrNode;
      } 
      
      const objNode = new UBridge(TYPES.OBJECT);
      seen.set(data, objNode);
      for (const key of Object.keys(data)) {
        objNode.setKey(key, UBridge.fromJS(data[key], seen));
      }
      return objNode;
    }

    // Fallback for Functions, Symbols, etc.
    return new UBridge(TYPES.NULL);
  }
}

module.exports = {
  UBridge,
  TYPES,
  // Optional: Export raw native bindings for hardcore users who want to manage pointers manually
  raw: native 
};
