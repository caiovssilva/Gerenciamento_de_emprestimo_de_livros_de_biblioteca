/**
 * assets/js/app.js — Controller principal: auth, navegação, sync, empréstimo, devolução.
 */

const USERS = [
  { login:"admin",      password:"ifes2024", name:"Administrador" },
  { login:"biblioteca", password:"ifes2024", name:"Bibliotecária"  },
];

// Roles: "admin" (acesso total, contas tradicionais com usuário/senha)
//        "librarian" (aluno com acesso liberado via "Permitir acesso" — vê acervo, faz/devolve/renova empréstimos)
let currentUser = null; // { role:'admin'|'librarian', login, name, student? }
let pendingLoan = { book:null, exemplar:null, student:null };
let pendingDevolutionId = null;
let _historyStudentId = null; // ID do aluno cujo histórico está aberto no momento

// ── Auth: login tradicional (usuário/senha) ───────────────────────────
function doLogin() {
  const user  = Utils.el("login-user").value.trim();
  const pass  = Utils.el("login-pass").value;
  const errEl = Utils.el("login-err");
  errEl.textContent = "";
  const found = USERS.find(u => u.login===user && u.password===pass);
  if (!found) { errEl.textContent = "Nome ou senha incorretos."; Utils.el("login-pass").value = ""; return; }
  _finishLogin({ role:"admin", login:found.login, name:found.name });
}

// ── Auth: login por QR Code (carteirinha) ─────────────────────────────
async function startQRLogin() {
  await QRScanner.start(null, async (res) => {
    const code = res.primary;
    if (!code) { Utils.toast("Código não reconhecido.","error"); return; }
    try {
      const r = await API.qr.login(code);
      if (r.access === "admin") {
        const found = USERS.find(u => u.login === r.data.login) || USERS[0];
        _showQRLoginResult({
          icon:"ti-shield-check", color:"var(--brand)",
          title:`Bem-vindo, ${found.name}`,
          sub:"Acesso administrativo confirmado.",
          action:() => _finishLogin({ role:"admin", login:found.login, name:found.name }),
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
  document.body.classList.toggle("role-librarian", isLibrarian);
  // Se a página atual ficou indisponível para o bibliotecário, redireciona
  if (isLibrarian) {
    const active = Utils.qs(".page.active");
    const adminOnlyPages = ["alunos","salas","generos","relatorios","config"];
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
  if (page==="emprestimo") { renderLoans(); resetLoanForm(); }
  if (page==="relatorios") Charts.init();
}

// ── Empréstimo ────────────────────────────────────────────────────────
function updateDueDate() {
  const days = parseInt(Utils.el("loan-days").value) || 7;
  const base = Utils.el("loan-date").value || Utils.today();
  Utils.el("due-date-text").textContent = `Devolução prevista: ${Utils.fmtDate(Utils.addDays(base,days))} (em ${days} dias)`;
}

function lookupBook() {
  const q = Utils.el("isbn-input").value.trim().toLowerCase();
  if (!q) return;
  const books = Store.books();
  const found = books.find(b =>
    (b.isbn||"").toLowerCase()===q ||
    (b.id||"").toLowerCase().startsWith(q) ||
    (b.titulo||b.title||"").toLowerCase().includes(q)
  );
  const infoEl = Utils.el("book-info");
  if (!found) { infoEl.innerHTML = `<span style="color:var(--red)"><i class="ti ti-alert-circle"></i> Livro não encontrado.</span>`; pendingLoan.book=null; return; }
  const loans  = Store.loans();
  const active = loans.filter(l=>l.livro_id===found.id && !l.devolvido_em);
  const total  = found.exemplares||found.copies||1;
  const avail  = total - active.length;
  const dispEx = Array.from({length:total},(_,i)=>String(i+1).padStart(3,"0")).filter(ex=>!active.find(l=>l.exemplar===ex));
  const genBadge = found.genero_nome ? `<span class="badge" style="background:${found.genero_cor||"#6366f1"}22;color:${found.genero_cor||"#6366f1"}">${found.genero_nome}</span>` : "";
  infoEl.innerHTML = avail>0
    ? `<div class="book-found"><strong>${found.titulo||found.title}</strong> — ${found.autor||found.author} ${genBadge}
       <br><small>${avail} de ${total} disponíveis</small>
       <div style="margin-top:6px;display:flex;gap:6px;flex-wrap:wrap;">
         ${dispEx.map(ex=>`<button class="btn btn-sm ${pendingLoan.exemplar===ex?"btn-primary":""}" onclick="selectExemplar('${found.id}','${ex}',this)">#${ex}</button>`).join("")}
       </div></div>`
    : `<div style="color:var(--red)"><i class="ti ti-alert-circle"></i> Todos os exemplares estão emprestados.</div>`;
  if (avail>0) { pendingLoan.book=found; if (!pendingLoan.exemplar && dispEx.length) selectExemplar(found.id, dispEx[0]); }
}

function selectExemplar(bookId, ex, btn) {
  pendingLoan.book     = Store.bookById(bookId);
  pendingLoan.exemplar = ex;
  Utils.qsa(".book-found .btn-sm").forEach(b => b.classList.remove("btn-primary"));
  btn?.classList.add("btn-primary");
}

function lookupStudent() {
  const q = Utils.el("student-search").value.trim().toLowerCase();
  if (!q) return;
  const studs = Store.students();
  const found = studs.find(s =>
    (s.carteirinha||s.card||"").toLowerCase()===q ||
    (s.id||"").toLowerCase().startsWith(q) ||
    (s.nome||s.name||"").toLowerCase().includes(q)
  );
  const infoEl = Utils.el("student-info");
  if (!found) { infoEl.innerHTML = `<span style="color:var(--red)"><i class="ti ti-alert-circle"></i> Aluno não encontrado.</span>`; pendingLoan.student=null; return; }
  const loans  = Store.loans().filter(l=>l.aluno_id===found.id && !l.devolvido_em);
  const overdue= loans.filter(l=>Utils.daysLeft(l.data_devolucao_prevista)<0);
  const status = overdue.length ? `<span class="badge badge-red">Irregular — ${overdue.length} atrasado(s)</span>`
               : loans.length   ? `<span class="badge badge-amber">${loans.length} empréstimo(s) ativo(s)</span>`
               : `<span class="badge badge-green">Regular</span>`;
  infoEl.innerHTML = `<div><strong>${found.nome||found.name}</strong> — ${found.turma||found.class} ${status}</div>`;
  pendingLoan.student = found;
}

async function confirmLoan() {
  if (!pendingLoan.book)    { Utils.toast("Selecione um livro.",  "error"); return; }
  if (!pendingLoan.exemplar){ Utils.toast("Selecione um exemplar.","error"); return; }
  if (!pendingLoan.student) { Utils.toast("Selecione um aluno.", "error"); return; }
  const days = parseInt(Utils.el("loan-days").value) || 7;
  const date = Utils.el("loan-date").value || Utils.today();
  const obs  = Utils.el("loan-obs").value.trim();
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
  } catch(e) { Utils.toast("Erro: "+e.message,"error"); }
}

function resetLoanForm() {
  pendingLoan = { book:null, exemplar:null, student:null };
  ["isbn-input","student-search","loan-obs"].forEach(id => { const el=Utils.el(id); if(el) el.value=""; });
  Utils.el("loan-date").value = Utils.today();
  Utils.el("loan-days").value = 7;
  Utils.el("book-info").innerHTML    = "";
  Utils.el("student-info").innerHTML = "";
  updateDueDate();
}

// ── Devolução ─────────────────────────────────────────────────────────
function openDevolution(loanId) {
  const loan = Store.loanById(loanId);
  if (!loan) return;
  const book = Store.bookById(loan.livro_id);
  const stud = Store.studentById(loan.aluno_id);
  pendingDevolutionId = loanId;
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
    await API.loans.return(pendingDevolutionId, { observacao: obs });
    Utils.toast("Devolução registrada!", "success");
    Utils.closeModal("modal-devolution");
    pendingDevolutionId = null;
    await syncData(); Charts.refresh();
    _refreshOpenStudentHistory();
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
  } catch(e) { Utils.toast("Erro: "+e.message,"error"); }
}

// Se o modal de histórico do aluno estiver aberto, redesenha com dados atualizados
function _refreshOpenStudentHistory() {
  if (Utils.el("modal-student-history")?.classList.contains("open") && _historyStudentId) {
    showStudentHistory(_historyStudentId);
  }
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
    if (res.type === "student" && res.data?.id) {
      if (!Store.studentById(res.data.id)) await syncData(); // garante que o aluno esteja no Store
      showStudentHistory(res.data.id);
      return;
    }
    if (res.type === "book" && res.data?.id) {
      const total = res.data.exemplares||res.data.copies||1;
      const active = Store.loans().filter(l=>l.livro_id===res.data.id && !l.devolvido_em).length;
      Utils.toast(`📖 ${res.data.titulo||res.data.title} — ${total-active} de ${total} disponíveis`, "info");
      return;
    }
    if (res.type === "admin") {
      Utils.toast("Este é um cartão administrativo. Faça login com ele na tela inicial.","info");
      return;
    }
    Utils.toast("Código não reconhecido — não corresponde a um aluno ou livro cadastrado.","error");
  });
}

// ── Init ──────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  // Login ao pressionar Enter
  Utils.el("login-pass")?.addEventListener("keydown", e => { if (e.key==="Enter") doLogin(); });
  Utils.el("login-user")?.addEventListener("keydown", e => { if (e.key==="Enter") doLogin(); });

  // Botão login — apenas um handler
  Utils.el("login-btn")?.addEventListener("click", doLogin);

  // Atualiza prévia da nova data ao trocar o prazo de renovação
  Utils.el("renew-days")?.addEventListener("change", _updateRenewalPreview);

  // Data inicial
  const ld = Utils.el("loan-date");
  if (ld) { ld.value = Utils.today(); updateDueDate(); }
});