<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
      <h3>🔗 第三方系统集成</h3>
      <el-button type="primary" @click="showCreate=true"><el-icon><Plus /></el-icon> 添加集成</el-button>
    </div>
    <el-row :gutter="16">
      <el-col :span="6" v-for="tmpl in templates" :key="tmpl.type">
        <el-card shadow="hover" class="tmpl-card" @click="useTemplate(tmpl)">
          <div style="text-align:center;"><span style="font-size:28px;">{{ tmpl.icon }}</span><div style="font-weight:600;margin-top:8px;">{{ tmpl.name }}</div><div style="font-size:11px;color:#909399;">{{ tmpl.desc }}</div></div>
        </el-card>
      </el-col>
    </el-row>
    <h4 style="margin:20px 0 12px;">已配置的集成</h4>
    <el-table :data="items" v-loading="loading" stripe>
      <el-table-column prop="name" label="名称" width="160" />
      <el-table-column prop="system_type" label="类型" width="100" />
      <el-table-column prop="api_url" label="API 地址" min-width="250" show-overflow-tooltip />
      <el-table-column label="状态" width="80"><template #default="{row}"><el-tag :type="row.is_active?'success':'info'" size="small">{{ row.is_active?'启用':'禁用' }}</el-tag></template></el-table-column>
      <el-table-column label="操作" width="120">
        <template #default="{row}"><el-button link size="small" @click="testConn(row.id)">测试</el-button><el-button link size="small" type="primary" @click="syncNow(row.id)">同步</el-button></template>
      </el-table-column>
    </el-table>
    <el-dialog title="添加第三方集成" v-model="showCreate" width="500px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="系统类型"><el-select v-model="form.system_type" style="width:100%"><el-option label="CMDB" value="cmdb" /><el-option label="Zabbix" value="zabbix" /><el-option label="Prometheus" value="prometheus" /><el-option label="OCS" value="ocs" /><el-option label="EDR" value="edr" /><el-option label="堡垒机" value="jumpserver" /><el-option label="其他" value="other" /></el-select></el-form-item>
        <el-form-item label="API 地址"><el-input v-model="form.api_url" placeholder="https://..." /></el-form-item>
        <el-form-item label="认证方式"><el-select v-model="form.auth_type" style="width:100%"><el-option label="API Key" value="api_key" /><el-option label="OAuth 2.0" value="oauth" /><el-option label="Basic Auth" value="basic" /></el-select></el-form-item>
        <el-form-item label="同步周期(分)"><el-input-number v-model="form.sync_interval_minutes" :min="5" style="width:100%" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="showCreate=false">取消</el-button><el-button type="primary" @click="create">添加</el-button></template>
    </el-dialog>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/api/request'
const items=ref([]),loading=ref(false),showCreate=ref(false)
const form=ref({name:'',system_type:'cmdb',api_url:'',auth_type:'api_key',sync_interval_minutes:60})
const templates=[
  {type:'cmdb',name:'CMDB',icon:'📦',desc:'蓝鲸/优维 CMDB'},
  {type:'zabbix',name:'Zabbix',icon:'📊',desc:'Zabbix 监控'},
  {type:'prometheus',name:'Prometheus',icon:'🔥',desc:'Prometheus 监控'},
  {type:'ocs',name:'OCS',icon:'💻',desc:'OCS 资产管理'},
  {type:'edr',name:'EDR',icon:'🛡️',desc:'深信服/奇安信 EDR'},
  {type:'jumpserver',name:'堡垒机',icon:'🏰',desc:'JumpServer'},
]
async function load(){loading.value=true;try{const r=await request.get('/auth/integrations');items.value=r.data?.items||[]}catch(e){}loading.value=false}
async function create(){if(!form.value.name||!form.value.api_url){ElMessage.warning('请填写完整');return};try{await request.post('/auth/integrations',form.value);ElMessage.success('添加成功');showCreate.value=false;load()}catch(e){ElMessage.error('添加失败')}}
function useTemplate(t){form.value.system_type=t.type;form.value.name=t.name;showCreate.value=true}
async function testConn(id){try{await request.post(`/auth/integrations/${id}/test`);ElMessage.success('连接测试成功')}catch(e){ElMessage.error('连接失败')}}
async function syncNow(id){try{await request.post(`/auth/integrations/${id}/sync`);ElMessage.success('同步已加入队列')}catch(e){}}
onMounted(load)
</script>
<style scoped>.tmpl-card{cursor:pointer;margin-bottom:12px;transition:transform 0.2s;}.tmpl-card:hover{transform:translateY(-4px);}</style>
