/**
 * assets/js/api.js  —  v3
 * Comunicação com o backend Flask.
 */

// Supabase config is provided by assets/js/lib/supabase-config.js when needed.
const API_BASE = (() => {
  const origin = window.location.origin;
  if (origin && origin !== "null") return `${origin}/api`;
  return "http://localhost:5000/api";
})();

async function apiFetch(path, options = {}) {
  try {
    const res = await fetch(API_BASE + path, {
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
      ...options,
    });
    if (res.status === 204) return {};

    const rawText = await res.text();
    let data = {};
    if (rawText) {
      try {
        data = JSON.parse(rawText);
      } catch {
        data = { error: rawText };
      }
    }

    if (!res.ok) throw new Error(data.error || `Erro HTTP ${res.status}`);
    return data;
  } catch (err) {
    console.error("[API]", path, err.message || err);
    throw err;
  }
}

const API = {
  books: {
    list:   (q="", genre="") => apiFetch(`/books/?q=${encodeURIComponent(q)}&genre=${encodeURIComponent(genre)}`),
    get:    id               => apiFetch(`/books/${id}`),
    create: body             => apiFetch("/books/",      { method:"POST",   body:JSON.stringify(body) }),
    update: (id,body)        => apiFetch(`/books/${id}`, { method:"PUT",    body:JSON.stringify(body) }),
    delete: id               => apiFetch(`/books/${id}`, { method:"DELETE" }),
  },
  students: {
    list:      (q="",cls="",sala="") => apiFetch(`/students/?q=${encodeURIComponent(q)}&class=${encodeURIComponent(cls)}&sala_id=${encodeURIComponent(sala)}`),
    get:       id                    => apiFetch(`/students/${id}`),
    create:    body                  => apiFetch("/students/",      { method:"POST",   body:JSON.stringify(body) }),
    update:    (id,body)             => apiFetch(`/students/${id}`, { method:"PUT",    body:JSON.stringify(body) }),
    delete:    id                    => apiFetch(`/students/${id}`, { method:"DELETE" }),
    importCSV: text                  => apiFetch("/students/import/csv", { method:"POST", headers:{"Content-Type":"text/plain"}, body:text }),
    toggleAccess: (id, isLibrarian)  => apiFetch(`/students/${id}/access`, { method:"PATCH", body:JSON.stringify({ is_librarian: isLibrarian }) }),
  },
  loans: {
    list:   (status="") => apiFetch(`/loans/?status=${status}`),
    get:    id           => apiFetch(`/loans/${id}`),
    create: body         => apiFetch("/loans/",              { method:"POST", body:JSON.stringify(body) }),
    return: (id,body)    => apiFetch(`/loans/${id}/return`,  { method:"POST", body:JSON.stringify(body) }),
    renew:  (id,body={}) => apiFetch(`/loans/${id}/renew`,   { method:"POST", body:JSON.stringify(body) }),
  },
  reports: {
    chartSummary:    ()          => apiFetch("/reports/chart-summary"),
    topBooks:        (n=8)       => apiFetch(`/reports/top-books?limit=${n}`),
    byClass:         ()          => apiFetch("/reports/by-class"),
    monthly:         ()          => apiFetch("/reports/monthly"),
    generateMonthly: (body={})   => apiFetch("/reports/monthly/generate", { method:"POST", body:JSON.stringify(body) }),
    exportURL:       type        => `${API_BASE}/reports/export/${type}`,
  },
  rooms: {
    list:   ()         => apiFetch("/rooms/"),
    get:    id         => apiFetch(`/rooms/${id}`),
    create: body       => apiFetch("/rooms/",      { method:"POST",   body:JSON.stringify(body) }),
    update: (id,body)  => apiFetch(`/rooms/${id}`, { method:"PUT",    body:JSON.stringify(body) }),
    delete: id         => apiFetch(`/rooms/${id}`, { method:"DELETE" }),
  },
  genres: {
    list:   ()         => apiFetch("/genres/"),
    create: body       => apiFetch("/genres/",      { method:"POST",   body:JSON.stringify(body) }),
    update: (id,body)  => apiFetch(`/genres/${id}`, { method:"PUT",    body:JSON.stringify(body) }),
    delete: id         => apiFetch(`/genres/${id}`, { method:"DELETE" }),
  },
  qr: {
    decode:        b64        => apiFetch("/qr/decode",             { method:"POST", body:JSON.stringify({ image:b64 }) }),
    generate:      (data,col) => apiFetch("/qr/generate",           { method:"POST", body:JSON.stringify({ data, color:col }) }),
    cardBook:      id         => apiFetch(`/qr/card/book/${id}`),
    cardStudent:   id         => apiFetch(`/qr/card/student/${id}`),
    cardAdmin:     login      => apiFetch(`/qr/card/admin/${login}`),
    login:         code       => apiFetch("/qr/login",              { method:"POST", body:JSON.stringify({ code }) }),
    start:         ()         => apiFetch("/qr/start",              { method:"POST", body:"{}" }),
    stop:          ()         => apiFetch("/qr/stop",               { method:"POST", body:"{}" }),
    result:        ()         => apiFetch("/qr/result"),
  },
  health: () => apiFetch("/health"),
};