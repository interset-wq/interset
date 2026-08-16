<script setup>
import { onMounted, ref } from "vue";

// 页面数据：英雄列表、团队列表、后端健康状态、SQL 执行日志
const heroes = ref([]);
const teams = ref([]);
const health = ref(null);
const sqlLogs = ref([]);
const error = ref("");
const loading = ref(false);

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
    throw new Error(body.detail || `请求失败：${res.status}`);
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

// 新增团队
async function createTeam() {
  error.value = "";
  if (!teamForm.value.name) {
    error.value = "name 为必填项";
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
    error.value = "name 和 secret_name 为必填项";
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
      后端状态：
      <span :class="health ? 'ok' : 'err'">
        {{ health ? health.status : "离线" }}
      </span>
    </p>

    <section class="card">
      <h2>新增英雄</h2>
      <form @submit.prevent="createHero">
        <input v-model="form.name" placeholder="name（必填）" />
        <input v-model="form.secret_name" placeholder="secret_name（必填）" />
        <input v-model.number="form.age" type="number" placeholder="age" />
        <select v-model="form.team_id">
          <option :value="null">— 无团队 —</option>
          <option v-for="t in teams" :key="t.id" :value="t.id">{{ t.name }}</option>
        </select>
        <button type="submit" :disabled="loading">
          {{ loading ? "提交中…" : "创建" }}
        </button>
      </form>
    </section>

    <section class="card">
      <h2>新增团队</h2>
      <form @submit.prevent="createTeam">
        <input v-model="teamForm.name" placeholder="name（必填）" />
        <input v-model="teamForm.headquarters" placeholder="headquarters" />
        <button type="submit" :disabled="loading">
          {{ loading ? "提交中…" : "创建团队" }}
        </button>
      </form>
    </section>

    <section class="card">
      <h2>团队（{{ teams.length }}）</h2>
      <ul v-if="teams.length">
        <li v-for="t in teams" :key="t.id">
          <strong>{{ t.name }}</strong> · {{ t.headquarters }} · {{ t.heroes.length }} 名成员
        </li>
      </ul>
      <p v-else class="muted">暂无团队，先创建一个吧！</p>
    </section>

    <section class="card">
      <h2>英雄列表（{{ heroes.length }}）</h2>
      <p v-if="error" class="err">{{ error }}</p>
      <ul v-if="heroes.length">
        <li v-for="h in heroes" :key="h.id">
          {{ h.name }}（{{ h.secret_name }}）
          <template v-if="h.age !== null">，{{ h.age }} 岁</template>
          <template v-if="h.team_id">，队伍 #{{ h.team_id }}</template>
          <button class="danger" @click="deleteHero(h.id)">删除</button>
        </li>
      </ul>
      <p v-else class="muted">暂无英雄，创建第一个吧！</p>
    </section>

    <section class="card">
      <h2>SQL 执行日志（最近 {{ sqlLogs.length }} 条）</h2>
      <p class="muted">每次操作（查询/新增/删除）对应的 SQL 语句，最新的在前。</p>
      <ul v-if="sqlLogs.length" class="sql-log">
        <li v-for="(log, i) in sqlLogs" :key="i">
          <code>{{ log.sql }}</code>
          <span v-if="log.params" class="muted">{{ log.params }}</span>
          <span class="log-time">{{ log.time }}</span>
        </li>
      </ul>
      <p v-else class="muted">暂无 SQL 日志</p>
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
  max-width: 720px;
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
}

.muted {
  color: #999;
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
  font-size: 1.1rem;
}

form {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
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
  margin-left: 8px;
  padding: 3px 10px;
  font-size: 0.85rem;
}

ul {
  list-style: none;
  padding: 0;
  margin: 8px 0 0;
}

li {
  padding: 6px 0;
  border-bottom: 1px dashed #eef0f4;
}

.sql-log code {
  display: block;
  font-size: 0.85rem;
  background: #f0f2f7;
  padding: 6px 8px;
  border-radius: 4px;
  word-break: break-all;
}

.sql-log .log-time {
  float: right;
  color: #999;
  font-size: 0.8rem;
  margin-top: 4px;
}
</style>
