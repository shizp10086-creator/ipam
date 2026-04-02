<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
      <h3>⚡ 自动化工作流</h3>
      <el-button type="primary" @click="showCreate=true"><el-icon><Plus /></el-icon> 新建工作流</el-button>
    </div>
    <el-table :data="items" v-loading="loading" stripe>
      <el-table-column prop="name" label="工作流名称" min-width="200" />
      <el-table-column label="触发器" width="120">
        <template #default="{row}"><el-tag size="small">{{ triggerMap[row.trigger_type]||row.trigger_type }}</el-tag></template>
      </el-table-column>
      <el-table-column label="状态" width="80">
        <template #default="{row}">
          <el-switch :model-value="row.enabled" size="small" @change="toggle(row)" />
        </template>
      </el-table-column>
      <el-table-column prop="last_run_at" label="上次执行" width="170" />
      <el-table-column prop="run_count" label="执行次数" width="90" />
      <el-table-column prop="created_at" label="创建时间" width="170" />
      <el-table-column label="操作" width="140">
        <template #default="{row}">
          <el-button link size="small" @click="run(row.id)">手动执行</el-button>
          <el-popconfirm title="确定删除？" @confirm="remove(row.id)">
            <template #reference><el-button link size="small" type="danger">删除</el-button></template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>
    <el-dialog title="新建自动化工作流" v-model="showCreate" width="520px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="触发器">
          <el-select v-model="form.trigger_type" style="width:100%">
            <el-option label="数据变更" value="data_change" /><el-option label="定时触发" value="cron" />
            <el-option label="Webhook" value="webhook" /><el-option label="告警触发" value="alert" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" :rows="2" /></el-form-item>
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
const form=ref({name:'',trigger_type:'data_change',description:''})
const triggerMap={data_change:'数据变更',cron:'定时',webhook:'Webhook',alert:'告警'}
async function load(){loading.value=true;try{const r=await request.get('/designer/automation?limit=100');items.value=r.data?.items||[]}catch(e){}loading.value=false}
async function create(){if(!form.value.name){ElMessage.warning('请输入名称');return};try{await request.post('/designer/automation',{...form.value,actions:[],enabled:true});ElMessage.success('创建成功');showCreate.value=false;load()}catch(e){}}
async function toggle(row){try{await request.put(`/designer/automation/${row.id}`,{enabled:!row.enabled});ElMessage.success(row.enabled?'已禁用':'已启用');load()}catch(e){}}
async function run(id){try{await request.post(`/designer/automation/${id}/run`);ElMessage.success('已触发执行')}catch(e){}}
async function remove(id){try{await request.delete(`/designer/automation/${id}`);ElMessage.success('已删除');load()}catch(e){}}
onMounted(load)
</script>
