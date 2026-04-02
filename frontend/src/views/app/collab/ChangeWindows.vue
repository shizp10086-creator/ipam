<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
      <h3>🔄 变更窗口管理</h3>
      <el-button type="primary" @click="showCreate=true"><el-icon><Plus /></el-icon> 创建变更窗口</el-button>
    </div>
    <el-alert type="info" :closable="false" style="margin-bottom:12px;">高风险操作（删除网段、批量配置下发）必须在审批通过的变更窗口内执行</el-alert>
    <el-table :data="items" v-loading="loading" stripe>
      <el-table-column prop="title" label="变更标题" min-width="200" />
      <el-table-column prop="start_time" label="开始时间" width="170" />
      <el-table-column prop="end_time" label="结束时间" width="170" />
      <el-table-column prop="owner" label="负责人" width="100" />
      <el-table-column label="状态" width="80"><template #default="{row}"><el-tag :type="{scheduled:'',in_progress:'warning',completed:'success',cancelled:'info'}[row.status]" size="small">{{ {scheduled:'计划中',in_progress:'执行中',completed:'已完成',cancelled:'已取消'}[row.status]||row.status }}</el-tag></template></el-table-column>
    </el-table>
    <el-dialog title="创建变更窗口" v-model="showCreate" width="480px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="标题"><el-input v-model="form.title" /></el-form-item>
        <el-form-item label="开始时间"><el-date-picker v-model="form.start_time" type="datetime" style="width:100%" value-format="YYYY-MM-DD HH:mm:ss" /></el-form-item>
        <el-form-item label="结束时间"><el-date-picker v-model="form.end_time" type="datetime" style="width:100%" value-format="YYYY-MM-DD HH:mm:ss" /></el-form-item>
        <el-form-item label="负责人"><el-input v-model="form.owner" /></el-form-item>
        <el-form-item label="范围"><el-input v-model="form.scope" placeholder="影响范围" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="showCreate=false">取消</el-button><el-button type="primary" @click="create">创建</el-button></template>
    </el-dialog>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/api/request'
const items=ref([]),loading=ref(false),showCreate=ref(false)
const form=ref({title:'',start_time:'',end_time:'',owner:'',scope:'',description:''})
async function load(){loading.value=true;try{const r=await request.get('/collab/change-windows');items.value=r.data?.items||[]}catch(e){}loading.value=false}
async function create(){if(!form.value.title){ElMessage.warning('请输入标题');return};try{await request.post('/collab/change-windows',form.value);ElMessage.success('创建成功');showCreate.value=false;load()}catch(e){ElMessage.error('创建失败')}}
onMounted(load)
</script>
