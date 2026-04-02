<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
      <h3>🔑 RADIUS 用户管理</h3>
      <el-button type="primary" @click="showCreate=true"><el-icon><Plus /></el-icon> 新建用户</el-button>
    </div>
    <div style="margin-bottom:12px;display:flex;gap:8px;">
      <el-select v-model="filterType" placeholder="用户类型" clearable style="width:130px;" @change="load">
        <el-option label="员工" value="employee" /><el-option label="访客" value="visitor" /><el-option label="设备" value="device" />
      </el-select>
      <el-input v-model="search" placeholder="搜索用户名/姓名" clearable style="width:200px;" @keyup.enter="load" @clear="load" />
      <el-button @click="load"><el-icon><Search /></el-icon></el-button>
    </div>
    <el-table :data="items" v-loading="loading" stripe>
      <el-table-column prop="username" label="用户名" width="140" />
      <el-table-column prop="real_name" label="姓名" width="100" />
      <el-table-column label="类型" width="80">
        <template #default="{row}"><el-tag size="small">{{ {employee:'员工',visitor:'访客',device:'设备'}[row.user_type]||row.user_type }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="department" label="部门" width="120" />
      <el-table-column prop="vlan_id" label="VLAN" width="70" />
      <el-table-column prop="acl_name" label="ACL" width="100" />
      <el-table-column label="带宽" width="120">
        <template #default="{row}">
          <span v-if="row.bandwidth_up">↑{{ row.bandwidth_up }}K ↓{{ row.bandwidth_down }}K</span>
          <span v-else style="color:#909399;">不限</span>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="70">
        <template #default="{row}"><el-tag :type="row.is_active?'success':'info'" size="small">{{ row.is_active?'启用':'禁用' }}</el-tag></template>
      </el-table-column>
      <el-table-column label="操作" width="80">
        <template #default="{row}">
          <el-popconfirm title="确定禁用？" @confirm="disable(row.username)">
            <template #reference><el-button link size="small" type="danger">禁用</el-button></template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>
    <el-dialog title="新建 RADIUS 用户" v-model="showCreate" width="520px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="用户名" required><el-input v-model="form.username" placeholder="802.1X 认证账号" /></el-form-item>
        <el-form-item label="密码" required><el-input v-model="form.password" type="password" show-password placeholder="认证密码" /></el-form-item>
        <el-form-item label="类型">
          <el-radio-group v-model="form.user_type">
            <el-radio label="employee">员工</el-radio><el-radio label="visitor">访客</el-radio><el-radio label="device">设备</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="姓名"><el-input v-model="form.real_name" /></el-form-item>
        <el-form-item label="部门"><el-input v-model="form.department" /></el-form-item>
        <el-form-item label="VLAN"><el-input-number v-model="form.vlan_id" :min="1" :max="4094" placeholder="认证通过后分配的 VLAN" style="width:100%;" /></el-form-item>
        <el-form-item label="ACL"><el-input v-model="form.acl_name" placeholder="下发的 ACL 名称（可选）" /></el-form-item>
        <el-row :gutter="12">
          <el-col :span="12"><el-form-item label="上行(K)"><el-input-number v-model="form.bandwidth_up" :min="0" style="width:100%;" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="下行(K)"><el-input-number v-model="form.bandwidth_down" :min="0" style="width:100%;" /></el-form-item></el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="showCreate=false">取消</el-button>
        <el-button type="primary" @click="create" :loading="saving">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/api/request'
const items=ref([]),loading=ref(false),showCreate=ref(false),saving=ref(false)
const filterType=ref(null),search=ref('')
const form=ref({username:'',password:'',user_type:'employee',real_name:'',department:'',vlan_id:null,acl_name:'',bandwidth_up:null,bandwidth_down:null})
async function load(){
  loading.value=true
  try{
    let url='/nac/radius/users?is_active=true'
    if(filterType.value)url+=`&user_type=${filterType.value}`
    if(search.value)url+=`&search=${search.value}`
    const r=await request.get(url);items.value=r.data?.items||[]
  }catch(e){}
  loading.value=false
}
async function create(){
  if(!form.value.username||!form.value.password){ElMessage.warning('请填写用户名和密码');return}
  saving.value=true
  try{
    await request.post('/nac/radius/users',form.value)
    ElMessage.success('RADIUS 用户创建成功');showCreate.value=false;load()
    form.value={username:'',password:'',user_type:'employee',real_name:'',department:'',vlan_id:null,acl_name:'',bandwidth_up:null,bandwidth_down:null}
  }catch(e){ElMessage.error(e.response?.data?.message||'创建失败')}
  saving.value=false
}
async function disable(username){
  try{await request.delete(`/nac/radius/users/${username}`);ElMessage.success('已禁用');load()}catch(e){}
}
onMounted(load)
</script>
