/**
 * pages/books.js  —  Acervo com filtro por gênero + QR + cartão imprimível
 */

function renderBooks() {
  const q      = (Utils.el("books-search")?.value||"").toLowerCase();
  const genre  = Utils.el("books-genre-filter")?.value||"";
  const books  = Store.books();
  const loans  = Store.loans();
  const genres = Store.genres();
  const loanByBook = new Map();

  loans.forEach(l => {
    if (!l.devolvido_em && l.livro_id) {
      const count = loanByBook.get(l.livro_id) || 0;
      loanByBook.set(l.livro_id, count + 1);
    }
  });

  let filtered = books;
  if (q) filtered = filtered.filter(b =>
    (b.titulo||b.title||"").toLowerCase().includes(q)||
    (b.autor||b.author||"").toLowerCase().includes(q)||
    (b.isbn||"").toLowerCase().includes(q)||
    (b.id||"").toLowerCase().startsWith(q)
  );
  if (genre) filtered = filtered.filter(b => b.genero_id === genre);

  const sel = Utils.el("books-genre-filter");
  if (sel) {
    const cur = sel.value;
    sel.innerHTML = '<option value="">Todos os gêneros</option>' +
      genres.map(g=>`<option value="${g.id}" ${g.id===cur?"selected":""}>${g.nome}</option>`).join("");
  }

  const tbody = Utils.el("books-tbody");
  if (!filtered.length) { tbody.innerHTML = Utils.emptyState("ti-books","Nenhum livro encontrado."); return; }

  tbody.innerHTML = filtered.map(b => {
    const copies = b.exemplares||b.copies||1;
    const active = loanByBook.get(b.id) || 0;
    const avail  = copies - active;
    const color  = avail===0?"var(--red)":avail<=1?"var(--amber)":"var(--green)";
    const genreStyle = b.genero_cor ? `background:${b.genero_cor}22;color:${b.genero_cor};border:1px solid ${b.genero_cor}44` : "";
    const genreBadge = b.genero_nome
      ? `<span class="badge" style="${genreStyle}"><i class="ti ${b.genero_icone||'ti-book'}"></i>${b.genero_nome}</span>`
      : `<span class="badge badge-gray">Sem gênero</span>`;

    const manageBtns = isLibrarian() ? "" : `
          <button class="btn btn-sm" title="Editar"          onclick="editBook('${b.id}')"><i class="ti ti-edit"></i></button>
          <button class="btn btn-sm btn-danger" title="Excluir" onclick="deleteBook('${b.id}')"><i class="ti ti-trash"></i></button>`;
    return `<tr>
      <td class="td-mono">${b.isbn||b.id.slice(0,8)}</td>
      <td><strong>${b.titulo||b.title}</strong></td>
      <td class="td-muted">${b.autor||b.author}</td>
      <td>${genreBadge}</td>
      <td><span class="badge badge-gray">${b.area||"—"}</span></td>
      <td>${copies}</td>
      <td style="font-weight:600;color:${color};">${avail}</td>
      <td>
        <div style="display:flex;gap:4px;flex-wrap:wrap;">
          <button class="btn btn-sm" title="Ver exemplares"  onclick="showExemplares('${b.id}')"><i class="ti ti-list-details"></i></button>
          <button class="btn btn-sm" title="QR Code"         onclick="showEntityQR('book','${b.id}')"><i class="ti ti-qrcode"></i></button>
          <button class="btn btn-sm" title="Imprimir cartão" onclick="printCard('book','${b.id}')"><i class="ti ti-printer"></i></button>${manageBtns}
        </div>
      </td>
    </tr>`;
  }).join("");
}

function openAddBook() {
  Utils.el("book-edit-id").value = "";
  Utils.el("modal-book-title").textContent = "Cadastrar livro";
  ["book-isbn","book-title","book-author"].forEach(id=>Utils.el(id).value="");
  Utils.el("book-area").value    = "Informática";
  Utils.el("book-copies").value  = 1;
  _populateGenreSelect("book-genre");
  Utils.el("book-genre").value   = "";
  Utils.el("book-isbn-status").textContent = "";
  Utils.openModal("modal-book");
}

function _normalizeIsbn(value) {
  return String(value || "").replace(/[^0-9Xx]/g, "").toUpperCase();
}

function _genreIdFromCategories(categories) {
  const available = Store.genres();
  const normalize = value => String(value || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
  const aliases = {
    "informatica": ["computer", "computing", "technology", "programming", "software"],
    "ficcao cientifica": ["science fiction", "sci-fi", "scifi"],
    "literatura brasileira": ["brazilian literature"],
    "matematica": ["mathematics", "math"],
    "engenharia": ["engineering"],
    "tecnico / didatico": ["computer", "computing", "technology", "programming", "software", "textbook", "technical"],
    "romance": ["romance", "love story"],
    "aventura": ["adventure"],
    "comedia": ["comedy", "humor"],
    "terror / suspense": ["horror", "thriller", "suspense"],
    "historia": ["history"],
    "biografia": ["biography", "autobiography"],
    "autoajuda": ["self-help", "self help"],
  };
  const normalized = (categories || []).map(normalize);
  const match = available.find(genre => {
    const name = normalize(genre.nome);
    const terms = [name, ...(aliases[name] || [])];
    return normalized.some(category => terms.some(term => category.includes(term) || term.includes(category)));
  });
  return match?.id || "";
}

async function lookupBookIsbn() {
  const input = Utils.el("book-isbn");
  const status = Utils.el("book-isbn-status");
  const isbn = _normalizeIsbn(input?.value);
  if (!isbn) {
    Utils.toast("Informe ou leia um ISBN.", "error");
    return;
  }

  status.textContent = "Pesquisando informações do livro...";
  try {
    const result = await API.books.lookupIsbn(isbn);
    if (!Store.genres().length && typeof syncGenres === "function") {
      await syncGenres();
    }
    _populateGenreSelect("book-genre");
    input.value = result.isbn || isbn;
    Utils.el("book-title").value = result.titulo || "";
    Utils.el("book-author").value = result.autor || "";
    Utils.el("book-genre").value = _genreIdFromCategories(result.categorias);
    status.textContent = result.categorias?.length
      ? `Encontrado: ${result.categorias.join(", ")}`
      : "Livro encontrado. Escolha o gênero manualmente, se necessário.";
    Utils.toast("Dados do livro preenchidos. Confira antes de salvar.", "success");
  } catch (error) {
    status.textContent = "Livro não encontrado. Você pode preencher os dados manualmente.";
    Utils.toast(error.message || "Livro não encontrado.", "error");
  }
}

function scanBookIsbn() {
  QRScanner.start("book-isbn", result => {
    const value = _normalizeIsbn(result.primary);
    Utils.el("book-isbn").value = value;
    lookupBookIsbn();
  });
}

function editBook(id) {
  const b = Store.bookById(id);
  if (!b) return;
  Utils.el("book-edit-id").value           = id;
  Utils.el("modal-book-title").textContent = "Editar livro";
  Utils.el("book-isbn").value    = b.isbn||"";
  Utils.el("book-title").value   = b.titulo||b.title||"";
  Utils.el("book-author").value  = b.autor||b.author||"";
  Utils.el("book-area").value    = b.area||"Geral";
  Utils.el("book-copies").value  = b.exemplares||b.copies||1;
  _populateGenreSelect("book-genre");
  Utils.el("book-genre").value   = b.genero_id||"";
  Utils.openModal("modal-book");
}

function _populateGenreSelect(selId) {
  const sel = Utils.el(selId);
  if (!sel) return;
  sel.innerHTML = '<option value="">— Sem gênero —</option>' +
    Store.genres().map(g=>`<option value="${g.id}">${g.nome}</option>`).join("");
}

async function saveBook() {
  const isbn   = Utils.el("book-isbn").value.trim();
  const titulo = Utils.el("book-title").value.trim();
  const autor  = Utils.el("book-author").value.trim();
  const area   = Utils.el("book-area").value;
  const copies = parseInt(Utils.el("book-copies").value)||1;
  const genre  = Utils.el("book-genre").value||null;
  const editId = Utils.el("book-edit-id").value;

  if (!titulo) { Utils.toast("Informe o título.", "error"); return; }
  if (!autor)  { Utils.toast("Informe o autor.",  "error"); return; }

  try {
    const payload = { isbn, titulo, autor, area, exemplares:copies, genero_id:genre };
    if (editId) {
      await API.books.update(editId, payload);
      Utils.toast("Livro atualizado!", "success");
      Utils.closeModal("modal-book");
    } else {
      const result = await API.books.create(payload);
      Utils.closeModal("modal-book");
      // Mostra QR Code gerado automaticamente
      if (result.qr_code) {
        _showQRResult(result.qr_code, `QR Code do livro: ${titulo}`, result.id, "book");
      }
      Utils.toast("Livro cadastrado! QR Code gerado.", "success");
    }
    await syncData();
    Charts.refresh();
  } catch(e) { Utils.toast("Erro: "+e.message,"error"); }
}

async function deleteBook(id) {
  if (!confirm("Excluir este livro do acervo?")) return;
  try {
    await API.books.delete(id);
    Utils.toast("Livro excluído.","info");
    await syncData(); Charts.refresh();
  } catch(e) { Utils.toast(e.message,"error"); }
}

function showExemplares(bookId) {
  const book = Store.bookById(bookId);
  if (!book) return;
  Utils.el("modal-ex-title").textContent = `Exemplares — ${book.titulo||book.title}`;

  const loans   = Store.loans();
  const studs   = Store.students();
  const loanMap = {};
  loans.filter(l=>l.livro_id===bookId&&!l.devolvido_em).forEach(l=>{loanMap[l.exemplar]=l;});

  const total = book.exemplares||book.copies||1;
  const all   = Array.from({length:total},(_,i)=>String(i+1).padStart(3,"0"));

  const html = all.map(ex => {
    const loan = loanMap[ex];
    if (loan) {
      const s  = studs.find(x=>x.id===loan.aluno_id);
      const dl = Utils.daysLeft(loan.data_devolucao_prevista);
      const tag = dl<0
        ? `<span class="badge badge-red">Atrasado ${Math.abs(dl)}d</span>`
        : `<span class="badge badge-amber">Dev. ${Utils.fmtDate(loan.data_devolucao_prevista)}</span>`;
      return `<div class="exemplar-item unavailable">
        <div><span class="exemplar-code">#${ex}</span> — ${s?.nome||s?.name||"Desconhecido"}</div>
        <div style="display:flex;align-items:center;gap:6px;">
          ${tag}
          <button class="btn btn-sm btn-success" onclick="openDevolution('${loan.id}');Utils.closeModal('modal-exemplares')">Devolver</button>
        </div>
      </div>`;
    }
    return `<div class="exemplar-item"><span class="exemplar-code">#${ex}</span><span class="badge badge-green" style="margin-left:8px;">Disponível</span></div>`;
  }).join("");

  Utils.el("exemplares-list").innerHTML = `<div class="exemplar-list">${html}</div>`;
  Utils.openModal("modal-exemplares");
}

// ── QR Code ───────────────────────────────────────────────────
async function showEntityQR(type, id) {
  const entity = type==="book" ? Store.bookById(id) : Store.studentById(id);
  const totalExemplares = type==="book" ? (entity?.exemplares || 1) : 1;
  if (type==="book" && totalExemplares > 1) {
    // Livro com múltiplos exemplares: cada um tem seu próprio QR único, então
    // reaproveita a mesma tela que já lista todos corretamente.
    return printCard(type, id);
  }
  Utils.toast("Gerando QR Code...","info");
  try {
    const color = type==="book" ? "#1a4f8a" : "#166534";
    const res   = await API.qr.generate(id, color);
    const entityId = entity?.id || id;
    const name   = entity ? (entity.titulo||entity.nome||entity.name||entity.title||entityId.slice(0,8)) : entityId.slice(0,8);
    _showQRResult(res.image, `QR Code — ${name}`, entityId, type);
  } catch(e) { Utils.toast("Erro ao gerar QR: "+e.message,"error"); }
}

async function printCard(type, id) {
  Utils.toast("Gerando cartão...","info");
  const win = window.open("","_blank","width=700,height=350");
  if (!win) {
    Utils.toast("Pop-up bloqueado. Permita janelas e tente novamente.", "error");
    return;
  }

  const emptyHtml = `<!DOCTYPE html><html><head><title>Gerando cartão...</title><style>body{margin:0;padding:24px;font-family:Arial,sans-serif;background:#f8fafc;color:#0f172a;display:flex;align-items:center;justify-content:center;min-height:100vh;} .loading{padding:20px 28px;border-radius:12px;background:#fff;box-shadow:0 10px 24px rgba(15,23,42,.12);font-weight:600;}</style></head><body><div class="loading">Gerando cartão... Aguarde.</div></body></html>`;
  win.document.write(emptyHtml);
  win.document.close();

  try {
    const res = type==="book" ? await API.qr.cardBook(id) : await API.qr.cardStudent(id);
    const cards = res.cards || [{ image: res.image, filename: res.filename, exemplar: "" }];
    requestAnimationFrame(() => _showPrintCard(cards, win));
  } catch(e) {
    Utils.toast("Erro ao gerar cartão: "+e.message,"error");
    if (!win.closed) {
      win.document.write(`<!DOCTYPE html><html><head><title>Erro</title></head><body style="font-family:Arial,sans-serif;padding:24px;color:#0f172a;">Erro ao gerar cartão.</body></html>`);
      win.document.close();
    }
  }
}

function _showQRResult(imgSrc, label, entityId, type) {
  Utils.el("qr-result-img").src     = imgSrc;
  Utils.el("qr-result-label").textContent = label;
  Utils.el("qr-result-id").textContent    = `ID: ${entityId}`;
  Utils.el("qr-download-btn").onclick     = () => _downloadImg(imgSrc, `qr-${entityId.replace(/[^a-zA-Z0-9]/g, "")}.png`);
  Utils.el("qr-print-card-btn").onclick   = () => printCard(type, entityId);
  Utils.openModal("modal-qr-result");
}

function _showPrintCard(cards, w = null) {
  const win = w || window.open("","_blank","width=700,height=350");
  if (!win) {
    Utils.toast("Pop-up bloqueado. Permita janelas e tente novamente.", "error");
    return;
  }

  const blocks = cards.map(c => `
<div class="card-wrap">
  ${c.exemplar ? `<div class="exemplar-label">Exemplar ${c.exemplar}</div>` : ""}
  <img src="${c.image}" alt="Cartão Biblioteca narceu de paiva filho">
  <div class="actions">
    <a class="dl-btn" href="${c.image}" download="${c.filename}" style="text-decoration:none;padding:8px 20px;border-radius:6px;font-size:14px;font-weight:600;background:#f1f5f9;color:#0f172a;border:1px solid #cbd5e1;">⬇️ Baixar PNG</a>
  </div>
</div>`).join("\n");

  const render = () => {
    win.document.open();
    win.document.write(`<!DOCTYPE html>
<html><head><title>Impressão — Biblioteca narceu de paiva filho</title>
<style>
  body{margin:0;padding:24px;display:flex;flex-wrap:wrap;gap:20px;align-items:flex-start;justify-content:center;min-height:100vh;background:#f1f5f9;}
  .card-wrap{background:#fff;padding:16px;border-radius:8px;box-shadow:0 4px 20px rgba(0,0,0,.15);}
  .exemplar-label{font-weight:700;text-align:center;margin-bottom:8px;color:#1a4f8a;}
  img{display:block;max-width:400px;width:100%;}
  .actions{display:flex;gap:8px;margin-top:12px;justify-content:center;}
  button{padding:8px 20px;border:none;border-radius:6px;cursor:pointer;font-size:14px;font-weight:600;}
  .print-btn{background:#1a4f8a;color:#fff;}
  .dl-btn{background:#f1f5f9;color:#0f172a;border:1px solid #cbd5e1;}
  .top-actions{width:100%;display:flex;justify-content:center;margin-bottom:8px;}
  @media print{.actions,.top-actions{display:none;}body{background:#fff;}}
</style></head>
<body>
<div class="top-actions"><button class="print-btn" onclick="window.print()">🖨️ Imprimir ${cards.length > 1 ? `todos (${cards.length})` : ""}</button></div>
${blocks}
</body></html>`);
    win.document.close();
  };

  if (win.requestAnimationFrame) {
    win.requestAnimationFrame(render);
  } else {
    setTimeout(render, 0);
  }
}

function _downloadImg(src, filename) {
  const a  = document.createElement("a");
  a.href   = src;
  a.download = filename;
  a.click();
}