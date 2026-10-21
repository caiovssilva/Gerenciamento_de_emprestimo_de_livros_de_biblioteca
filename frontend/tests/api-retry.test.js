const assert = require("assert");
const fs = require("fs");
const vm = require("vm");
const path = require("path");

const calls = [];
const errors = [];
const responses = [
  { ok: false, status: 502, body: JSON.stringify({ error: "Bad Gateway" }) },
  { ok: true, status: 200, body: JSON.stringify({ primary: "BOOK-1", type: "book" }) },
];

const context = {
  window: { location: { origin: "https://library.example" } },
  fetch: async (url, options) => {
    calls.push({ url, options });
    const response = responses.shift();
    return {
      ok: response.ok,
      status: response.status,
      text: async () => response.body,
    };
  },
  setTimeout: callback => {
    callback();
    return 0;
  },
  console: { error: (...args) => errors.push(args) },
};

vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(__dirname, "../assets/js/api.js"), "utf8"), context);

(async () => {
  const result = await vm.runInContext('API.qr.decode("image-data")', context);

  assert.strictEqual(result.primary, "BOOK-1");
  assert.strictEqual(calls.length, 2, "A leitura deve ser repetida uma vez após erro 502");
  assert.ok(calls.every(call => call.url === "https://library.example/api/qr/decode"));
  assert.deepStrictEqual(errors, [], "Falha transitória recuperada não deve ser registrada como erro final");
  console.log("api retry test passed");
})().catch(error => {
  console.error(error);
  process.exit(1);
});
