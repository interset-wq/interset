<script setup>
// 可编辑数据网格（Neon/Supabase 风格）：单元格点击编辑、行删除
import { computed, ref, watch } from "vue";

const props = defineProps({
  columns: { type: Array, required: true }, // 列定义（含 primary_key/type）
  rows: { type: Array, required: true },
  fkColumns: { type: Array, default: () => [] }, // 当前表的外键列名
  fkOptions: { type: Object, default: () => ({}) }, // 列名 -> [{id, label}]
  editingCell: { type: Object, default: null }, // {rowIdx, column}
});

const emit = defineEmits(["start-edit", "save-cell", "cancel-edit", "delete-row"]);

// 编辑草稿值：本地维护，保存时随事件传给父组件
const draftValue = ref("");
watch(
  () => props.editingCell,
  (cell) => {
    if (cell) {
      const row = props.rows[cell.rowIdx];
      draftValue.value = row ? row[cell.column] ?? "" : "";
    }
  },
  { immediate: true }
);

// 主键列名集合（主键不可编辑）
const pks = computed(
  () => new Set(props.columns.filter((c) => c.primary_key).map((c) => c.column))
);

// 单元格是否为外键列
function isFkColumn(column) {
  return props.fkColumns.includes(column);
}

function fkOptionsOf(column) {
  return props.fkOptions[column] || [];
}

// 当前单元格是否处于编辑态
function isEditing(rowIdx, column) {
  return (
    props.editingCell &&
    props.editingCell.rowIdx === rowIdx &&
    props.editingCell.column === column
  );
}

// 展示值：NULL / 外键 label / 普通值
function cellText(row, column) {
  const v = row[column];
  if (v === null || v === undefined) return "NULL";
  const opts = props.fkOptions[column];
  if (opts && props.fkColumns.includes(column)) {
    const hit = opts.find((o) => o.id === v);
    if (hit) return `${hit.label} (${v})`;
  }
  return String(v);
}
</script>

<template>
  <div class="table-wrap">
    <table class="grid-table">
      <thead>
        <tr>
          <th v-for="c in columns" :key="c.column" class="col-header">
            {{ c.column }}
          </th>
          <th class="col-actions"></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(row, i) in rows" :key="i">
          <td
            v-for="c in columns"
            :key="c.column"
            class="cell"
            :class="{ editable: !pks.has(c.column) }"
            @click="!pks.has(c.column) && emit('start-edit', row, i, c.column)"
          >
            <template v-if="isEditing(i, c.column)">
              <select
                v-if="isFkColumn(c.column)"
                :value="draftValue"
                class="cell-input"
                autofocus
                @change="emit('save-cell', row, i, $event.target.value)"
                @blur="emit('save-cell', row, i, draftValue)"
              >
                <option :value="null">NULL</option>
                <option v-for="o in fkOptionsOf(c.column)" :key="o.id" :value="o.id">
                  {{ o.label }}
                </option>
              </select>
              <input
                v-else
                :value="draftValue"
                class="cell-input"
                autofocus
                @input="draftValue = $event.target.value"
                @keydown.enter="emit('save-cell', row, i, draftValue)"
                @keydown.esc="emit('cancel-edit')"
                @blur="emit('save-cell', row, i, draftValue)"
              />
            </template>
            <template v-else>{{ cellText(row, c.column) }}</template>
          </td>
          <td class="cell-actions">
            <button class="danger small" @click="emit('delete-row', row)">🗑</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
