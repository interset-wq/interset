// 表数据 composable：管理当前表、schema、分页、单元格编辑与 CRUD 逻辑
import { computed, onMounted, ref } from "vue";
import { api } from "../api.js";

// 表列表（Neon/Supabase 风格 sidebar）
export const TABLE_NAMES = ["hero", "team", "mission", "mission_hero"];

// 外键列：hero.team_id / mission_hero.mission_id / mission_hero.hero_id
export const FK_COLUMNS = {
  hero: ["team_id"],
  mission: [],
  mission_hero: ["mission_id", "hero_id"],
  team: [],
};

export function useTableData() {
  // ---- 页面状态 ----
  const health = ref(null);
  const error = ref("");
  const warning = ref("");
  const loading = ref(false);
  const sqlLogs = ref([]);

  const activeTable = ref(null); // 当前选中的表名
  const schema = ref({}); // 表名 -> 列定义 [{column,type,nullable,default,primary_key}]
  const rows = ref([]); // 当前表的数据行
  const fkOptions = ref({}); // 外键选项：列名 -> [{id, label}]
  const loadedTables = ref({}); // 记录已加载的表（避免重复请求 schema）

  // 编辑 / 插入状态
  const editingCell = ref(null); // {rowIdx, column}
  const insertMode = ref(false);
  const insertForm = ref({});

  // 分页状态（hero 表使用后端分页，默认每页 5 条）
  const page = ref(1);
  const pageSize = ref(5);
  const total = ref(0);

  // 总页数
  const totalPages = computed(() =>
    Math.max(1, Math.ceil(total.value / pageSize.value))
  );

  // schema 视图：按表分组的表结构（psql \d 风格，每张表一个表格）
  const tableGroups = computed(() =>
    Object.entries(schema.value).map(([table, columns]) => ({ table, columns }))
  );

  // 当前表的列定义（用于表头渲染）
  function currentColumns() {
    return schema.value[activeTable.value] || [];
  }

  // 主键列名集合
  function pkSet(table) {
    return new Set(
      (schema.value[table] || [])
        .filter((c) => c.primary_key)
        .map((c) => c.column)
    );
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
      // 主数据：所有表都走后端分页（offset/limit + total）
      const offset = (page.value - 1) * pageSize.value;
      const limit = pageSize.value;
      let data;
      if (name === "hero") {
        data = await api(`/heroes?offset=${offset}&limit=${limit}`);
      } else if (name === "team") {
        data = await api(`/teams?offset=${offset}&limit=${limit}`);
      } else if (name === "mission") {
        data = await api(`/missions?offset=${offset}&limit=${limit}`);
      } else if (name === "mission_hero") {
        data = await api(`/missions/links?offset=${offset}&limit=${limit}`);
      }
      // 兼容新旧后端：{items,total} 或纯数组；纯数组说明后端过旧，无法分页
      if (Array.isArray(data)) {
        rows.value = data;
        total.value = data.length;
        warning.value =
          "Backend returned legacy array format — pagination unavailable. Please restart the backend (uv run python main.py).";
      } else {
        rows.value = data?.items ?? [];
        total.value = data?.total ?? 0;
        warning.value = "";
      }
      // 外键选项（并行加载关联表，兼容 {items,total} 或纯数组）
      const fks = FK_COLUMNS[name] || [];
      const tasks = [];
      if (fks.includes("team_id")) {
        tasks.push(
          api("/teams?limit=100").then(
            (d) =>
              (fkOptions.value.team_id = (Array.isArray(d) ? d : d?.items ?? []).map(
                (t) => ({ id: t.id, label: t.name })
              ))
          )
        );
      }
      if (fks.includes("mission_id")) {
        tasks.push(
          api("/missions?limit=100").then(
            (d) =>
              (fkOptions.value.mission_id = (Array.isArray(d) ? d : d?.items ?? []).map(
                (m) => ({ id: m.id, label: m.name })
              ))
          )
        );
      }
      if (fks.includes("hero_id")) {
        tasks.push(
          api("/heroes?limit=100").then(
            (d) =>
              (fkOptions.value.hero_id = (Array.isArray(d) ? d : d?.items ?? []).map(
                (h) => ({ id: h.id, label: h.name })
              ))
          )
        );
      }
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
  }

  function cancelEdit() {
    editingCell.value = null;
  }

  function isEditing(rowIdx, column) {
    return (
      editingCell.value &&
      editingCell.value.rowIdx === rowIdx &&
      editingCell.value.column === column
    );
  }

  // 保存单元格（PATCH）；value 由子组件在保存时传入
  async function saveCell(row, rowIdx, value) {
    const { column } = editingCell.value;
    const table = activeTable.value;
    let v = value;
    const colDef = currentColumns().find((c) => c.column === column);
    if (colDef && colDef.type.toUpperCase().includes("INT")) {
      v = v === "" || v === "NULL" ? null : Number(v);
    } else if (v === "NULL" || v === "") {
      v = null;
    }
    try {
      if (table === "hero") {
        await api(`/heroes/${row.id}`, {
          method: "PATCH",
          body: JSON.stringify({ [column]: v }),
        });
      } else if (table === "team") {
        await api(`/teams/${row.id}`, {
          method: "PATCH",
          body: JSON.stringify({ [column]: v }),
        });
      } else if (table === "mission") {
        await api(`/missions/${row.id}`, {
          method: "PATCH",
          body: JSON.stringify({ [column]: v }),
        });
      } else if (table === "mission_hero") {
        await api(`/missions/links/${row.mission_id}/${row.hero_id}`, {
          method: "PATCH",
          body: JSON.stringify({ [column]: v }),
        });
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
      else if (table === "mission")
        await api(`/missions/${row.id}`, { method: "DELETE" });
      else if (table === "mission_hero")
        await api(`/missions/links/${row.mission_id}/${row.hero_id}`, {
          method: "DELETE",
        });
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
      if (table === "hero") {
        await api("/heroes", { method: "POST", body: JSON.stringify(body) });
      } else if (table === "team") {
        await api("/teams", { method: "POST", body: JSON.stringify(body) });
      } else if (table === "mission") {
        await api("/missions", { method: "POST", body: JSON.stringify(body) });
      } else if (table === "mission_hero") {
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

  // 初始只检查后端健康状态，不查询任何表
  onMounted(async () => {
    try {
      health.value = await api("/health");
    } catch (e) {
      error.value = e.message;
    }
  });

  return {
    health,
    error,
    warning,
    loading,
    sqlLogs,
    activeTable,
    schema,
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
    pkSet,
    loadTable,
    goToPage,
    cellText,
    startEdit,
    cancelEdit,
    isEditing,
    saveCell,
    deleteRow,
    startInsert,
    cancelInsert,
    isFkColumn,
    fkOptionsOf,
    saveInsert,
  };
}
