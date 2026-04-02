<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
      <h3>👤 访客管理</h3>
      <el-button type="primary" @click="showCreate=true"><el-icon><Plus /></el-icon> 创建访客账号</el-button>
    </div>
    <el-table :data="items" v-loading="loading" stripe>
      <el-table-column prop="visitor_name" label="访客姓名" width="120" />
      <el-table-column prop="visitor_company" label="单位" width="150" />
      <el-table-column prop="username" label="账号" width="140" />
      <el-table-column prop="sponsor_name" label="邀请人" width="100" />
      <el-table-column label="权限" width="100">
        <template #default="{row}">
          <el-tag size="small">{{ {internet_only:'仅互联网',limited:'受限',full:'完全'}[row.access_level] }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="valid_until" label="有效期至" width="170" />
      <el-table-column label="状态" width="80">
        <template #default="{row}">
          <el-tag :type="row.is_active?'success':'info'" size="small">{{ row.is_active?'有效':'过期' }}</el-tag>
        </template>
      </el-table-column>
    </el-table>
    <el-dialog title="创建访客账号" v-model="showCreate" width="450px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="姓名"><el-input v-model="form.visitor_name" /></el-form-item>
        <el-form-item label="单位"><el-input v-model="form.visitor_company" /></el-form-item>
        <el-form-item label="手机"><el-input v-model="form.visitor_phone" /></el-form-item>
        <el-form-item label="邀请人"><el-input v-model="form.sponsor_name" /></el-form-item>
        <el-form-item label="权限">
          <el-select v-model="form.access_level" style="width:100%">
            <el-option label="仅互联网" value="internet_only" />
            <el-option label="受限访问" value="limited" />
            <el-option label="完全访问" value="full" />
          </el-select>
        </el-form-item>
        <el-form-item label="时长(h)"><el-input-number v-model="form.duration_hours" :min="1" :max="720" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate=false">取消</el-button>
        <el-button type="primary" @click="create">创建</el-button>
      </template>
    </el-dialog>
    <el-dialog title="访客账号信息" v-model="showResult" width="400px">
      <el-descriptions :column="1" border v-if="createdAccount">
        <el-descriptions-item label="账号">{{ createdAccount.username }}</el-descriptions-item>
        <el-descriptions-item label="密码"><el-tag type="danger">{{ createdAccount.password }}</el-tag></el-descriptions-item>
        <el-descriptions-item label="有效期至">{{ createdAccount.valid_until }}</el-descriptions-item>
      </el-descriptions>
      <p style="color:#e6a23c;margin-top:12px;font-size:13px;">⚠️ 请将账号密码告知访客，密码仅显示一次</p>
    </el-dialog>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/api/request'
const items = ref([]), loading = ref(false), showCreate = ref(false), showResult = ref(false)
const form = ref({visitor_name:'',visitor_company:'',visitor_phone:'',sponsor_name:'',access_level:'internet_only',duration_hours:24})
const createdAccount = ref(null)
async function load() {
  loading.value = true
  try { const r = await request.get('/nac/visitors'); items.value = r.data?.items||[] } catch(e){}
  loading.value = false
}
async function create() {
  if(!form.value.visitor_name){ElMessage.warning('请输入姓名');return}
  try {
    const r = await request.post('/nac/visitors', form.value)
    createdAccount.value = r.data
    showCreate.value = false; showResult.value = true; load()
  } catch(e) { ElMessage.error('创建失败') }
}
onMounted(load)
</script>
