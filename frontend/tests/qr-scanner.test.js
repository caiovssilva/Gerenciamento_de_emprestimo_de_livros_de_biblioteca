const assert = require('assert');
const fs = require('fs');
const vm = require('vm');
const path = require('path');

class FakeElement {
  constructor(tagName = 'div', id = '') {
    this.tagName = tagName.toUpperCase();
    this.id = id;
    this.innerHTML = '';
    this.value = '';
    this.style = {};
    this.children = [];
    this.listeners = {};
    this.className = '';
    this.play = async () => {};
    this.classList = {
      add: () => {},
      remove: () => {},
      contains: () => false,
    };
    this.dataset = {};
    this._lookup = {};
    this.readyState = 2;
    this.videoWidth = 640;
    this.videoHeight = 480;
    this.getContext = () => ({
      drawImage: () => {},
      getImageData: () => ({ data: new Uint8ClampedArray(640 * 480 * 4), width: 640, height: 480 }),
    });
  }

  appendChild(child) {
    this.children.push(child);
    return child;
  }

  remove() {
    this.removed = true;
  }

  addEventListener(type, fn) {
    this.listeners[type] = this.listeners[type] || [];
    this.listeners[type].push(fn);
  }

  dispatchEvent(event) {
    (this.listeners[event.type] || []).forEach((fn) => fn(event));
  }

  querySelector(selector) {
    if (selector.startsWith('#')) {
      const key = selector.slice(1);
      if (!this._lookup[key]) this._lookup[key] = new FakeElement('div', key);
      return this._lookup[key];
    }
    if (selector.startsWith('.')) {
      const key = selector.slice(1);
      if (!this._lookup[key]) this._lookup[key] = new FakeElement('button');
      this._lookup[key].className = key;
      return this._lookup[key];
    }
    return null;
  }
}

const documentStub = {
  body: new FakeElement('body', 'body'),
  createElement(tagName) {
    return new FakeElement(tagName);
  },
  getElementById(id) {
    return this._elements?.[id] || null;
  },
  addEventListener() {},
  removeEventListener() {},
  _elements: {},
};

const utilsStub = {
  toast() {},
};

const windowStub = {
  jsQR: () => ({ data: 'ABC123' }),
};

const focusApplications = [];
const videoTrack = {
  getCapabilities: () => ({ focusMode: ['continuous'] }),
  applyConstraints: async (constraints) => {
    focusApplications.push(constraints);
  },
  stop: () => {},
};

const navigatorStub = {
  mediaDevices: {
    getUserMedia: async () => ({
      getTracks: () => [videoTrack],
      getVideoTracks: () => [videoTrack],
    }),
    enumerateDevices: async () => [],
  },
};

const context = {
  window: windowStub,
  document: documentStub,
  navigator: navigatorStub,
  Utils: utilsStub,
  console,
  setInterval: (fn) => {
    fn();
    return 1;
  },
  clearInterval: () => {},
  setTimeout: () => 1,
  clearTimeout: () => {},
};
context.window.window = windowStub;
context.window.document = documentStub;
context.window.navigator = navigatorStub;
context.global = context;
context.globalThis = context;

const source = fs.readFileSync(path.join(__dirname, '../assets/js/qr-scanner.js'), 'utf8');
vm.createContext(context);
vm.runInContext(source, context);

(async () => {
  let called = false;
  await context.window.QRScanner.start(null, (result) => {
    called = true;
    assert.strictEqual(result.primary, 'ABC123');
  });

  assert.strictEqual(called, true, 'O callback do scanner deveria ser executado após ler o QR');
  assert.strictEqual(focusApplications.length, 1, 'O scanner deveria tentar configurar o foco uma vez');
  assert.strictEqual(
    focusApplications[0].advanced[0].focusMode,
    'continuous',
    'O scanner deveria aplicar foco contínuo quando a câmera o anuncia',
  );
  console.log('qr-scanner callback test passed');
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
