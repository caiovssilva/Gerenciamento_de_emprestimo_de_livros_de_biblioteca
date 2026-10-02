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
      lookupIsbn: async (isbn) => isbn === '9788576831303'
        ? {
            isbn: '9788576831303',
            titulo: 'Livro didático',
            autor: 'Autor da API',
            categorias: ['Textbook'],
            genero_id: 'genre-1',
            genero_nome: 'Técnico / Didático',
            area: 'Geral',
          }
        : {
            isbn: '9780000000002',
            titulo: 'Segundo livro',
            autor: 'Segundo autor',
            categorias: [],
            area: 'Literatura',
          },
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
  assert.strictEqual(elements['book-author'].value, 'Autor da API');
  assert.strictEqual(elements['book-genre'].value, 'genre-1');

  elements['book-isbn'].value = '978-00-00000-00-2';
  await context.lookupBookIsbn();
  assert.strictEqual(elements['book-isbn'].value, '9780000000002');
  assert.strictEqual(elements['book-title'].value, 'Segundo livro');
  assert.strictEqual(elements['book-author'].value, 'Segundo autor');
  assert.strictEqual(elements['book-area'].value, 'Literatura');
  console.log('books ISBN form test passed');
})().catch((error) => {
  console.error(error);
  process.exit(1);
});