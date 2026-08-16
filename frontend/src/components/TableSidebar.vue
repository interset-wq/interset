<script setup>
// 左侧表列表 sidebar（Neon/Supabase 风格）：表名 + schema 视图入口
defineProps({
  tableNames: { type: Array, required: true },
  activeTable: { type: String, default: null },
});

const emit = defineEmits(["select"]);
</script>

<template>
  <aside class="sidebar">
    <div class="sidebar-title">Tables</div>
    <button
      v-for="t in tableNames"
      :key="t"
      class="table-item"
      :class="{ active: activeTable === t }"
      @click="emit('select', t)"
    >
      {{ t }}
    </button>
    <div class="sidebar-sep"></div>
    <div class="sidebar-title">Views</div>
    <button
      class="table-item"
      :class="{ active: activeTable === 'schema' }"
      @click="emit('select', 'schema')"
    >
      schema
    </button>
  </aside>
</template>
