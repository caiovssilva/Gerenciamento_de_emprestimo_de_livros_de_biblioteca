/**
 * pages/genres.js  —  Gerenciamento de Gêneros de Livro
 */

function renderGenres() {
  const genres = Store.genres();
  const wrap   = Utils.el("genres-grid");
  if (!wrap) return;

  if (!genres.length) {
    wrap.innerHTML = `<div class="empty-state" style="grid-column:1/-1;"><i class="ti ti-books"></i><p>Nenhum gênero cadastrado.</p></div>`;
    return;
  }

  wrap.innerHTML = genres.map(g => {
    const total = (g.total_livros||0);
    const ico   = g.icone||"ti-book";
    const cor   = g.cor||"#6366f1";
    return `<div class="genre-card" style="border-top:3px solid ${cor};">
      <div class="genre-icon" style="background:${cor}22;color:${cor};">
        <i class="ti ${ico}"></i>
      </div>
      <div class="genre-info">
        <div class="genre-name">${g.nome}</div>
        <div class="genre-count">${total} livro(s)</div>
      </div>
      <div class="genre-actions">
        <button class="btn btn-sm" title="Editar"  onclick="editGenre('${g.id}')"><i class="ti ti-edit"></i></button>
        <button class="btn btn-sm btn-danger" title="Excluir" onclick="deleteGenre('${g.id}')"><i class="ti ti-trash"></i></button>
      </div>
    </div>`;
  }).join("");
}

function openAddGenre() {
  Utils.el("genre-edit-id").value = "";
  Utils.el("modal-genre-title").textContent = "Novo gênero";
  Utils.el("genre-name").value  = "";
  Utils.el("genre-icon").value  = "ti-book";
  Utils.el("genre-color").value = "#6366f1";
  Utils.openModal("modal-genre");
}

function editGenre(id) {
  const g = Store.genreById(id);
  if (!g) return;
  Utils.el("genre-edit-id").value           = id;
  Utils.el("modal-genre-title").textContent = "Editar gênero";
  Utils.el("genre-name").value  = g.nome||"";
  Utils.el("genre-icon").value  = g.icone||"ti-book";
  Utils.el("genre-color").value = g.cor||"#6366f1";
  Utils.openModal("modal-genre");
}

async function saveGenre() {
  const nome  = Utils.el("genre-name").value.trim();
  const icone = Utils.el("genre-icon").value.trim()||"ti-book";
  const cor   = Utils.el("genre-color").value||"#6366f1";
  const editId = Utils.el("genre-edit-id").value;

  if (!nome) { Utils.toast("Informe o nome do gênero.","error"); return; }

  try {
    const payload = { nome, icone, cor };
    if (editId) {
      await API.genres.update(editId, payload);
      Utils.toast("Gênero atualizado!","success");
    } else {
      await API.genres.create(payload);
      Utils.toast("Gênero criado!","success");
    }
    Utils.closeModal("modal-genre");
    await syncGenres();
  } catch(e) { Utils.toast("Erro: "+e.message,"error"); }
}

async function deleteGenre(id) {
  if (!confirm("Excluir este gênero? Os livros vinculados ficarão sem gênero.")) return;
  try {
    await API.genres.delete(id);
    Utils.toast("Gênero excluído.","info");
    await syncGenres();
    await syncData();
  } catch(e) { Utils.toast(e.message,"error"); }
}

async function syncGenres() {
  try {
    const genres = await API.genres.list();
    Store.setGenres(genres);
    renderGenres();
  } catch(e) { console.warn("genres sync:", e.message); }
}