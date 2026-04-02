<template>
  <div>
    <h3 style="margin-bottom:16px;">⏰ 定时任务管理</h3>
    <el-table :data="tasks" stripe>
      <el-table-column prop="name" label="任务名称" min-width="200" />
      <el-table-column prop="schedule" label="执行周期" width="140" />
      <el-table-column prop="last_run" label="上次执行" width="170" />
      <el-table-column prop="next_run" label="下次执行" width="170" />
      <el-table-column label="状态" width="80"><template #default="{row}"><el-tag :type="row.enabled?'success':'info'" size="small">{{ row.enabled?'启用':'暂停' }}</el-tag></template></el-table-column>
      <el-table-column label="上次结果" width="80"><template #default="{row}"><el-tag :type="row.last_result==='success'?'success':'danger'" size="small">{{ row.last_result==='success'?'成功':'失败' }}</el-tag></template></el-table-column>
      <el-table-column label="操作" width="160">
        <template #default="{row}">
          <el-button link size="small" @click="toggle(row)">{{ row.enabled?'暂停':'恢复' }}</el-button>
          <el-button link size="small" type="primary" @click="runNow(row)">立即执行</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>
<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
const tasks=ref([
  {name:'临时 IP 过期检查',schedule:'每 5 分钟',last_run:'2026-04-02 17:30:00',next_run:'2026-04-02 17:35:00',enabled:true,last_result:'success'},
  {name:'保留 IP 过期检查',schedule:'每小时',last_run:'2026-04-02 17:00:00',next_run:'2026-04-02 18:00:00',enabled:true,last_result:'success'},
  {name:'网段使用率告警',schedule:'每 10 分钟',last_run:'2026-04-02 17:30:00',next_run:'2026-04-02 17:40:00',enabled:true,last_result:'success'},
  {name:'数据库自动备份',schedule:'每天 02:00',last_run:'2026-04-02 02:00:00',next_run:'2026-04-03 02:00:00',enabled:true,last_result:'success'},
  {name:'LDAP 用户同步',schedule:'每 6 小时',last_run:'2026-04-02 12:00:00',next_run:'2026-04-02 18:00:00',enabled:false,last_result:'success'},
  {name:'设备配置自动备份',schedule:'每天 03:00',last_run:'2026-04-02 03:00:00',next_run:'2026-04-03 03:00:00',enabled:true,last_result:'success'},
  {name:'数据清洗',schedule:'每周一 01:00',last_run:'2026-03-31 01:00:00',next_run:'2026-04-07 01:00:00',enabled:true,last_result:'success'},
])
function toggle(t){t.enabled=!t.enabled;ElMessage.success(`任务已${t.enabled?'恢复':'暂停'}`)}
function runNow(t){ElMessage.info(`正在执行: ${t.name}`);setTimeout(()=>ElMessage.success(`${t.name} 执行完成`),1500)}
</script>
