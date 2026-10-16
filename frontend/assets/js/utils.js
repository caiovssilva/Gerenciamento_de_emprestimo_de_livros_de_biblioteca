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
    const baseZ = parseInt(getComputedStyle(el).zIndex) || 100;
    const maxZ = open.reduce((m,o)=>Math.max(m, parseInt(getComputedStyle(o).zIndex)||100), baseZ);
    el.style.zIndex = String(maxZ + 1);
    el.classList.add("open");
    _syncModalInteraction();
    const dialog = el.querySelector(".modal") || el;
    _focusModal(dialog);
  },
  closeModal(id, { restoreFocus = true } = {}) {
    const el = document.getElementById(id);
    if (!el) return;
    el.classList.remove("open");
    el.style.zIndex = "";
    _syncModalInteraction();
    const previousFocus = _modalFocus.get(el);
    _modalFocus.delete(el);
    if (restoreFocus && previousFocus?.isConnected && !previousFocus.inert) previousFocus.focus();
  },

  confirmDialog(message, {
    title = "Confirmar ação",
    confirmText = "Confirmar",
    cancelText = "Cancelar",
    danger = false,
  } = {}) {
    const overlay = document.createElement("div");
    overlay.id = `app-dialog-${Utils.uid()}`;
    overlay.className = "overlay";
    overlay.innerHTML = `<section class="modal app-dialog" role="dialog" aria-modal="true">
      <div class="modal-head"><h2></h2><button class="modal-close app-dialog-close" type="button" aria-label="Fechar"><i class="ti ti-x"></i></button></div>
      <div class="modal-body"><p class="app-dialog-message"></p></div>
      <div class="modal-foot"><button class="btn app-dialog-cancel" type="button"></button><button class="btn app-dialog-confirm" type="button"></button></div>
    </section>`;
    const dialog = overlay.querySelector(".modal");
    const titleEl = overlay.querySelector(".modal-head h2");
    const messageEl = overlay.querySelector(".app-dialog-message");
    const cancelButton = overlay.querySelector(".app-dialog-cancel");
    const confirmButton = overlay.querySelector(".app-dialog-confirm");
    titleEl.textContent = title;
    messageEl.textContent = message;
    cancelButton.textContent = cancelText;
    confirmButton.textContent = confirmText;
    confirmButton.classList.add(danger ? "btn-danger" : "btn-primary");
    document.body.appendChild(overlay);

    return new Promise((resolve) => {
      let settled = false;
      const finish = (confirmed) => {
        if (settled) return;
        settled = true;
        document.removeEventListener("keydown", onKeyDown);
        try {
          Utils.closeModal(overlay.id, { restoreFocus: !confirmed });
        } finally {
          overlay.remove();
          resolve(confirmed);
        }
      };
      const onKeyDown = (event) => {
        if (event.key === "Escape") {
          event.preventDefault();
          event.stopImmediatePropagation();
          finish(false);
        }
        if (event.key === "Enter" && overlay.classList.contains("open")) {
          event.preventDefault();
          event.stopImmediatePropagation();
          finish(true);
        }
      };
      cancelButton.addEventListener("click", () => finish(false));
      confirmButton.addEventListener("click", () => finish(true));
      overlay.querySelector(".app-dialog-close").addEventListener("click", () => finish(false));
      overlay.addEventListener("click", (event) => {
        if (event.target === overlay) finish(false);
      });
      document.addEventListener("keydown", onKeyDown);
      Utils.openModal(overlay.id);
      confirmButton.focus();
    });
  },

  promptPassword({
    title = "Confirme sua senha",
    message = "Digite sua senha para continuar.",
    confirmText = "Continuar",
  } = {}) {
    const overlay = document.createElement("div");
    overlay.id = `app-dialog-${Utils.uid()}`;
    overlay.className = "overlay";
    overlay.innerHTML = `<form class="modal app-dialog app-password-dialog" role="dialog" aria-modal="true">
      <div class="modal-head"><h2></h2><button class="modal-close app-dialog-close" type="button" aria-label="Fechar"><i class="ti ti-x"></i></button></div>
      <div class="modal-body"><p class="app-dialog-message"></p><div class="form-group"><label for="app-dialog-password">Senha</label><input id="app-dialog-password" type="password" autocomplete="current-password" required></div></div>
      <div class="modal-foot"><button class="btn app-dialog-cancel" type="button">Cancelar</button><button class="btn btn-primary app-dialog-confirm" type="submit"></button></div>
    </form>`;
    const form = overlay.querySelector("form");
    const input = overlay.querySelector("#app-dialog-password");
    overlay.querySelector(".modal-head h2").textContent = title;
    overlay.querySelector(".app-dialog-message").textContent = message;
    overlay.querySelector(".app-dialog-confirm").textContent = confirmText;
    document.body.appendChild(overlay);

    return new Promise((resolve) => {
      let settled = false;
      const finish = (password) => {
        if (settled) return;
        settled = true;
        document.removeEventListener("keydown", onKeyDown);
        try {
          Utils.closeModal(overlay.id, { restoreFocus: password === null });
        } finally {
          overlay.remove();
          resolve(password);
        }
      };
      const onKeyDown = (event) => {
        if (event.key === "Escape") {
          event.preventDefault();
          event.stopImmediatePropagation();
          finish(null);
        }
      };
      form.addEventListener("submit", (event) => {
        event.preventDefault();
        if (input.value) finish(input.value);
        else input.focus();
      });
      form.querySelector(".app-dialog-cancel").addEventListener("click", () => finish(null));
      overlay.querySelector(".app-dialog-close").addEventListener("click", () => finish(null));
      overlay.addEventListener("click", (event) => {
        if (event.target === overlay) finish(null);
      });
      document.addEventListener("keydown", onKeyDown);
      Utils.openModal(overlay.id);
      input.focus();
    });
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

const _modalFocus = new WeakMap();
const _modalInertState = new Map();

function _topModal() {
  return Utils.qsa(".overlay.open").reduce((top, overlay) => {
    if (!top) return overlay;
    return (parseInt(getComputedStyle(overlay).zIndex) || 100) >=
      (parseInt(getComputedStyle(top).zIndex) || 100) ? overlay : top;
  }, null);
}

function _syncModalInteraction() {
  const top = _topModal();
  document.body.classList.toggle("modal-open", Boolean(top));

  if (top) {
    [...document.body.children].forEach((child) => {
      if (!_modalInertState.has(child)) {
        _modalInertState.set(child, {
          inert: child.inert,
          ariaHidden: child.getAttribute("aria-hidden"),
        });
      }
      const blocked = child !== top;
      child.inert = blocked;
      if (blocked) child.setAttribute("aria-hidden", "true");
      else {
        const state = _modalInertState.get(child);
        if (state.ariaHidden === null) child.removeAttribute("aria-hidden");
        else child.setAttribute("aria-hidden", state.ariaHidden);
      }
    });

    const dialog = top.querySelector(".modal") || top;
    dialog.setAttribute("role", "dialog");
    dialog.setAttribute("aria-modal", "true");
    const heading = dialog.querySelector("h2");
    if (heading?.id) dialog.setAttribute("aria-labelledby", heading.id);
  } else {
    _modalInertState.forEach((state, child) => {
      child.inert = state.inert;
      if (state.ariaHidden === null) child.removeAttribute("aria-hidden");
      else child.setAttribute("aria-hidden", state.ariaHidden);
    });
    _modalInertState.clear();
  }
}

function _focusableIn(dialog) {
  return [...dialog.querySelectorAll(
    'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
  )].filter((element) => !element.inert && element.getAttribute("aria-hidden") !== "true");
}

function _focusModal(dialog) {
  const overlay = dialog.closest(".overlay");
  if (overlay && !_modalFocus.has(overlay)) _modalFocus.set(overlay, document.activeElement);
  const focusable = _focusableIn(dialog);
  if (focusable.length) focusable[0].focus();
  else {
    if (!dialog.hasAttribute("tabindex")) dialog.setAttribute("tabindex", "-1");
    dialog.focus();
  }
}

document.addEventListener("click", (event) => {
  if (event.target.classList.contains("overlay") && event.target === _topModal()) {
    Utils.closeModal(event.target.id);
  }
});

document.addEventListener("keydown", (event) => {
  const overlay = _topModal();
  if (!overlay) return;

  if (event.key === "Escape") {
    event.preventDefault();
    Utils.closeModal(overlay.id);
    return;
  }
  if (event.key !== "Tab") return;

  const dialog = overlay.querySelector(".modal") || overlay;
  const focusable = _focusableIn(dialog);
  if (!focusable.length) {
    event.preventDefault();
    dialog.focus();
    return;
  }
  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  if (event.shiftKey && (document.activeElement === first || !dialog.contains(document.activeElement))) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && (document.activeElement === last || !dialog.contains(document.activeElement))) {
    event.preventDefault();
    first.focus();
  }
});