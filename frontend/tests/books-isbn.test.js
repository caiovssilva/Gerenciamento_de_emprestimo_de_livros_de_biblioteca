const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const elements = {
  'book-isbn': { value: '978-85-7683-130-3' },
  'book-title': { value: '' },
  'book-author': { value: 'Autor digitado' },
  'book-area': { value: 'Informática' },
  'book-genre': { value: '', innerHTML: '' },
  'book-isbn-status': { textContent: '' },
};

const context = {
  console,
  Utils: {
    el: (id) => elements[id],
    toast: () => {},
  },
  Store: {
    genres: () => [{ id: 'genre-1', nome: 'Técnico / Didático' }],
  },
  API: {
    books: {
      lookupIsbn: async () => ({
        isbn: '9788576831303',
        titulo: 'Livro didático',
        autor: 'Autor da API',
        categorias: ['Textbook'],
        genero_id: 'genre-1',
        genero_nome: 'Técnico / Didático',
        area: 'Geral',
      }),
    },
  },
  syncGenres: async () => {},
};

vm.createContext(context);
vm.runInContext(
  fs.readFileSync(path.join(__dirname, '../assets/js/pages/books.js'), 'utf8'),
  context,
);

(async () => {
  await context.lookupBookIsbn();
  assert.strictEqual(elements['book-isbn'].value, '9788576831303');
  assert.strictEqual(elements['book-title'].value, 'Livro didático');
  assert.strictEqual(elements['book-author'].value, 'Autor digitado');
  assert.strictEqual(elements['book-genre'].value, 'genre-1');
  console.log('books ISBN form test passed');
})().catch((error) => {
  console.error(error);
  process.exit(1);
});