<script setup>
import { computed, onMounted, ref } from "vue";

// ---- 页面状态 ----
const health = ref(null);
const error = ref("");
const loading = ref(false);
const sqlLogs = ref([]);

// 左侧表列表（Neon/Supabase 风格 sidebar）
const tableNames = ["hero", "team", "mission", "mission_hero"];
const activeTable = ref(null); // 当前选中的表名
const schema = ref({}); // 表名 -> 列定义 [{column,type,nullable,default,primary_key}]
const rows = ref([]); // 当前表的数据行
const fkOptions = ref({}); // 外键选项：列名 -> [{id, label}]
const loadedTables = ref({}); // 记录已加载的表（避免重复请求 schema）

// 编辑 / 插入状态
const editingCell = ref(null); // {rowIdx, column}
const editValue = ref("");
const insertMode = ref(false);
const insertForm = ref({});

// ---- 请求封装 ----
async function api(path, options = {}) {
  const res = await fetch(`/api${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed: ${res.status}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

// ---- SQL 日志 ----
async function loadSqlLogs() {
  sqlLogs.value = await api("/sql-logs?limit=5");
}

// ---- 表结构（schema）----
async function loadSchemaOnce() {
  if (loadedTables.value.schema) return;
  const cols = await api("/tables");
  const map = {};
  for (const c of cols) {
    if (!map[c.table]) map[c.table] = [];
    map[c.table].push(c);
  }
  schema.value = map;
  loadedTables.value.schema = true;
}

// 当前表的列定义（用于表头渲染）
function currentColumns() {
  return schema.value[activeTable.value] || [];
}

// 主键列名集合
function pkSet(table) {
  return new Set(
    (schema.value[table] || []).filter((c) => c.primary_key).map((c) => c.column)
  );
}

// schema 视图：按表分组的表结构（psql \d 风格，每张表一个表格）
const tableGroups = computed(() =>
  Object.entries(schema.value).map(([table, columns]) => ({ table, columns }))
);

// 某张表的主键列（Indexes 行展示）
function pkColumns(group) {
  const pks = group.columns.filter((c) => c.primary_key).map((c) => c.column);
  return pks.length ? pks.join(", ") : "(none)";
}

// 外键列：hero.team_id / mission_hero.mission_id / mission_hero.hero_id
const FK_COLUMNS = {
  hero: ["team_id"],
  mission: [],
  mission_hero: ["mission_id", "hero_id"],
  team: [],
};

// 分页状态（hero 表使用后端分页，默认每页 5 条）
const page = ref(1);
const pageSize = ref(5);
const total = ref(0);

// 总页数
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)));

// ---- 加载指定表的数据 ----
async function loadTable(name, resetPage = true) {
  error.value = "";
  activeTable.value = name;
  if (resetPage) page.value = 1;
  loading.value = true;
  try {
    await loadSchemaOnce();
    // schema 视图：只显示表结构，不加载数据行
    if (name === "schema") {
      rows.value = [];
      fkOptions.value = {};
      return;
    }
    // 主数据（hero 走后端分页，其余表数据量小直接全量）
    if (name === "hero") {
      const data = await api(
        `/heroes?offset=${(page.value - 1) * pageSize.value}&limit=${pageSize.value}`
      );
      // 兼容新旧后端：{items,total} 或纯数组，避免 rows 为 undefined 导致模板崩溃
      rows.value = Array.isArray(data) ? data : data?.items ?? [];
      total.value = Array.isArray(data) ? data.length : data?.total ?? 0;
    } else if (name === "team") rows.value = await api("/teams");
    else if (name === "mission") rows.value = await api("/missions");
    else if (name === "mission_hero") rows.value = await api("/missions/links");
    // 外键选项（并行加载关联表）
    const fks = FK_COLUMNS[name] || [];
    const tasks = [];
    if (fks.includes("team_id")) tasks.push(api("/teams").then((d) => (fkOptions.value.team_id = (d ?? []).map((t) => ({ id: t.id, label: t.name })))));
    if (fks.includes("mission_id")) tasks.push(api("/missions").then((d) => (fkOptions.value.mission_id = (d ?? []).map((m) => ({ id: m.id, label: m.name })))));
    if (fks.includes("hero_id")) tasks.push(api("/heroes?limit=100").then((d) => (fkOptions.value.hero_id = (Array.isArray(d) ? d : d?.items ?? []).map((h) => ({ id: h.id, label: h.name })))));
    await Promise.all(tasks);
    await loadSqlLogs();
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}

// 翻页（保留当前表与页码，不重置）
async function goToPage(p) {
  if (p < 1 || p > totalPages.value) return;
  page.value = p;
  await loadTable(activeTable.value, false);
}

// ---- 单元格展示值 ----
function cellText(row, column) {
  const v = row[column];
  if (v === null || v === undefined) return "NULL";
  // 外键列显示 label
  const opts = fkOptions.value[column];
  if (opts && FK_COLUMNS[activeTable.value]?.includes(column)) {
    const hit = opts.find((o) => o.id === v);
    if (hit) return `${hit.label} (${v})`;
  }
  return String(v);
}

// ---- 单元格编辑 ----
function startEdit(row, rowIdx, column) {
  if (pkSet(activeTable.value).has(column)) return; // 主键不可编辑
  editingCell.value = { rowIdx, column };
  editValue.value = row[column] ?? "";
}

function cancelEdit() {
  editingCell.value = null;
}

function isEditing(rowIdx, column) {
  return editingCell.value && editingCell.value.rowIdx === rowIdx && editingCell.value.column === column;
}

// 保存单元格（PATCH）
async function saveCell(row, rowIdx) {
  const { column } = editingCell.value;
  const table = activeTable.value;
  let value = editValue.value;
  const colDef = currentColumns().find((c) => c.column === column);
  if (colDef && colDef.type.toUpperCase().includes("INT")) {
    value = value === "" || value === "NULL" ? null : Number(value);
  } else if (value === "NULL" || value === "") {
    value = null;
  }
  try {
    if (table === "hero") {
      await api(`/heroes/${row.id}`, { method: "PATCH", body: JSON.stringify({ [column]: value }) });
    } else if (table === "team") {
      await api(`/teams/${row.id}`, { method: "PATCH", body: JSON.stringify({ [column]: value }) });
    } else if (table === "mission") {
      await api(`/missions/${row.id}`, { method: "PATCH", body: JSON.stringify({ [column]: value }) });
    } else if (table === "mission_hero") {
      await api(`/missions/links/${row.mission_id}/${row.hero_id}`, { method: "PATCH", body: JSON.stringify({ [column]: value }) });
    }
    cancelEdit();
    await loadTable(table);
  } catch (e) {
    error.value = e.message;
  }
}

// ---- 删除行 ----
async function deleteRow(row) {
  error.value = "";
  const table = activeTable.value;
  if (!confirm(`Delete this row from ${table}?`)) return;
  try {
    if (table === "hero") await api(`/heroes/${row.id}`, { method: "DELETE" });
    else if (table === "team") await api(`/teams/${row.id}`, { method: "DELETE" });
    else if (table === "mission") await api(`/missions/${row.id}`, { method: "DELETE" });
    else if (table === "mission_hero") await api(`/missions/links/${row.mission_id}/${row.hero_id}`, { method: "DELETE" });
    await loadTable(table);
  } catch (e) {
    error.value = e.message;
  }
}

// ---- 插入行 ----
function startInsert() {
  insertMode.value = true;
  const f = {};
  for (const c of currentColumns()) {
    if (c.primary_key) continue; // 自增主键不填
    f[c.column] = "";
  }
  insertForm.value = f;
}

function cancelInsert() {
  insertMode.value = false;
}

// 插入行字段是否为外键
function isFkColumn(column) {
  return (FK_COLUMNS[activeTable.value] || []).includes(column);
}

function fkOptionsOf(column) {
  return fkOptions.value[column] || [];
}

async function saveInsert() {
  error.value = "";
  const table = activeTable.value;
  const body = {};
  for (const [col, val] of Object.entries(insertForm.value)) {
    const colDef = currentColumns().find((c) => c.column === col);
    if (val === "" || val === "NULL") {
      body[col] = null;
    } else if (colDef && colDef.type.toUpperCase().includes("INT")) {
      body[col] = Number(val);
    } else {
      body[col] = val;
    }
  }
  loading.value = true;
  try {
    if (table === "hero") await api("/heroes", { method: "POST", body: JSON.stringify(body) });
    else if (table === "team") await api("/teams", { method: "POST", body: JSON.stringify(body) });
    else if (table === "mission") await api("/missions", { method: "POST", body: JSON.stringify(body) });
    else if (table === "mission_hero") {
      await api("/missions/links", {
        method: "POST",
        body: JSON.stringify({
          mission_id: Number(insertForm.value.mission_id),
          hero_id: Number(insertForm.value.hero_id),
          role: insertForm.value.role || null,
        }),
      });
    }
    insertMode.value = false;
    await loadTable(table);
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}

// ---- 初始：只检查后端健康状态，不查询任何表 ----
onMounted(async () => {
  try {
    health.value = await api("/health");
  } catch (e) {
    error.value = e.message;
  }
});
</script>

<template>
  <main class="container">
    <h1>⚡ interset</h1>
    <p class="health">
      Backend status:
      <span :class="health ? 'ok' : 'err'">
        {{ health ? health.status : "offline" }}
      </span>
    </p>

    <p v-if="error" class="err">{{ error }}</p>

    <!-- 布局：左侧表列表 + 右侧数据网格 -->
    <div class="editor-layout">
      <!-- 左侧 sidebar：表列表 + schema 视图入口 -->
      <aside class="sidebar">
        <div class="sidebar-title">Tables</div>
        <button
          v-for="t in tableNames"
          :key="t"
          class="table-item"
          :class="{ active: activeTable === t }"
          @click="loadTable(t)"
        >
          {{ t }}
        </button>
        <div class="sidebar-sep"></div>
        <div class="sidebar-title">Views</div>
        <button
          class="table-item"
          :class="{ active: activeTable === 'schema' }"
          @click="loadTable('schema')"
        >
          schema
        </button>
      </aside>

      <!-- 右侧：schema 视图 / 数据网格 -->
      <section class="grid-panel">
        <!-- schema 视图：仅显示表结构（psql \d 风格），不加载数据行 -->
        <template v-if="activeTable === 'schema'">
          <div class="grid-toolbar">
            <span class="table-name">schema</span>
            <span class="col-count">{{ tableGroups.length }} tables</span>
            <button class="secondary" @click="loadTable('schema')">Refresh</button>
          </div>
          <div v-for="group in tableGroups" :key="group.table" class="schema-table">
            <h3 class="query-sql">Table "{{ group.table }}"</h3>
            <div class="table-wrap">
              <table class="cli-table">
                <thead>
                  <tr>
                    <th>Column</th>
                    <th>Type</th>
                    <th>Nullable</th>
                    <th>Default</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="col in group.columns" :key="col.column">
                    <td>{{ col.column }}</td>
                    <td>{{ col.type }}</td>
                    <td>{{ col.nullable ? "" : "not null" }}</td>
                    <td>{{ col.default ?? "" }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p class="indexes">Indexes: PRIMARY KEY ({{ pkColumns(group) }})</p>
          </div>
          <p v-if="!tableGroups.length" class="muted">0 tables</p>
        </template>

        <!-- 数据表视图 -->
        <template v-else-if="activeTable">
          <div class="grid-toolbar">
            <span class="table-name">{{ activeTable }}</span>
            <span class="col-count">{{ currentColumns().length }} columns</span>
            <button v-if="!insertMode" class="primary" @click="startInsert">Insert row</button>
            <button class="secondary" @click="loadTable(activeTable)">Refresh</button>
          </div>

          <!-- 插入行表单 -->
          <form v-if="insertMode" class="insert-form" @submit.prevent="saveInsert">
            <label v-for="c in currentColumns()" :key="c.column" class="insert-field">
              <span>{{ c.column }}</span>
              <select v-if="isFkColumn(c.column)" v-model="insertForm[c.column]">
                <option value="">— NULL —</option>
                <option v-for="o in fkOptionsOf(c.column)" :key="o.id" :value="o.id">
                  {{ o.label }}
                </option>
              </select>
              <input
                v-else
                v-model="insertForm[c.column]"
                :type="c.type.toUpperCase().includes('INT') ? 'number' : 'text'"
                :placeholder="c.nullable ? 'NULL' : 'required'"
              />
            </label>
            <div class="insert-actions">
              <button type="submit" :disabled="loading">Save</button>
              <button type="button" class="secondary" @click="cancelInsert">Cancel</button>
            </div>
          </form>

          <!-- 数据网格 -->
          <div class="table-wrap">
            <table class="grid-table">
              <thead>
                <tr>
                  <th v-for="c in currentColumns()" :key="c.column" class="col-header">
                    {{ c.column }}
                  </th>
                  <th class="col-actions"></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, i) in rows" :key="i">
                  <td
                    v-for="c in currentColumns()"
                    :key="c.column"
                    class="cell"
                    :class="{ editable: !pkSet(activeTable).has(c.column) }"
                    @click="!pkSet(activeTable).has(c.column) && startEdit(row, i, c.column)"
                  >
                    <template v-if="isEditing(i, c.column)">
                      <select
                        v-if="isFkColumn(c.column)"
                        v-model="editValue"
                        class="cell-input"
                        autofocus
                        @change="saveCell(row, i)"
                        @blur="saveCell(row, i)"
                      >
                        <option :value="null">NULL</option>
                        <option v-for="o in fkOptionsOf(c.column)" :key="o.id" :value="o.id">
                          {{ o.label }}
                        </option>
                      </select>
                      <input
                        v-else
                        v-model="editValue"
                        class="cell-input"
                        autofocus
                        @keydown.enter="saveCell(row, i)"
                        @keydown.esc="cancelEdit"
                        @blur="saveCell(row, i)"
                      />
                    </template>
                    <template v-else>{{ cellText(row, c.column) }}</template>
                  </td>
                  <td class="cell-actions">
                    <button class="danger small" @click="deleteRow(row)">🗑</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 分页控件（hero 表使用后端分页） -->
          <div v-if="activeTable === 'hero'" class="pagination">
            <button
              class="secondary small"
              :disabled="page <= 1"
              @click="goToPage(page - 1)"
            >
              ← Prev
            </button>
            <span class="page-info">
              Page {{ page }} / {{ totalPages }}（{{ total }} rows）
            </span>
            <button
              class="secondary small"
              :disabled="page >= totalPages"
              @click="goToPage(page + 1)"
            >
              Next →
            </button>
            <select
              v-model.number="pageSize"
              class="page-size"
              @change="loadTable(activeTable, false)"
            >
              <option :value="5">5 / page</option>
              <option :value="10">10 / page</option>
              <option :value="20">20 / page</option>
              <option :value="50">50 / page</option>
            </select>
          </div>

          <p v-if="!rows.length" class="muted">0 rows</p>
        </template>

        <div v-else class="empty-state">
          <p>Select a table from the left sidebar to browse and edit data.</p>
        </div>
      </section>
    </div>

    <!-- SQL 日志：content 区域下方独立 section -->
    <section class="card">
      <h2>SQL Log (recent {{ sqlLogs.length }}, newest first)</h2>
      <p class="muted">
        Actual SQL statements executed by SQLModel for each operation
        (query / insert / delete), parameters inlined.
      </p>

      <div class="table-wrap">
        <table class="cli-table">
          <thead>
            <tr>
              <th>time</th>
              <th>sql</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(log, i) in sqlLogs" :key="i">
              <td class="log-time">{{ log.time }}</td>
              <td><code>{{ log.sql }}</code></td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-if="!sqlLogs.length" class="muted">0 rows — no SQL logs yet</p>
    </section>
  </main>
</template>

<style>
* {
  box-sizing: border-box;
}

body {
  margin: 0;
  /* 全站统一使用代码友好（等宽）字体，与 SQL 列保持一致 */
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Courier New",
    monospace;
  background: #f5f6fa;
  color: #2c3e50;
}

.container {
  max-width: 1100px;
  margin: 0 auto;
  padding: 24px 16px 48px;
}

h1 {
  text-align: center;
  margin-bottom: 4px;
}

.health {
  text-align: center;
  color: #666;
  margin-top: 0;
}

.ok {
  color: #27ae60;
  font-weight: 600;
}

.err {
  color: #e74c3c;
  font-weight: 600;
}

.muted {
  color: #999;
}

/* ---- Table Editor 布局：左侧 sidebar + 右侧网格 ---- */
.editor-layout {
  display: flex;
  gap: 14px;
  margin: 14px 0;
  align-items: flex-start;
}

/* 左侧表列表 */
.sidebar {
  flex: 0 0 170px;
  background: #fff;
  border: 1px solid #d5d8e0;
  border-radius: 8px;
  padding: 8px;
}

.sidebar-sep {
  border-top: 1px solid #e2e5ec;
  margin: 8px 2px;
}

.sidebar-title {
  font-size: 0.75rem;
  text-transform: uppercase;
  color: #999;
  padding: 4px 8px 8px;
  letter-spacing: 0.05em;
}

.table-item {
  display: block;
  width: 100%;
  text-align: left;
  padding: 7px 10px;
  margin: 2px 0;
  border: none;
  border-radius: 5px;
  background: transparent;
  color: #2c3e50;
  font-size: 0.9rem;
  font-family: inherit;
  cursor: pointer;
}

.table-item:hover {
  background: #eef1f6;
}

.table-item.active {
  background: #2c6fbb;
  color: #fff;
  font-weight: 600;
}

/* 右侧数据网格 */
.grid-panel {
  flex: 1;
  background: #fff;
  border: 1px solid #d5d8e0;
  border-radius: 8px;
  padding: 12px 14px;
  min-width: 0;
}

.grid-toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.table-name {
  font-size: 1.05rem;
  font-weight: 700;
}

.col-count {
  color: #999;
  font-size: 0.8rem;
}

/* 插入行表单 */
.insert-form {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: flex-end;
  padding: 10px;
  margin-bottom: 10px;
  background: #f0f4fb;
  border: 1px solid #c9d8ef;
  border-radius: 6px;
}

.insert-field {
  display: flex;
  flex-direction: column;
  gap: 3px;
  font-size: 0.75rem;
  color: #555;
}

.insert-field input,
.insert-field select {
  padding: 5px 8px;
  border: 1px solid #d5d8e0;
  border-radius: 4px;
  font-family: inherit;
  font-size: 0.85rem;
  min-width: 110px;
}

.insert-actions {
  display: flex;
  gap: 6px;
}

/* ---- 数据网格（Neon/Supabase 风格）---- */
.table-wrap {
  overflow-x: auto;
}

.grid-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}

.grid-table th,
.grid-table td {
  border: 1px solid #e2e5ec;
  padding: 6px 8px;
  text-align: left;
  vertical-align: middle;
}

.grid-table thead th {
  background: #f7f8fc;
  white-space: nowrap;
}

.col-header {
  /* 保持 th 默认的 table-cell 布局（display:flex 会让表头脱离表格单元格） */
  font-weight: 700;
  white-space: nowrap;
}

.cell {
  white-space: nowrap;
  max-width: 260px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.cell.editable {
  cursor: text;
}

.cell.editable:hover {
  background: #eef4fc;
  box-shadow: inset 0 0 0 1px #2c6fbb;
}

.cell-input {
  width: 100%;
  min-width: 90px;
  padding: 4px 6px;
  border: 1px solid #2c6fbb;
  border-radius: 4px;
  font-family: inherit;
  font-size: 0.85rem;
}

.cell-actions {
  text-align: center;
  white-space: nowrap;
}

.empty-state {
  color: #999;
  text-align: center;
  padding: 40px 0;
}

/* ---- 分页控件 ---- */
.pagination {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
  flex-wrap: wrap;
}

.page-info {
  font-size: 0.85rem;
  color: #555;
}

.page-size {
  padding: 5px 8px;
  border: 1px solid #d5d8e0;
  border-radius: 4px;
  font-family: inherit;
  font-size: 0.85rem;
}

/* ---- 按钮 ---- */
button {
  padding: 6px 12px;
  border: none;
  border-radius: 5px;
  background: #2c6fbb;
  color: #fff;
  font-size: 0.85rem;
  font-family: inherit;
  cursor: pointer;
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

button.primary {
  background: #2c6fbb;
}

button.secondary {
  background: #7f8c8d;
}

button.danger {
  background: #e74c3c;
}

button.small {
  padding: 3px 8px;
  font-size: 0.8rem;
}

/* ---- SQL 日志（cli-table）---- */
.card {
  background: #fff;
  border-radius: 8px;
  padding: 14px 16px;
  margin: 14px 0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.card h2 {
  margin-top: 0;
  font-size: 1rem;
  color: #555;
}

/* ---- schema 视图（psql \d 风格）---- */
.schema-table {
  margin-bottom: 18px;
}

.query-sql {
  margin: 0 0 8px;
  font-size: 0.85rem;
  font-weight: 600;
  color: #2c6fbb;
  background: #eef4fc;
  border-left: 3px solid #2c6fbb;
  padding: 6px 10px;
  border-radius: 4px;
}

.schema-table .indexes {
  margin: 6px 0 0;
  font-size: 0.8rem;
  color: #7f8c8d;
}

.cli-table {
  width: 100%;
  border-collapse: collapse;
  font-family: ui-monospace, Consolas, "Courier New", monospace;
  font-size: 0.85rem;
}

.cli-table th,
.cli-table td {
  border: 1px solid #d5d8e0;
  padding: 6px 10px;
  text-align: left;
  vertical-align: top;
}

.cli-table thead th {
  background: #2c3e50;
  color: #fff;
  font-weight: 600;
  white-space: nowrap;
}

.cli-table tbody tr:nth-child(even) {
  background: #f7f8fc;
}

.cli-table code {
  font-family: inherit;
  font-size: 0.82rem;
  word-break: break-all;
}

.cli-table .log-time {
  white-space: nowrap;
  color: #666;
}

/* ---- 移动端适配 ---- */
@media (max-width: 768px) {
  .container {
    padding: 16px 10px 40px;
  }

  h1 {
    font-size: 1.4rem;
  }

  /* 布局改为上下堆叠：sidebar 在上，数据网格在下 */
  .editor-layout {
    flex-direction: column;
    gap: 10px;
  }

  /* sidebar 全宽、表名横排滚动 */
  .sidebar {
    flex: none;
    width: 100%;
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    padding: 6px;
  }

  .sidebar-title {
    width: 100%;
    padding-bottom: 4px;
  }

  .sidebar-sep {
    width: 100%;
  }

  .table-item {
    width: auto;
    flex: 0 0 auto;
    padding: 6px 10px;
    border: 1px solid #e2e5ec;
  }

  .grid-panel {
    padding: 10px;
  }

  .grid-toolbar {
    flex-wrap: wrap;
    gap: 6px;
  }

  .grid-toolbar button {
    flex: 1 1 auto;
  }

  /* 表格容器横向滚动，避免挤压列宽 */
  .table-wrap {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }

  .insert-form {
    gap: 6px;
  }

  .insert-field {
    flex: 1 1 45%;
    min-width: 120px;
  }
}
</style>
