<script setup>
// SQL 执行日志面板（content 区域下方独立 section，显示最近 5 条）
defineProps({
  sqlLogs: { type: Array, required: true },
});
</script>

<template>
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
</template>
