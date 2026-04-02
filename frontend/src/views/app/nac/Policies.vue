<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
      <h3>🔐 认证策略</h3>
      <el-button type="primary" @click="showCreate=true"><el-icon><Plus /></el-icon> 新建策略</el-button>
    </div>
    <el-table :data="items" v-loading="loading" stripe>
      <el-table-column prop="name" label="策略名称" min-width="160" />
      <el-table-column prop="priority" label="优先级" width="80" sortable />
      <el-table-column label="认证方式" width="120">
        <template #default="{row}">
          <el-tag size="small">{{ row.auth_method }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="80">
        <template #default="{row}">
          <el-tag :type="row.is_active?'success':'info'" size="small">{{ row.is_active?'启用':'禁用' }}</el-tag>
        </template>
      </el-table-column>
    </el-table>
    <el-dialog title="新建认证策略" v-model="showCreate" width="500px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="策略名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="优先级"><el-input-number v-model="form.priority" :min="1" /></el-form-item>
        <el-form-item label="认证方式">
          <el-select v-model="form.auth_method" style="width:100%">
            <el-option label="802.1X" value="802.1x" /><el-option label="Portal" value="portal" />
            <el-option label="MAC" value="mac" /><el-option label="PPSK" value="ppsk" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate=false">取消</el-button>
        <el-button type="primary" @click="create">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/api/request'
const items = ref([]), loading = ref(false), showCreate = ref(false)
const form = ref({name:'',priority:100,auth_method:'802.1x',conditions:{},actions:{}})
async function load() {
  loading.value = true
  try { const r = await request.get('/nac/policies'); items.value = r.data?.items||[] } catch(e){}
  loading.value = false
}
async function create() {
  try {
    await request.post('/nac/policies', form.value)
    ElMessage.success('创建成功'); showCreate.value=false; load()
  } catch(e) { ElMessage.error('创建失败') }
}
onMounted(load)
</script>
