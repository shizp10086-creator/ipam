<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
      <h3>📋 MAC 白名单（哑终端认证）</h3>
      <el-button type="primary" @click="showCreate=true"><el-icon><Plus /></el-icon> 添加 MAC</el-button>
    </div>
    <el-table :data="items" v-loading="loading" stripe>
      <el-table-column prop="mac_address" label="MAC 地址" width="160" />
      <el-table-column prop="device_name" label="设备名称" width="160" />
      <el-table-column label="设备类型" width="100">
        <template #default="{row}"><el-tag size="small">{{ {printer:'打印机',camera:'摄像头',phone:'IP电话',iot:'IoT',other:'其他'}[row.device_type]||row.device_type }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="location" label="安装位置" min-width="200" />
      <el-table-column prop="vlan_id" label="VLAN" width="70" />
      <el-table-column prop="acl_name" label="ACL" width="100" />
    </el-table>
    <el-dialog title="添加 MAC 白名单" v-model="showCreate" width="480px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="MAC" required><el-input v-model="form.mac_address" placeholder="AA:BB:CC:DD:EE:FF" /></el-form-item>
        <el-form-item label="设备名称"><el-input v-model="form.device_name" /></el-form-item>
        <el-form-item label="设备类型">
          <el-select v-model="form.device_type" style="width:100%">
            <el-option label="打印机" value="printer" /><el-option label="摄像头" value="camera" />
            <el-option label="IP 电话" value="phone" /><el-option label="IoT" value="iot" /><el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="位置"><el-input v-model="form.location" placeholder="安装位置" /></el-form-item>
        <el-form-item label="VLAN"><el-input-number v-model="form.vlan_id" :min="1" :max="4094" style="width:100%;" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate=false">取消</el-button>
        <el-button type="primary" @click="create">添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/api/request'
const items=ref([]),loading=ref(false),showCreate=ref(false)
const form=ref({mac_address:'',device_name:'',device_type:'other',location:'',vlan_id:null})
async function load(){
  loading.value=true
  try{const r=await request.get('/nac/radius/mac-auth');items.value=r.data?.items||[]}catch(e){}
  loading.value=false
}
async function create(){
  if(!form.value.mac_address){ElMessage.warning('请输入 MAC 地址');return}
  try{
    await request.post('/nac/radius/mac-auth',form.value)
    ElMessage.success('MAC 已添加');showCreate.value=false;load()
  }catch(e){ElMessage.error(e.response?.data?.message||'添加失败')}
}
onMounted(load)
</script>
