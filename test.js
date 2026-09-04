const assert = require("assert");
const ubridge = require("./index.js");

function expectThrow(fn, message) {
  assert.throws(fn, message);
}

function test(name, fn) {
  try {
    fn();
    console.log(`PASS  ${name}`);
  } catch (error) {
    console.error(`FAIL  ${name}`);
    throw error;
  }
}

console.log("uBridge native integration tests");
console.log("================================");

test("module loads", () => {
  assert.ok(ubridge);
});

test("integer serialization", () => {
  const value = ubridge.fromJS(123);
  const output = value.process();

  assert.strictEqual(typeof output, "string");
  assert.ok(output.startsWith("UB1;"));
  assert.ok(output.includes("123"));
});

test("negative integer serialization", () => {
  const value = ubridge.fromJS(-987654321);
  const output = value.process();

  assert.ok(output.includes("-987654321"));
});

test("large integer uses exact representation", () => {
  const value = ubridge.fromJS(9007199254740991n);
  const output = value.process();

  assert.ok(output.includes("9007199254740991"));
});

test("large negative integer uses exact representation", () => {
  const value = ubridge.fromJS(-9007199254740991n);
  const output = value.process();

  assert.ok(output.includes("-9007199254740991"));
});

test("unsafe JavaScript integer is rejected", () => {
  expectThrow(
    () => ubridge.fromJS(9007199254740992),
    /safe|integer|BigInt/i
  );
});

test("non-finite number is rejected", () => {
  expectThrow(
    () => ubridge.fromJS(Infinity),
    /finite|number/i
  );

  expectThrow(
    () => ubridge.fromJS(NaN),
    /finite|number/i
  );
});

test("string serialization", () => {
  const value = ubridge.fromJS("hello uBridge");
  const output = value.process();

  assert.ok(output.includes("P:13:aGVsbG8gdUJyaWRnZQ=="));
});

test("embedded NUL string is rejected", () => {
  expectThrow(
    () => ubridge.fromJS("hello\0world"),
    /NUL|null|invalid/i
  );
});

test("boolean serialization", () => {
  const trueValue = ubridge.fromJS(true);
  const falseValue = ubridge.fromJS(false);

  assert.ok(trueValue.process().includes("true"));
  assert.ok(falseValue.process().includes("false"));
});

test("array serialization", () => {
  const value = ubridge.fromJS([
    1,
    2,
    3,
    "four",
    true
  ]);

  const output = value.process();

  assert.ok(output.includes("1"));
  assert.ok(output.includes("2"));
  assert.ok(output.includes("3"));
  assert.ok(output.includes("four"));
  assert.ok(output.includes("true"));
});

test("object serialization", () => {
  const value = ubridge.fromJS({
    name: "uBridge",
    version: 2,
    active: true
  });

  const output = value.process();

  assert.ok(output.includes("name"));
  assert.ok(output.includes("uBridge"));
  assert.ok(output.includes("version"));
  assert.ok(output.includes("2"));
  assert.ok(output.includes("active"));
  assert.ok(output.includes("true"));
});

test("nested structures", () => {
  const value = ubridge.fromJS({
    user: {
      name: "test",
      scores: [10, 20, 30]
    },
    enabled: true
  });

  const output = value.process();

  assert.ok(output.includes("user"));
  assert.ok(output.includes("name"));
  assert.ok(output.includes("scores"));
  assert.ok(output.includes("30"));
});

test("deterministic object serialization", () => {
  const first = ubridge.fromJS({
    z: 1,
    a: 2,
    m: 3
  });

  const second = ubridge.fromJS({
    m: 3,
    z: 1,
    a: 2
  });

  assert.strictEqual(first.process(), second.process());
});

test("null serialization", () => {
  const value = ubridge.fromJS(null);
  const output = value.process();

  assert.ok(output.includes("NULL") || output.includes("null"));
});

test("cyclic object serialization", () => {
  const value = {};
  value.self = value;

  const root = ubridge.fromJS(value);
  const output = root.process();

  assert.strictEqual(typeof output, "string");
  assert.ok(output.startsWith("UB1;"));
});

test("shared references serialize without crashing", () => {
  const shared = {
    value: 42
  };

  const value = ubridge.fromJS({
    first: shared,
    second: shared
  });

  const output = value.process();

  assert.strictEqual(typeof output, "string");
  assert.ok(output.includes("42"));
});

test("deep structure does not crash the process", () => {
  let value = 0;

  for (let i = 0; i < 100; i += 1) {
    value = {
      next: value
    };
  }

  const root = ubridge.fromJS(value);
  const output = root.process();

  assert.strictEqual(typeof output, "string");
});

test("unsupported values are rejected", () => {
  expectThrow(
    () => ubridge.fromJS(() => {}),
    /unsupported|function|type/i
  );
});

test("repeated processing is deterministic", () => {
  const value = ubridge.fromJS({
    alpha: 123,
    beta: "hello",
    gamma: [1, 2, 3]
  });

  const first = value.process();
  const second = value.process();

  assert.strictEqual(first, second);
});

test("native graph can be explicitly freed", () => {
  const value = ubridge.fromJS({
    nested: {
      array: [1, 2, 3]
    }
  });

  assert.doesNotThrow(() => value.free());
});

console.log("================================");
console.log("All uBridge tests passed.");
