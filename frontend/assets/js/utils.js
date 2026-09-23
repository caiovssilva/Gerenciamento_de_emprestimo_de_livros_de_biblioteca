/**
 * assets/js/utils.js — Utilitários gerais: datas, toast, modal, DOM.
 */
const Utils = {
  today: () => {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}-${String(d.getDate()).padStart(2,"0")}`;
  },

  // Corrigido: sem bug de fuso horário (UTC-3 não adianta mais 1 dia)
  addDays(dateStr, n) {
    const [y, m, d] = dateStr.split("-").map(Number);
    const dt = new Date(y, m - 1, d + n);
    return `${dt.getFullYear()}-${String(dt.getMonth()+1).padStart(2,"0")}-${String(dt.getDate()).padStart(2,"0")}`;
  },

  fmtDate(d) {
    if (!d) return "—";
    const [y, m, day] = String(d).slice(0, 10).split("-");
    return `${day}/${m}/${y}`;
  },

  daysLeft(dueDate) {
    if (!dueDate) return 0;
    const [y, m, d] = String(dueDate).slice(0, 10).split("-").map(Number);
    const now = new Date(); now.setHours(0,0,0,0);
    const due = new Date(y, m-1, d);
    return Math.round((due - now) / 86400000);
  },

  uid: () => "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, c => {
    const r = (Math.random()*16)|0;
    return (c==="x" ? r : (r&0x3)|0x8).toString(16);
  }),

  toast(msg, type = "info") {
    const icons = { success:"ti-circle-check", error:"ti-alert-circle", info:"ti-info-circle" };
    const el = document.createElement("div");
    el.className = `toast-item t-${type}`;
    el.innerHTML = `<i class="ti ${icons[type]||icons.info}"></i><span>${msg}</span>`;
    document.getElementById("toast")?.appendChild(el);
    setTimeout(() => el.remove(), 4500);
  },

  openModal(id) {
    const el = document.getElementById(id);
    if (!el) return;
    // Garante que o modal aberto mais recentemente fique por cima de outros já abertos
    // (independente da ordem em que aparecem no DOM, ex: histórico do aluno > devolução/renovação).
    const open = Utils.qsa(".overlay.open");
    const maxZ = open.reduce((m,o)=>Math.max(m, parseInt(getComputedStyle(o).zIndex)||100), 100);
    el.style.zIndex = String(maxZ + 1);
    el.classList.add("open");
  },
  closeModal(id) {
    const el = document.getElementById(id);
    if (!el) return;
    el.classList.remove("open");
    el.style.zIndex = "";
  },

  statusBadge(status, dl = 0) {
    if (status === "returned") return `<span class="badge badge-green"><i class="ti ti-check"></i> Devolvido</span>`;
    if (status === "overdue")  return `<span class="badge badge-red"><i class="ti ti-clock-exclamation"></i> Atrasado ${Math.abs(dl)}d</span>`;
    if (dl === 0) return `<span class="badge badge-amber">Vence hoje</span>`;
    return `<span class="badge badge-amber">${dl}d restam</span>`;
  },

  el:  id  => document.getElementById(id),
  qs:  sel => document.querySelector(sel),
  qsa: sel => [...document.querySelectorAll(sel)],
  emptyState: (icon, msg) =>
    `<tr><td colspan="99"><div class="empty-state"><i class="ti ${icon}"></i><p>${msg}</p></div></td></tr>`,
};

document.addEventListener("click", e => {
  if (e.target.classList.contains("overlay")) { e.target.classList.remove("open"); e.target.style.zIndex = ""; }
});
document.addEventListener("keydown", e => {
  if (e.key === "Escape") Utils.qsa(".overlay.open").forEach(o => { o.classList.remove("open"); o.style.zIndex = ""; });
});