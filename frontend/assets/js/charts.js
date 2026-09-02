/**
 * assets/js/charts.js
 * Gráficos interativos com Chart.js v4.
 * Tipos: bar | bar-h (horizontal) | pie | doughnut | line | polarArea
 * Atualização automática via polling (15s).
 *
 * CORREÇÃO: Chart.js v4 não tem 'horizontalBar'.
 * Barras horizontais = type:'bar' + options.indexAxis:'y'
 */

const Charts = (() => {
  let _charts   = { summary: null, topbooks: null, byclass: null, exports: null };
  let _summarySeq = 0;
  let _topBooksSeq = 0;
  let _byClassSeq = 0;
  let _exportSeq = 0;

  // ── Paleta ────────────────────────────────────────────────────
  const PALETTE = {
    emprestados: { bg: "rgba(245,158,11,0.85)", border: "#f59e0b" },
    atrasados:   { bg: "rgba(239,68,68,0.85)",  border: "#ef4444" },
    devolvidos:  { bg: "rgba(34,197,94,0.85)",  border: "#22c55e" },
    multi: [
      "#6366f1","#8b5cf6","#ec4899","#f43f5e",
      "#f97316","#eab308","#22c55e","#14b8a6",
    ],
  };

  // ── Opções base por tipo ───────────────────────────────────────
  function _opts(rawType) {
    const isRound = ["pie", "doughnut", "polarArea"].includes(rawType);
    const isHBar  = rawType === "bar-h";

    const base = {
      responsive:          true,
      maintainAspectRatio: false,
      animation:           { duration: 450 },
      plugins: {
        legend: {
          display:  true,
          position: isRound ? "right" : "top",
          labels:   { font: { family: "'DM Sans',sans-serif", size: 12 }, padding: 16 },
        },
        tooltip: {
          backgroundColor: "#0f172a",
          titleFont: { family: "'DM Sans',sans-serif", weight: "600" },
          bodyFont:  { family: "'DM Sans',sans-serif" },
          cornerRadius: 8,
          padding: 10,
        },
      },
    };

    if (!isRound) {
      base.scales = {
        x: {
          grid:  { display: isHBar },
          ticks: { font: { family: "'DM Sans',sans-serif" } },
        },
        y: {
          beginAtZero: true,
          grid:  { color: "rgba(0,0,0,0.06)", display: !isHBar },
          ticks: { font: { family: "'DM Sans',sans-serif" } },
        },
      };
      if (isHBar) base.indexAxis = "y";
    }

    return base;
  }

  /** Converte tipo do <select> para tipo real do Chart.js */
  function _chartType(rawType) {
    return rawType === "bar-h" ? "bar" : rawType;
  }

  function _destroy(key) {
    _charts[key]?.destroy();
    _charts[key] = null;
  }

  // ── Gráfico 1: Resumo (emprestados / atrasados / devolvidos) ──
  async function _buildSummary(rawType = "bar") {
    const seq = ++_summarySeq;
    const ctx = Utils.el("chart-summary");
    if (!ctx) return;
    _destroy("summary");

    let data;
    try { data = await API.reports.chartSummary(); } catch { return; }
    if (seq !== _summarySeq) return;

    const isRound = ["pie","doughnut","polarArea"].includes(rawType);
    const bgColors = [
      PALETTE.emprestados.bg, PALETTE.atrasados.bg, PALETTE.devolvidos.bg,
    ];
    const bdColors = [
      PALETTE.emprestados.border, PALETTE.atrasados.border, PALETTE.devolvidos.border,
    ];

    _charts.summary = new Chart(ctx, {
      type: _chartType(rawType),
      data: {
        labels:   data.labels,
        datasets: [{
          label:           "Livros",
          data:            data.values,
          backgroundColor: bgColors,
          borderColor:     bdColors,
          borderWidth:     2,
          borderRadius:    rawType === "bar" || rawType === "bar-h" ? 6 : 0,
        }],
      },
      options: _opts(rawType),
    });

    // Atualiza contadores na página
    const [emp, atr, dev] = data.values;
    const se = Utils.el("stat-emprestados");
    const sa = Utils.el("stat-atrasados");
    const sd = Utils.el("stat-devolvidos");
    if (se) se.textContent = emp ?? "—";
    if (sa) sa.textContent = atr ?? "—";
    if (sd) sd.textContent = dev ?? "—";
  }

  // ── Gráfico 2: Top livros ─────────────────────────────────────
  async function _buildTopBooks(rawType = "bar") {
    const seq = ++_topBooksSeq;
    const ctx = Utils.el("chart-topbooks");
    if (!ctx) return;
    _destroy("topbooks");

    let data;
    try { data = await API.reports.topBooks(8); } catch { return; }
    if (!data?.length) return;
    if (seq !== _topBooksSeq) return;

    const isRound = ["pie","doughnut","polarArea"].includes(rawType);
    const labels  = data.map(d => d.titulo.length > 22 ? d.titulo.slice(0,22) + "…" : d.titulo);
    const values  = data.map(d => d.total);

    _charts.topbooks = new Chart(ctx, {
      type: _chartType(rawType),
      data: {
        labels,
        datasets: [{
          label:           "Empréstimos",
          data:            values,
          backgroundColor: isRound ? PALETTE.multi : PALETTE.multi[0],
          borderColor:     isRound ? "#fff" : PALETTE.multi[0],
          borderWidth:     isRound ? 2 : 0,
          borderRadius:    rawType === "bar" || rawType === "bar-h" ? 5 : 0,
        }],
      },
      options: _opts(rawType),
    });
  }

  // ── Gráfico 3: Por turma ──────────────────────────────────────
  async function _buildByClass(rawType = "bar") {
    const seq = ++_byClassSeq;
    const ctx = Utils.el("chart-byclass");
    if (!ctx) return;
    _destroy("byclass");

    let data;
    try { data = await API.reports.byClass(); } catch { return; }
    if (!data?.labels?.length) return;
    if (seq !== _byClassSeq) return;

    const isRound = ["pie","doughnut","polarArea"].includes(rawType);

    const datasets = isRound
      ? [{
          label:           "Total",
          data:            data.active.map((v, i) => v + data.overdue[i] + data.returned[i]),
          backgroundColor: PALETTE.multi,
          borderColor:     "#fff",
          borderWidth:     2,
        }]
      : [
          {
            label: "Ativos",
            data:  data.active,
            backgroundColor: PALETTE.emprestados.bg,
            borderColor:     PALETTE.emprestados.border,
            borderWidth: 2, borderRadius: 4,
          },
          {
            label: "Atrasados",
            data:  data.overdue,
            backgroundColor: PALETTE.atrasados.bg,
            borderColor:     PALETTE.atrasados.border,
            borderWidth: 2, borderRadius: 4,
          },
          {
            label: "Devolvidos",
            data:  data.returned,
            backgroundColor: PALETTE.devolvidos.bg,
            borderColor:     PALETTE.devolvidos.border,
            borderWidth: 2, borderRadius: 4,
          },
        ];

    _charts.byclass = new Chart(ctx, {
      type: _chartType(rawType),
      data: { labels: data.labels, datasets },
      options: _opts(rawType),
    });
  }

  // ── Gráfico 4: Resumo em colunas para exportações ─────────────
  async function _buildExportColumns() {
    const seq = ++_exportSeq;
    const ctx = Utils.el("chart-exports");
    if (!ctx) return;
    _destroy("exports");

    let data;
    try { data = await API.reports.chartSummary(); } catch { return; }
    if (!data?.labels?.length) return;
    if (seq !== _exportSeq) return;

    _charts.exports = new Chart(ctx, {
      type: "bar",
      data: {
        labels: data.labels,
        datasets: [{
          label: "Quantidade",
          data: data.values,
          backgroundColor: [PALETTE.emprestados.bg, PALETTE.atrasados.bg, PALETTE.devolvidos.bg],
          borderColor: [PALETTE.emprestados.border, PALETTE.atrasados.border, PALETTE.devolvidos.border],
          borderWidth: 2,
          borderRadius: 6,
        }],
      },
      options: _opts("bar"),
    });
  }

  // ── API pública ───────────────────────────────────────────────
  return {
    async init() {
      this.destroy();
      await Promise.all([
        _buildSummary( Utils.el("chart-type-summary")?.value  || "bar"),
        _buildTopBooks(Utils.el("chart-type-topbooks")?.value || "bar"),
        _buildByClass( Utils.el("chart-type-byclass")?.value  || "bar"),
        _buildExportColumns(),
      ]);
    },

    start() { return this.init(); },
    stop() { this.destroy(); },

    async changeSummaryType(t)  { await _buildSummary(t);  },
    async changeTopBooksType(t) { await _buildTopBooks(t); },
    async changeClassType(t)    { await _buildByClass(t);  },

    async refresh() {
      await Promise.all([
        _buildSummary( Utils.el("chart-type-summary")?.value  || "bar"),
        _buildTopBooks(Utils.el("chart-type-topbooks")?.value || "bar"),
        _buildByClass( Utils.el("chart-type-byclass")?.value  || "bar"),
        _buildExportColumns(),
      ]);
    },

    destroy() {
      _summarySeq += 1;
      _topBooksSeq += 1;
      _byClassSeq += 1;
      _exportSeq += 1;
      Object.keys(_charts).forEach(_destroy);
    },
  };
})();