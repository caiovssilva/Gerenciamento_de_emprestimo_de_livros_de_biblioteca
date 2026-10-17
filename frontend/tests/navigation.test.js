const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const loginMarkup = fs.readFileSync(path.join(__dirname, '../index.html'), 'utf8');
assert.match(loginMarkup, /id="self-service-student-card"/);
assert.match(loginMarkup, /id="self-service-books-search"/);
assert.match(loginMarkup, /id="self-service-books-list"/);
assert.match(loginMarkup, /id="self-service-history-rows"/);
assert.match(loginMarkup, /id="self-service-books-list"/);
assert.doesNotMatch(loginMarkup, /data-self-service-tab|self-service-panel-/);
assert.match(loginMarkup, /id="self-service-kiosk-status"/);
assert.match(loginMarkup, /id="self-service-scan-btn"/);
assert.match(loginMarkup, /id="self-service-exit-btn"/);
assert.match(loginMarkup, /data-page="controle" data-role="admin"/);
assert.match(loginMarkup, /id="page-controle"/);
const configPageMarkup = loginMarkup.split('id="page-config"')[1].split('<!--')[0];
assert.doesNotMatch(configPageMarkup, /self-service-setting-enabled/);
const appSource = fs.readFileSync(path.join(__dirname, '../assets/js/app.js'), 'utf8');
assert.match(appSource, /onError:\s*\(error\)\s*=>/);
assert.doesNotMatch(appSource, /onStop:\s*returnFromSelfServiceLoginScreen/);

function classList() {
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

const pages = ['dashboard', 'emprestimo', 'livros', 'salas', 'generos', 'auto-historico', 'controle'].map((name) => ({
  id: `page-${name}`,
  classList: classList(),
}));
const navButtons = ['dashboard', 'emprestimo', 'livros', 'salas', 'generos', 'controle'].map((name) => ({
  dataset: { page: name },
  classList: classList(),
}));
const elements = new Map();
const getElement = (id) => {
  const page = pages.find((item) => item.id === id);
  if (page) return page;
  if (!elements.has(id)) {
    elements.set(id, { style: {}, classList: classList(), textContent: '', innerHTML: '', value: '' });
  }
  return elements.get(id);
};

pages[0].classList.add('active');
navButtons[0].classList.add('active');

const context = {
  console,
  document: {
    cookie: '',
    body: { classList: classList() },
    addEventListener: () => {},
  },
  window: {},
  setTimeout: () => 1,
  clearTimeout: () => {},
  Utils: {
    el: getElement,
    qsa: (selector) => selector === '.page' ? pages
      : selector === '.nav-btn[data-page]' ? navButtons : [],
    qs: (selector) => {
      if (selector === '.page.active') return pages.find((page) => page.classList.contains('active'));
      const match = selector.match(/^\.nav-btn\[data-page="([^"]+)"\]$/);
      return match ? navButtons.find((button) => button.dataset.page === match[1]) : null;
    },
  },
  renderDashboard: () => {},
  renderBooks: () => {},
  renderLoans: () => {},
  loadSelfServiceHistory: () => {},
  loadSelfServiceBooks: () => {},
  resetLoanForm: () => {},
  renderLoanScanPanel: () => {},
};

vm.createContext(context);
vm.runInContext(
  fs.readFileSync(path.join(__dirname, '../assets/js/app.js'), 'utf8'),
  context,
);

(async () => {
  let finishSync;
  context.syncAll = () => new Promise((resolve) => { finishSync = resolve; });

  const login = context._finishLogin({ role: 'admin', login: 'admin', name: 'Admin' }, false);
  context.navigateTo('livros');
  finishSync();
  await login;

  assert.strictEqual(
    pages.find((page) => page.classList.contains('active')).id,
    'page-livros',
    'a conclusão da sincronização não deve substituir a página escolhida',
  );
  vm.runInContext("currentUser = { role: 'self_service' }", context);
  let historyLoads = 0;
  let bookLoads = 0;
  context.loadSelfServiceHistory = () => { historyLoads += 1; };
  context.loadSelfServiceBooks = () => { bookLoads += 1; };
  context.navigateTo('relatorios');
  assert.strictEqual(
    pages.find((page) => page.classList.contains('active')).id,
    'page-auto-historico',
    'autoatendimento não deve navegar para páginas administrativas',
  );
  assert.strictEqual(historyLoads, 1, 'a única tela carrega o histórico do aluno');
  assert.strictEqual(bookLoads, 1, 'a única tela carrega o acervo para novos empréstimos');

  const qrLogins = [];
  let qrCallback;
  context.QRScanner = {
    start: async (_input, callback) => { qrCallback = callback; },
  };
  context.Utils.toast = () => {};
  context._finishLogin = async (user) => { qrLogins.push(user); };
  context.API = {
    qr: {
      login: async () => ({
        access: 'librarian',
        data: { id: 'staff-1', nome: 'Bibliotecária', carteirinha: 'STAFF-1' },
      }),
    },
  };
  await context.startQRLogin();
  await qrCallback({ primary: 'STAFF-1' });
  assert.strictEqual(qrLogins[0].role, 'librarian', 'carteirinha autorizada deve concluir o login sem confirmação extra');

  context.Utils.promptPassword = async () => 'senha-validada';
  context.API.qr.login = async (_code, password) => {
    assert.strictEqual(password, 'senha-validada', 'acesso administrativo mantém validação de senha');
    return { access: 'admin', data: { login: 'admin', nome: 'Administrador' } };
  };
  await context.startQRLogin();
  await qrCallback({ primary: 'ADMIN-admin' });
  assert.strictEqual(qrLogins[1].role, 'admin', 'acesso administrativo confirmado deve entrar imediatamente');
  console.log('navigation remains on selected page during initial sync');

  const syncOptions = [];
  let roomRenders = 0;
  context.syncData = async (options) => syncOptions.push(options);
  context.syncRooms = async (options) => syncOptions.push(options);
  context.syncGenres = async (options) => syncOptions.push(options);
  context.renderRooms = () => { roomRenders += 1; };
  pages.forEach((page) => page.classList.remove('active'));
  pages.find((page) => page.id === 'page-salas').classList.add('active');

  await context.syncAll();
  assert.strictEqual(syncOptions.length, 3);
  assert.strictEqual(syncOptions.every((options) => options.render === false), true);
  assert.strictEqual(roomRenders, 1, 'o sync agregado renderiza apenas a página ativa');
})().catch((error) => {
  console.error(error);
  process.exit(1);
});