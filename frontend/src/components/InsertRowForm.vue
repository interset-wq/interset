<script setup>
// 插入行表单：按列生成输入项，外键列渲染为下拉选择
defineProps({
  columns: { type: Array, required: true },
  fkColumns: { type: Array, default: () => [] },
  fkOptions: { type: Object, default: () => ({}) },
  loading: { type: Boolean, default: false },
  insertForm: { type: Object, required: true },
});

const emit = defineEmits(["save", "cancel"]);
</script>

<template>
  <form class="insert-form" @submit.prevent="emit('save')">
    <label v-for="c in columns" :key="c.column" class="insert-field">
      <span>{{ c.column }}</span>
      <select
        v-if="fkColumns.includes(c.column)"
        v-model="insertForm[c.column]"
      >
        <option value="">— NULL —</option>
        <option v-for="o in fkOptions[c.column] || []" :key="o.id" :value="o.id">
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
      <button type="button" class="secondary" @click="emit('cancel')">Cancel</button>
    </div>
  </form>
</template>
