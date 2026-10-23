/**
 * assets/js/store.js — Estado global da aplicação.
 */
const Store = (() => {
  const LS = {
    get: k => { try { return JSON.parse(localStorage.getItem(k)); } catch { return null; } },
    set: (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch {} },
  };

  let _books=[], _students=[], _loans=[], _rooms=[], _genres=[];
  const _state = { books: _books, students: _students, loans: _loans, rooms: _rooms, genres: _genres };

  function _normBook(b) {
    return { ...b, title: b.titulo||b.title||"", author: b.autor||b.author||"", copies: b.exemplares||b.copies||1 };
  }
  function _normStudent(s) {
    return { ...s, name: s.nome||s.name||"", class: s.turma||s.class||"", card: s.carteirinha||s.card||"" };
  }

  const _syncState = () => {
    _state.books = _books;
    _state.students = _students;
    _state.loans = _loans;
    _state.rooms = _rooms;
    _state.genres = _genres;
    return _state;
  };

  return {
    books:    () => _books,
    students: () => _students,
    loans:    () => _loans,
    rooms:    () => _rooms,
    genres:   () => _genres,
    state:    () => _syncState(),

    setBooks:    arr => { _books    = arr.map(_normBook);    LS.set("lib_books",    _books);    _syncState(); },
    setStudents: arr => { _students = arr.map(_normStudent); LS.set("lib_students", _students); _syncState(); },
    setLoans:    arr => { _loans    = arr;                   LS.set("lib_loans",    _loans);    _syncState(); },
    setRooms:    arr => { _rooms    = arr;                   LS.set("lib_rooms",    _rooms);    _syncState(); },
    setGenres:   arr => { _genres   = arr;                   LS.set("lib_genres",   _genres);   _syncState(); },

    setPartial: (partial = {}) => {
      if (Array.isArray(partial.books)) _books = partial.books.map(_normBook);
      if (Array.isArray(partial.students)) _students = partial.students.map(_normStudent);
      if (Array.isArray(partial.loans)) _loans = partial.loans;
      if (Array.isArray(partial.rooms)) _rooms = partial.rooms;
      if (Array.isArray(partial.genres)) _genres = partial.genres;
      _syncState();
    },

    loadLocal() {
      _books    = (LS.get("lib_books")    ||[]).map(_normBook);
      _students = (LS.get("lib_students") ||[]).map(_normStudent);
      _loans    = LS.get("lib_loans")    || [];
      _rooms    = LS.get("lib_rooms")    || [];
      _genres   = LS.get("lib_genres")   || [];
      _syncState();
    },

    bookById:    id => _books.find(b => b.id===id),
    studentById: id => _students.find(s => s.id===id),
    loanById:    id => _loans.find(l => l.id===id),
    roomById:    id => _rooms.find(r => r.id===id),
    genreById:   id => _genres.find(g => g.id===id),

    loanStatus(loan) {
      if (loan.devolvido_em) return "returned";
      return Utils.daysLeft(loan.data_devolucao_prevista) < 0 ? "overdue" : "active";
    },
    activeLoans:  () => _loans.filter(l => !l.devolvido_em),
    overdueLoans: () => _loans.filter(l => !l.devolvido_em && Utils.daysLeft(l.data_devolucao_prevista) < 0),
    classes:      () => [...new Set(_students.map(s => s.turma||s.class||""))].filter(Boolean).sort(),
  };
})();