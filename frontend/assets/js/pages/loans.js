/**
 * assets/js/pages/loans.js  —  v3
 * Empréstimos + Dashboard com sala e gênero.
 */

function renderLoans() {
  const q      = (Utils.el("loans-search")?.value||"").toLowerCase();
  const filter = Utils.el("loans-filter")?.value||"";
  const books  = Store.books();
  const studs  = Store.students();

  let loans = [...Store.loans()].sort((a,b)=>b.data_emprestimo.localeCompare(a.data_emprestimo));
  if (filter) loans = loans.filter(l=>Store.loanStatus(l)===filter);
  if (q) loans = loans.filter(l=>{
    const b=books.find(x=>x.id===l.livro_id);
    const s=studs.find(x=>x.id===l.aluno_id);
    return (b&&(b.titulo||b.title||"").toLowerCase().includes(q))||
           (s&&(s.nome||s.name||"").toLowerCase().includes(q))||
           (s&&(s.turma||s.class||"").toLowerCase().includes(q));
  });

  const tbody = Utils.el("loans-tbody");
  if (!loans.length) { tbody.innerHTML = Utils.emptyState("ti-transfer","Nenhum registro encontrado."); return; }

  tbody.innerHTML = loans.map((l,i)=>{
    const b  = books.find(x=>x.id===l.livro_id);
    const s  = studs.find(x=>x.id===l.aluno_id);
    const st = Store.loanStatus(l);
    const dl = Utils.daysLeft(l.data_devolucao_prevista);
    const action = st!=="returned"
      ? `<button class="btn btn-sm btn-success" onclick="openDevolution('${l.id}')"><i class="ti ti-check"></i>Devolver</button>`
      : "";
    return `<tr>
      <td class="td-muted" style="font-size:11px;">${String(i+1).padStart(3,"0")}</td>
      <td><strong>${s?.nome||s?.name||"—"}</strong></td>
      <td>${s?.turma||s?.class||"—"}</td>
      <td>${b?.titulo||b?.title||"—"}</td>
      <td class="td-mono">${l.exemplar?"#"+l.exemplar:"—"}</td>
      <td>${Utils.fmtDate(l.data_emprestimo)}</td>
      <td>${Utils.fmtDate(l.data_devolucao_prevista)}</td>
      <td>${Utils.statusBadge(st,dl)}</td>
      <td>${action}</td>
    </tr>`;
  }).join("");
}

function renderDashboard() {
  const loans  = Store.loans();
  const books  = Store.books();
  const studs  = Store.students();
  const rooms  = Store.rooms();
  const active = Store.activeLoans();
  const overdue= Store.overdueLoans();
  const total  = books.reduce((a,b)=>a+(b.exemplares||b.copies||1),0);

  Utils.el("metrics-row").innerHTML = `
    <div class="metric-card"><div class="metric-label">Total de exemplares</div><div class="metric-val c-blue">${total}</div></div>
    <div class="metric-card"><div class="metric-label">Emprestados</div><div class="metric-val c-amber">${active.length}</div></div>
    <div class="metric-card"><div class="metric-label">Alunos cadastrados</div><div class="metric-val c-green">${studs.length}</div></div>
    <div class="metric-card"><div class="metric-label">Atrasados</div><div class="metric-val c-red">${overdue.length}</div></div>`;

  const priorityStudents = studs
    .map((student) => {
      const studentLoans = loans.filter((loan) => loan.aluno_id === student.id && !loan.devolvido_em);
      const overdueLoans = studentLoans.filter((loan) => Utils.daysLeft(loan.data_devolucao_prevista) < 0);
      const urgentLoans = studentLoans.filter((loan) => Utils.daysLeft(loan.data_devolucao_prevista) >= 0 && Utils.daysLeft(loan.data_devolucao_prevista) <= 2);
      return { student, studentLoans, overdueLoans, urgentLoans };
    })
    .filter((item) => item.studentLoans.length)
    .sort((a, b) => {
      if (b.overdueLoans.length !== a.overdueLoans.length) return b.overdueLoans.length - a.overdueLoans.length;
      if (b.urgentLoans.length !== a.urgentLoans.length) return b.urgentLoans.length - a.urgentLoans.length;
      return (a.student.nome || a.student.name || "").localeCompare(b.student.nome || b.student.name || "");
    })
    .slice(0, 6);

  const priorityPanel = Utils.el("dashboard-priority-students");
  if (priorityPanel) {
    priorityPanel.innerHTML = priorityStudents.length
      ? `<div class="card" style="margin-bottom:1rem;"><div class="card-header"><h2><i class="ti ti-user-check" style="vertical-align:-2px;margin-right:6px;color:var(--amber);"></i>Alunos com atenção</h2></div><div class="card-body">${priorityStudents.map(({ student, overdueLoans, urgentLoans }) => {
          const badge = overdueLoans.length ? `<span class="badge badge-red">${overdueLoans.length} atrasado(s)</span>` : urgentLoans.length ? `<span class="badge badge-amber">Vence em até 2 dias</span>` : `<span class="badge badge-green">Em dia</span>`;
          return `<button class="btn" style="display:block;width:100%;text-align:left;margin-bottom:0.5rem;" onclick="showStudentHistory('${student.id}')"><strong>${student.nome || student.name}</strong><div style="font-size:0.85rem;color:var(--muted);margin-top:0.2rem;">${badge}</div></button>`;
        }).join("")}</div></div>`
      : `<div class="card" style="margin-bottom:1rem;"><div class="card-header"><h2><i class="ti ti-user-check" style="vertical-align:-2px;margin-right:6px;color:var(--green);"></i>Alunos com atenção</h2></div><div class="card-body"><div class="empty-state"><i class="ti ti-mood-happy"></i><p>Nenhum aluno com empréstimo em risco no momento.</p></div></div></div>`;
  }

  const tbody = Utils.el("dash-loans-tbody");
  if (!active.length) {
    tbody.innerHTML = `<tr><td colspan="9"><div class="empty-state"><i class="ti ti-mood-happy"></i><p>Nenhum empréstimo ativo. Tudo em dia!</p></div></td></tr>`;
    return;
  }

  const sorted = [...active].sort((a,b)=>a.data_devolucao_prevista.localeCompare(b.data_devolucao_prevista));
  tbody.innerHTML = sorted.map(l=>{
    const b  = books.find(x=>x.id===l.livro_id);
    const s  = studs.find(x=>x.id===l.aluno_id);
    const room = rooms.find(r=>r.id===s?.sala_id);
    const dl = Utils.daysLeft(l.data_devolucao_prevista);
    const bc = dl<0?"badge-red":dl<=2?"badge-amber":"badge-green";
    const bt = dl<0?`Atrasado ${Math.abs(dl)}d`:dl===0?"Vence hoje":`${dl}d restantes`;

    // Badge de gênero
    const genBadge = b?.genero_nome
      ? `<span class="badge" style="background:${b.genero_cor||"#6366f1"}22;color:${b.genero_cor||"#6366f1"};font-size:10px;">${b.genero_nome}</span>`
      : `<span class="badge badge-gray" style="font-size:10px;">—</span>`;

    return `<tr>
      <td><strong>${s?.nome||s?.name||"—"}</strong></td>
      <td>${s?.turma||s?.class||"—"}</td>
      <td>${room?`<span class="badge badge-blue" style="font-size:10px;">${room.nome}</span>`:"<span class='badge badge-gray' style='font-size:10px;'>—</span>"}</td>
      <td>${b?.titulo||b?.title||"—"}</td>
      <td>${genBadge}</td>
      <td class="td-mono">#${l.exemplar}</td>
      <td>${Utils.fmtDate(l.data_devolucao_prevista)}</td>
      <td><span class="badge ${bc}">${bt}</span></td>
      <td><button class="btn btn-sm btn-success" onclick="openDevolution('${l.id}')"><i class="ti ti-check"></i>Devolver</button></td>
    </tr>`;
  }).join("");
}