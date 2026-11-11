const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const listeners = {};
const elements = new Map();

function makeClassList() {
  const values = new Set();
  return {
    add: (value) => values.add(value),
    remove: (value) => values.delete(value),
    toggle: (value, force) => {
      if (force === undefined ? !values.has(value) : force) values.add(value);
      else values.delete(value);
    },
    contains: (value) => values.has(value),
  };
}

function makeElement(id, options = {}) {
  const attributes = new Map();
  const eventHandlers = new Map();
  const element = {
    id,
    style: {},
    classList: makeClassList(),
    children: [],
    focusables: options.focusables || [],
    inert: false,
    isConnected: true,
    cssZIndex: options.cssZIndex || '100',
    parentOverlay: null,
    getAttribute: (name) => attributes.has(name) ? attributes.get(name) : null,
    setAttribute: (name, value) => attributes.set(name, String(value)),
    removeAttribute: (name) => attributes.delete(name),
    hasAttribute: (name) => attributes.has(name),
    querySelector: (selector) => selector === '.modal' ? element.dialog
      : selector === 'h2' ? element.heading : null,
    querySelectorAll: () => element.focusables,
    closest: (selector) => selector === '.overlay' ? element.parentOverlay : null,
    contains: (candidate) => candidate === element || element.focusables.includes(candidate),
    focus: () => { document.activeElement = element; },
    addEventListener: (name, handler) => {
      if (!eventHandlers.has(name)) eventHandlers.set(name, []);
      eventHandlers.get(name).push(handler);
    },
    removeEventListener: (name, handler) => {
      eventHandlers.set(name, (eventHandlers.get(name) || []).filter((item) => item !== handler));
    },
    dispatch: (name, event = {}) => {
      (eventHandlers.get(name) || []).forEach((handler) => handler({ target: element, ...event }));
    },
    dispatchEvent: (event) => {
      element.dispatch(event.type, event);
      return true;
    },
    remove: () => {
      element.isConnected = false;
      if (element.parentOverlay) {
        body.children = body.children.filter((child) => child !== element);
      }
    },
  };
  elements.set(id, element);
  return element;
}

const body = makeElement('body');
body.children = [];
const document = {
  body,
  activeElement: null,
  addEventListener: (name, handler) => { listeners[name] = handler; },
  removeEventListener: (name, handler) => {
    if (listeners[name] === handler) delete listeners[name];
  },
  getElementById: (id) => elements.get(id) || null,
  createElement: (tag) => {
    const overlay = makeElement(`dialog-${elements.size}`);
    overlay.tagName = tag.toUpperCase();
    overlay.classList.add('overlay');
    overlay.parentOverlay = overlay;
    overlay.querySelector = (selector) => overlay.selectors?.[selector] || null;
    overlay.querySelectorAll = () => [];
    overlay.selectors = {};
    overlay.remove = () => {
      overlay.isConnected = false;
      body.children = body.children.filter((child) => child !== overlay);
    };
    Object.defineProperty(overlay, 'innerHTML', {
      set: () => {
        const modal = makeElement(`${overlay.id}-modal`);
        const heading = makeElement(`${overlay.id}-heading`);
        const message = makeElement(`${overlay.id}-message`);
        const cancel = makeElement(`${overlay.id}-cancel`);
        const confirm = makeElement(`${overlay.id}-confirm`);
        const close = makeElement(`${overlay.id}-close`);
        const focusables = [close, cancel, confirm];
        modal.focusables = focusables;
        modal.parentOverlay = overlay;
        modal.heading = heading;
        modal.querySelector = (selector) => selector === 'h2' ? heading : null;
        modal.setAttribute = () => {};
        overlay.selectors = {
          '.modal': modal,
          '.modal-head h2': heading,
          '.app-dialog-message': message,
          '.app-dialog-cancel': cancel,
          '.app-dialog-confirm': confirm,
          '.app-dialog-close': close,
        };
        overlay.dialogControls = { cancel, confirm, close };
      },
    });
    return overlay;
  },
  querySelectorAll: (selector) => selector === '.overlay.open'
    ? body.children.filter((child) => child.classList.contains('overlay') && child.classList.contains('open'))
    : [],
};
body.appendChild = (element) => {
  element.parentNode = body;
  element.parentOverlay = element;
  element.isConnected = true;
  body.children.push(element);
  elements.set(element.id, element);
};
const trigger = makeElement('trigger');
const app = makeElement('app');
const studentOverlay = makeElement('modal-student-history', { cssZIndex: '100' });
const studentDialog = makeElement('student-dialog');
const historyHeading = { id: 'history-title' };
const historyClose = makeElement('history-close');
const historyAction = makeElement('history-action');
studentDialog.focusables = [historyClose, historyAction];
studentDialog.heading = historyHeading;
studentDialog.parentOverlay = studentOverlay;
studentOverlay.dialog = studentDialog;
studentOverlay.children = [studentDialog];
studentOverlay.classList.add('overlay');

const nestedOverlay = makeElement('modal-devolution', { cssZIndex: '100' });
const nestedDialog = makeElement('devolution-dialog');
const nestedClose = makeElement('devolution-close');
nestedDialog.focusables = [nestedClose];
nestedDialog.parentOverlay = nestedOverlay;
nestedOverlay.dialog = nestedDialog;
nestedOverlay.classList.add('overlay');

body.children = [app, studentOverlay, nestedOverlay];
document.activeElement = trigger;

const context = {
  document,
  Event: class Event {
    constructor(type) { this.type = type; }
  },
  getComputedStyle: (element) => ({ zIndex: element.style.zIndex || element.cssZIndex }),
};
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(__dirname, '../assets/js/utils.js'), 'utf8'), context);

const utils = vm.runInContext('Utils', context);
utils.openModal(studentOverlay.id);
assert.strictEqual(app.inert, true, 'conteúdo da aplicação fica inerte com o histórico aberto');
assert.strictEqual(app.getAttribute('aria-hidden'), 'true');
assert.strictEqual(document.activeElement, historyClose, 'foco entra no modal aberto');
assert.strictEqual(studentDialog.getAttribute('aria-modal'), 'true');

let tabPrevented = false;
document.activeElement = historyAction;
listeners.keydown({ key: 'Tab', shiftKey: false, preventDefault: () => { tabPrevented = true; } });
assert.strictEqual(tabPrevented, true);
assert.strictEqual(document.activeElement, historyClose, 'Tab não sai do modal');
tabPrevented = false;
listeners.keydown({ key: 'Tab', shiftKey: true, preventDefault: () => { tabPrevented = true; } });
assert.strictEqual(tabPrevented, true);
assert.strictEqual(document.activeElement, historyAction, 'Shift+Tab também não sai do modal');

document.activeElement = historyClose;
utils.openModal(nestedOverlay.id);
assert.strictEqual(studentOverlay.inert, true, 'modal anterior fica inerte quando há um diálogo aninhado');
assert.strictEqual(nestedOverlay.inert, false);
assert.strictEqual(document.activeElement, nestedClose);

let prevented = false;
listeners.keydown({ key: 'Escape', preventDefault: () => { prevented = true; } });
assert.strictEqual(prevented, true);
assert.strictEqual(nestedOverlay.classList.contains('open'), false, 'Escape fecha apenas o diálogo superior');
assert.strictEqual(studentOverlay.classList.contains('open'), true);
assert.strictEqual(studentOverlay.inert, false);
assert.strictEqual(document.activeElement, historyClose, 'o foco é restaurado ao diálogo anterior');

utils.closeModal(studentOverlay.id);
assert.strictEqual(app.inert, false, 'o fundo volta a ser interativo ao fechar o histórico');
assert.strictEqual(app.getAttribute('aria-hidden'), null);
assert.strictEqual(body.classList.contains('modal-open'), false);
assert.strictEqual(document.activeElement, trigger, 'o foco volta ao elemento que abriu o modal');

let confirmedAction = false;
document.activeElement = trigger;
const confirmation = utils.confirmDialog('Sair do sistema?', { confirmText: 'Sim, sair' });
const confirmationOverlay = body.children.find((child) => child.dialogControls);
confirmationOverlay.dialogControls.confirm.dispatch('click');
confirmation.then((confirmed) => {
  if (confirmed) confirmedAction = true;
});
setImmediate(async () => {
  assert.strictEqual(await confirmation, true, 'o botão de confirmação retorna a escolha afirmativa');
  assert.strictEqual(confirmedAction, true, 'a ação afirmativa pode ser executada após confirmar');
  assert.strictEqual(confirmationOverlay.isConnected, false, 'o diálogo some imediatamente após confirmar');
  assert.strictEqual(body.classList.contains('modal-open'), false, 'a tela volta a ficar utilizável após confirmar');

  const cancellation = utils.confirmDialog('Excluir registro?');
  const cancellationOverlay = body.children.find((child) => child.dialogControls);
  cancellationOverlay.dialogControls.cancel.dispatch('click');
  assert.strictEqual(await cancellation, false, 'o botão de cancelar retorna a escolha negativa');
  assert.strictEqual(cancellationOverlay.isConnected, false, 'o diálogo também some ao cancelar');
  assert.strictEqual(body.classList.contains('modal-open'), false, 'a tela volta a ficar utilizável após cancelar');
  console.log('modal interaction lock, nested dialogs, keyboard, focus restoration and confirmation cleanup');
});
