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
    this._classes = new Set();
    this.classList = {
      add: (value) => this._classes.add(value),
      remove: (value) => this._classes.delete(value),
      contains: (value) => this._classes.has(value),
    };
    this.pause = () => { this.paused = true; };
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

const modalEvents = [];
const utilsStub = {
  toast() {},
  openModal(id) {
    modalEvents.push(`open:${id}`);
    documentStub.body.children.find((child) => child.id === id)?.classList.add('open');
  },
  closeModal(id) {
    modalEvents.push(`close:${id}`);
    const overlay = [...documentStub.body.children].reverse().find((child) => child.id === id && !child.removed);
    overlay?.classList.remove('open');
    overlay?.dispatchEvent({ type: 'modal:closed' });
  },
};

let qrValue = 'ABC123';
const windowStub = {
  jsQR: () => qrValue ? ({ data: qrValue }) : null,
};

const focusApplications = [];
let trackStopCount = 0;
let nextMediaRequest = null;
const videoTrack = {
  getCapabilities: () => ({ focusMode: ['continuous'] }),
  applyConstraints: async (constraints) => {
    focusApplications.push(constraints);
  },
  stop: () => { trackStopCount += 1; },
};

const navigatorStub = {
  mediaDevices: {
    getUserMedia: async () => nextMediaRequest || ({
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
  assert.deepStrictEqual(modalEvents, ['open:cam-overlay', 'close:cam-overlay']);
  assert.strictEqual(focusApplications.length, 1, 'O scanner deveria tentar configurar o foco uma vez');
  assert.strictEqual(
    focusApplications[0].advanced[0].focusMode,
    'continuous',
    'O scanner deveria aplicar foco contínuo quando a câmera o anuncia',
  );

  const firstOverlay = documentStub.body.children.find((child) => child.id === 'cam-overlay');
  const firstVideo = firstOverlay.querySelector('#cam-video');
  assert.strictEqual(trackStopCount, 1, 'A câmera deveria desligar após ler um código');
  assert.strictEqual(firstVideo.srcObject, null, 'O vídeo deveria soltar a stream após a leitura');

  qrValue = null;
  await context.window.QRScanner.start(null, () => {});
  const activeOverlay = [...documentStub.body.children].reverse().find((child) => child.id === 'cam-overlay' && !child.removed);
  const activeVideo = activeOverlay.querySelector('#cam-video');
  assert.ok(activeVideo.srcObject, 'A câmera deveria estar ligada antes de fechar o modal');
  utilsStub.closeModal('cam-overlay');
  assert.strictEqual(trackStopCount, 2, 'A câmera deveria desligar ao fechar o modal externamente');
  assert.strictEqual(activeVideo.srcObject, null, 'O vídeo deveria soltar a stream ao fechar o modal');

  let resolvePendingStream;
  nextMediaRequest = new Promise((resolve) => { resolvePendingStream = resolve; });
  const pendingStart = context.window.QRScanner.start(null, () => {});
  await Promise.resolve();
  const pendingOverlay = [...documentStub.body.children].reverse().find((child) => child.id === 'cam-overlay' && !child.removed);
  utilsStub.closeModal('cam-overlay');
  resolvePendingStream({
    getTracks: () => [videoTrack],
    getVideoTracks: () => [videoTrack],
  });
  await pendingStart;
  assert.strictEqual(trackStopCount, 3, 'A stream que chega depois do fechamento deveria ser parada imediatamente');
  assert.strictEqual(pendingOverlay.removed, true, 'A tela fechada não deveria ser reaberta após liberar a câmera');
  console.log('qr-scanner callback test passed');
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
