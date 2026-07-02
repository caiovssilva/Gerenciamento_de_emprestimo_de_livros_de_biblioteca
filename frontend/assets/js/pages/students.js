/**
 * pages/students.js  —  Alunos com salas + QR + carteirinha imprimível
 */

function renderStudents() {
  const q    = (Utils.el("students-search")?.value||"").toLowerCase();
  const cls  = Utils.el("students-class-filter")?.value||"";
  const sala = Utils.el("students-room-filter")?.value||"";
  const all  = Store.students();

  // Preenche filtro de turmas
  const selCls = Utils.el("students-class-filter");
  if (selCls) {
    const cur = selCls.value;
    selCls.innerHTML = '<option value="">Todas as turmas</option>' +
      Store.classes().map(c=>`<option value="${c}" ${c===cur?"selected":""}>${c}</option>`).join("");
  }
  // Preenche filtro de salas
  const selRoom = Utils.el("students-room-filter");
  if (selRoom) {
    const cur = selRoom.value;
    selRoom.innerHTML = '<option value="">Todas as salas</option>' +
      Store.rooms().map(r=>`<option value="${r.id}" ${r.id===cur?"selected":""}>${r.nome}</option>`).join("");
  }

  let studs = all;
  if (q)    studs = studs.filter(s=>(s.nome||s.name||"").toLowerCase().includes(q)||(s.turma||s.class||"").toLowerCase().includes(q)||(s.carteirinha||s.card||"").includes(q));
  if (cls)  studs = studs.filter(s=>(s.turma||s.class)===cls);
  if (sala) studs = studs.filter(s=>s.sala_id===sala);

  const tbody = Utils.el("students-tbody");
  if (!studs.length) { tbody.innerHTML = Utils.emptyState("ti-users","Nenhum aluno encontrado."); return; }

  const loans = Store.loans();
  tbody.innerHTML = studs.map(s => {
    const actives = loans.filter(l=>l.aluno_id===s.id&&!l.devolvido_em);
    const overdue = actives.filter(l=>Utils.daysLeft(l.data_devolucao_prevista)<0);
    const bcls    = overdue.length?"badge-red":actives.length?"badge-amber":"badge-green";
    const btxt    = overdue.length?"Irregular":actives.length?"Com empréstimo":"Regular";
    const room    = Store.rooms().find(r=>r.id===s.sala_id);
    const roomBadge = room
      ? `<span class="badge badge-blue"><i class="ti ti-door"></i>${room.nome}</span>`
      : `<span class="badge badge-gray">Sem sala</span>`;
    const libBadge = s.is_librarian
      ? `<span class="badge badge-librarian" title="Possui acesso ao painel como Bibliotecário"><i class="ti ti-id-badge2"></i>Bibliotecário</span>`
      : "";
    const accessBtn = s.is_librarian
      ? `<button class="btn btn-sm btn-danger" title="Revogar acesso de bibliotecário" onclick="toggleLibrarianAccess('${s.id}', false)"><i class="ti ti-id-badge-off"></i></button>`
      : `<button class="btn btn-sm" title="Permitir acesso (tornar Bibliotecário)" onclick="toggleLibrarianAccess('${s.id}', true)"><i class="ti ti-id-badge2"></i></button>`;
    return `<tr>
      <td class="td-mono">${s.carteirinha||s.card||s.id.slice(0,8)}</td>
      <td><strong>${s.nome||s.name}</strong> ${libBadge}</td>
      <td>${s.turma||s.class}</td>
      <td>${roomBadge}</td>
      <td>${actives.length}</td>
      <td><span class="badge ${bcls}">${btxt}</span></td>
      <td>
        <div style="display:flex;gap:4px;flex-wrap:wrap;">
          <button class="btn btn-sm" title="Histórico"   onclick="showStudentHistory('${s.id}')"><i class="ti ti-history"></i></button>
          <button class="btn btn-sm" title="QR Code"     onclick="showEntityQR('student','${s.id}')"><i class="ti ti-qrcode"></i></button>
          <button class="btn btn-sm" title="Carteirinha" onclick="printCard('student','${s.id}')"><i class="ti ti-printer"></i></button>
          ${accessBtn}
          <button class="btn btn-sm" title="Editar"      onclick="editStudent('${s.id}')"><i class="ti ti-edit"></i></button>
          <button class="btn btn-sm btn-danger" title="Excluir" onclick="deleteStudent('${s.id}')"><i class="ti ti-trash"></i></button>
        </div>
      </td>
    </tr>`;
  }).join("");
}

// Concede ou revoga o título de Bibliotecário para um aluno.
async function toggleLibrarianAccess(studentId, grant) {
  const s = Store.studentById(studentId);
  if (!s) return;
  const action = grant ? "permitir acesso de Bibliotecário a" : "revogar o acesso de Bibliotecário de";
  if (!confirm(`Deseja ${action} ${s.nome||s.name}?`)) return;
  try {
    await API.students.toggleAccess(studentId, grant);
    Utils.toast(grant ? `${s.nome||s.name} agora é Bibliotecário(a)!` : "Acesso de bibliotecário revogado.", "success");
    await syncData();
  } catch(e) { Utils.toast("Erro: "+e.message,"error"); }
}

function openAddStudent() {
  Utils.el("student-edit-id").value = "";
  Utils.el("modal-student-title").textContent = "Cadastrar aluno";
  ["student-name","student-class","student-card"].forEach(id=>Utils.el(id).value="");
  _populateRoomSelect("student-room");
  Utils.el("student-room").value = "";
  Utils.openModal("modal-student");
}

function editStudent(id) {
  const s = Store.studentById(id);
  if (!s) return;
  Utils.el("student-edit-id").value           = id;
  Utils.el("modal-student-title").textContent = "Editar aluno";
  Utils.el("student-name").value  = s.nome||s.name||"";
  Utils.el("student-class").value = s.turma||s.class||"";
  Utils.el("student-card").value  = s.carteirinha||s.card||"";
  _populateRoomSelect("student-room");
  Utils.el("student-room").value  = s.sala_id||"";
  Utils.openModal("modal-student");
}

function _populateRoomSelect(selId) {
  const sel = Utils.el(selId);
  if (!sel) return;
  sel.innerHTML = '<option value="">— Sem sala —</option>' +
    Store.rooms().map(r=>`<option value="${r.id}">${r.nome} (${r.codigo||""})</option>`).join("");
}

async function saveStudent() {
  const nome   = Utils.el("student-name").value.trim();
  const turma  = Utils.el("student-class").value.trim().toUpperCase();
  const card   = Utils.el("student-card").value.trim();
  const sala   = Utils.el("student-room").value||null;
  const editId = Utils.el("student-edit-id").value;

  if (!nome)  { Utils.toast("Informe o nome.","error");  return; }
  if (!turma) { Utils.toast("Informe a turma.","error"); return; }

  try {
    const payload = { nome, turma, carteirinha:card, sala_id:sala };
    const duplicate = card ? Store.students().find(s => (s.carteirinha||s.card||"") === card) : null;
    if (duplicate && (!editId || duplicate.id !== editId)) {
      Utils.toast(`Carteirinha já pertence a ${duplicate.nome||duplicate.name}. Corrija antes de salvar.`, "error");
      return;
    }

    if (editId) {
      await API.students.update(editId, payload);
      Utils.toast("Aluno atualizado!","success");
      Utils.closeModal("modal-student");
    } else {
      const result = await API.students.create(payload);
      Utils.closeModal("modal-student");
      // Mostra QR gerado automaticamente
      if (result.qr_code) {
        _showQRResult(result.qr_code, `QR Code de ${nome}`, result.id, "student");
      }
      Utils.toast("Aluno cadastrado! QR Code gerado.","success");
    }
    await syncData();
  } catch(e) { Utils.toast("Erro: "+e.message,"error"); }
}

function scanStudentCard() {
  QRScanner.start('student-card', async (res) => {
    const input = Utils.el('student-card');
    if (!input) return;
    const code = (res?.primary || '').trim();
    if (!code) {
      Utils.toast('Não foi possível ler o QR. Tente novamente.', 'error');
      return;
    }

    input.value = code;
    const scanned = await resolveQRCodeAsync(code);

    if (scanned.type === 'student') {
      Utils.toast(`Carteirinha de aluno reconhecida: ${scanned.data.nome||scanned.data.name}.`, 'success');
      return;
    }

    if (scanned.type === 'book') {
      Utils.toast('O QR lido pertence a um livro. Use o campo de livro ou escaneie a carteirinha do aluno.', 'error');
      return;
    }

    if (scanned.type === 'admin') {
      Utils.toast('O QR lido é de acesso administrativo. Use a tela de login por QR.', 'error');
      return;
    }

    Utils.toast('Carteirinha preenchida. Complete os dados do aluno e salve.', 'success');
  });
}

async function deleteStudent(id) {
  if (!confirm("Excluir este aluno?")) return;
  try {
    await API.students.delete(id);
    Utils.toast("Aluno excluído.","info");
    await syncData();
  } catch(e) { Utils.toast(e.message,"error"); }
}

async function importCSV(event) {
  const file = event.target?.files?.[0];
  if (!file) return;
  const text = await file.text();
  try {
    const result = await API.students.importCSV(text);
    Utils.toast(`${result.added} importados${result.skipped?`, ${result.skipped} ignorados`:"."}`,"success");
    await syncData();
  } catch(e) { Utils.toast("Erro: "+e.message,"error"); }
  if (event.target) event.target.value = "";
}

// Estado do "pegar livro" feito de dentro do histórico do aluno
let pendingHistoryLoan = { book:null, exemplar:null };

function showStudentHistory(id) {
  const s = Store.studentById(id);
  if (!s) return;
  _historyStudentId = id;
  pendingHistoryLoan = { book:null, exemplar:null };
  Utils.el("modal-history-title").textContent = `Histórico — ${s.nome||s.name}`;

  _renderHistoryCard(s);
  _renderHistoryActiveLoans(s);
  _renderHistoryNewLoan(s);
  _renderHistoryTable(s);

  Utils.openModal("modal-student-history");
}

// ── Bloco 1: "carteirinha" visual com dados do aluno ───────────────────
function _renderHistoryCard(s) {
  const loans   = Store.loans().filter(l=>l.aluno_id===s.id && !l.devolvido_em);
  const overdue = loans.filter(l=>Utils.daysLeft(l.data_devolucao_prevista)<0);
  const room    = Store.rooms().find(r=>r.id===s.sala_id);
  const ini     = (s.nome||s.name||"?").split(" ").map(w=>w[0]).slice(0,2).join("").toUpperCase();
  const statusCls  = overdue.length ? "irregular" : "";
  const statusText = overdue.length ? `Irregular — ${overdue.length} atrasado(s)`
                    : loans.length   ? `${loans.length} empréstimo(s) ativo(s)`
                    : "Regular";
  const libBadge = s.is_librarian ? ` · <i class="ti ti-id-badge2"></i> Bibliotecário(a)` : "";

  Utils.el("student-history-card").innerHTML = `
    <div class="student-id-card">
      <div class="sic-avatar">${ini}</div>
      <div class="sic-info">
        <div class="sic-name">${s.nome||s.name}</div>
        <div class="sic-meta">
          <span><i class="ti ti-id-badge"></i> ${s.carteirinha||s.card||s.id.slice(0,8)}</span>
          <span><i class="ti ti-school"></i> ${s.turma||s.class}</span>
          <span><i class="ti ti-door"></i> ${room?room.nome:"Sem sala"}</span>${libBadge}
        </div>
      </div>
      <div class="sic-status ${statusCls}">${statusText}</div>
    </div>`;
}

// ── Bloco 2: empréstimos ativos — devolver / renovar ───────────────────
function _renderHistoryActiveLoans(s) {
  const loans = Store.loans().filter(l=>l.aluno_id===s.id && !l.devolvido_em)
    .sort((a,b)=>a.data_devolucao_prevista.localeCompare(b.data_devolucao_prevista));
  const books = Store.books();
  const el = Utils.el("student-history-active");

  if (!loans.length) {
    el.innerHTML = `<div class="active-loans-block"><h4><i class="ti ti-books" style="vertical-align:-2px;"></i> Empréstimos ativos</h4>
      <div class="empty-state" style="padding:1rem;"><i class="ti ti-mood-happy"></i><p>Nenhum empréstimo ativo.</p></div></div>`;
    return;
  }

  el.innerHTML = `<div class="active-loans-block">
    <h4><i class="ti ti-books" style="vertical-align:-2px;"></i> Empréstimos ativos (${loans.length})</h4>
    ${loans.map(l=>{
      const b  = books.find(x=>x.id===l.livro_id);
      const dl = Utils.daysLeft(l.data_devolucao_prevista);
      const renov = l.renovacoes ? `<span class="badge badge-blue" style="margin-left:4px;">Renovado ${l.renovacoes}x</span>` : "";
      return `<div class="active-loan-item">
        <div class="ali-info">
          <div class="ali-title">${b?.titulo||b?.title||"—"} <span class="td-mono" style="font-size:11px;">#${l.exemplar}</span></div>
          <div class="ali-sub">${Utils.statusBadge(Store.loanStatus(l),dl)} · Devolução: ${Utils.fmtDate(l.data_devolucao_prevista)} ${renov}</div>
        </div>
        <div class="ali-actions">
          <button class="btn btn-sm" title="Renovar por mais dias" onclick="openRenewal('${l.id}')"><i class="ti ti-rotate-clockwise"></i>Renovar</button>
          <button class="btn btn-sm btn-success" title="Registrar devolução" onclick="openDevolution('${l.id}')"><i class="ti ti-check"></i>Devolver</button>
        </div>
      </div>`;
    }).join("")}
  </div>`;
}

// ── Bloco 3: "pegar livro" — novo empréstimo a partir do histórico ─────
function _renderHistoryNewLoan(s) {
  const el = Utils.el("student-history-newloan");
  el.innerHTML = `<div class="history-new-loan">
    <h4><i class="ti ti-book-plus" style="vertical-align:-2px;"></i> Pegar livro emprestado</h4>
    <div class="barcode-row">
      <div class="form-group"><label>Buscar por título, autor, ISBN ou ID</label>
        <input type="text" id="hist-book-input" placeholder="Digite ou use a câmera..." onkeydown="if(event.key==='Enter')lookupHistoryBook()">
      </div>
      <button class="scan-btn" onclick="QRScanner.start('hist-book-input',r=>{Utils.el('hist-book-input').value=(r.type==='book'&&r.data)?r.data.id:r.primary;lookupHistoryBook();})">
        <i class="ti ti-camera"></i></button>
      <button class="scan-btn" onclick="lookupHistoryBook()"><i class="ti ti-search"></i></button>
    </div>
    <div id="hist-book-result" style="margin-top:.5rem;"></div>
    <div class="form-row cols-2" style="margin-top:.6rem;">
      <div class="form-group" style="margin-bottom:0;"><label>Prazo</label>
        <select id="hist-loan-days">
          <option value="7">7 dias (padrão)</option><option value="14">14 dias</option>
          <option value="3">3 dias</option><option value="30">30 dias</option>
        </select>
      </div>
      <div style="display:flex;align-items:flex-end;">
        <button class="btn btn-primary" style="width:100%;" onclick="confirmHistoryLoan('${s.id}')"><i class="ti ti-check"></i>Confirmar empréstimo</button>
      </div>
    </div>
  </div>`;
}

function lookupHistoryBook() {
  const q = Utils.el("hist-book-input").value.trim().toLowerCase();
  if (!q) return;
  const books = Store.books();
  const found = books.find(b =>
    (b.isbn||"").toLowerCase()===q ||
    (b.id||"").toLowerCase().startsWith(q) ||
    (b.titulo||b.title||"").toLowerCase().includes(q)
  );
  const resEl = Utils.el("hist-book-result");
  if (!found) { resEl.innerHTML = `<span style="color:var(--red);font-size:12px;"><i class="ti ti-alert-circle"></i> Livro não encontrado.</span>`; pendingHistoryLoan.book=null; pendingHistoryLoan.exemplar=null; return; }

  const loans  = Store.loans();
  const active = loans.filter(l=>l.livro_id===found.id && !l.devolvido_em);
  const total  = found.exemplares||found.copies||1;
  const avail  = total - active.length;
  const dispEx = Array.from({length:total},(_,i)=>String(i+1).padStart(3,"0")).filter(ex=>!active.find(l=>l.exemplar===ex));

  if (avail<=0) {
    resEl.innerHTML = `<div style="color:var(--red);font-size:12px;"><i class="ti ti-alert-circle"></i> Todos os exemplares de "${found.titulo||found.title}" estão emprestados.</div>`;
    pendingHistoryLoan.book=null; pendingHistoryLoan.exemplar=null; return;
  }
  pendingHistoryLoan.book = found;
  resEl.innerHTML = `<div style="font-size:12px;"><strong>${found.titulo||found.title}</strong> — ${found.autor||found.author}
    <br><small>${avail} de ${total} disponíveis — escolha o exemplar:</small>
    <div style="margin-top:4px;display:flex;gap:6px;flex-wrap:wrap;">
      ${dispEx.map(ex=>`<button class="btn btn-sm ${pendingHistoryLoan.exemplar===ex?"btn-primary":""}" onclick="selectHistoryExemplar('${found.id}','${ex}',this)">#${ex}</button>`).join("")}
    </div></div>`;
  if (!pendingHistoryLoan.exemplar) selectHistoryExemplar(found.id, dispEx[0]);
}

function selectHistoryExemplar(bookId, ex, btn) {
  pendingHistoryLoan.book     = Store.bookById(bookId);
  pendingHistoryLoan.exemplar = ex;
  Utils.qsa("#hist-book-result .btn-sm").forEach(b=>b.classList.remove("btn-primary"));
  btn?.classList.add("btn-primary");
}

async function confirmHistoryLoan(studentId) {
  if (!pendingHistoryLoan.book)     { Utils.toast("Busque e selecione um livro.","error"); return; }
  if (!pendingHistoryLoan.exemplar) { Utils.toast("Selecione um exemplar.","error"); return; }
  const days = parseInt(Utils.el("hist-loan-days")?.value)||7;
  try {
    await API.loans.create({
      livro_id: pendingHistoryLoan.book.id,
      aluno_id: studentId,
      exemplar: pendingHistoryLoan.exemplar,
      dias: days, data_emprestimo: Utils.today(),
      criado_por: currentUser?.login||"sistema",
    });
    Utils.toast(`Empréstimo registrado — ${pendingHistoryLoan.book.titulo||pendingHistoryLoan.book.title}`,"success");
    await syncData(); Charts.refresh();
    showStudentHistory(studentId); // redesenha tudo, já com o novo empréstimo
  } catch(e) { Utils.toast("Erro: "+e.message,"error"); }
}

// ── Bloco 4: histórico completo (tabela) ───────────────────────────────
function _renderHistoryTable(s) {
  const loans = Store.loans().filter(l=>l.aluno_id===s.id).sort((a,b)=>b.data_emprestimo.localeCompare(a.data_emprestimo));
  const books = Store.books();

  const html = loans.length
    ? `<h4 style="font-size:12px;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.04em;margin-bottom:.5rem;"><i class="ti ti-history" style="vertical-align:-2px;"></i> Histórico completo</h4>
       <table style="width:100%;font-size:13px;border-collapse:collapse;">
        <thead><tr>
          <th style="padding:6px 8px;text-align:left;font-size:11px;color:var(--muted);border-bottom:1px solid var(--border);">Livro</th>
          <th style="padding:6px 8px;font-size:11px;color:var(--muted);border-bottom:1px solid var(--border);">Empréstimo</th>
          <th style="padding:6px 8px;font-size:11px;color:var(--muted);border-bottom:1px solid var(--border);">Status</th>
        </tr></thead>
        <tbody>${loans.map(l=>{
          const b=books.find(x=>x.id===l.livro_id);
          const st=Store.loanStatus(l);
          const bc=st==="returned"?"badge-green":st==="overdue"?"badge-red":"badge-amber";
          const bt=st==="returned"?`Devolvido ${Utils.fmtDate(l.devolvido_em)}`:st==="overdue"?"Atrasado":"Em dia";
          return `<tr>
            <td style="padding:7px 8px;border-bottom:1px solid var(--border);">${b?.titulo||b?.title||"—"}</td>
            <td style="padding:7px 8px;border-bottom:1px solid var(--border);">${Utils.fmtDate(l.data_emprestimo)}</td>
            <td style="padding:7px 8px;border-bottom:1px solid var(--border);"><span class="badge ${bc}">${bt}</span></td>
          </tr>`;
        }).join("")}</tbody></table>`
    : `<div class="empty-state"><i class="ti ti-history"></i><p>Nenhum empréstimo no histórico.</p></div>`;

  Utils.el("student-history-content").innerHTML = html;
}