<script setup>
import { onMounted, ref } from "vue";

// 页面数据：英雄、团队、健康状态、SQL 执行日志
const heroes = ref([]);
const teams = ref([]);
const health = ref(null);
const sqlLogs = ref([]);
const error = ref("");
const loading = ref(false);

// 当前激活的 Tab：heroes / teams / logs
const activeTab = ref("heroes");

// 新增英雄表单
const form = ref({
  name: "",
  secret_name: "",
  age: null,
  team_id: null,
});

// 新增团队表单
const teamForm = ref({
  name: "",
  headquarters: "",
});

// 统一请求封装：前端与后端同源（同一 FastAPI 应用托管），直接调用 /api
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

async function loadAll() {
  const [hs, ts, logs] = await Promise.all([
    api("/heroes?limit=100"),
    api("/teams"),
    api("/sql-logs"),
  ]);
  heroes.value = hs;
  teams.value = ts;
  sqlLogs.value = logs;
}

// 英雄表格里显示团队名（id → name），无团队显示 NULL
function teamName(id) {
  if (!id) return "NULL";
  return teams.value.find((t) => t.id === id)?.name ?? `#${id}`;
}

// 新增团队
async function createTeam() {
  error.value = "";
  if (!teamForm.value.name) {
    error.value = "name is required";
    return;
  }
  loading.value = true;
  try {
    await api("/teams", {
      method: "POST",
      body: JSON.stringify({
        name: teamForm.value.name,
        headquarters: teamForm.value.headquarters || null,
      }),
    });
    teamForm.value = { name: "", headquarters: "" };
    await loadAll();
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}

// 新增英雄
async function createHero() {
  error.value = "";
  if (!form.value.name || !form.value.secret_name) {
    error.value = "name and secret_name are required";
    return;
  }
  loading.value = true;
  try {
    await api("/heroes", {
      method: "POST",
      body: JSON.stringify({
        name: form.value.name,
        secret_name: form.value.secret_name,
        age: form.value.age || null,
        team_id: form.value.team_id || null,
      }),
    });
    form.value = { name: "", secret_name: "", age: null, team_id: null };
    await loadAll();
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}

// 删除英雄
async function deleteHero(id) {
  error.value = "";
  try {
    await api(`/heroes/${id}`, { method: "DELETE" });
    await loadAll();
  } catch (e) {
    error.value = e.message;
  }
}

onMounted(async () => {
  try {
    health.value = await api("/health");
    await loadAll();
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

    <!-- Tab 导航 -->
    <nav class="tabs">
      <button :class="{ active: activeTab === 'heroes' }" @click="activeTab = 'heroes'">
        hero（{{ heroes.length }}）
      </button>
      <button :class="{ active: activeTab === 'teams' }" @click="activeTab = 'teams'">
        team（{{ teams.length }}）
      </button>
      <button :class="{ active: activeTab === 'logs' }" @click="activeTab = 'logs'">
        sql_log（{{ sqlLogs.length }}）
      </button>
    </nav>

    <!-- 英雄 Tab：表单 + hero 表 -->
    <section v-if="activeTab === 'heroes'" class="card">
      <h2>INSERT INTO hero</h2>
      <form @submit.prevent="createHero">
        <input v-model="form.name" placeholder="name (required)" />
        <input v-model="form.secret_name" placeholder="secret_name (required)" />
        <input v-model.number="form.age" type="number" placeholder="age" />
        <select v-model="form.team_id">
          <option :value="null">— no team —</option>
          <option v-for="t in teams" :key="t.id" :value="t.id">{{ t.name }}</option>
        </select>
        <button type="submit" :disabled="loading">
          {{ loading ? "Submitting…" : "Create" }}
        </button>
      </form>

      <div class="table-wrap">
        <table class="cli-table">
          <thead>
            <tr>
              <th>id</th>
              <th>name</th>
              <th>secret_name</th>
              <th>age</th>
              <th>team</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="h in heroes" :key="h.id">
              <td>{{ h.id }}</td>
              <td>{{ h.name }}</td>
              <td>{{ h.secret_name }}</td>
              <td>{{ h.age ?? "NULL" }}</td>
              <td>{{ teamName(h.team_id) }}</td>
              <td><button class="danger" @click="deleteHero(h.id)">Delete</button></td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-if="!heroes.length" class="muted">0 rows — no heroes yet, create one!</p>
    </section>

    <!-- 团队 Tab：表单 + team 表 -->
    <section v-if="activeTab === 'teams'" class="card">
      <h2>INSERT INTO team</h2>
      <form @submit.prevent="createTeam">
        <input v-model="teamForm.name" placeholder="name (required)" />
        <input v-model="teamForm.headquarters" placeholder="headquarters" />
        <button type="submit" :disabled="loading">
          {{ loading ? "Submitting…" : "Create team" }}
        </button>
      </form>

      <div class="table-wrap">
        <table class="cli-table">
          <thead>
            <tr>
              <th>id</th>
              <th>name</th>
              <th>headquarters</th>
              <th>heroes</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="t in teams" :key="t.id">
              <td>{{ t.id }}</td>
              <td>{{ t.name }}</td>
              <td>{{ t.headquarters }}</td>
              <td>
                <template v-if="t.heroes.length">
                  {{ t.heroes.map((h) => h.name).join(", ") }}
                </template>
                <template v-else>NULL</template>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-if="!teams.length" class="muted">0 rows — no teams yet, create one!</p>
    </section>

    <!-- SQL 日志 Tab -->
    <section v-if="activeTab === 'logs'" class="card">
      <h2>sql_log (recent {{ sqlLogs.length }}, newest first)</h2>
      <p class="muted">
        Actual SQL statements and parameters executed for each operation
        (query / insert / delete).
      </p>

      <div class="table-wrap">
        <table class="cli-table">
          <thead>
            <tr>
              <th>time</th>
              <th>sql</th>
              <th>params</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(log, i) in sqlLogs" :key="i">
              <td class="log-time">{{ log.time }}</td>
              <td><code>{{ log.sql }}</code></td>
              <td class="log-params">{{ log.params }}</td>
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
  font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
  background: #f5f6fa;
  color: #2c3e50;
}

.container {
  max-width: 960px;
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

/* ---- Tab 导航 ---- */
.tabs {
  display: flex;
  gap: 6px;
  margin: 16px 0;
}

.tabs button {
  padding: 8px 18px;
  border: 1px solid #d5d8e0;
  border-radius: 6px;
  background: #fff;
  color: #2c3e50;
  font-size: 0.95rem;
  font-family: ui-monospace, Consolas, monospace;
  cursor: pointer;
}

.tabs button.active {
  background: #2c6fbb;
  border-color: #2c6fbb;
  color: #fff;
}

.card {
  background: #fff;
  border-radius: 10px;
  padding: 16px 20px;
  margin: 16px 0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.card h2 {
  margin-top: 0;
  font-size: 1rem;
  font-family: ui-monospace, Consolas, monospace;
  color: #555;
}

form {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
}

input,
select {
  padding: 8px 10px;
  border: 1px solid #d5d8e0;
  border-radius: 6px;
  font-size: 0.95rem;
  flex: 1;
  min-width: 120px;
}

button {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  background: #2c6fbb;
  color: #fff;
  font-size: 0.95rem;
  cursor: pointer;
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

button.danger {
  background: #e74c3c;
  padding: 3px 10px;
  font-size: 0.85rem;
}

/* ---- SQL CLI 风格表格 ---- */
.table-wrap {
  overflow-x: auto;
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
  font-size: 0.82rem;
  word-break: break-all;
}

.cli-table .log-time,
.cli-table .log-params {
  white-space: nowrap;
  color: #666;
}

.cli-table .log-params {
  font-size: 0.8rem;
}
</style>
