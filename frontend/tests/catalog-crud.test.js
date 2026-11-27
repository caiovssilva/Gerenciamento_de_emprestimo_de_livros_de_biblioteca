const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const elements = new Map();
const getElement = (id) => {
  if (!elements.has(id)) elements.set(id, { value: '', textContent: '', innerHTML: '' });
  return elements.get(id);
};

let books = [];
let students = [];
let bookRenders = 0;
let studentRenders = 0;
let syncCalls = 0;
const genres = [{ id: 'genre-1', nome: 'Literatura', cor: '#123456', icone: 'ti-book' }];
const context = {
  Utils: {
    el: getElement,
    toast: () => {},
    closeModal: () => {},
    confirmDialog: async () => true,
  },
  Store: {
    books: () => books,
    students: () => students,
    bookById: (id) => books.find((book) => book.id === id),
    studentById: (id) => students.find((student) => student.id === id),
    genreById: (id) => genres.find((genre) => genre.id === id),
    genres: () => genres,
    setBooks: (value) => { books = value; },
    setStudents: (value) => { students = value; },
  },
  API: {
    books: {
      create: async (payload) => ({ ...payload, id: 'book-1' }),
      update: async (id, payload) => ({ ...payload, id }),
      delete: async () => ({}),
    },
    students: {
      create: async (payload) => ({ ...payload, id: 'student-1' }),
      update: async (id, payload) => ({ ...payload, id }),
      delete: async () => ({}),
    },
  },
  Charts: { refresh: () => {} },
  isLibrarian: () => false,
  syncData: async () => { syncCalls += 1; },
  renderBooks: () => { bookRenders += 1; },
  renderStudents: () => { studentRenders += 1; },
};

vm.createContext(context);
for (const file of ['books.js', 'students.js']) {
  vm.runInContext(
    fs.readFileSync(path.join(__dirname, '../assets/js/pages', file), 'utf8'),
    context,
  );
}
context.renderBooks = () => { bookRenders += 1; };
context.renderStudents = () => { studentRenders += 1; };

(async () => {
  getElement('book-title').value = 'Livro novo';
  getElement('book-author').value = 'Autora';
  getElement('book-area').value = 'Literatura';
  getElement('book-copies').value = '1';
  getElement('book-genre').value = 'genre-1';
  await context.saveBook();
  assert.strictEqual(books[0].titulo, 'Livro novo');
  assert.strictEqual(bookRenders, 1);

  getElement('book-edit-id').value = 'book-1';
  getElement('book-title').value = 'Livro atualizado';
  await context.saveBook();
  assert.strictEqual(books.length, 1);
  assert.strictEqual(books[0].titulo, 'Livro atualizado');
  await context.deleteBook('book-1');
  assert.strictEqual(books.length, 0);
  assert.strictEqual(bookRenders, 3);

  getElement('student-name').value = 'Aluna nova';
  getElement('student-class').value = '7A';
  getElement('student-card').value = '';
  getElement('student-room').value = '';
  await context.saveStudent();
  assert.strictEqual(students[0].nome, 'Aluna nova');
  assert.strictEqual(studentRenders, 1);

  getElement('student-edit-id').value = 'student-1';
  getElement('student-name').value = 'Aluna atualizada';
  await context.saveStudent();
  assert.strictEqual(students.length, 1);
  assert.strictEqual(students[0].nome, 'Aluna atualizada');
  await context.deleteStudent('student-1');
  assert.strictEqual(students.length, 0);
  assert.strictEqual(studentRenders, 3);
  assert.strictEqual(syncCalls, 0, 'o CRUD não deve aguardar uma sincronização global');
  console.log('book and student CRUD updates local catalog immediately');
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
