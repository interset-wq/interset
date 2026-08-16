<script setup>
// 插入行表单：按列生成输入项，外键列渲染为下拉选择；主键列（id 等）不在表单中创建
import { computed } from "vue";

const props = defineProps({
  columns: { type: Array, required: true },
  fkColumns: { type: Array, default: () => [] },
  fkOptions: { type: Object, default: () => ({}) },
  loading: { type: Boolean, default: false },
  insertForm: { type: Object, required: true },
});

const emit = defineEmits(["save", "cancel"]);

// 仅展示非主键列（PK 由数据库自动生成，禁止通过表单填写）
const editableColumns = computed(() =>
  props.columns.filter((c) => !c.primary_key)
);
</script>

<template>
  <form class="insert-form" @submit.prevent="emit('save')">
    <label v-for="c in editableColumns" :key="c.column" class="insert-field">
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
