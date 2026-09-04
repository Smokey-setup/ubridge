'use strict';

const ffi = require('@napi-ffi/ffi-napi');
const path = require('path');
const os = require('os');
const fs = require('fs');

/* =========================
 * NATIVE LIBRARY RESOLUTION
 * ========================= */
const prefix = os.platform() === 'win32' ? '' : 'lib';
const ext = os.platform() === 'win32' ? '.dll' : os.platform() === 'darwin' ? '.dylib' : '.so';
const libPath = path.join(__dirname, `${prefix}ubridge${ext}`);

if (!fs.existsSync(libPath)) {
  throw new Error(
    `[@set-up/ubridge] FATAL: Native library not found at ${libPath}. ` +
    `Ensure it is compiled for ${os.platform()}-${os.arch()}.`
  );
}

/* ===============
 * NATIVE FFI ABI
 * Must remain exactly synchronized with ubridge.h / ubridge.c.
 * =============== */
const native = ffi.Library(libPath, {
  ub_create: ['pointer', ['uint8']],
  ub_int: ['void', ['pointer', 'int64']],
  ub_float: ['void', ['pointer', 'double']],
  ub_str: ['void', ['pointer', 'string']],
  ub_array: ['void', ['pointer', 'pointer']],
  ub_object: ['void', ['pointer', 'string', 'pointer']],
  /*
   * C returns an allocated char*.
   * JS reads it and MUST release it with ub_string_free().
   */
  ub_process: ['pointer', ['pointer']],
  ub_free: ['void', ['pointer']],
  ub_string_free: ['void', ['pointer']],
  ub_scientific: ['void', ['pointer', 'int64', 'int32']]
});

/* =============================
 * TYPE IDENTIFIERS
 * ============================= */
const TYPES = Object.freeze({
  NULL: 0,
  INT: 1,
  FLOAT: 2,
  STRING: 3,
  BOOL: 4,
  ARRAY: 5,
  OBJECT: 6
});

/* =================
 * PRECISION MODES
 * ================= */
const MODES = Object.freeze({
  FIXED: 1,
  SCIENTIFIC: 2
});

/* ===========
 * CONSTANTS
 * =========== */
const INT64_MIN = -(2n ** 63n);
const INT64_MAX = (2n ** 63n) - 1n;
const INT32_MIN = -(2 ** 31);
const INT32_MAX = (2 ** 31) - 1;

/* ==========================
 * NATIVE POINTER VALIDATION
 * ========================== */
function isValidPointer(ptr) {
  return ptr && typeof ptr.isNull === 'function' && !ptr.isNull();
}

/* ==============================
 * JS NUMBER → INT64 VALIDATION
 * ============================== */
function toInt64(value, name = 'value') {
  if (typeof value === 'bigint') {
    if (value < INT64_MIN || value > INT64_MAX) {
      throw new RangeError(`[@set-up/ubridge] ${name} is outside int64 range.`);
    }
    return value.toString();
  }
  if (typeof value !== 'number' || !Number.isFinite(value) || !Number.isInteger(value)) {
    throw new TypeError(`[@set-up/ubridge] ${name} must be an integer Number or BigInt.`);
  }
  if (!Number.isSafeInteger(value)) {
    throw new RangeError(
      `[@set-up/ubridge] ${name} exceeds JavaScript's safe integer range. Use BigInt instead.`
    );
  }
  return value;
}

/* =============================
 * JS NUMBER → INT32 VALIDATION
 * ============================= */
function toInt32(value, name = 'value') {
  if (typeof value !== 'number' || !Number.isFinite(value) || !Number.isInteger(value)) {
    throw new TypeError(`[@set-up/ubridge] ${name} must be an integer Number.`);
  }
  if (value < INT32_MIN || value > INT32_MAX) {
    throw new RangeError(`[@set-up/ubridge] ${name} is outside int32 range.`);
  }
  return value;
}

/* ============
 * GC REGISTRY
 * ============ */
const gcRegistry = new FinalizationRegistry((ptr) => {
  try {
    if (state && isValidPointer(state.ptr)) {
      native.ub_free(ptr);
      state.ptr = null;
    }
  } catch (_) {
    /* Finalizers must never allow an exception to escape. */
  }
});

/* =============
 * UBRIDGE NODE
 * ============= */
class UBridge {
  constructor(type) {
    if (!Number.isInteger(type) || type < TYPES.NULL || type > TYPES.OBJECT) {
      throw new TypeError('[@set-up/ubridge] Invalid UNode type.');
    }
    const ptr = native.ub_create(type);
    if (!isValidPointer(ptr)) {
      throw new Error('[@set-up/ubridge] Native ub_create() failed.');
    }
    this.ptr = ptr;
    this._gcState = { ptr };
    this.isFreed = false;
    this._type = type;
    gcRegistry.register(this, this._gcState, this);
  }

  get type() {
    return this._type;
  }

  /* ========================
   * INTERNAL LIFETIME CHECK
   * ======================== */
  _checkAlive() {
    if (this.isFreed || !isValidPointer(this.ptr)) {
      throw new Error('[@set-up/ubridge] Attempted to operate on a freed native UNode.');
    }
  }

  /* =======
   * INTEGER
   * ======== */
  setInt(value) {
    this._checkAlive();
    const int64 = toInt64(value, 'integer');
    native.ub_int(this.ptr, int64);
    return this;
  }

  /* =====
   * FLOAT
   * ===== */
  setFloat(value) {
    this._checkAlive();
    const number = Number(value);
    if (!Number.isFinite(number)) {
      throw new TypeError('[@set-up/ubridge] Float must be finite.');
    }
    native.ub_float(this.ptr, number);
    return this;
  }

  /* ======
   * STRING
   * ====== */
  setStr(value) {
    this._checkAlive();
    if (typeof value !== 'string') {
      value = String(value);
    }
    if (value.includes('\0')) {
      throw new TypeError('[@set-up/ubridge] String cannot contain embedded NUL bytes.');
    }
    native.ub_str(this.ptr, value);
    return this;
  }

  /* ========
   * BOOLEAN
   * ======== */
  setBool(value) {
    this._checkAlive();
    const intval = value ? 1n : 0n;
    native.ub_int(this.ptr, toInt64(intval, 'boolean'));
    return this;
  }

  /* ===============
   * SCIENTIFIC FLOAT
   * =============== */
  setScientific(coefficient, exponent) {
    this._checkAlive();
    const coeff = toInt64(coefficient, 'scientific coefficient');
    const exp = toInt32(exponent, 'scientific exponent');
    native.ub_scientific(this.ptr, coeff, exp);
    return this;
  }

  /* ======
   * ARRAY
   * ====== */
  push(itemNode) {
    this._checkAlive();
    if (!(itemNode instanceof UBridge)) {
      throw new TypeError('[@set-up/ubridge] Array item must be a UBridge node.');
    }
    itemNode._checkAlive();
    if (this.type !== undefined && this.type !== TYPES.ARRAY) {
      throw new TypeError('[@set-up/ubridge] push() requires an ARRAY node.');
    }
    native.ub_array(this.ptr, itemNode.ptr);
    /*
     * Keep the JS child alive for as long as the parent is alive.
     */
    this._retainChild(itemNode);
    return this;
  }

  /* ========
   * OBJECT
   * ======== */
  setKey(key, valNode) {
    this._checkAlive();
    if (!(valNode instanceof UBridge)) {
      throw new TypeError('[@set-up/ubridge] Object value must be a UBridge node.');
    }
    valNode._checkAlive();
    if (this.type !== undefined && this.type !== TYPES.OBJECT) {
      throw new TypeError('[@set-up/ubridge] setKey() requires an OBJECT node.');
    }
    const normalizedKey = String(key);
    native.ub_object(this.ptr, normalizedKey, valNode.ptr);
    this._retainChild(valNode);
    return this;
  }

  /* ================
   * CHILD RETENTION
   * ================ */
  _retainChild(child) {
    if (!this._children) {
      this._children = new Set();
    }
    this._children.add(child);
  }

  /* ==============
   * SERIALIZATION
   * ============== */
  process() {
    this._checkAlive();
    const resultPtr = native.ub_process(this.ptr);
    if (!isValidPointer(resultPtr)) {
      return null;
    }
    try {
      return resultPtr.readCString();
    } finally {
      native.ub_string_free(resultPtr);
    }
  }

  /* =============
   * EXPLICIT FREE
   * ============= */
  free() {
    if (this.isFreed) {
      return;
    }
    const state = this._gcState;
    this._gcState = null;
    const ptr = this.ptr;
    this.ptr = null;
    this.isFreed = true;
    gcRegistry.unregister(this);
    if (state) {
      state.ptr = null;
    }
    if (isValidPointer(ptr)) {
      native.ub_free(ptr);
    }
    /*
     * Drop JS references after native memory has been released.
     */
    if (this._children) {
      this._children.clear();
      this._children = null;
    }
  }

  /* =====================
   * JAVASCRIPT → UBRIDGE
   * ===================== */
  static fromJS(data, seen = new WeakMap()) {
    if (data === null || data === undefined) {
      return new UBridge(TYPES.NULL);
    }
    if (typeof data === 'boolean') {
      return new UBridge(TYPES.BOOL).setBool(data);
    }
    if (typeof data === 'string') {
      return new UBridge(TYPES.STRING).setStr(data);
    }
    if (typeof data === 'bigint') {
      return new UBridge(TYPES.INT).setInt(data);
    }
    if (typeof data === 'number') {
      if (!Number.isFinite(data)) {
        throw new TypeError('[@set-up/ubridge] Number must be finite.');
      }
      if (Number.isInteger(data)) {
        return new UBridge(TYPES.INT).setInt(data);
      }
      return new UBridge(TYPES.FLOAT).setFloat(data);
    }
    if (typeof data === 'object') {
      if (seen.has(data)) {
        return seen.get(data);
      }
      if (Array.isArray(data)) {
        const arrNode = new UBridge(TYPES.ARRAY);
        seen.set(data, arrNode);
        for (let i = 0; i < data.length; ++i) {
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
    throw new TypeError(`[@set-up/ubridge] Unsupported JavaScript type: ${typeof data}`);
  }
}

/* =========
 * EXPORTS
 * ========= */
module.exports = {
  UBridge,
  fromJS: (data, seen) => UBridge.fromJS(data, seen),
  TYPES,
  MODES,
  createNode: (type) => new UBridge(type),
  isUBridge: (value) => value instanceof UBridge
};
