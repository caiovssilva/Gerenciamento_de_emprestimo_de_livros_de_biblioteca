/**
 * assets/js/store.js  — v3
 * Estado global com suporte a salas e gêneros.
 */
const Store = (() => {
  const LS = {
    get: k => { try { return JSON.parse(localStorage.getItem(k)); } catch { return null; } },
    set: (k,v) => localStorage.setItem(k, JSON.stringify(v)),
  };

  let _books=[], _students=[], _loans=[], _rooms=[], _genres=[];

  function _normBook(b) {
    return { ...b, title:b.titulo||b.title||"", author:b.autor||b.author||"", copies:b.exemplares||b.copies||1 };
  }
  function _normStudent(s) {
    return { ...s, name:s.nome||s.name||"", class:s.turma||s.class||"", card:s.carteirinha||s.card||"" };
  }

  return {
    books:    () => _books,
    students: () => _students,
    loans:    () => _loans,
    rooms:    () => _rooms,
    genres:   () => _genres,

    setBooks:    arr => { _books    = arr.map(_normBook);    LS.set("lib_books",    _books);    },
    setStudents: arr => { _students = arr.map(_normStudent); LS.set("lib_students", _students); },
    setLoans:    arr => { _loans    = arr;                   LS.set("lib_loans",    _loans);    },
    setRooms:    arr => { _rooms    = arr;                   LS.set("lib_rooms",    _rooms);    },
    setGenres:   arr => { _genres   = arr;                   LS.set("lib_genres",   _genres);   },

    loadLocal() {
      _books    = (LS.get("lib_books")    ||[]).map(_normBook);
      _students = (LS.get("lib_students") ||[]).map(_normStudent);
      _loans    = LS.get("lib_loans")    ||[];
      _rooms    = LS.get("lib_rooms")    ||[];
      _genres   = LS.get("lib_genres")   ||[];
    },

    bookById:    id => _books.find(b=>b.id===id),
    studentById: id => _students.find(s=>s.id===id),
    loanById:    id => _loans.find(l=>l.id===id),
    roomById:    id => _rooms.find(r=>r.id===id),
    genreById:   id => _genres.find(g=>g.id===id),

    loanStatus(loan) {
      if (loan.devolvido_em) return "returned";
      return Utils.daysLeft(loan.data_devolucao_prevista) < 0 ? "overdue" : "active";
    },
    activeLoans:  () => _loans.filter(l=>!l.devolvido_em),
    overdueLoans: () => _loans.filter(l=>!l.devolvido_em && Utils.daysLeft(l.data_devolucao_prevista)<0),
    classes:      () => [...new Set(_students.map(s=>s.turma||s.class||""))].filter(Boolean).sort(),
  };
})();
