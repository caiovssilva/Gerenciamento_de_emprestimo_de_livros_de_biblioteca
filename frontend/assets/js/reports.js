/**
 * Pré-visualização acessível e exportação dos relatórios exibidos na tela.
 */
const Reports = (() => {
  let _reports = [];

  function cleanRows(rows) {
    if (!Array.isArray(rows) || rows.length === 0) {
      throw new Error("O relatório não contém cabeçalhos válidos.");
    }
    const [headers, ...records] = rows;
    const seen = new Set();
    const uniqueRecords = records.filter((row) => {
      const key = JSON.stringify(row);
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
    return [headers, ...uniqueRecords];
  }

  function toCsv(rows) {
    return rows.map((row) => row.map((value) => {
      const cell = value == null ? "" : String(value);
      return `"${cell.replaceAll('"', '""')}"`;
    }).join(",")).join("\r\n");
  }

  function downloadCsv(filename, rows) {
    const blob = new Blob(["\ufeff", toCsv(rows)], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
  }

  function makeCell(tagName, value, className = "") {
    const cell = document.createElement(tagName);
    cell.textContent = value == null ? "" : String(value);
    if (className) cell.className = className;
    return cell;
  }

  function renderReport(report) {
    const [headers, ...records] = report.rows;
    const card = document.createElement("article");
    card.className = "report-data-card";

    const heading = document.createElement("div");
    heading.className = "report-data-heading";
    const titleGroup = document.createElement("div");
    const title = makeCell("h3", report.title);
    const description = makeCell("p", report.description);
    description.className = "report-desc";
    titleGroup.append(title, description);

    const actions = document.createElement("div");
    actions.className = "report-data-actions";
    const count = makeCell("span", `${records.length} ${records.length === 1 ? "registro" : "registros"}`, "report-count");
    const download = makeCell("button", "");
    download.type = "button";
    download.className = "btn btn-sm";
    download.setAttribute("aria-label", `Baixar ${report.title} em CSV`);
    const icon = document.createElement("i");
    icon.className = "ti ti-download";
    icon.setAttribute("aria-hidden", "true");
    download.append(icon, document.createTextNode("Baixar CSV"));
    download.addEventListener("click", () => downloadCsv(report.filename, report.rows));
    actions.append(count, download);
    heading.append(titleGroup, actions);

    const wrapper = document.createElement("div");
    wrapper.className = "report-table-wrap";
    const table = document.createElement("table");
    table.className = "report-data-table";
    const caption = document.createElement("caption");
    caption.className = "sr-only";
    caption.textContent = report.title;
    table.appendChild(caption);
    const thead = document.createElement("thead");
    const headerRow = document.createElement("tr");
    headers.forEach((header) => headerRow.appendChild(makeCell("th", header, "report-table-header")));
    thead.appendChild(headerRow);
    const tbody = document.createElement("tbody");

    if (records.length) {
      records.forEach((row) => {
        const tableRow = document.createElement("tr");
        row.forEach((value, index) => {
          const cell = makeCell("td", value);
          cell.dataset.label = String(headers[index] ?? "");
          tableRow.appendChild(cell);
        });
        tbody.appendChild(tableRow);
      });
    } else {
      const emptyRow = document.createElement("tr");
      const emptyCell = makeCell("td", "Nenhum registro encontrado para este relatório.");
      emptyCell.colSpan = headers.length;
      emptyCell.className = "report-empty-cell";
      emptyRow.appendChild(emptyCell);
      tbody.appendChild(emptyRow);
    }

    table.append(thead, tbody);
    wrapper.appendChild(table);
    card.append(heading, wrapper);
    return card;
  }

  function render() {
    const list = document.getElementById("reports-list");
    const status = document.getElementById("reports-status");
    const count = document.getElementById("reports-count");
    const downloadAllButton = document.getElementById("reports-download-all");
    list.replaceChildren(..._reports.map(renderReport));
    const totalRows = _reports.reduce((total, report) => total + report.rows.length - 1, 0);
    count.textContent = `${_reports.length} relatórios · ${totalRows} registros`;
    status.textContent = _reports.length ? "" : "Nenhum relatório disponível.";
    status.hidden = _reports.length > 0;
    downloadAllButton.disabled = _reports.length === 0;
  }

  async function refresh() {
    const status = document.getElementById("reports-status");
    const downloadAllButton = document.getElementById("reports-download-all");
    status.hidden = false;
    status.textContent = "Carregando relatórios...";
    downloadAllButton.disabled = true;

    try {
      const response = await API.reports.data();
      if (!Array.isArray(response)) throw new Error("O servidor retornou dados de relatório inválidos.");
      _reports = response.map((report) => ({
        ...report,
        rows: cleanRows(report.rows),
      }));
      render();
    } catch (error) {
      console.error("Não foi possível carregar os relatórios:", error);
      status.textContent = `Não foi possível carregar os relatórios. ${error.message}`;
      status.hidden = false;
      document.getElementById("reports-list").replaceChildren();
      document.getElementById("reports-count").textContent = "";
    }
  }

  return {
    cleanRows,
    toCsv,
    init: refresh,
    refresh,
    downloadAll() {
      if (!_reports.length) return;
      const rows = [];
      _reports.forEach((report, index) => {
        if (index) rows.push([]);
        rows.push([report.title], report.rows[0], ...report.rows.slice(1));
      });
      downloadCsv("relatorios-biblioteca.csv", rows);
    },
  };
})();

async function refreshReports() {
  await Promise.all([Reports.refresh(), Charts.refresh()]);
}
