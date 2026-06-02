/**
 * assets/js/app.js  —  v3
 * Controller principal: auth, navegação, sync, empréstimo, devolução.
 */

const SUPABASE_URL = "https://jwncagbmqipbzoeldlet.supabase.co";
const SUPABASE_KEY = "sb_publishable_erfwnkHOevFoIX1pHN-9-g_i8xcqPkX";

const USERS = [
  { login:"admin",      password:"ifes2024", name:"Administrador" },
  { login:"biblioteca", password:"ifes2024", name:"Bibliotecária"  },
];
let currentUser=null, pendingLoan={book:null,exemplar:null,student:null}, pendingDevolutionId=null;

// ── Auth ──────────────────────────────────────────────────────────────
function doLogin() {
  const user=Utils.el("login-user").value.trim(), pass=Utils.el("login-pass").value;
  const errEl=Utils.el("login-err"); errEl.textContent="";
  const found=USERS.find(u=>u.login===user&&u.password===pass);
  if (!found) { errEl.textContent="nome ou senha inseridos estão incorretos"; Utils.el("login-pass").value=""; return; }
  currentUser=found;
  Utils.el("login-screen").style.display="none";
  Utils.el("app").style.display="flex";
  const ini=found.name.split(" ").map(w=>w[0]).slice(0,2).join("").toUpperCase();
  Utils.el("sb-avatar-initials").textContent=ini;
  Utils.el("sb-user-name").textContent=found.name;
  Store.loadLocal();
  syncAll();
  navigateTo("dashboard");
}
function doLogout() {
  if (!confirm("Sair do sistema?")) return;
  currentUser=null; Charts.destroy();
  Utils.el("app").style.display="none";
  Utils.el("login-screen").style.display="flex";
  Utils.el("login-user").value=""; Utils.el("login-pass").value="";
}

// ── Sync ───────────────────────────────────────────────────────────────
async function syncAll() {
  await Promise.all([syncData(), syncRooms(), syncGenres()]);
}

async function syncData() {
  const st=Utils.el("cloud-status");
  if (st) st.innerHTML=`<i class="ti ti-loader" style="animation:spin 1s linear infinite;display:inline-block;"></i> Sincronizando...`;
  try {
    const [books,students,loans]=await Promise.all([API.books.list(),API.students.list(),API.loans.list()]);
    Store.setBooks(books); Store.setStudents(students); Store.setLoans(loans);
    if (st) st.innerHTML=`<span style="color:var(--green)"><i class="ti ti-cloud-check"></i> Conectado — ${new Date().toLocaleTimeString("pt-BR")}</span>`;
    renderDashboard(); renderBooks(); renderStudents(); renderLoans();
  } catch(err) {
    if (st) st.innerHTML=`<span style="color:var(--amber)"><i class="ti ti-alert-triangle"></i> Offline — cache local</span>`;
    Store.loadLocal(); renderDashboard(); renderBooks(); renderStudents(); renderLoans();
  }
}

// ── Navegação ─────────────────────────────────────────────────────────
const PAGE_META = {
  dashboard:  { title:"Painel",          sub:"Visão geral da biblioteca",        action:"" },
  emprestimo: { title:"Empréstimos",     sub:"Registrar e gerenciar empréstimos", action:"" },
  livros:     { title:"Acervo",          sub:"Livros por gênero e área",
    action:`<button class="btn btn-primary" onclick="openAddBook()"><i class="ti ti-plus"></i>Novo livro</button>` },
  alunos:     { title:"Alunos",          sub:"Cadastro de alunos por sala",
    action:`<button class="btn btn-primary" onclick="openAddStudent()"><i class="ti ti-plus"></i>Novo aluno</button>` },
  salas:      { title:"Salas",           sub:"Organização de alunos por sala",
    action:`<button class="btn btn-primary" onclick="openAddRoom()"><i class="ti ti-plus"></i>Nova sala</button>` },
  generos:    { title:"Gêneros de Livro", sub:"Tipos e categorias do acervo",
    action:`<button class="btn btn-primary" onclick="openAddGenre()"><i class="ti ti-plus"></i>Novo gênero</button>` },
  relatorios: { title:"Relatórios",      sub:"Gráficos e exportação",
    action:`<button class="btn" onclick="Charts.refresh()"><i class="ti ti-refresh"></i>Atualizar</button>` },
  config:     { title:"Configurações",   sub:"Sistema e conexão",                action:"" },
};

function navigateTo(page) {
  Utils.qsa(".page").forEach(p=>p.classList.remove("active"));
  Utils.qsa(".nav-btn[data-page]").forEach(b=>b.classList.remove("active"));
  Utils.el("page-"+page)?.classList.add("active");
  Utils.qs(`.nav-btn[data-page="${page}"]`)?.classList.add("active");
  const meta=PAGE_META[page]||{};
  Utils.el("topbar-title").textContent=meta.title||page;
  Utils.el("topbar-sub").textContent  =meta.sub||"";
  Utils.el("topbar-actions").innerHTML=meta.action||"";
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
  const days=parseInt(Utils.el("loan-days").value)||7;
  const base=Utils.el("loan-date").value||Utils.today();
  Utils.el("due-date-text").textContent=`Devolução prevista: ${Utils.fmtDate(Utils.addDays(base,days))} (em ${days} dias)`;
}

function lookupBook() {
  const q=Utils.el("isbn-input").value.trim().toLowerCase();
  const div=Utils.el("book-result");
  if (!q) { Utils.toast("Informe o código, ISBN ou ID.","error"); return; }

  const book=Store.books().find(b=>
    (b.isbn||"").toLowerCase()===q||
    (b.titulo||b.title||"").toLowerCase().includes(q)||
    (b.id||"").toLowerCase().startsWith(q)
  );
  if (!book) {
    pendingLoan.book=null;
    div.innerHTML=`<div class="lookup-result error"><i class="ti ti-alert-circle"></i><div><div class="lr-name">Livro não encontrado</div></div></div>`;
    return;
  }
  const used=Store.loans().filter(l=>l.livro_id===book.id&&!l.devolvido_em).map(l=>l.exemplar);
  const avail=Array.from({length:book.exemplares||book.copies||1},(_,i)=>String(i+1).padStart(3,"0")).filter(c=>!used.includes(c));
  if (!avail.length) {
    pendingLoan.book=null;
    div.innerHTML=`<div class="lookup-result error"><i class="ti ti-books-off"></i><div><div class="lr-name">${book.titulo||book.title}</div><div class="lr-sub">Todos os exemplares estão emprestados.</div></div></div>`;
    return;
  }
  pendingLoan.book=book; pendingLoan.exemplar=avail[0];
  const genBadge=book.genero_nome?`<span class="badge" style="background:${book.genero_cor||"#6366f1"}22;color:${book.genero_cor||"#6366f1"};">${book.genero_nome}</span>`:"";
  div.innerHTML=`<div class="lookup-result book"><i class="ti ti-book"></i><div>
    <div class="lr-name">${book.titulo||book.title} ${genBadge}</div>
    <div class="lr-sub">${book.autor||book.author} · Exemplar <strong>#${avail[0]}</strong> · ${avail.length} disponível(is)</div>
  </div></div>`;
}

function lookupStudent() {
  const q=Utils.el("student-input").value.trim().toLowerCase();
  const div=Utils.el("student-result");
  if (!q) { Utils.toast("Informe a carteirinha ou ID.","error"); return; }
  const s=Store.students().find(st=>
    (st.carteirinha||st.card||"").toLowerCase()===q||
    (st.nome||st.name||"").toLowerCase().includes(q)||
    (st.id||"").toLowerCase().startsWith(q)
  );
  if (!s) { pendingLoan.student=null; div.innerHTML=`<div class="lookup-result error"><i class="ti ti-user-off"></i><div><div class="lr-name">Aluno não encontrado</div></div></div>`; return; }
  const overdue=Store.loans().filter(l=>l.aluno_id===s.id&&!l.devolvido_em&&Utils.daysLeft(l.data_devolucao_prevista)<0);
  const warn=overdue.length?`<div class="alert alert-red" style="margin-top:.5rem;"><i class="ti ti-alert-triangle"></i>${overdue.length} empréstimo(s) em atraso!</div>`:"";
  const room=Store.rooms().find(r=>r.id===s.sala_id);
  pendingLoan.student=s;
  div.innerHTML=`<div class="lookup-result student"><i class="ti ti-user-check"></i><div>
    <div class="lr-name">${s.nome||s.name}</div>
    <div class="lr-sub">Turma ${s.turma||s.class}${room?" · Sala: "+room.nome:""}${s.carteirinha?" · "+s.carteirinha:""}</div>
  </div></div>${warn}`;
}

async function confirmLoan() {
  if (!pendingLoan.book||!pendingLoan.student) { Utils.toast("Localize o livro e o aluno primeiro.","error"); return; }
  const loanDate=Utils.el("loan-date").value||Utils.today();
  const days=parseInt(Utils.el("loan-days").value)||7;
  try {
    await API.loans.create({ livro_id:pendingLoan.book.id, aluno_id:pendingLoan.student.id, dias:days, data_emprestimo:loanDate, criado_por:currentUser?.login||"system" });
    Utils.toast(`Empréstimo registrado! Devolução: ${Utils.fmtDate(Utils.addDays(loanDate,days))}`,"success");
    resetLoanForm(); await syncData(); Charts.refresh();
  } catch(e) { Utils.toast("Erro: "+e.message,"error"); }
}

function resetLoanForm() {
  pendingLoan={book:null,exemplar:null,student:null};
  Utils.el("isbn-input").value=""; Utils.el("student-input").value="";
  Utils.el("book-result").innerHTML=""; Utils.el("student-result").innerHTML="";
  Utils.el("loan-date").value=Utils.today(); updateDueDate();
}

// ── Devolução ──────────────────────────────────────────────────────────
function openDevolution(loanId) {
  const loan=Store.loans().find(l=>l.id===loanId); if (!loan) return;
  pendingDevolutionId=loanId;
  const b=Store.books().find(x=>x.id===loan.livro_id);
  const s=Store.students().find(x=>x.id===loan.aluno_id);
  const dl=Utils.daysLeft(loan.data_devolucao_prevista);
  const late=dl<0?`<div class="row"><span>Atraso</span><strong style="color:var(--red);">${Math.abs(dl)} dia(s)</strong></div>`:"";
  Utils.el("dev-info").innerHTML=`
    <div class="row"><span>Aluno</span><strong>${s?.nome||s?.name||"—"}</strong></div>
    <div class="row"><span>Turma</span><strong>${s?.turma||s?.class||"—"}</strong></div>
    <div class="row"><span>Livro</span><strong>${b?.titulo||b?.title||"—"}</strong></div>
    <div class="row"><span>Exemplar</span><strong>#${loan.exemplar}</strong></div>
    <div class="row"><span>Devolução prevista</span><strong>${Utils.fmtDate(loan.data_devolucao_prevista)}</strong></div>${late}`;
  Utils.el("dev-obs").value="";
  Utils.openModal("modal-devolution");
}

async function confirmDevolution() {
  if (!pendingDevolutionId) return;
  try {
    await API.loans.return(pendingDevolutionId,{observacao:Utils.el("dev-obs").value.trim()});
    Utils.toast("Devolução registrada!","success");
    Utils.closeModal("modal-devolution"); pendingDevolutionId=null;
    await syncData(); Charts.refresh();
  } catch(e) { Utils.toast("Erro: "+e.message,"error"); }
}

// ── Leitor QR (câmera do browser) ────────────────────────────────────
// Quando o QR é lido, o backend resolve o tipo (livro/aluno) automaticamente
// e o frontend preenche o campo correto ou exibe informações
async function handleQRResolved(result) {
  if (!result || !result.primary) return;
  if (result.type==="book" && result.data) {
    Utils.el("isbn-input").value = result.data.id;
    lookupBook();
  } else if (result.type==="student" && result.data) {
    Utils.el("student-input").value = result.data.id;
    lookupStudent();
  } else {
    // Tenta como texto genérico
    Utils.toast("Código lido: "+result.primary,"info");
  }
}

// ── Init ───────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  Utils.el("login-user")?.focus();
  ["login-user","login-pass"].forEach(id=>Utils.el(id)?.addEventListener("keydown",e=>{if(e.key==="Enter")doLogin();}));
  // Garantir que o botão de login dispare a função mesmo se onclick inline falhar
  const loginBtn = document.getElementById("login-btn");
  if (loginBtn) loginBtn.addEventListener("click", doLogin);
  if (loginBtn) loginBtn.onclick = doLogin;

  Utils.qsa(".nav-btn[data-page]").forEach(btn=>btn.addEventListener("click",()=>navigateTo(btn.dataset.page)));

  Utils.qsa("#emp-tabs .tab-btn").forEach(btn=>{
    btn.addEventListener("click",()=>{
      Utils.qsa("#emp-tabs .tab-btn").forEach(b=>b.classList.remove("active")); btn.classList.add("active");
      Utils.el("tab-novo").style.display  =btn.dataset.tab==="novo"  ?"block":"none";
      Utils.el("tab-lista").style.display =btn.dataset.tab==="lista" ?"block":"none";
      if (btn.dataset.tab==="lista") renderLoans();
    });
  });

  // Drag&drop CSV
  const zone=Utils.el("import-zone");
  if (zone) {
    zone.addEventListener("dragover", e=>{e.preventDefault();zone.classList.add("drag-over");});
    zone.addEventListener("dragleave",()=>zone.classList.remove("drag-over"));
    zone.addEventListener("drop",e=>{
      e.preventDefault();zone.classList.remove("drag-over");
      const file=e.dataTransfer.files[0];
      if (file?.name.endsWith(".csv")) importCSV({target:{files:[file]}});
      else Utils.toast("Apenas .csv são aceitos.","error");
    });
  }
});
