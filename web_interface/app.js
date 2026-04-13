const statusPanel = document.getElementById("statusPanel");
const tableSelect = document.getElementById("tableSelect");
const refreshBtn = document.getElementById("refreshBtn");
const createTableForm = document.getElementById("createTableForm");
const newTableName = document.getElementById("newTableName");
const tableInfoCard = document.getElementById("tableInfoCard");
const tableNameLabel = document.getElementById("tableName");
const tableColCount = document.getElementById("tableColCount");
const tableRowCount = document.getElementById("tableRowCount");
const deleteTableBtn = document.getElementById("deleteTableBtn");
const columnsCard = document.getElementById("columnsCard");
const columnList = document.getElementById("columnList");
const columnFormCard = document.getElementById("columnFormCard");
const addColumnForm = document.getElementById("addColumnForm");
const columnName = document.getElementById("columnName");
const columnType = document.getElementById("columnType");
const columnNullable = document.getElementById("columnNullable");

let currentTable = null;

function showStatus(message, type = "info") {
  statusPanel.textContent = message;
  statusPanel.style.color = type === "error" ? "#fda4af" : "#a5f3fc";
}

async function requestJson(url, method = "GET", body = null) {
  const options = { method, headers: { "Content-Type": "application/json" } };
  if (body) options.body = JSON.stringify(body);
  const res = await fetch(url, options);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || `${res.status} ${res.statusText}`);
  return data;
}

async function loadTypes() {
  const data = await requestJson("/api/types");
  columnType.innerHTML = data.map(type => `<option value="${type}">${type}</option>`).join("");
}

async function loadTables() {
  const data = await requestJson("/api/tables");
  tableSelect.innerHTML = data.tables.length
    ? data.tables.map(name => `<option value="${name}">${name}</option>`).join("")
    : '<option value="" disabled>Nenhuma tabela disponível</option>';
  if (data.tables.length) {
    currentTable = data.tables[0];
    tableSelect.value = currentTable;
    await loadTable(currentTable);
  } else {
    tableInfoCard.hidden = true;
    columnsCard.hidden = true;
    columnFormCard.hidden = true;
    showStatus("Nenhuma tabela encontrada. Crie uma tabela para começar.");
  }
}

function encodeTableName(name) {
  return encodeURIComponent(name);
}

async function loadTable(name) {
  const encodedName = encodeTableName(name);
  const data = await requestJson(`/api/tables/${encodedName}`);
  currentTable = name;
  tableInfoCard.hidden = false;
  columnsCard.hidden = false;
  columnFormCard.hidden = false;
  tableNameLabel.textContent = data.name;
  tableColCount.textContent = data.col_count;
  tableRowCount.textContent = data.row_count;
  populateColumnList(data.columns);
  showStatus(`Tabela carregada: ${data.name}`);
}

function populateColumnList(columns) {
  columnList.innerHTML = columns.length
    ? columns.map(col => `
      <tr>
        <td>${col.name}</td>
        <td>${col.type}</td>
        <td>${col.nullable ? "Sim" : "Não"}</td>
        <td class="actions">
          <input class="rename-input" placeholder="Novo nome" data-col="${col.name}" />
          <button class="small" data-action="rename" data-col="${col.name}">Renomear</button>
          <button class="small danger" data-action="delete" data-col="${col.name}">Excluir</button>
        </td>
      </tr>`
    ).join("")
    : `<tr><td colspan="4">Nenhuma coluna definida para esta tabela.</td></tr>`;
}

async function refreshTableList() {
  await loadTables();
}

async function onCreateTable(event) {
  event.preventDefault();
  const name = newTableName.value.trim();
  if (!name) return showStatus("Digite o nome da nova tabela.", "error");
  try {
    await requestJson("/api/tables", "POST", { name });
    newTableName.value = "";
    await refreshTableList();
    showStatus(`Tabela '${name}' criada.`);
  } catch (err) {
    showStatus(err.message, "error");
  }
}

async function onAddColumn(event) {
  event.preventDefault();
  const name = columnName.value.trim();
  const type = columnType.value;
  const nullable = columnNullable.checked;
  if (!name) return showStatus("Digite o nome da coluna.", "error");
  try {
    await requestJson(`/api/tables/${encodeTableName(currentTable)}/columns`, "POST", { name, type, nullable });
    columnName.value = "";
    await loadTable(currentTable);
    showStatus(`Coluna '${name}' adicionada.`);
  } catch (err) {
    showStatus(err.message, "error");
  }
}

async function onColumnListClick(event) {
  const button = event.target.closest("button");
  if (!button) return;
  const action = button.dataset.action;
  const colName = button.dataset.col;

  if (action === "delete") {
    if (!confirm(`Excluir coluna '${colName}'?`)) return;
    try {
      await requestJson(`/api/tables/${encodeTableName(currentTable)}/columns/${encodeURIComponent(colName)}`, "DELETE");
      await loadTable(currentTable);
      showStatus(`Coluna '${colName}' removida.`);
    } catch (err) {
      showStatus(err.message, "error");
    }
    return;
  }

  if (action === "rename") {
    const input = document.querySelector(`input.rename-input[data-col="${colName}"]`);
    const newName = input?.value.trim();
    if (!newName) return showStatus("Digite o novo nome da coluna.", "error");
    try {
      await requestJson(`/api/tables/${encodeTableName(currentTable)}/columns/${encodeURIComponent(colName)}/rename`, "POST", { new_name: newName });
      await loadTable(currentTable);
      showStatus(`Coluna '${colName}' renomeada para '${newName}'.`);
    } catch (err) {
      showStatus(err.message, "error");
    }
  }
}

async function onDeleteTable() {
  if (!currentTable) return;
  if (!confirm(`Excluir tabela '${currentTable}'? Esta ação não pode ser desfeita.`)) return;
  try {
    await requestJson(`/api/tables/${encodeTableName(currentTable)}`, "DELETE");
    await refreshTableList();
    showStatus(`Tabela '${currentTable}' excluída.`);
  } catch (err) {
    showStatus(err.message, "error");
  }
}

refreshBtn.addEventListener("click", refreshTableList);
createTableForm.addEventListener("submit", onCreateTable);
addColumnForm.addEventListener("submit", onAddColumn);
columnList.addEventListener("click", onColumnListClick);
deleteTableBtn.addEventListener("click", onDeleteTable);
tableSelect.addEventListener("change", async () => {
  await loadTable(tableSelect.value);
});

loadTypes().then(loadTables).catch(err => showStatus(err.message, "error"));
