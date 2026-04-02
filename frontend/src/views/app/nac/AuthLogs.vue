<template>
  <div>
    <h3 style="margin-bottom:16px;">📋 认证日志</h3>
    <div style="margin-bottom:12px;display:flex;gap:8px;">
      <el-select v-model="filterResult" placeholder="认证结果" clearable size="default" style="width:140px;" @change="load">
        <el-option label="成功" value="success" /><el-option label="失败" value="failed" /><el-option label="拒绝" value="rejected" />
      </el-select>
      <el-input v-model="filterMac" placeholder="搜索 MAC" clearable style="width:200px;" @clear="load" @keyup.enter="load" />
      <el-button @click="load"><el-icon><Search /></el-icon></el-button>
    </div>
    <el-table :data="items" v-loading="loading" stripe>
      <el-table-column prop="mac_address" label="MAC" width="150" />
      <el-table-column prop="ip_address" label="IP" width="130" />
      <el-table-column prop="username" label="用户" width="100" />
      <el-table-column prop="auth_method" label="方式" width="80" />
      <el-table-column label="结果" width="80">
        <template #default="{row}">
          <el-tag :type="{success:'success',failed:'danger',rejected:'warning'}[row.result]" size="small">
            {{ {success:'成功',failed:'失败',rejected:'拒绝'}[row.result] }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="failure_reason" label="失败原因" min-width="200" show-overflow-tooltip />
      <el-table-column prop="switch_ip" label="交换机" width="130" />
      <el-table-column prop="created_at" label="时间" width="170" />
    </el-table>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import request from '@/api/request'
const items = ref([]), loading = ref(false), filterResult = ref(null), filterMac = ref('')
async function load() {
  loading.value = true
  try {
    let url = '/nac/auth-logs?limit=100'
    if (filterResult.value) url += `&result=${filterResult.value}`
    if (filterMac.value) url += `&mac=${filterMac.value}`
    const r = await request.get(url)
    items.value = r.data?.items||[]
  } catch(e){}
  loading.value = false
}
onMounted(load)
</script>
