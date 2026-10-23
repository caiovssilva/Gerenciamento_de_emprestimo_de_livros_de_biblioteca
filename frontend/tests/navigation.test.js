const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const loginMarkup = fs.readFileSync(path.join(__dirname, '../index.html'), 'utf8');
assert.match(loginMarkup, /id="self-service-student-card"/);
assert.doesNotMatch(loginMarkup, /self-service-books-search|self-service-books-list|self-service-catalog/);
assert.match(loginMarkup, /id="self-service-borrow-scan-btn"/);
assert.match(loginMarkup, /id="self-service-history-rows"/);
assert.match(loginMarkup, /class="self-service-session-close"/);
assert.match(loginMarkup, /aria-label="Sair do histórico e voltar ao início"/);
assert.match(loginMarkup, /onclick="leaveSelfServiceStudentSession\(\)"/);
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
assert.match(appSource, /function leaveSelfServiceStudentSession\(\)/);
assert.match(appSource, /self-service-login-screen.*style\.display = "flex"/s);
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
    elements.set(id, { style: {}, classList: classList(), textContent: '', innerHTML: '', value: '', setAttribute: () => {} });
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
  resetLoanForm: () => {},
  renderLoanScanPanel: () => {},
};

vm.createContext(context);
vm.runInContext(
  fs.readFileSync(path.join(__dirname, '../assets/js/app.js'), 'utf8'),
  context,
);

  context.Store = {
    books: () => [{
      id: 'book-legacy',
      exemplares_meta: [{ id: 'book-legacy-EX-002-copy-id', code: '002', qr_data: '' }],
    }],
    students: () => [],
  };
  const legacyExemplar = context.resolveQRCode('book-legacy-EX-002-copy-id');
  assert.strictEqual(legacyExemplar.type, 'book', 'ID puro registrado deve resolver para o exemplar correto');
  assert.strictEqual(legacyExemplar.data.exemplar, '002');

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

  let forcedSyncCalls = 0;
  context.Store = {
    books: () => [{}],
    students: () => [],
    loans: () => [],
    setBooks: () => {},
    setStudents: () => {},
    setLoans: () => {},
  };
  context.API = {
    books: { list: async () => { forcedSyncCalls += 1; return []; } },
    students: { list: async () => { forcedSyncCalls += 1; return []; } },
    loans: { list: async () => { forcedSyncCalls += 1; return []; } },
  };
  vm.runInContext('_lastSuccessfulSyncTs = Date.now()', context);
  await context.syncData({ render: false });
  assert.strictEqual(forcedSyncCalls, 0, 'a sincronização normal respeita o cooldown recente');
  await context.syncData({ force: true, render: false });
  assert.strictEqual(forcedSyncCalls, 3, 'a sincronização forçada atualiza mesmo durante o cooldown');

  vm.runInContext("currentUser = { role: 'self_service' }", context);
  await context.syncData({ force: true, render: false });
  assert.strictEqual(forcedSyncCalls, 3, 'o autoatendimento não consulta a API geral de empréstimos');
  let historyLoads = 0;
  context.loadSelfServiceHistory = () => { historyLoads += 1; };
  context.navigateTo('relatorios');
  assert.strictEqual(
    pages.find((page) => page.classList.contains('active')).id,
    'page-auto-historico',
    'autoatendimento não deve navegar para páginas administrativas',
  );
  assert.strictEqual(historyLoads, 1, 'a única tela carrega o histórico do aluno');
  assert.doesNotMatch(appSource, /loadSelfServiceBooks|renderSelfServiceBooks|selfServiceBooks/);

  let scannedLoanBody;
  let scanCallback;
  context.QRScanner = { start: async (_input, callback) => { scanCallback = callback; } };
  context.API = {
    auth: {
      selfServiceCreateLoan: async (token, body) => {
        assert.strictEqual(token, 'student-token');
        scannedLoanBody = body;
      },
    },
  };
  context.Utils.toast = () => {};
  context.loadSelfServiceHistory = async () => {};
  vm.runInContext(
    "currentUser = { role: 'self_service', accessToken: 'student-token' }; selfServiceSettings.allow_borrow = true",
    context,
  );
  await context.startSelfServiceBookScan();
  await scanCallback({ primary: 'EXEMPLAR-book-1-EX-001-copy-1' });
  assert.strictEqual(JSON.stringify(scannedLoanBody), JSON.stringify({ exemplar_qr: 'EXEMPLAR-book-1-EX-001-copy-1' }));

  const selfServiceLoan = {
    loan_id: 'loan-self-service',
    book_id: 'book-self-service',
    book_title: 'Livro do empréstimo',
    exemplar: '005',
    exemplar_id: 'copy-self-service',
    returned_at: null,
  };
  let renewalRequest = null;
  let returnRequest = null;
  let selfServiceScanStarts = 0;
  let cardScanCallback;
  let returnCardVerification = null;
  const validExemplarQr = 'EXEMPLAR-book-self-service-EX-005-copy-self-service';
  const selfServiceDialogs = [];
  const dialogResponses = [];
  context.API.auth = {
    selfServiceRenewLoan: async (...args) => { renewalRequest = args; },
    selfServiceReturnLoan: async (...args) => { returnRequest = args; },
    selfServiceVerifyReturnCard: async (...args) => {
      returnCardVerification = args;
      const proofCode = args[2].find((code) => ['CARD-1', validExemplarQr].includes(code));
      if (!proofCode) {
        throw new Error('O QR não corresponde à carteirinha nem ao exemplar deste empréstimo.');
      }
      return { proof_code: proofCode };
    },
  };
  context.QRScanner.start = async (_input, callback, options) => {
    selfServiceScanStarts += 1;
    cardScanCallback = callback;
    assert.strictEqual(options.suppressToasts, true);
  };
  let historyRefreshes = 0;
  context.loadSelfServiceHistory = async () => { historyRefreshes += 1; };
  context.Utils.confirmDialog = async (message, options) => {
    selfServiceDialogs.push({ message, options });
    return dialogResponses.shift() ?? false;
  };
  context.selfServiceLoan = selfServiceLoan;
  vm.runInContext(
    "currentUser = { role: 'self_service', accessToken: 'student-token', name: 'Ana' }; selfServiceSettings.allow_renew = true; selfServiceSettings.allow_return = true; selfServiceHistory = [selfServiceLoan]",
    context,
  );

  dialogResponses.push(false);
  await context.operateSelfServiceLoan('loan-self-service', 'renew');
  assert.match(selfServiceDialogs[0].message, /Carteirinha: Ana.*Livro: Livro do empréstimo.*Exemplar: #005.*Confirma renovar/s);
  assert.strictEqual(selfServiceDialogs[0].options.confirmText, 'Sim, renovar');
  assert.strictEqual(selfServiceDialogs[0].options.cancelText, 'Não');
  assert.strictEqual(renewalRequest, null, 'responder não cancela a renovação');

  dialogResponses.push(true);
  await context.operateSelfServiceLoan('loan-self-service', 'renew');
  assert.strictEqual(JSON.stringify(renewalRequest), JSON.stringify([
    'student-token',
    'loan-self-service',
    {},
  ]));

  dialogResponses.push(true);
  await context.operateSelfServiceLoan('loan-self-service', 'return');
  assert.match(selfServiceDialogs.at(-1).message, /carteirinha de Ana ou o QR do exemplar #005/s);
  assert.strictEqual(selfServiceDialogs.at(-1).options.confirmText, 'Ler QR');
  assert.strictEqual(selfServiceScanStarts, 1);

  dialogResponses.push(false);
  await cardScanCallback({ primary: 'CARD-2', codes: ['CARD-2'] });
  assert.strictEqual(JSON.stringify(returnCardVerification), JSON.stringify([
    'student-token', 'loan-self-service', ['CARD-2'],
  ]));
  assert.strictEqual(returnRequest, null, 'carteirinha errada nunca devolve o livro');
  assert.match(selfServiceDialogs.at(-1).message, /não corresponde à carteirinha nem ao exemplar/);

  dialogResponses.push(true);
  await context.operateSelfServiceLoan('loan-self-service', 'return');
  dialogResponses.push(false);
  await cardScanCallback({ primary: 'EXEMPLAR-book-other-EX-005-copy-other', codes: ['EXEMPLAR-book-other-EX-005-copy-other'] });
  assert.strictEqual(returnRequest, null, 'QR de outro livro nunca devolve o empréstimo');
  assert.match(selfServiceDialogs.at(-1).message, /não corresponde à carteirinha nem ao exemplar/);

  dialogResponses.push(true);
  await context.operateSelfServiceLoan('loan-self-service', 'return');
  dialogResponses.push(false);
  await cardScanCallback({ primary: 'CARD-1', codes: ['CARD-1'] });
  assert.strictEqual(JSON.stringify(returnCardVerification), JSON.stringify([
    'student-token', 'loan-self-service', ['CARD-1'],
  ]));
  assert.strictEqual(returnRequest, null, 'não na confirmação cancela a devolução');
  assert.strictEqual(selfServiceDialogs.at(-1).options.cancelText, 'Não');

  dialogResponses.push(true);
  await context.operateSelfServiceLoan('loan-self-service', 'return');
  dialogResponses.push(true);
  await cardScanCallback({ primary: 'secondary-code', codes: ['secondary-code', validExemplarQr] });
  assert.strictEqual(JSON.stringify(returnCardVerification), JSON.stringify([
    'student-token', 'loan-self-service', ['secondary-code', validExemplarQr],
  ]));
  assert.strictEqual(JSON.stringify(returnRequest), JSON.stringify([
    'student-token',
    'loan-self-service',
    { proof_code: validExemplarQr },
  ]));
  assert.strictEqual(selfServiceScanStarts, 4, 'cada tentativa iniciada de devolução lê uma identificação');
  assert.strictEqual(historyRefreshes, 2, 'o histórico atualiza após renovar e devolver');

  const selectedLoan = {
    id: 'loan-1', livro_id: 'book-1', exemplar: '1', exemplar_id: 'old-copy-id', aluno_id: 'student-1', devolvido_em: null,
  };
  const otherLoan = {
    id: 'loan-2', livro_id: 'book-2', exemplar: '002', exemplar_id: 'copy-2', aluno_id: 'student-2', devolvido_em: null,
  };
  const selectedQr = 'EXEMPLAR-book-1-EX-001-copy-1';
  const otherQr = 'EXEMPLAR-book-2-EX-002-copy-2';
  let returnCallback;
  let openedDevolution = null;
  let directReturnCalls = 0;
  context.Store = {
    loans: () => [selectedLoan, otherLoan],
    loanById: (id) => [selectedLoan, otherLoan].find((loan) => loan.id === id),
    studentById: (id) => ({ id, nome: id }),
  };
  context.resolveQRCodeAsync = async (code) => {
    if (code === selectedQr) return { type: 'book', data: { id: 'book-1', exemplar: '001' } };
    if (code === otherQr) return { type: 'book', data: { id: 'book-2', exemplar: '002' } };
    if (code === 'BOOK-1') return { type: 'book', data: { id: 'book-1' } };
    if (code === 'CARD-1') return { type: 'student', data: { id: 'student-1', nome: 'Ana' } };
    return { type: 'unknown', data: null };
  };
  context.openDevolution = (loanId, studentId) => { openedDevolution = { loanId, studentId }; };
  context.QRScanner.start = async (_input, callback) => { returnCallback = callback; };
  context.API.loans = { return: async () => { directReturnCalls += 1; } };
  context.renderLoanScanPanel = () => {};
  context.Utils.toast = () => {};
  await context.openLoanScanner();
  await returnCallback({ primary: 'BOOK-1' });
  assert.strictEqual(vm.runInContext('pendingReturnLoanId', context), null, 'QR genérico não seleciona uma cópia para devolução');
  await returnCallback({ primary: selectedQr });
  assert.strictEqual(vm.runInContext('pendingReturnLoanId', context), 'loan-1');
  await returnCallback({ primary: otherQr });
  assert.strictEqual(vm.runInContext('pendingReturnLoanId', context), 'loan-1', 'uma segunda leitura não troca o exemplar travado');
  await returnCallback({ primary: 'CARD-1' });
  assert.deepStrictEqual(openedDevolution, { loanId: 'loan-1', studentId: 'student-1' });
  assert.strictEqual(vm.runInContext('pendingDevolutionQr', context), selectedQr);
  assert.strictEqual(directReturnCalls, 0, 'a carteirinha abre confirmação em vez de devolver sem revisão');

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