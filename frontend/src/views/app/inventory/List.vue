<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
      <h3>📋 资产盘点</h3>
      <el-button type="primary" @click="showCreate=true"><el-icon><Plus /></el-icon> 发起盘点</el-button>
    </div>
    <div style="margin-bottom:16px;display:flex;gap:16px;">
      <el-card style="flex:1;text-align:center;"><div style="font-size:24px;font-weight:bold;color:#409eff;">{{ stats.total }}</div><div style="color:#909399;font-size:13px;">资产总数</div></el-card>
      <el-card style="flex:1;text-align:center;"><div style="font-size:24px;font-weight:bold;color:#67c23a;">{{ stats.in_use }}</div><div style="color:#909399;font-size:13px;">在用</div></el-card>
      <el-card style="flex:1;text-align:center;"><div style="font-size:24px;font-weight:bold;color:#e6a23c;">{{ stats.idle }}</div><div style="color:#909399;font-size:13px;">闲置</div></el-card>
      <el-card style="flex:1;text-align:center;"><div style="font-size:24px;font-weight:bold;color:#f56c6c;">{{ stats.retired }}</div><div style="color:#909399;font-size:13px;">报废</div></el-card>
    </div>
    <el-tabs v-model="activeTab">
      <el-tab-pane label="盘点任务" name="tasks">
        <el-table :data="tasks" v-loading="loading" stripe>
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="name" label="盘点名称" min-width="200" />
          <el-table-column label="类型" width="100"><template #default="{row}"><el-tag size="small">{{ row.type==='full'?'全面盘点':'抽样盘点' }}</el-tag></template></el-table-column>
          <el-table-column label="状态" width="80"><template #default="{row}"><el-tag :type="{pending:'warning',in_progress:'',completed:'success'}[row.status]" size="small">{{ {pending:'待执行',in_progress:'进行中',completed:'已完成'}[row.status] }}</el-tag></template></el-table-column>
          <el-table-column prop="progress" label="进度" width="100"><template #default="{row}"><el-progress :percentage="row.progress||0" :stroke-width="6" /></template></el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="170" />
        </el-table>
      </el-tab-pane>
      <el-tab-pane label="流转记录" name="transfers">
        <el-table :data="transfers" v-loading="loadingTransfers" stripe>
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="username" label="操作人" width="100" />
          <el-table-column prop="operation_type" label="操作类型" width="100" />
          <el-table-column prop="resource_type" label="资源类型" width="100" />
          <el-table-column prop="details" label="详情" min-width="300" />
          <el-table-column prop="created_at" label="时间" width="170" />
        </el-table>
      </el-tab-pane>
    </el-tabs>
    <el-dialog title="发起盘点" v-model="showCreate" width="450px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称"><el-input v-model="form.name" placeholder="如：2026年Q2全面盘点" /></el-form-item>
        <el-form-item label="类型"><el-radio-group v-model="form.type"><el-radio label="full">全面盘点</el-radio><el-radio label="sample">抽样盘点</el-radio></el-radio-group></el-form-item>
        <el-form-item label="说明"><el-input v-model="form.description" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="showCreate=false">取消</el-button><el-button type="primary" @click="create">发起</el-button></template>
    </el-dialog>
  </div>
</template>
<script setup>
import { ref, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/api/request'
const tasks=ref([]),transfers=ref([]),loading=ref(false),loadingTransfers=ref(false),showCreate=ref(false)
const stats=ref({total:0,in_use:0,idle:0,retired:0}),activeTab=ref('tasks')
const form=ref({name:'',type:'full',description:''})
async function loadStats(){try{const r=await request.get('/asset/lifecycle/stats');Object.assign(stats.value,r.data||{})}catch(e){}}
async function loadTransfers(){loadingTransfers.value=true;try{const r=await request.get('/asset/lifecycle/transfers');transfers.value=r.data?.items||[]}catch(e){}loadingTransfers.value=false}
async function create(){if(!form.value.name){ElMessage.warning('请输入盘点名称');return};tasks.value.unshift({id:tasks.value.length+1,name:form.value.name,type:form.value.type,status:'pending',progress:0,created_at:new Date().toISOString().slice(0,19).replace('T',' ')});ElMessage.success('盘点任务已创建');showCreate.value=false}
watch(activeTab,(v)=>{if(v==='transfers'&&transfers.value.length===0)loadTransfers()})
onMounted(()=>{loadStats()})
</script>
