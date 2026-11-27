const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const removedKeys = [];
let localReads = 0;
let localWrites = 0;
const context = {
  localStorage: {
    getItem() {
      localReads += 1;
      return JSON.stringify([{ id: 'stale-local-record' }]);
    },
    setItem() {
      localWrites += 1;
    },
    removeItem(key) {
      removedKeys.push(key);
    },
  },
  console: { warn() {} },
  Utils: { daysLeft: () => 0 },
};

vm.createContext(context);
vm.runInContext(
  `${fs.readFileSync(path.join(__dirname, '../assets/js/store.js'), 'utf8')}\nglobalThis.__testStore = Store;`,
  context,
);

const store = context.__testStore;
assert.strictEqual(store.books().length, 0);
assert.strictEqual(store.students().length, 0);
assert.strictEqual(localReads, 0, 'O store não deve ler registros do localStorage');

store.setBooks([{ id: 'book-1' }]);
store.setStudents([{ id: 'student-1' }]);
store.setLoans([{ id: 'loan-1' }]);
store.setRooms([{ id: 'room-1' }]);
store.setGenres([{ id: 'genre-1' }]);
assert.strictEqual(localWrites, 0, 'O store não deve persistir registros no localStorage');

store.clear();
for (const collection of ['books', 'students', 'loans', 'rooms', 'genres']) {
  assert.strictEqual(store[collection]().length, 0);
}
assert.deepStrictEqual(removedKeys.sort(), [
  'lib_books',
  'lib_genres',
  'lib_loans',
  'lib_rooms',
  'lib_students',
].sort());
