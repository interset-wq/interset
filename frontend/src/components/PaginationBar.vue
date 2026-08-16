<script setup>
// 分页控件（hero 表使用后端分页）
defineProps({
  page: { type: Number, required: true },
  totalPages: { type: Number, required: true },
  total: { type: Number, required: true },
  pageSize: { type: Number, required: true },
});

const emit = defineEmits(["go-page", "change-page-size"]);
</script>

<template>
  <div class="pagination">
    <button
      class="secondary small"
      :disabled="page <= 1"
      @click="emit('go-page', page - 1)"
    >
      ← Prev
    </button>
    <span class="page-info">
      Page {{ page }} / {{ totalPages }}（{{ total }} rows）
    </span>
    <button
      class="secondary small"
      :disabled="page >= totalPages"
      @click="emit('go-page', page + 1)"
    >
      Next →
    </button>
    <select
      :value="pageSize"
      class="page-size"
      @change="emit('change-page-size', Number($event.target.value))"
    >
      <option :value="5">5 / page</option>
      <option :value="10">10 / page</option>
      <option :value="20">20 / page</option>
      <option :value="50">50 / page</option>
    </select>
  </div>
</template>
