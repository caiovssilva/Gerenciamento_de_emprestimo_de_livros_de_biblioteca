/**
 * assets/js/app.js — Controller principal: auth, navegação, sync, empréstimo, devolução.
 */

// IMPORTANTE: Senhas não devem estar no código do cliente!
// A autenticação é validada no backend via API.
// Credenciais padrão para desenvolvimento são carregadas do backend de forma segura.

let currentUser = null; // { role:'admin'|'librarian', login, name, student? }
let pendingLoan = { book:null, exemplar:null, student:null };
let pendingDevolutionId = null;
let pendingDevolutionStudentId = null;
let pendingReturnLoanId = null;
let scannedLoanStudentId = null;
let _historyStudentId = null; // ID do aluno cujo histórico está aberto no momento

// ── Auth: login tradicional (usuário/senha) ───────────────────────────
async function doLogin() {
  const user  = Utils.el("login-user").value.trim();
  const pass  = Utils.el("login-pass").value;
  const errEl = Utils.el("login-err");
  errEl.textContent = "";
  
  if (!user || !pass) {
    errEl.textContent = "Usuário e senha são obrigatórios.";
    return;
  }

  try {
    // Valida as credenciais no backend de forma segura
    const response = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ login: user, password: pass })
    });

    if (!response.ok) {
      const error = await response.json().catch(() => null);
      if (response.status === 401) {
        errEl.textContent = error?.error || "Usuário ou senha incorretos.";
      } else {
        errEl.textContent = error?.error || "Erro ao fazer login.";
      }
      Utils.el("login-pass").value = "";
      return;
    }

    const result = await response.json();
      if (result.access === "admin") {
      _finishLogin({ role: "admin", login: result.login, name: result.name });
    } else if (result.access === "librarian") {
      _finishLogin({ role: "librarian", login: result.login, name: result.name });
    } else {
      errEl.textContent = "Nome ou senha incorretos.";
      Utils.el("login-pass").value = "";
    }
  } catch (error) {
    console.error("Erro ao fazer login:", error);
    errEl.textContent = "Erro de conexão. Tente novamente.";
    Utils.el("login-pass").value = "";
  }
}

// ── Auth: login por QR Code (carteirinha) ─────────────────────────────
async function startQRLogin() {
  await QRScanner.start(null, async (res) => {
    const code = res.primary;
    if (!code) { Utils.toast("Código não reconhecido.","error"); return; }
    try {
      const r = await API.qr.login(code);
      if (r.access === "admin") {
        const adminData = r.data || {};
        const login = adminData.login || "admin";
        const name = login === "biblioteca" ? "Bibliotecária" : "Administrador";
        _showQRLoginResult({
          icon:"ti-shield-check", color:"var(--brand)",
          title:`Bem-vindo, ${name}`,
          sub:"Acesso administrativo confirmado.",
          action:() => _finishLogin({ role:"admin", login, name }),
        });
      } else if (r.access === "librarian") {
        const student = r.data;
        _showQRLoginResult({
          icon:"ti-id-badge2", color:"var(--green)",
          title:"Carteirinha reconhecida!",
          sub:`${student.nome} — ${student.turma}`,
          action:() => _finishLogin({ role:"librarian", login:student.carteirinha||student.id, name:student.nome, student }, true),
        });
      } else {
        _showQRLoginResult({
          icon:"ti-lock", color:"var(--red)",
          title:"Acesso negado",
          sub: r.message || "Esta carteirinha não possui acesso ao painel.",
          action:null,
        });
      }
    } catch(e) { Utils.toast("Erro ao validar QR: "+e.message,"error"); }
  });
}

function _showQRLoginResult({icon, color, title, sub, action}) {
  Utils.el("login-card-form").style.display = "none";
  const body = Utils.el("login-qr-result-body");
  body.innerHTML = `
    <div class="login-qr-success">
      <i class="ti ${icon}" style="color:${color};"></i>
      <div class="lqs-title">${title}</div>
      <div class="lqs-sub">${sub}</div>
      ${action ? `<button class="btn btn-login" style="margin-top:1.25rem;" id="qr-login-confirm-btn"><i class="ti ti-login" style="vertical-align:-2px;margin-right:6px;"></i>Entrar</button>` : ""}
    </div>`;
  if (action) Utils.el("qr-login-confirm-btn").onclick = action;
  Utils.el("login-card-qr-result").style.display = "block";
}

function cancelQRLoginResult() {
  Utils.el("login-card-qr-result").style.display = "none";
  Utils.el("login-qr-result-body").innerHTML = "";
  Utils.el("login-card-form").style.display = "block";
}

// ── Finaliza login (qualquer origem) e aplica permissões ──────────────
function _finishLogin(user, showRoleToast) {
  currentUser = user;
  Utils.el("login-screen").style.display = "none";
  Utils.el("login-card-qr-result").style.display = "none";
  Utils.el("login-qr-result-body").innerHTML = "";
  Utils.el("login-card-form").style.display = "block";
  Utils.el("app").style.display = "flex";

  const ini = user.name.split(" ").map(w=>w[0]).slice(0,2).join("").toUpperCase();
  Utils.el("sb-avatar-initials").textContent = ini;
  Utils.el("sb-user-name").textContent = user.name;

  const roleBadge = Utils.el("sb-role-badge");
  roleBadge.innerHTML = user.role === "librarian"
    ? `<span class="role-badge role-librarian"><i class="ti ti-id-badge2"></i>Bibliotecário</span>`
    : `<span class="role-badge role-admin"><i class="ti ti-shield-check"></i>Administrador</span>`;

  _applyRolePermissions();

  Store.loadLocal();
  syncAll();
  navigateTo(user.role === "librarian" ? "emprestimo" : "dashboard");

  if (showRoleToast) {
    Utils.el("role-success-icon").style.color = "var(--green)";
    Utils.el("role-success-title").textContent = "Você entrou como Bibliotecário";
    Utils.el("role-success-sub").textContent = `${user.name} — acesso liberado para empréstimos, devoluções e renovações.`;
    Utils.openModal("modal-role-success");
  }
}

// ── Permissões por role ────────────────────────────────────────────────
function _applyRolePermissions() {
  const isLibrarian = currentUser?.role === "librarian";
  Utils.qsa('[data-role="admin"]').forEach(el => el.classList.toggle("lib-hidden", isLibrarian));
  Utils.qsa('[data-role="librarian-hide"]').forEach(el => el.classList.toggle("lib-hidden", isLibrarian));
  document.body.classList.toggle("role-librarian", isLibrarian);
  if (isLibrarian) {
    const active = Utils.qs(".page.active");
    const adminOnlyPages = ["alunos","salas","generos","relatorios","livros"];
    if (active && adminOnlyPages.includes(active.id.replace("page-",""))) navigateTo("emprestimo");
  }
}

function isLibrarian() { return currentUser?.role === "librarian"; }

function doLogout() {
  if (!confirm("Sair do sistema?")) return;
  currentUser = null;
  Charts.destroy();
  Utils.el("app").style.display = "none";
  Utils.el("login-screen").style.display = "flex";
  Utils.el("login-user").value = "";
  Utils.el("login-pass").value = "";
  Utils.el("login-err").textContent = "";
  cancelQRLoginResult();
  Utils.qsa('[data-role="admin"]').forEach(el => el.classList.remove("lib-hidden"));
  document.body.classList.remove("role-librarian");
  toggleMobileSidebar(false);
}

function toggleMobileSidebar(force) {
  const shouldOpen = typeof force === "boolean" ? force : !document.body.classList.contains("sidebar-open");
  document.body.classList.toggle("sidebar-open", shouldOpen);
}

function setupNavigationBindings() {
  Utils.qsa(".nav-btn[data-page]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const page = btn.dataset.page;
      if (!page) return;
      navigateTo(page);
      toggleMobileSidebar(false);
    });
  });

  Utils.qsa("#emp-tabs .tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const tab = btn.dataset.tab;
      if (!tab) return;
      Utils.qsa("#emp-tabs .tab-btn").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");

      const novo = Utils.el("tab-novo");
      const lista = Utils.el("tab-lista");
      if (novo) novo.style.display = tab === "novo" ? "block" : "none";
      if (lista) lista.style.display = tab === "lista" ? "block" : "none";
      if (tab === "lista") renderLoans();
    });
  });
}


function improveFormAccessibility() {
  const controls = Utils.qsa("input, select, textarea");

  controls.forEach((control, idx) => {
    if (control.type === "hidden" || control.id === "csv-file-input") return;

    if (!control.id) control.id = `field-auto-${idx + 1}`;

    const hasAccessibleName =
      control.getAttribute("aria-label") ||
      control.getAttribute("aria-labelledby") ||
      control.getAttribute("title");

    const explicitLabel = Utils.qs(`label[for="${control.id}"]`);
    const nearbyLabel = control.closest(".form-group, .form-field")?.querySelector("label");
    const label = explicitLabel || nearbyLabel;

    if (label && !label.getAttribute("for")) {
      label.setAttribute("for", control.id);
    }

    if (!hasAccessibleName) {
      const baseText = (label?.textContent || control.getAttribute("placeholder") || control.name || control.id || "campo").trim();
      control.setAttribute("aria-label", baseText.replace(/\*/g, "").trim());
    }
  });
}


// ── Sync ──────────────────────────────────────────────────────────────
async function syncAll() {
  await Promise.all([syncData(), syncRooms(), syncGenres()]);
}

async function syncData() {
  const st = Utils.el("cloud-status");
  if (st) st.innerHTML = `<i class="ti ti-loader" style="animation:spin 1s linear infinite;display:inline-block;"></i> Sincronizando...`;
  try {
    const [books, students, loans] = await Promise.all([API.books.list(), API.students.list(), API.loans.list()]);
    Store.setBooks(books); Store.setStudents(students); Store.setLoans(loans);
    if (st) st.innerHTML = `<span style="color:var(--green)"><i class="ti ti-cloud-check"></i> Conectado — ${new Date().toLocaleTimeString("pt-BR")}</span>`;
    renderDashboard(); renderBooks(); renderStudents(); renderLoans();
  } catch {
    if (st) st.innerHTML = `<span style="color:var(--amber)"><i class="ti ti-alert-triangle"></i> Offline — cache local</span>`;
    Store.loadLocal();
    renderDashboard(); renderBooks(); renderStudents(); renderLoans();
  }
}

// ── Navegação ─────────────────────────────────────────────────────────
const PAGE_META = {
  dashboard:  { title:"Painel",           sub:"Visão geral da biblioteca",         action:"" },
  emprestimo: { title:"Empréstimos",      sub:"Registrar e gerenciar empréstimos", action:"" },
  livros:     { title:"Acervo",           sub:"Livros por gênero e área",
    action:`<button class="btn btn-primary" onclick="openAddBook()"><i class="ti ti-plus"></i>Novo livro</button>` },
  alunos:     { title:"Alunos",           sub:"Cadastro de alunos por sala",
    action:`<button class="btn btn-primary" onclick="openAddStudent()"><i class="ti ti-plus"></i>Novo aluno</button>` },
  salas:      { title:"Salas",            sub:"Organização de alunos por sala",
    action:`<button class="btn btn-primary" onclick="openAddRoom()"><i class="ti ti-plus"></i>Nova sala</button>` },
  generos:    { title:"Gêneros de Livro", sub:"Tipos e categorias do acervo",
    action:`<button class="btn btn-primary" onclick="openAddGenre()"><i class="ti ti-plus"></i>Novo gênero</button>` },
  relatorios: { title:"Relatórios",       sub:"Gráficos e exportação",
    action:`<button class="btn" onclick="Charts.refresh()"><i class="ti ti-refresh"></i>Atualizar</button>` },
  config:     { title:"Configurações",    sub:"Sistema e conexão", action:"" },
};

function navigateTo(page) {
  toggleMobileSidebar(false);
  Utils.qsa(".page").forEach(p => p.classList.remove("active"));
  Utils.qsa(".nav-btn[data-page]").forEach(b => b.classList.remove("active"));
  Utils.el("page-"+page)?.classList.add("active");
  Utils.qs(`.nav-btn[data-page="${page}"]`)?.classList.add("active");
  const meta = PAGE_META[page] || {};
  Utils.el("topbar-title").textContent  = meta.title || page;
  Utils.el("topbar-sub").textContent    = meta.sub   || "";
  // Bibliotecário vê o acervo mas não pode cadastrar novos livros
  Utils.el("topbar-actions").innerHTML  = (page==="livros" && isLibrarian()) ? "" : (meta.action || "");
  if (page==="dashboard")  renderDashboard();
  if (page==="livros")     renderBooks();
  if (page==="alunos")     renderStudents();
  if (page==="salas")      renderRooms();
  if (page==="generos")    renderGenres();
  if (page==="emprestimo") { renderLoans(); resetLoanForm(); renderLoanScanPanel(); }
  if (page==="relatorios") Charts.init();
  if (page==="config" && isLibrarian()) {
    Utils.el("topbar-actions").innerHTML = "";
  }
}

// ── Empréstimo ────────────────────────────────────────────────────────
function updateDueDate() {
  const days = parseInt(Utils.el("loan-days").value) || 7;
  const base = Utils.el("loan-date").value || Utils.today();
  Utils.el("due-date-text").textContent = `Devolução prevista: ${Utils.fmtDate(Utils.addDays(base,days))} (em ${days} dias)`;
}

function normalizeQueryValue(value) {
  return String(value || "").trim().toLowerCase();
}

function parseExemplarCode(code) {
  const normalized = String(code || "").trim();
  const match = normalized.match(/^EXEMPLAR-(.+)-(.+)-(.+)$/i);
  if (match) return { bookId: match[1], exemplar: match[2], exemplarId: match[3] };
  const legacy = normalized.match(/^EXEMPLAR-(.+)-(.+)$/i);
  if (!legacy) return null;
  return { bookId: legacy[1], exemplar: legacy[2], exemplarId: legacy[2] };
}

function setLoanStudent(student) {
  if (!student) {
    pendingLoan.student = null;
    const infoEl = Utils.el("student-result");
    if (infoEl) infoEl.innerHTML = `<span style="color:var(--red)"><i class="ti ti-alert-circle"></i> Aluno não encontrado.</span>`;
    return;
  }

  pendingLoan.student = student;
  const infoEl = Utils.el("student-result");
  if (!infoEl) return;

  const loans  = Store.loans().filter(l => l.aluno_id === student.id && !l.devolvido_em);
  const overdue= loans.filter(l => Utils.daysLeft(l.data_devolucao_prevista) < 0);
  const status = overdue.length ? `<span class="badge badge-red">Irregular — ${overdue.length} atrasado(s)</span>`
               : loans.length   ? `<span class="badge badge-amber">${loans.length} empréstimo(s) ativo(s)</span>`
               : `<span class="badge badge-green">Regular</span>`;
  infoEl.innerHTML = `<div><strong>${student.nome||student.name}</strong> — ${student.turma||student.class} ${status}</div>`;
}

function lookupBook() {
  const q = normalizeQueryValue(Utils.el("isbn-input").value);
  if (!q) return;
  const books = Store.books();
  const found = books.find(b =>
    normalizeQueryValue(b.isbn) === q ||
    normalizeQueryValue(b.qr_id) === q ||
    normalizeQueryValue(b.id).startsWith(q) ||
    normalizeQueryValue(b.titulo || b.title).includes(q)
  );
  const infoEl = Utils.el("book-result");
  if (!found) {
    if (infoEl) infoEl.innerHTML = `<span style="color:var(--red)"><i class="ti ti-alert-circle"></i> Livro não encontrado.</span>`;
    pendingLoan.book = null;
    return;
  }
  const loans  = Store.loans();
  const active = loans.filter(l => l.livro_id === found.id && !l.devolvido_em);
  const total  = found.exemplares||found.copies||1;
  const avail  = total - active.length;
  const dispEx = Array.from({length: total}, (_, i) => String(i+1).padStart(3, "0")).filter(ex => !active.find(l => l.exemplar === ex));
  const genBadge = found.genero_nome ? `<span class="badge" style="background:${found.genero_cor||"#6366f1"}22;color:${found.genero_cor||"#6366f1"}">${found.genero_nome}</span>` : "";
  infoEl.innerHTML = avail > 0
    ? `<div class="book-found"><strong>${found.titulo||found.title}</strong> — ${found.autor||found.author} ${genBadge}
       <br><small>${avail} de ${total} disponíveis</small>
       <div style="margin-top:6px;display:flex;gap:6px;flex-wrap:wrap;">
         ${dispEx.map(ex => `<button class="btn btn-sm ${pendingLoan.exemplar===ex?"btn-primary":""}" onclick="selectExemplar('${found.id}','${ex}',this)">#${ex}</button>`).join("")}
       </div></div>`
    : `<div style="color:var(--red)"><i class="ti ti-alert-circle"></i> Todos os exemplares estão emprestados.</div>`;
  if (avail > 0) {
    pendingLoan.book = found;
    if (!pendingLoan.exemplar && dispEx.length) selectExemplar(found.id, dispEx[0]);
  }
}

function selectExemplar(bookId, ex, btn) {
  pendingLoan.book     = Store.bookById(bookId);
  pendingLoan.exemplar = ex;
  Utils.qsa(".book-found .btn-sm").forEach(b => b.classList.remove("btn-primary"));
  btn?.classList.add("btn-primary");
}

function lookupStudent() {
  const q = normalizeQueryValue(Utils.el("student-input").value);
  if (!q) return;
  const studs = Store.students();
  const found = studs.find(s => {
    const id    = normalizeQueryValue(s.id);
    const card  = normalizeQueryValue(s.card || s.carteirinha);
    const qrId  = normalizeQueryValue(s.qr_id);
    const name  = normalizeQueryValue(s.nome || s.name);
    return id === q || card === q || qrId === q || id.startsWith(q) || name.includes(q);
  });
  if (!found) {
    setLoanStudent(null);
    return;
  }
  setLoanStudent(found);
}

async function scanLoanStudent() {
  await QRScanner.start('student-input', async (res) => {
    const code = (res?.primary || '').trim();
    if (!code) {
      Utils.toast('Não foi possível ler o código. Tente novamente.', 'error');
      return;
    }

    const input = Utils.el('student-input');
    if (input) input.value = code;

    const scanned = await resolveQRCodeAsync(code);
    if (scanned.type === 'student' && scanned.data?.id) {
      const student = scanned.data;
      if (!Store.studentById(student.id)) {
        Store.setStudents([...Store.students(), student]);
      }
      if (input) input.value = student.carteirinha||student.card||student.id;
      setLoanStudent(student);
      showStudentHistory(student.id);
      Utils.toast(`Aluno identificado: ${student.nome||student.name}`, 'success');
      return;
    }

    if (scanned.type === 'admin') {
      Utils.toast('Este QR é de administrador. Use a tela de login por QR.', 'error');
      return;
    }

    if (scanned.type === 'book') {
      Utils.toast('Este QR é de livro. Escaneie a carteirinha do aluno.', 'error');
      return;
    }

    setLoanStudent(null);
  });
}

async function confirmLoan() {
  if (!pendingLoan.book)    { Utils.toast("Selecione um livro.",  "error"); return; }
  if (!pendingLoan.exemplar){ Utils.toast("Selecione um exemplar.","error"); return; }
  if (!pendingLoan.student) { Utils.toast("Selecione um aluno.", "error"); return; }
  const days = parseInt(Utils.el("loan-days").value) || 7;
  const date = Utils.el("loan-date").value || Utils.today();
  const obsEl = Utils.el("loan-obs");
  const obs = obsEl ? obsEl.value.trim() : "";
  try {
    await API.loans.create({
      livro_id: pendingLoan.book.id,
      aluno_id: pendingLoan.student.id,
      exemplar: pendingLoan.exemplar,
      dias: days, data_emprestimo: date,
      observacao: obs, criado_por: currentUser?.login||"sistema",
    });
    Utils.toast(`Empréstimo registrado — ${pendingLoan.book.titulo||pendingLoan.book.title}`, "success");
    resetLoanForm();
    await syncData();
    Charts.refresh();
    renderLoanScanPanel();
  } catch(e) { Utils.toast("Erro: "+e.message,"error"); }
}

function resetLoanForm() {
  pendingLoan = { book:null, exemplar:null, student:null };
  ["isbn-input","student-input","loan-obs"].forEach(id => { const el=Utils.el(id); if(el) el.value=""; });
  Utils.el("loan-date").value = Utils.today();
  Utils.el("loan-days").value = 7;
  Utils.el("book-result").innerHTML    = "";
  Utils.el("student-result").innerHTML = "";
  updateDueDate();
}

// ── Devolução ─────────────────────────────────────────────────────────
function openDevolution(loanId, studentId = null) {
  const loan = Store.loanById(loanId);
  if (!loan) return;
  const book = Store.bookById(loan.livro_id);
  const stud = Store.studentById(loan.aluno_id);
  pendingDevolutionId = loanId;
  pendingDevolutionStudentId = studentId || null;
  Utils.el("dev-info").innerHTML = `
    <strong>${stud?.nome||stud?.name||"—"}</strong> — ${book?.titulo||book?.title||"—"}
    <br><small>Exemplar #${loan.exemplar} · Previsto: ${Utils.fmtDate(loan.data_devolucao_prevista)}</small>`;
  Utils.el("dev-obs").value = "";
  Utils.openModal("modal-devolution");
}

async function confirmDevolution() {
  if (!pendingDevolutionId) return;
  const obs = Utils.el("dev-obs").value.trim();
  try {
    await API.loans.return(pendingDevolutionId, {
      observacao: obs,
      student_id: pendingDevolutionStudentId || null,
    });
    Utils.toast("Devolução registrada!", "success");
    Utils.closeModal("modal-devolution");
    pendingDevolutionId = null;
    pendingDevolutionStudentId = null;
    await syncData(); Charts.refresh();
    _refreshOpenStudentHistory();
    renderLoanScanPanel();
  } catch(e) { Utils.toast("Erro: "+e.message,"error"); }
}

// ── Renovação ─────────────────────────────────────────────────────────
let pendingRenewalId = null;

function openRenewal(loanId) {
  const loan = Store.loanById(loanId);
  if (!loan) return;
  const book = Store.bookById(loan.livro_id);
  const stud = Store.studentById(loan.aluno_id);
  pendingRenewalId = loanId;
  Utils.el("renew-info").innerHTML = `
    <strong>${stud?.nome||stud?.name||"—"}</strong> — ${book?.titulo||book?.title||"—"}
    <br><small>Exemplar #${loan.exemplar} · Prazo atual: ${Utils.fmtDate(loan.data_devolucao_prevista)}</small>`;
  Utils.el("renew-days").value = 7;
  _updateRenewalPreview();
  Utils.openModal("modal-renewal");
}

function _updateRenewalPreview() {
  const loan = Store.loanById(pendingRenewalId);
  if (!loan) return;
  const days = parseInt(Utils.el("renew-days").value)||7;
  const base = loan.data_devolucao_prevista || Utils.today();
  Utils.el("renew-new-date-text").textContent = `Nova devolução prevista: ${Utils.fmtDate(Utils.addDays(base,days))} (+${days} dias)`;
}

async function confirmRenewal() {
  if (!pendingRenewalId) return;
  const days = parseInt(Utils.el("renew-days").value)||7;
  try {
    await API.loans.renew(pendingRenewalId, { dias: days });
    Utils.toast(`Empréstimo renovado por +${days} dias!`, "success");
    Utils.closeModal("modal-renewal");
    pendingRenewalId = null;
    await syncData(); Charts.refresh();
    _refreshOpenStudentHistory();
    renderLoanScanPanel();
  } catch(e) { Utils.toast("Erro: "+e.message,"error"); }
}

// Se o modal de histórico do aluno estiver aberto, redesenha com dados atualizados
function _refreshOpenStudentHistory() {
  if (Utils.el("modal-student-history")?.classList.contains("open") && _historyStudentId) {
    showStudentHistory(_historyStudentId);
  }
}

function resolveQRCode(code) {
  if (!code || typeof code !== "string") return { type: "unknown", data: null };
  const normalized = code.trim();
  if (normalized.startsWith("ADMIN-")) {
    return { type: "admin", data: { login: normalized.substring(6) || "admin" } };
  }
  const parsedExemplar = parseExemplarCode(normalized);
  if (parsedExemplar) {
    const book = Store.books().find(b => b.id === parsedExemplar.bookId || (b.isbn||"") === parsedExemplar.bookId || (b.qr_id||"") === parsedExemplar.bookId);
    if (book) return { type: "book", data: { ...book, exemplar: parsedExemplar.exemplar, exemplarId: parsedExemplar.exemplarId, uniqueQrCode: normalized } };
  }
  const student = Store.students().find(s => s.id === normalized || (s.card||s.carteirinha||"") === normalized || (s.qr_id||"") === normalized);
  if (student) return { type: "student", data: student };
  const book = Store.books().find(b => b.id === normalized || (b.isbn||"") === normalized || (b.qr_id||"") === normalized);
  if (book) return { type: "book", data: book };
  return { type: "unknown", data: null };
}

async function resolveQRCodeAsync(code) {
  const normalized = (code || "").trim();
  if (!normalized) return { type: "unknown", data: null };
  const local = resolveQRCode(normalized);
  if (local.type !== "unknown") return local;

  if (normalized.startsWith("ADMIN-")) {
    return { type: "admin", data: { login: normalized.substring(6) || "admin" } };
  }

  const parsedExemplar = parseExemplarCode(normalized);
  if (parsedExemplar) {
    const book = Store.books().find(b => b.id === parsedExemplar.bookId || (b.isbn||"") === parsedExemplar.bookId || (b.qr_id||"") === parsedExemplar.bookId);
    if (book) return { type: "book", data: { ...book, exemplar: parsedExemplar.exemplar, exemplarId: parsedExemplar.exemplarId, uniqueQrCode: normalized } };
  }

  try {
    const student = await API.students.get(normalized);
    if (student?.id) {
      return { type: "student", data: student };
    }
  } catch (_err) {
    // Não encontrou aluno no backend.
  }

  try {
    const book = await API.books.get(normalized);
    if (book?.id) {
      return { type: "book", data: book };
    }
  } catch (_err) {
    // Não encontrou livro no backend.
  }

  return { type: "unknown", data: null };
}

async function openLoanScanner() {
  QRScanner.start(null, async (res) => {
    const code = (res?.primary || "").trim();
    if (!code) {
      Utils.toast("Não foi possível ler o código. Tente novamente.", "error");
      return;
    }

    const scanned = await resolveQRCodeAsync(code);
    if (scanned.type === "student" && scanned.data?.id) {
      if (pendingReturnLoanId) {
        const loan = Store.loanById(pendingReturnLoanId);
        if (loan && !loan.devolvido_em && String(loan.aluno_id) === String(scanned.data.id)) {
          await API.loans.return(pendingReturnLoanId, { student_id: scanned.data.id, observacao: "" });
          Utils.toast(`Devolução registrada para ${scanned.data.nome||scanned.data.name}.`, "success");
          pendingReturnLoanId = null;
          await syncData(); Charts.refresh(); _refreshOpenStudentHistory(); renderLoanScanPanel();
          return;
        }
        if (loan && !loan.devolvido_em) {
          const borrower = Store.studentById(loan.aluno_id);
          Utils.toast(`Este exemplar pertence a ${borrower?.nome||borrower?.name||"outro aluno"}.`, "error");
          return;
        }
      }
      scannedLoanStudentId = scanned.data.id;
      if (!Store.studentById(scanned.data.id)) await syncData();
      renderLoanScanPanel();
      Utils.qs('#emp-tabs .tab-btn[data-tab="novo"]')?.click();
      return;
    }
    if (scanned.type === "book" && scanned.data?.id) {
      const targetExemplar = scanned.data.exemplar || null;
      const targetExemplarId = scanned.data.exemplarId || null;
      const activeLoan = Store.loans().find((loan) => {
        if (loan.livro_id !== scanned.data.id || loan.devolvido_em) return false;
        if (targetExemplar && String(loan.exemplar) !== String(targetExemplar)) return false;
        if (targetExemplarId && String(loan.exemplar_id || "") !== String(targetExemplarId)) return false;
        return true;
      });
      if (activeLoan) {
        const borrower = Store.studentById(activeLoan.aluno_id);
        pendingReturnLoanId = activeLoan.id;
        scannedLoanStudentId = activeLoan.aluno_id;
        renderLoanScanPanel();
        Utils.toast(`📖 Exemplar emprestado para ${borrower?.nome||borrower?.name||"o aluno responsável"}. Leia a carteirinha do aluno para devolver.`, "info");
        return;
      }
      pendingReturnLoanId = null;
      const total = scanned.data.exemplares||scanned.data.copies||1;
      const active = Store.loans().filter(l=>l.livro_id===scanned.data.id && !l.devolvido_em).length;
      Utils.toast(`📖 ${scanned.data.titulo||scanned.data.title} — ${total-active} de ${total} disponíveis`, "info");
      return;
    }
    if (scanned.type === "admin") {
      Utils.toast("Cartão administrativo lido. Use-o na tela de login.", "info");
      return;
    }
    Utils.toast("Código não reconhecido — tente outro QR ou digite manualmente.", "error");
  });
}

function selectLoanStudent(studentId) {
  const student = Store.studentById(studentId);
  if (!student) return;
  scannedLoanStudentId = studentId;
  const studentInput = Utils.el("student-input");
  if (studentInput) studentInput.value = student.card||student.carteirinha||student.id||"";
  lookupStudent();
}

function clearLoanScanStudent() {
  scannedLoanStudentId = null;
  pendingReturnLoanId = null;
  renderLoanScanPanel();
}

function renderLoanScanPanel() {
  const panel = Utils.el("loan-scan-panel");
  if (!panel) return;
  if (!scannedLoanStudentId) {
    panel.innerHTML = `<div style="display:flex;align-items:center;gap:0.5rem;flex-wrap:wrap;">
      <i class="ti ti-info-circle" style="font-size:1.3rem;color:var(--muted);"></i>
      <span>Use o botão "Escanear aluno" para ler a carteirinha de um aluno e exibir suas informações e histórico.</span>
    </div>`;
    return;
  }

  const student = Store.studentById(scannedLoanStudentId);
  if (!student) {
    panel.innerHTML = `<div style="color:var(--red)">Aluno não encontrado. Atualize os dados e tente novamente.</div>`;
    return;
  }

  const lockLoan = pendingReturnLoanId ? Store.loanById(pendingReturnLoanId) : null;
  const lockStudent = lockLoan ? Store.studentById(lockLoan.aluno_id) : null;
  const loans = Store.loans().filter(l => l.aluno_id === student.id).sort((a,b)=>b.data_emprestimo.localeCompare(a.data_emprestimo));
  const active = loans.filter(l => !l.devolvido_em);
  const overdue = active.filter(l => Utils.daysLeft(l.data_devolucao_prevista) < 0);
  const room = Store.rooms().find(r => r.id === student.sala_id);
  const status = overdue.length ? `Irregular — ${overdue.length} atraso(s)` : active.length ? `${active.length} empréstimo(s) ativo(s)` : `Regular`;
  const badgeClass = overdue.length ? "badge-red" : active.length ? "badge-amber" : "badge-green";

  const lockBlock = lockLoan && !lockLoan.devolvido_em
    ? `<div style="margin-bottom:0.9rem;padding:0.8rem;border:1px solid var(--amber);background:rgba(245,158,11,0.12);border-radius:10px;">
        <div style="font-weight:700;color:var(--amber);margin-bottom:0.25rem;"><i class="ti ti-lock"></i> Exemplar travado para devolução</div>
        <div><strong>${lockStudent?.nome||lockStudent?.name||"—"}</strong> está com este exemplar.</div>
        <div style="font-size:0.9rem;color:var(--muted);margin-top:0.2rem;">Leia a carteirinha do aluno para registrar a devolução.</div>
      </div>`
    : "";

  panel.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:0.75rem;flex-wrap:wrap;">
      <div style="min-width:240px;flex:1;">
        ${lockBlock}
        <div style="padding:0.75rem;border:1px solid var(--border);border-radius:10px;">
          <div style="font-weight:600;font-size:1rem;margin-bottom:0.25rem;">${student.nome||student.name||"—"}</div>
          <div style="font-size:0.9rem;color:var(--muted);">${student.carteirinha||student.card||student.id.slice(0,8)} · ${student.turma||student.class||"Sem turma"}${room?` · ${room.nome}`:""}</div>
          <div style="margin-top:0.75rem;"><span class="badge ${badgeClass}">${status}</span></div>
        </div>
      </div>
      <div style="display:flex;gap:0.5rem;flex-wrap:wrap;align-items:center;">
        <button class="btn btn-primary" onclick="selectLoanStudent('${student.id}')"><i class="ti ti-plus"></i> Usar aluno</button>
        <button class="btn btn-secondary" onclick="clearLoanScanStudent()"><i class="ti ti-x"></i> Limpar</button>
      </div>
    </div>
    <div style="margin-top:1rem;">
      <div style="font-size:0.95rem;font-weight:600;margin-bottom:0.5rem;">Empréstimos ativos</div>
      ${active.length ? active.map(l => {
        const book = Store.bookById(l.livro_id);
        const dl = Utils.daysLeft(l.data_devolucao_prevista);
        return `<div style="display:flex;justify-content:space-between;align-items:center;padding:0.65rem 0;border-bottom:1px solid var(--border);">
          <div style="min-width:0;">
            <strong style="display:block;margin-bottom:0.2rem;">${book?.titulo||book?.title||"—"} #${l.exemplar}</strong>
            <small style="color:var(--muted);">${Utils.fmtDate(l.data_devolucao_prevista)} · ${Utils.statusBadge(Store.loanStatus(l), dl)}</small>
          </div>
          <div style="display:flex;gap:0.35rem;flex-wrap:wrap;">
            <button class="btn btn-sm" onclick="openRenewal('${l.id}')"><i class="ti ti-rotate-clockwise"></i>Renovar</button>
            <button class="btn btn-sm btn-success" onclick="openDevolution('${l.id}')"><i class="ti ti-check"></i>Devolver</button>
          </div>
        </div>`;
      }).join("") : `<div class="empty-state" style="padding:1rem;">Nenhum empréstimo ativo para este aluno.</div>`}
    </div>
    <div style="margin-top:1rem;font-size:0.92rem;color:var(--muted);">Histórico total: ${loans.length} empréstimo(s). Último registro: ${loans.length ? Utils.fmtDate(loans[0].data_emprestimo) : "—"}.</div>
  `;
}


// ── Config ────────────────────────────────────────────────────────────
async function testConnection() {
  const btn = Utils.el("test-conn-btn");
  if (btn) btn.disabled = true;
  try {
    const r = await API.health();
    Utils.toast(r.database === "conectado" ? "Supabase conectado!" : "Offline — usando dados locais.", r.database==="conectado"?"success":"info");
  } catch { Utils.toast("Backend não encontrado.","error"); }
  finally { if (btn) btn.disabled = false; }
}

// Gera e abre para impressão a carteirinha do usuário admin logado
async function printAdminCard() {
  if (!currentUser?.login) return;
  Utils.toast("Gerando carteirinha...","info");
  try {
    const res = await API.qr.cardAdmin(currentUser.login);
    _showPrintCard(res.image, res.filename);
  } catch(e) { Utils.toast("Erro ao gerar carteirinha: "+e.message,"error"); }
}

// ── Câmera global (topbar) — ler QR de carteirinha de aluno ────────────
async function openGlobalScanner() {
  await QRScanner.start(null, async (res) => {
    const scanned = await resolveQRCodeAsync(res.primary);
    const currentPage = Utils.qs(".page.active")?.id;

    if (scanned.type === "student" && scanned.data?.id) {
      if (!Store.studentById(scanned.data.id)) await syncData();
      const student = Store.studentById(scanned.data.id) || scanned.data;

      if (currentPage === "page-emprestimo") {
        const input = Utils.el("student-input");
        if (input) input.value = student.carteirinha||student.card||student.id;
        setLoanStudent(student);
        showStudentHistory(student.id);
        Utils.toast(`Aluno registrado para empréstimo: ${student.nome||student.name}`, "success");
        return;
      }

      showStudentHistory(student.id);
      return;
    }

    if (scanned.type === "book" && scanned.data?.id) {
      const targetExemplar = scanned.data.exemplar || null;
      const activeLoan = Store.loans().find((loan) => loan.livro_id === scanned.data.id && !loan.devolvido_em && (!targetExemplar || loan.exemplar === targetExemplar));
      if (activeLoan) {
        const student = Store.studentById(activeLoan.aluno_id);
        Utils.toast(`Este exemplar já está emprestado. Use o histórico do aluno para devolver ou renovar.`, "info");
        if (student) showStudentHistory(student.id);
        return;
      }
      if (currentPage === "page-emprestimo") {
        const input = Utils.el("isbn-input");
        if (input) input.value = scanned.data.id;
        lookupBook();
        Utils.toast(`Livro registrado no formulário de empréstimo: ${scanned.data.titulo||scanned.data.title}`, "success");
        return;
      }
      const total = scanned.data.exemplares||scanned.data.copies||1;
      const active = Store.loans().filter(l=>l.livro_id===scanned.data.id && !l.devolvido_em).length;
      Utils.toast(`📖 ${scanned.data.titulo||scanned.data.title} — ${total-active} de ${total} disponíveis`, "info");
      return;
    }

    if (scanned.type === "admin") {
      Utils.toast("Este é um cartão administrativo. Faça login com ele na tela inicial.","info");
      return;
    }

    Utils.toast("Código não reconhecido — não corresponde a um aluno ou livro cadastrado.","error");
  });
}

function decodeQrPayload(code) {
  return resolveQRCode(code);
}

// ── Init ──────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  loadSupabaseConfig?.().then((config) => {
    if (!config) {
      const status = Utils.el("cloud-status");
      if (status && !status.textContent.includes("Offline")) {
        status.innerHTML = `<span style="color:var(--amber)"><i class="ti ti-cloud-off"></i> Conexão Supabase não disponível — usando dados locais</span>`;
      }
    }
  });

  // Login ao pressionar Enter
  Utils.el("login-pass")?.addEventListener("keydown", e => { if (e.key==="Enter") doLogin(); });
  Utils.el("login-user")?.addEventListener("keydown", e => { if (e.key==="Enter") doLogin(); });

  // Botão login — apenas um handler
  Utils.el("login-btn")?.addEventListener("click", doLogin);

  // Ações principais sem depender de onclick inline (compatível com CSP mais restritiva)
  Utils.el("login-card-form")?.querySelector(".btn-qr-login")?.addEventListener("click", startQRLogin);
  Utils.el("app")?.querySelector(".logout-btn")?.addEventListener("click", doLogout);
  Utils.el("app")?.querySelector(".topbar-cam-btn")?.addEventListener("click", openGlobalScanner);
  Utils.el("mobile-nav-toggle")?.addEventListener("click", () => toggleMobileSidebar());
  Utils.el("sidebar-backdrop")?.addEventListener("click", () => toggleMobileSidebar(false));
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") toggleMobileSidebar(false);
  });

  setupNavigationBindings();
  improveFormAccessibility();

  // Atualiza prévia da nova data ao trocar o prazo de renovação
  Utils.el("renew-days")?.addEventListener("change", _updateRenewalPreview);

  // Data inicial
  const ld = Utils.el("loan-date");
  if (ld) { ld.value = Utils.today(); updateDueDate(); }
});