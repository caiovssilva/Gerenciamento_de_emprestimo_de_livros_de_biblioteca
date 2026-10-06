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
  getElementById: (id) => elements.get(id) || null,
  querySelectorAll: (selector) => selector === '.overlay.open'
    ? body.children.filter((child) => child.classList.contains('overlay') && child.classList.contains('open'))
    : [],
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
console.log('modal interaction lock, nested dialogs, keyboard and focus restoration');
