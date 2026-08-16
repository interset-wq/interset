<script setup>
// 分页控件：仅显示上一页/下一页与页码信息（每页条数固定为 5，不允许调整）
defineProps({
  page: { type: Number, required: true },
  totalPages: { type: Number, required: true },
  total: { type: Number, required: true },
});

const emit = defineEmits(["go-page"]);
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
  </div>
</template>
