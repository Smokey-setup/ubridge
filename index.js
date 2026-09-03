const ffi = require('ffi-napi');
const path = require('path');

const libPath = path.join(__dirname, 'libubridge.so');

const lib = ffi.Library(libPath, {
  'ub_create': ['pointer', ['uint8']],
  'ub_float': ['void', ['pointer', 'double']],
  'ub_process': ['string', ['pointer']],
  'ub_free': ['void', ['pointer']]
});

module.exports = lib;
