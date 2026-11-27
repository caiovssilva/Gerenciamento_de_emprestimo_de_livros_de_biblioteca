const assert = require('assert');
const fs = require('fs');
const vm = require('vm');
const path = require('path');

const sourcePath = (file) => path.join(__dirname, '../assets/js', file);

async function loadUtils() {
  const scripts = [];
  const containers = new Map();
  const createElement = () => {
    const element = {
      children: [],
      addEventListener(_event, callback) {
        this.click = callback;
      },
      appendChild(child) {
        this.children.push(child);
      },
      remove() {},
    };
    Object.defineProperty(element, "innerHTML", {
      set() {
        this.children = [];
      },
    });
    return element;
  };
  const document = {
    head: {
      appendChild(script) {
        scripts.push(script);
        return script;
      },
    },
    createElement,
    getElementById: (id) => containers.get(id) || null,
    addEventListener() {},
  };
  const context = { document, console, setTimeout, clearTimeout, getComputedStyle() {} };
  vm.createContext(context);
  vm.runInContext(fs.readFileSync(sourcePath('utils.js'), 'utf8'), context);
  return { context, scripts, containers, createElement };
}

(async () => {
  {
    const { context, containers, createElement } = await loadUtils();
    const pagination = createElement();
    containers.set("list-pagination", pagination);
    const records = Array.from({ length: 121 }, (_, index) => index);
    context.testRecords = records;
    context.testOptions = {
      containerId: "list-pagination",
      pageSize: 50,
    };
    const firstPage = vm.runInContext("Utils.paginate(testRecords, testOptions)", context);
    assert.strictEqual(firstPage.items.length, 50, "A lista deve desenhar no máximo 50 linhas por página");
    assert.strictEqual(pagination.hidden, false);

    let selectedPage;
    context.testOptions = {
      containerId: "list-pagination",
      page: 99,
      pageSize: 50,
      onPageChange: (page) => { selectedPage = page; },
    };
    const lastPage = vm.runInContext("Utils.paginate(testRecords, testOptions)", context);
    assert.strictEqual(lastPage.page, 3, "Páginas fora do limite devem ser ajustadas");
    assert.deepStrictEqual(lastPage.items, [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120]);
    pagination.children[0].click();
    assert.strictEqual(selectedPage, 2, "O botão anterior deve navegar para a página anterior");
    assert.strictEqual(pagination.children[2].disabled, true, "A última página não pode avançar");
  }

  {
    const html = fs.readFileSync(path.join(__dirname, '../index.html'), 'utf8');
    assert.doesNotMatch(html, /fonts\.googleapis\.com/, "A fonte remota não deve atrasar a abertura");
    assert.match(html, /tabler-icons\.min\.css" media="print"/, "Os ícones devem carregar sem bloquear a renderização");
    assert.match(html, /id="books-pagination"/);
    assert.match(html, /id="students-pagination"/);
    assert.match(html, /id="loans-pagination"/);
  }

  {
    const { context, scripts } = await loadUtils();
    const promises = vm.runInContext(
      'Promise.all([Utils.loadScript("/shared.js"), Utils.loadScript("/shared.js")])',
      context,
    );
    assert.strictEqual(scripts.length, 1, 'Chamadas simultâneas devem inserir apenas um script');
    scripts[0].onload();
    await promises;
  }

  {
    const { context, scripts } = await loadUtils();
    const promise = vm.runInContext('Utils.loadScript("/retry.js")', context);
    scripts[0].onerror();
    await assert.rejects(promise, /Não foi possível carregar/);
    const retry = vm.runInContext('Utils.loadScript("/retry.js")', context);
    assert.strictEqual(scripts.length, 2, 'Falhas devem permitir nova tentativa de carregamento');
    scripts[1].onload();
    await retry;
  }

  {
    let loadCount = 0;
    const context = {
      Utils: {
        loadScript: async () => {
          loadCount += 1;
          context.Chart = class Chart {};
        },
        toast() {},
        el: () => null,
      },
      API: { reports: {} },
      console,
    };
    vm.createContext(context);
    vm.runInContext(fs.readFileSync(sourcePath('charts.js'), 'utf8'), context);
    assert.strictEqual(loadCount, 0, 'Chart.js não deve ser carregado no início');
    await vm.runInContext('Charts.init()', context);
    assert.strictEqual(loadCount, 1, 'Chart.js deve ser carregado ao abrir os relatórios');
  }

  console.log('lazy-loading tests passed');
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
