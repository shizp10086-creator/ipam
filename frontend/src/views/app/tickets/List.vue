<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
      <h3>📋 工单协作</h3>
      <el-button type="primary" @click="showCreate=true"><el-icon><Plus /></el-icon> 新建工单</el-button>
    </div>
    <div style="margin-bottom:12px;display:flex;gap:8px;">
      <el-select v-model="filterStatus" placeholder="状态" clearable style="width:120px;" @change="load">
        <el-option label="待审批" value="pending" /><el-option label="处理中" value="in_progress" />
        <el-option label="已通过" value="approved" /><el-option label="已驳回" value="rejected" />
      </el-select>
      <el-select v-model="filterType" placeholder="类型" clearable style="width:140px;" @change="load">
        <el-option label="IP申请" value="ip_apply" /><el-option label="设备上线" value="device_onboard" />
        <el-option label="权限申请" value="permission_apply" /><el-option label="变更请求" value="change_request" />
        <el-option label="故障报修" value="incident" />
      </el-select>
    </div>
    <el-table :data="items" v-loading="loading" stripe>
      <el-table-column prop="ticket_no" label="工单号" width="180" />
      <el-table-column prop="title" label="标题" min-width="200" />
      <el-table-column label="类型" width="100">
        <template #default="{row}"><el-tag size="small">{{ typeMap[row.ticket_type]||row.ticket_type }}</el-tag></template>
      </el-table-column>
      <el-table-column label="优先级" width="80">
        <template #default="{row}">
          <el-tag :type="{urgent:'danger',high:'warning',medium:'',low:'info'}[row.priority]" size="small">
            {{ {urgent:'紧急',high:'高',medium:'中',low:'低'}[row.priority] }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="80">
        <template #default="{row}">
          <el-tag :type="{pending:'warning',in_progress:'',approved:'success',rejected:'danger',completed:'success'}[row.status]" size="small">
            {{ statusMap[row.status] }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="applicant_name" label="申请人" width="80" />
      <el-table-column prop="created_at" label="创建时间" width="170" />
      <el-table-column label="操作" width="120">
        <template #default="{row}">
          <el-button v-if="row.status==='pending'" link size="small" type="success" @click="approve(row.id)">通过</el-button>
          <el-button v-if="row.status==='pending'" link size="small" type="danger" @click="reject(row.id)">驳回</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-dialog title="新建工单" v-model="showCreate" width="500px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="标题"><el-input v-model="form.title" /></el-form-item>
        <el-form-item label="类型">
          <el-select v-model="form.ticket_type" style="width:100%">
            <el-option label="IP 申请" value="ip_apply" /><el-option label="设备上线" value="device_onboard" />
            <el-option label="权限申请" value="permission_apply" /><el-option label="变更请求" value="change_request" />
            <el-option label="故障报修" value="incident" /><el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级">
          <el-radio-group v-model="form.priority">
            <el-radio label="low">低</el-radio><el-radio label="medium">中</el-radio>
            <el-radio label="high">高</el-radio><el-radio label="urgent">紧急</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" :rows="3" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate=false">取消</el-button>
        <el-button type="primary" @click="create">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/api/request'
const items=ref([]),loading=ref(false),showCreate=ref(false),filterStatus=ref(null),filterType=ref(null)
const form=ref({title:'',ticket_type:'ip_apply',priority:'medium',description:''})
const typeMap={ip_apply:'IP申请',device_onboard:'设备上线',permission_apply:'权限申请',change_request:'变更请求',incident:'故障报修',other:'其他'}
const statusMap={draft:'草稿',pending:'待审批',in_progress:'处理中',approved:'已通过',rejected:'已驳回',completed:'已完成',cancelled:'已取消'}
async function load(){
  loading.value=true
  try{
    let url='/tickets/tickets?limit=50'
    if(filterStatus.value)url+=`&status=${filterStatus.value}`
    if(filterType.value)url+=`&ticket_type=${filterType.value}`
    const r=await request.get(url);items.value=r.data?.items||[]
  }catch(e){}
  loading.value=false
}
async function create(){
  if(!form.value.title){ElMessage.warning('请输入标题');return}
  try{await request.post('/tickets/tickets',form.value);ElMessage.success('工单创建成功');showCreate.value=false;load()}catch(e){ElMessage.error('创建失败')}
}
async function approve(id){try{await request.put(`/tickets/tickets/${id}/approve`);ElMessage.success('已通过');load()}catch(e){}}
async function reject(id){try{await request.put(`/tickets/tickets/${id}/reject`);ElMessage.success('已驳回');load()}catch(e){}}
onMounted(load)
</script>
