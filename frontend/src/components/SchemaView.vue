<script setup>
// schema 视图：仅显示表结构（psql \d 风格，每张表一个表格），不加载数据行
defineProps({
  tableGroups: { type: Array, required: true },
});

const emit = defineEmits(["refresh"]);

// 某张表的主键列（Indexes 行展示）
function pkColumns(group) {
  const pks = group.columns.filter((c) => c.primary_key).map((c) => c.column);
  return pks.length ? pks.join(", ") : "(none)";
}
</script>

<template>
  <div class="grid-toolbar">
    <span class="table-name">schema</span>
    <span class="col-count">{{ tableGroups.length }} tables</span>
    <button class="secondary" @click="emit('refresh')">Refresh</button>
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
