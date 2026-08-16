<script setup>
// 根组件：组装左侧表列表、数据网格、schema 视图、SQL 日志等子组件
import { FK_COLUMNS, TABLE_NAMES, useTableData } from "./composables/useTableData.js";
import DataGrid from "./components/DataGrid.vue";
import InsertRowForm from "./components/InsertRowForm.vue";
import PaginationBar from "./components/PaginationBar.vue";
import SchemaView from "./components/SchemaView.vue";
import SqlLogPanel from "./components/SqlLogPanel.vue";
import TableSidebar from "./components/TableSidebar.vue";

const {
  health,
  error,
  warning,
  loading,
  sqlLogs,
  activeTable,
  rows,
  fkOptions,
  editingCell,
  insertMode,
  insertForm,
  page,
  pageSize,
  total,
  totalPages,
  tableGroups,
  currentColumns,
  loadTable,
  goToPage,
  startEdit,
  cancelEdit,
  saveCell,
  deleteRow,
  startInsert,
  cancelInsert,
  saveInsert,
} = useTableData();

// 当前表的外键列名（传给网格/表单用于渲染下拉选择）
function currentFkColumns() {
  return FK_COLUMNS[activeTable.value] || [];
}
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
    <p v-if="warning" class="warn">{{ warning }}</p>

    <!-- 布局：左侧表列表 + 右侧数据网格 / schema 视图 -->
    <div class="editor-layout">
      <TableSidebar
        :table-names="TABLE_NAMES"
        :active-table="activeTable"
        @select="loadTable"
      />

      <section class="grid-panel">
        <!-- schema 视图 -->
        <template v-if="activeTable === 'schema'">
          <SchemaView :table-groups="tableGroups" @refresh="loadTable('schema')" />
        </template>

        <!-- 数据表视图 -->
        <template v-else-if="activeTable">
          <div class="grid-toolbar">
            <span class="table-name">{{ activeTable }}</span>
            <span class="col-count">{{ currentColumns().length }} columns</span>
            <button v-if="!insertMode" class="primary" @click="startInsert">
              Insert row
            </button>
            <button class="secondary" @click="loadTable(activeTable)">Refresh</button>
          </div>

          <InsertRowForm
            v-if="insertMode"
            :columns="currentColumns()"
            :fk-columns="currentFkColumns()"
            :fk-options="fkOptions"
            :loading="loading"
            :insert-form="insertForm"
            @save="saveInsert"
            @cancel="cancelInsert"
          />

          <DataGrid
            :columns="currentColumns()"
            :rows="rows"
            :fk-columns="currentFkColumns()"
            :fk-options="fkOptions"
            :editing-cell="editingCell"
            @start-edit="startEdit"
            @save-cell="saveCell"
            @cancel-edit="cancelEdit"
            @delete-row="deleteRow"
          />

          <PaginationBar
            :page="page"
            :total-pages="totalPages"
            :total="total"
            @go-page="goToPage"
          />

          <p v-if="!rows.length" class="muted">0 rows</p>
        </template>

        <div v-else class="empty-state">
          <p>Select a table from the left sidebar to browse and edit data.</p>
        </div>
      </section>
    </div>

    <!-- SQL 日志：content 区域下方独立 section -->
    <SqlLogPanel :sql-logs="sqlLogs" />
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

.warn {
  color: #d68910;
  font-weight: 600;
  background: #fdf3e7;
  border: 1px solid #f5cba7;
  border-radius: 6px;
  padding: 8px 12px;
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
