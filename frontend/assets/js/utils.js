/**
 * assets/js/utils.js
 * Utilitários gerais: datas, toast, modal, DOM.
 */

const Utils = {
  today:   () => new Date().toISOString().slice(0, 10),

  addDays(dateStr, n) {
    const d = new Date(dateStr);
    d.setDate(d.getDate() + n);
    return d.toISOString().slice(0, 10);
  },

  fmtDate(d) {
    if (!d) return "—";
    const s = String(d).slice(0, 10);
    const [y, m, day] = s.split("-");
    return `${day}/${m}/${y}`;
  },

  daysLeft(dueDate) {
    if (!dueDate) return 0;
    const now = new Date(); now.setHours(0, 0, 0, 0);
    const due = new Date(String(dueDate).slice(0, 10)); due.setHours(0, 0, 0, 0);
    return Math.round((due - now) / 86400000);
  },

  uid: () =>
    "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, c => {
      const r = (Math.random() * 16) | 0;
      return (c === "x" ? r : (r & 0x3) | 0x8).toString(16);
    }),

  // ── Toast ─────────────────────────────────────────────────────
  toast(msg, type = "info") {
    const icons = { success: "ti-circle-check", error: "ti-alert-circle", info: "ti-info-circle" };
    const el    = document.createElement("div");
    el.className = `toast-item t-${type}`;
    el.innerHTML = `<i class="ti ${icons[type] || icons.info}"></i><span>${msg}</span>`;
    document.getElementById("toast")?.appendChild(el);
    setTimeout(() => el.remove(), 4500);
  },

  // ── Modal ──────────────────────────────────────────────────────
  openModal:  (id) => document.getElementById(id)?.classList.add("open"),
  closeModal: (id) => document.getElementById(id)?.classList.remove("open"),

  // ── Badges ─────────────────────────────────────────────────────
  statusBadge(status, dl = 0) {
    if (status === "returned")
      return `<span class="badge badge-green"><i class="ti ti-check"></i> Devolvido</span>`;
    if (status === "overdue")
      return `<span class="badge badge-red"><i class="ti ti-clock-exclamation"></i> Atrasado ${Math.abs(dl)}d</span>`;
    if (dl === 0)
      return `<span class="badge badge-amber">Vence hoje</span>`;
    return `<span class="badge badge-amber">${dl}d restam</span>`;
  },

  // ── DOM ────────────────────────────────────────────────────────
  el:  (id)  => document.getElementById(id),
  qs:  (sel) => document.querySelector(sel),
  qsa: (sel) => [...document.querySelectorAll(sel)],

  emptyState: (icon, msg) =>
    `<tr><td colspan="99"><div class="empty-state"><i class="ti ${icon}"></i><p>${msg}</p></div></td></tr>`,
};

// Fecha modais clicando fora
document.addEventListener("click", e => {
  if (e.target.classList.contains("overlay")) e.target.classList.remove("open");
});
document.addEventListener("keydown", e => {
  if (e.key === "Escape")
    Utils.qsa(".overlay.open").forEach(o => o.classList.remove("open"));
});
