const ffi = require('ffi-napi');
const path = require('path');
const os = require('os');

// Automatically detect host runtime environment constraints
let ext = '.so';
if (os.platform() === 'darkwin' || os.platform() === 'darwin') ext = '.dylib';
if (os.platform() === 'win32') ext = '.dll';

const libPath = path.join(__dirname, `libubridge${ext}`);

const lib = ffi.Library(libPath, {
  'ub_create': ['pointer', ['uint8']],
  'ub_int': ['void', ['pointer', 'int64']],
  'ub_float': ['void', ['pointer', 'double']],
  'ub_str': ['void', ['pointer', 'string']],
  'ub_array': ['void', ['pointer', 'pointer']],
  'ub_object': ['void', ['pointer', 'string', 'pointer']],
  'ub_process': ['string', ['pointer']],
  'ub_free': ['void', ['pointer']],
  'ub_string_free': ['void', ['pointer']]
});

module.exports = lib;
