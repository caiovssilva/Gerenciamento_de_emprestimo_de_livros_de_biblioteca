/**
 * assets/js/store.js — Estado global da aplicação.
 */
const Store = (() => {
  let _books=[], _students=[], _loans=[], _rooms=[], _genres=[];
  const _state = { books: _books, students: _students, loans: _loans, rooms: _rooms, genres: _genres };

  try {
    ["lib_books", "lib_students", "lib_loans", "lib_rooms", "lib_genres"]
      .forEach(key => localStorage.removeItem(key));
  } catch (error) {
    console.warn("Não foi possível remover caches antigos da biblioteca:", error);
  }

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

    setBooks:    arr => { _books    = arr.map(_normBook);    _syncState(); },
    setStudents: arr => { _students = arr.map(_normStudent); _syncState(); },
    setLoans:    arr => { _loans    = arr;                   _syncState(); },
    setRooms:    arr => { _rooms    = arr;                   _syncState(); },
    setGenres:   arr => { _genres   = arr;                   _syncState(); },

    clear() {
      _books = [];
      _students = [];
      _loans = [];
      _rooms = [];
      _genres = [];
      _syncState();
    },

    setPartial: (partial = {}) => {
      if (Array.isArray(partial.books)) _books = partial.books.map(_normBook);
      if (Array.isArray(partial.students)) _students = partial.students.map(_normStudent);
      if (Array.isArray(partial.loans)) _loans = partial.loans;
      if (Array.isArray(partial.rooms)) _rooms = partial.rooms;
      if (Array.isArray(partial.genres)) _genres = partial.genres;
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