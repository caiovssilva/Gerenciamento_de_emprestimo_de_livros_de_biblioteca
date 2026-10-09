const assert = require('assert');
const fs = require('fs');
const vm = require('vm');
const path = require('path');

const context = {};
vm.createContext(context);
vm.runInContext(
  fs.readFileSync(path.join(__dirname, '../assets/js/reports.js'), 'utf8'),
  context,
);
vm.runInContext('globalThis.reportsTestApi = Reports', context);

const rows = [
  ['Aluno', 'Livro'],
  ['Ana', 'Duna'],
  ['Ana', 'Duna'],
  ['Bia', 'A "viagem"'],
];
const cleaned = context.reportsTestApi.cleanRows(rows);
assert.strictEqual(cleaned.length, 3, 'registros repetidos devem ser removidos');
assert.deepStrictEqual(Array.from(cleaned[2]), ['Bia', 'A "viagem"']);
assert.strictEqual(
  context.reportsTestApi.toCsv(cleaned),
  '"Aluno","Livro"\r\n"Ana","Duna"\r\n"Bia","A ""viagem"""',
  'o CSV deve exportar os mesmos dados limpos e escapar aspas',
);
console.log('reports duplicate cleanup and CSV export tests passed');
