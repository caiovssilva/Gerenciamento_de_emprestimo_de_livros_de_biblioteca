/**
 * pages/rooms.js  —  Gerenciamento de Salas
 */

function renderRooms() {
  const q     = (Utils.el("rooms-search")?.value||"").toLowerCase();
  let   rooms = Store.rooms();
  if (q) rooms = rooms.filter(r=>(r.nome||"").toLowerCase().includes(q)||(r.codigo||"").toLowerCase().includes(q));

  const tbody = Utils.el("rooms-tbody");
  if (!tbody) return;
  if (!rooms.length) { tbody.innerHTML = Utils.emptyState("ti-door","Nenhuma sala cadastrada."); return; }

  const studs = Store.students();
  tbody.innerHTML = rooms.map(r => {
    const count = studs.filter(s=>s.sala_id===r.id).length;
    const pct   = r.capacidade ? Math.min(100, Math.round(count/r.capacidade*100)) : 0;
    const barColor = pct>=90?"var(--red)":pct>=70?"var(--amber)":"var(--green)";
    return `<tr>
      <td class="td-mono">${r.codigo||"—"}</td>
      <td><strong>${r.nome}</strong></td>
      <td class="td-muted">${r.descricao||"—"}</td>
      <td>${r.capacidade}</td>
      <td>
        <div style="display:flex;align-items:center;gap:8px;">
          <div style="flex:1;height:6px;background:var(--bg);border-radius:99px;overflow:hidden;min-width:60px;">
            <div style="width:${pct}%;height:100%;background:${barColor};border-radius:99px;"></div>
          </div>
          <span style="font-size:12px;font-weight:600;color:${barColor};">${count}/${r.capacidade}</span>
        </div>
      </td>
      <td>
        <div style="display:flex;gap:4px;">
          <button class="btn btn-sm" title="Ver alunos" onclick="showRoomStudents('${r.id}')"><i class="ti ti-users"></i></button>
          <button class="btn btn-sm" title="Editar"     onclick="editRoom('${r.id}')"><i class="ti ti-edit"></i></button>
          <button class="btn btn-sm btn-danger" title="Excluir" onclick="deleteRoom('${r.id}')"><i class="ti ti-trash"></i></button>
        </div>
      </td>
    </tr>`;
  }).join("");
}

function openAddRoom() {
  Utils.el("room-edit-id").value = "";
  Utils.el("modal-room-title").textContent = "Criar sala";
  ["room-name","room-code","room-desc"].forEach(id=>Utils.el(id).value="");
  Utils.el("room-cap").value = 40;
  Utils.openModal("modal-room");
}

function editRoom(id) {
  const r = Store.roomById(id);
  if (!r) return;
  Utils.el("room-edit-id").value           = id;
  Utils.el("modal-room-title").textContent = "Editar sala";
  Utils.el("room-name").value = r.nome||"";
  Utils.el("room-code").value = r.codigo||"";
  Utils.el("room-desc").value = r.descricao||"";
  Utils.el("room-cap").value  = r.capacidade||40;
  Utils.openModal("modal-room");
}

async function saveRoom() {
  const nome   = Utils.el("room-name").value.trim();
  const codigo = Utils.el("room-code").value.trim().toUpperCase();
  const desc   = Utils.el("room-desc").value.trim();
  const cap    = parseInt(Utils.el("room-cap").value)||40;
  const editId = Utils.el("room-edit-id").value;

  if (!nome) { Utils.toast("Informe o nome da sala.","error"); return; }

  try {
    const payload = { nome, codigo, descricao:desc, capacidade:cap };
    if (editId) {
      await API.rooms.update(editId, payload);
      Utils.toast("Sala atualizada!","success");
    } else {
      await API.rooms.create(payload);
      Utils.toast("Sala criada!","success");
    }
    Utils.closeModal("modal-room");
    await syncRooms();
  } catch(e) { Utils.toast("Erro: "+e.message,"error"); }
}

async function deleteRoom(id) {
  const r = Store.roomById(id);
  const studs = Store.students().filter(s=>s.sala_id===id);
  const msg = studs.length
    ? `Esta sala tem ${studs.length} aluno(s). Eles ficarão sem sala. Confirmar exclusão?`
    : "Excluir esta sala?";
  if (!confirm(msg)) return;
  try {
    await API.rooms.delete(id);
    Utils.toast("Sala excluída.","info");
    await syncRooms();
    await syncData();
  } catch(e) { Utils.toast(e.message,"error"); }
}

function showRoomStudents(roomId) {
  const r     = Store.roomById(roomId);
  if (!r) return;
  const studs = Store.students().filter(s=>s.sala_id===roomId);
  const loans = Store.loans();

  Utils.el("modal-room-students-title").textContent = `Alunos — ${r.nome}`;
  const html = studs.length
    ? `<div style="margin-bottom:.75rem;font-size:13px;color:var(--muted);">${studs.length} aluno(s) nesta sala</div>
       <table style="width:100%;font-size:13px;border-collapse:collapse;">
         <thead><tr>
           <th style="padding:6px 8px;text-align:left;font-size:11px;color:var(--muted);border-bottom:1px solid var(--border);">Nome</th>
           <th style="padding:6px 8px;font-size:11px;color:var(--muted);border-bottom:1px solid var(--border);">Turma</th>
           <th style="padding:6px 8px;font-size:11px;color:var(--muted);border-bottom:1px solid var(--border);">Situação</th>
           <th style="padding:6px 8px;font-size:11px;color:var(--muted);border-bottom:1px solid var(--border);"></th>
         </tr></thead>
         <tbody>${studs.map(s=>{
           const actives = loans.filter(l=>l.aluno_id===s.id&&!l.devolvido_em);
           const overdue = actives.filter(l=>Utils.daysLeft(l.data_devolucao_prevista)<0);
           const bc = overdue.length?"badge-red":actives.length?"badge-amber":"badge-green";
           const bt = overdue.length?"Irregular":actives.length?"Com empréstimo":"Regular";
           return `<tr>
             <td style="padding:7px 8px;border-bottom:1px solid var(--border);"><strong>${s.nome||s.name}</strong></td>
             <td style="padding:7px 8px;border-bottom:1px solid var(--border);">${s.turma||s.class}</td>
             <td style="padding:7px 8px;border-bottom:1px solid var(--border);"><span class="badge ${bc}">${bt}</span></td>
             <td style="padding:7px 8px;border-bottom:1px solid var(--border);">
               <button class="btn btn-sm" onclick="showEntityQR('student','${s.id}')"><i class="ti ti-qrcode"></i></button>
             </td>
           </tr>`;
         }).join("")}</tbody></table>`
    : `<div class="empty-state"><i class="ti ti-users-off"></i><p>Nenhum aluno nesta sala.</p></div>`;

  Utils.el("room-students-content").innerHTML = html;
  Utils.openModal("modal-room-students");
}

async function syncRooms() {
  try {
    const rooms = await API.rooms.list();
    Store.setRooms(rooms);
    renderRooms();
  } catch(e) { console.warn("rooms sync:", e.message); }
}
