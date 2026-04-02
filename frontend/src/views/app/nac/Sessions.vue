<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
      <h3>📡 在线终端</h3>
      <div>
        <el-tag type="success" style="margin-right:8px;">在线: {{ stats.online }}</el-tag>
        <el-button size="small" @click="load"><el-icon><Refresh /></el-icon> 刷新</el-button>
      </div>
    </div>
    <el-table :data="items" v-loading="loading" stripe>
      <el-table-column prop="mac_address" label="MAC 地址" width="150" />
      <el-table-column prop="ip_address" label="IP 地址" width="140" />
      <el-table-column prop="username" label="用户名" width="120" />
      <el-table-column prop="auth_method" label="认证方式" width="100" />
      <el-table-column prop="vlan_id" label="VLAN" width="70" />
      <el-table-column prop="switch_ip" label="交换机" width="140" />
      <el-table-column prop="switch_port" label="端口" width="100" />
      <el-table-column label="合规" width="80">
        <template #default="{row}">
          <el-tag :type="{compliant:'success',non_compliant:'danger',quarantined:'warning'}[row.compliance_status]||'info'" size="small">
            {{ {compliant:'合规',non_compliant:'不合规',quarantined:'隔离',unknown:'未知'}[row.compliance_status] }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="80">
        <template #default="{row}">
          <el-popconfirm title="确定断开？" @confirm="disconnect(row.id)">
            <template #reference><el-button link size="small" type="danger">断开</el-button></template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/api/request'
const items = ref([]), loading = ref(false), stats = ref({online:0})
async function load() {
  loading.value = true
  try {
    const r = await request.get('/nac/sessions')
    items.value = r.data?.items||[]
    stats.value = {online: r.data?.online_count||0}
  } catch(e){}
  loading.value = false
}
async function disconnect(id) {
  try { await request.post(`/nac/sessions/${id}/disconnect`); ElMessage.success('已断开'); load() } catch(e){}
}
onMounted(load)
</script>
