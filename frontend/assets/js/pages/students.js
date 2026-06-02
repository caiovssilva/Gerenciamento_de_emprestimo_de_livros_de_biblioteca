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
    return `<tr>
      <td class="td-mono">${s.carteirinha||s.card||s.id.slice(0,8)}</td>
      <td><strong>${s.nome||s.name}</strong></td>
      <td>${s.turma||s.class}</td>
      <td>${roomBadge}</td>
      <td>${actives.length}</td>
      <td><span class="badge ${bcls}">${btxt}</span></td>
      <td>
        <div style="display:flex;gap:4px;flex-wrap:wrap;">
          <button class="btn btn-sm" title="Histórico"   onclick="showStudentHistory('${s.id}')"><i class="ti ti-history"></i></button>
          <button class="btn btn-sm" title="QR Code"     onclick="showEntityQR('student','${s.id}')"><i class="ti ti-qrcode"></i></button>
          <button class="btn btn-sm" title="Carteirinha" onclick="printCard('student','${s.id}')"><i class="ti ti-printer"></i></button>
          <button class="btn btn-sm" title="Editar"      onclick="editStudent('${s.id}')"><i class="ti ti-edit"></i></button>
          <button class="btn btn-sm btn-danger" title="Excluir" onclick="deleteStudent('${s.id}')"><i class="ti ti-trash"></i></button>
        </div>
      </td>
    </tr>`;
  }).join("");
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

function showStudentHistory(id) {
  const s = Store.studentById(id);
  if (!s) return;
  Utils.el("modal-history-title").textContent = `Histórico — ${s.nome||s.name}`;
  const loans = Store.loans().filter(l=>l.aluno_id===id).sort((a,b)=>b.data_emprestimo.localeCompare(a.data_emprestimo));
  const books = Store.books();

  const html = loans.length
    ? `<table style="width:100%;font-size:13px;border-collapse:collapse;">
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
    : `<div class="empty-state"><i class="ti ti-history"></i><p>Nenhum empréstimo.</p></div>`;

  Utils.el("student-history-content").innerHTML = html;
  Utils.openModal("modal-student-history");
}
