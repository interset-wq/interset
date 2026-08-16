<script setup>
import { computed, onMounted, ref } from "vue";

// 页面数据：英雄、团队、任务、中间表、健康状态、SQL 执行日志、关联表、表结构
const heroes = ref([]);
const teams = ref([]);
const missions = ref([]);
const missionLinks = ref([]);
const health = ref(null);
const sqlLogs = ref([]);
const joined = ref([]);
const tables = ref([]);
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

// 新增任务表单（hero_ids 多选，关联英雄写入中间表 mission_hero）
const missionForm = ref({
  name: "",
  location: "",
  hero_ids: [],
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
  const [hs, ts, mss, links, logs, jd, tbs] = await Promise.all([
    api("/heroes?limit=100"),
    api("/teams"),
    api("/missions"),
    api("/missions/links"),
    api("/sql-logs?limit=5"),
    api("/heroes/joined"),
    api("/tables"),
  ]);
  heroes.value = hs;
  teams.value = ts;
  missions.value = mss;
  missionLinks.value = links;
  sqlLogs.value = logs;
  joined.value = jd;
  tables.value = tbs;
}

// 英雄表格里显示团队名（id → name），无团队显示 NULL
function teamName(id) {
  if (!id) return "NULL";
  return teams.value.find((t) => t.id === id)?.name ?? `#${id}`;
}

// 表结构按表分组（psql \d 风格：每张表一个表格）
const tableGroups = computed(() => {
  const map = new Map();
  for (const col of tables.value) {
    if (!map.has(col.table)) map.set(col.table, []);
    map.get(col.table).push(col);
  }
  return [...map.entries()].map(([table, columns]) => ({ table, columns }));
});

// 某张表的主键列（psql Indexes 行展示）
function pkColumns(group) {
  const pks = group.columns.filter((c) => c.primary_key).map((c) => c.column);
  return pks.length ? pks.join(", ") : "(none)";
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

// 新增任务（hero_ids 关联英雄，写入 M2M 中间表 mission_hero）
async function createMission() {
  error.value = "";
  if (!missionForm.value.name) {
    error.value = "name is required";
    return;
  }
  loading.value = true;
  try {
    await api("/missions", {
      method: "POST",
      body: JSON.stringify({
        name: missionForm.value.name,
        location: missionForm.value.location || null,
        hero_ids: missionForm.value.hero_ids,
      }),
    });
    missionForm.value = { name: "", location: "", hero_ids: [] };
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

// 查看单个英雄详情（GET /heroes/{id}）
const heroDetail = ref(null);
async function viewHero(id) {
  error.value = "";
  try {
    heroDetail.value = await api(`/heroes/${id}`);
  } catch (e) {
    error.value = e.message;
  }
}

// 行内编辑英雄（PATCH /heroes/{id}）
const editingHeroId = ref(null);
const editHeroForm = ref({ name: "", secret_name: "", age: null, team_id: null });

function startEditHero(h) {
  editingHeroId.value = h.id;
  editHeroForm.value = {
    name: h.name,
    secret_name: h.secret_name,
    age: h.age,
    team_id: h.team_id,
  };
}

function cancelEditHero() {
  editingHeroId.value = null;
}

async function saveHero(id) {
  error.value = "";
  loading.value = true;
  try {
    await api(`/heroes/${id}`, {
      method: "PATCH",
      body: JSON.stringify({
        name: editHeroForm.value.name,
        secret_name: editHeroForm.value.secret_name,
        age: editHeroForm.value.age || null,
        team_id: editHeroForm.value.team_id || null,
      }),
    });
    editingHeroId.value = null;
    await loadAll();
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}

// 查看单个团队详情（GET /teams/{id}）
const teamDetail = ref(null);
async function viewTeam(id) {
  error.value = "";
  try {
    teamDetail.value = await api(`/teams/${id}`);
  } catch (e) {
    error.value = e.message;
  }
}

// 行内编辑团队（PATCH /teams/{id}）
const editingTeamId = ref(null);
const editTeamForm = ref({ name: "", headquarters: "" });

function startEditTeam(t) {
  editingTeamId.value = t.id;
  editTeamForm.value = {
    name: t.name,
    headquarters: t.headquarters,
  };
}

function cancelEditTeam() {
  editingTeamId.value = null;
}

async function saveTeam(id) {
  error.value = "";
  loading.value = true;
  try {
    await api(`/teams/${id}`, {
      method: "PATCH",
      body: JSON.stringify({
        name: editTeamForm.value.name,
        headquarters: editTeamForm.value.headquarters,
      }),
    });
    editingTeamId.value = null;
    await loadAll();
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}

// 删除团队（DELETE /teams/{id}）
async function deleteTeam(id) {
  error.value = "";
  try {
    await api(`/teams/${id}`, { method: "DELETE" });
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
      <button :class="{ active: activeTab === 'missions' }" @click="activeTab = 'missions'">
        mission（{{ missions.length }}）
      </button>
      <button
        :class="{ active: activeTab === 'mission_hero' }"
        @click="activeTab = 'mission_hero'"
      >
        mission_hero（{{ missionLinks.length }}）
      </button>
      <button :class="{ active: activeTab === 'joined' }" @click="activeTab = 'joined'">
        hero LEFT JOIN team（{{ joined.length }}）
      </button>
      <button :class="{ active: activeTab === 'schema' }" @click="activeTab = 'schema'">
        schema（{{ tables.length }}）
      </button>
    </nav>

    <!-- 英雄 Tab：表单 + hero 表 -->
    <section v-if="activeTab === 'heroes'" class="card">
      <h2>INSERT INTO hero</h2>
      <form @submit.prevent="createHero">
        <input v-model="form.name" placeholder="Hero name (required)" />
        <input v-model="form.secret_name" placeholder="Secret identity (required)" />
        <input v-model.number="form.age" type="number" placeholder="Age" />
        <select v-model="form.team_id">
          <option :value="null">— No team —</option>
          <option v-for="t in teams" :key="t.id" :value="t.id">{{ t.name }}</option>
        </select>
        <button type="submit" :disabled="loading">
          {{ loading ? "Submitting…" : "Create" }}
        </button>
      </form>

      <div v-if="heroDetail" class="detail-box">
        <strong>GET /api/heroes/{{ heroDetail.id }}</strong>
        <pre>{{ JSON.stringify(heroDetail, null, 2) }}</pre>
        <button class="secondary" @click="heroDetail = null">Close</button>
      </div>

      <h3 class="query-sql">SELECT * FROM hero</h3>

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
            <template v-for="h in heroes" :key="h.id">
              <tr v-if="editingHeroId === h.id">
                <td>{{ h.id }}</td>
                <td><input v-model="editHeroForm.name" placeholder="Hero name" /></td>
                <td><input v-model="editHeroForm.secret_name" placeholder="Secret identity" /></td>
                <td><input v-model.number="editHeroForm.age" type="number" placeholder="Age" /></td>
                <td>
                  <select v-model="editHeroForm.team_id">
                    <option :value="null">— No team —</option>
                    <option v-for="t in teams" :key="t.id" :value="t.id">{{ t.name }}</option>
                  </select>
                </td>
                <td>
                  <button @click="saveHero(h.id)">Save</button>
                  <button class="secondary" @click="cancelEditHero">Cancel</button>
                </td>
              </tr>
              <tr v-else>
                <td>{{ h.id }}</td>
                <td>{{ h.name }}</td>
                <td>{{ h.secret_name }}</td>
                <td>{{ h.age ?? "NULL" }}</td>
                <td>{{ teamName(h.team_id) }}</td>
                <td>
                  <button class="secondary" @click="viewHero(h.id)">View</button>
                  <button class="secondary" @click="startEditHero(h)">Edit</button>
                  <button class="danger" @click="deleteHero(h.id)">Delete</button>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
      <p v-if="!heroes.length" class="muted">0 rows — no heroes yet, create one!</p>
    </section>

    <!-- 团队 Tab：表单 + team 表 -->
    <section v-if="activeTab === 'teams'" class="card">
      <h2>INSERT INTO team</h2>
      <form @submit.prevent="createTeam">
        <input v-model="teamForm.name" placeholder="Team name (required)" />
        <input v-model="teamForm.headquarters" placeholder="Headquarters" />
        <button type="submit" :disabled="loading">
          {{ loading ? "Submitting…" : "Create team" }}
        </button>
      </form>

      <div v-if="teamDetail" class="detail-box">
        <strong>GET /api/teams/{{ teamDetail.id }}</strong>
        <pre>{{ JSON.stringify(teamDetail, null, 2) }}</pre>
        <button class="secondary" @click="teamDetail = null">Close</button>
      </div>

      <h3 class="query-sql">SELECT * FROM team</h3>

      <div class="table-wrap">
        <table class="cli-table">
          <thead>
            <tr>
              <th>id</th>
              <th>name</th>
              <th>headquarters</th>
              <th>heroes</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <template v-for="t in teams" :key="t.id">
              <tr v-if="editingTeamId === t.id">
                <td>{{ t.id }}</td>
                <td><input v-model="editTeamForm.name" placeholder="Team name" /></td>
                <td><input v-model="editTeamForm.headquarters" placeholder="Headquarters" /></td>
                <td>
                  <template v-if="t.heroes.length">
                    {{ t.heroes.map((h) => h.name).join(", ") }}
                  </template>
                  <template v-else>NULL</template>
                </td>
                <td>
                  <button @click="saveTeam(t.id)">Save</button>
                  <button class="secondary" @click="cancelEditTeam">Cancel</button>
                </td>
              </tr>
              <tr v-else>
                <td>{{ t.id }}</td>
                <td>{{ t.name }}</td>
                <td>{{ t.headquarters }}</td>
                <td>
                  <template v-if="t.heroes.length">
                    {{ t.heroes.map((h) => h.name).join(", ") }}
                  </template>
                  <template v-else>NULL</template>
                </td>
                <td>
                  <button class="secondary" @click="viewTeam(t.id)">View</button>
                  <button class="secondary" @click="startEditTeam(t)">Edit</button>
                  <button class="danger" @click="deleteTeam(t.id)">Delete</button>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
      <p v-if="!teams.length" class="muted">0 rows — no teams yet, create one!</p>
    </section>

    <!-- 任务 Tab：表单 + mission 表（M2M，hero_ids 关联英雄） -->
    <section v-if="activeTab === 'missions'" class="card">
      <h2>INSERT INTO mission</h2>
      <form @submit.prevent="createMission">
        <input v-model="missionForm.name" placeholder="Mission name (required)" />
        <input v-model="missionForm.location" placeholder="Location" />
        <select v-model="missionForm.hero_ids" multiple size="3">
          <option v-for="h in heroes" :key="h.id" :value="h.id">
            {{ h.name }}（#{{ h.id }}）
          </option>
        </select>
        <button type="submit" :disabled="loading">
          {{ loading ? "Submitting…" : "Create mission" }}
        </button>
      </form>

      <h3 class="query-sql">SELECT * FROM mission</h3>

      <div class="table-wrap">
        <table class="cli-table">
          <thead>
            <tr>
              <th>id</th>
              <th>name</th>
              <th>location</th>
              <th>heroes</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="m in missions" :key="m.id">
              <td>{{ m.id }}</td>
              <td>{{ m.name }}</td>
              <td>{{ m.location ?? "NULL" }}</td>
              <td>
                <template v-if="m.heroes.length">
                  {{ m.heroes.map((h) => h.name).join(", ") }}
                </template>
                <template v-else>NULL</template>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-if="!missions.length" class="muted">0 rows — no missions yet, create one!</p>
    </section>

    <!-- 中间表 Tab：mission_hero 的 DB 实际行 -->
    <section v-if="activeTab === 'mission_hero'" class="card">
      <h2>mission_hero（Hero ↔ Mission M2M 中间表）</h2>
      <p class="muted">DB 层面的中间表实际数据行（含关联名称便于阅读）。</p>

      <h3 class="query-sql">SELECT * FROM mission_hero</h3>

      <div class="table-wrap">
        <table class="cli-table">
          <thead>
            <tr>
              <th>mission_id</th>
              <th>hero_id</th>
              <th>role</th>
              <th>mission_name</th>
              <th>hero_name</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(link, i) in missionLinks" :key="i">
              <td>{{ link.mission_id }}</td>
              <td>{{ link.hero_id }}</td>
              <td>{{ link.role ?? "NULL" }}</td>
              <td>{{ link.mission_name }}</td>
              <td>{{ link.hero_name }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-if="!missionLinks.length" class="muted">
        0 rows — no links yet, create a mission with heroes
      </p>
    </section>

    <!-- 关联表 Tab：hero LEFT JOIN team -->
    <section v-if="activeTab === 'joined'" class="card">
      <h2>SELECT hero.*, team.name AS team_name FROM hero LEFT JOIN team</h2>

      <div class="table-wrap">
        <table class="cli-table">
          <thead>
            <tr>
              <th>id</th>
              <th>name</th>
              <th>secret_name</th>
              <th>age</th>
              <th>team_id</th>
              <th>team_name</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in joined" :key="row.id">
              <td>{{ row.id }}</td>
              <td>{{ row.name }}</td>
              <td>{{ row.secret_name }}</td>
              <td>{{ row.age ?? "NULL" }}</td>
              <td>{{ row.team_id ?? "NULL" }}</td>
              <td>{{ row.team_name }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-if="!joined.length" class="muted">0 rows — no joined rows yet</p>
    </section>

    <!-- 表结构 Tab：psql \d 风格，每张表一个表格 -->
    <section v-if="activeTab === 'schema'" class="card">
      <h2>Schema（psql \d）</h2>

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

      <p v-if="!tableGroups.length" class="muted">0 rows — no tables found</p>
    </section>

    <!-- SQL 日志：content 区域下方独立 section，始终显示 -->
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

/* 表格对应的查询 SQL 标题 */
.query-sql {
  margin: 0 0 10px;
  font-size: 0.85rem;
  font-weight: 600;
  font-family: ui-monospace, Consolas, monospace;
  color: #2c6fbb;
  background: #eef4fc;
  border-left: 3px solid #2c6fbb;
  padding: 6px 10px;
  border-radius: 4px;
  word-break: break-all;
}

/* 表结构：每张表一个区块（psql \d 风格） */
.schema-table {
  margin-bottom: 20px;
}

.schema-table .indexes {
  margin: 6px 0 0;
  font-size: 0.8rem;
  font-family: ui-monospace, Consolas, monospace;
  color: #7f8c8d;
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

button.secondary {
  background: #7f8c8d;
  padding: 3px 10px;
  font-size: 0.85rem;
}

/* 单个记录详情（GET /{id} 结果） */
.detail-box {
  margin-bottom: 12px;
  padding: 10px 12px;
  background: #f0f2f7;
  border: 1px solid #d5d8e0;
  border-radius: 6px;
}

.detail-box strong {
  font-size: 0.85rem;
  color: #555;
}

.detail-box pre {
  margin: 8px 0;
  padding: 8px;
  background: #fff;
  border: 1px solid #e2e5ec;
  border-radius: 4px;
  font-size: 0.8rem;
  overflow-x: auto;
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
  /* 继承 .cli-table 的等宽字体栈，避免浏览器默认 code 字体不一致 */
  font-family: inherit;
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
