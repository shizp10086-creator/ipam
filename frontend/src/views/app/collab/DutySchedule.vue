<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
      <h3>📅 值班排班</h3>
      <el-button type="primary" @click="showCreate=true"><el-icon><Plus /></el-icon> 新建排班</el-button>
    </div>
    <el-table :data="items" v-loading="loading" stripe>
      <el-table-column prop="date" label="日期" width="120" />
      <el-table-column label="班次" width="80"><template #default="{row}"><el-tag size="small">{{ {day:'白班',night:'夜班',all_day:'全天'}[row.shift] }}</el-tag></template></el-table-column>
      <el-table-column prop="primary" label="主值班" width="100" />
      <el-table-column prop="backup" label="备班" width="100" />
      <el-table-column label="确认" width="70"><template #default="{row}"><el-tag :type="row.confirmed?'success':'warning'" size="small">{{ row.confirmed?'已确认':'待确认' }}</el-tag></template></el-table-column>
    </el-table>
    <el-dialog title="新建排班" v-model="showCreate" width="400px">
      <el-form label-width="60px">
        <el-form-item label="日期"><el-date-picker v-model="newDate" type="date" style="width:100%;" /></el-form-item>
        <el-form-item label="主值班"><el-input v-model="newPrimary" /></el-form-item>
        <el-form-item label="备班"><el-input v-model="newBackup" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="showCreate=false">取消</el-button><el-button type="primary" @click="create">创建</el-button></template>
    </el-dialog>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/api/request'
const items=ref([]),loading=ref(false),showCreate=ref(false),newDate=ref(''),newPrimary=ref(''),newBackup=ref('')
async function load(){loading.value=true;try{const r=await request.get('/collab/duty');items.value=r.data?.items||[]}catch(e){}loading.value=false}
async function create(){if(!newDate.value||!newPrimary.value){ElMessage.warning('请填写日期和值班人');return};try{const d=new Date(newDate.value).toISOString().split('T')[0];await request.post(`/collab/duty?date=${d}&primary_name=${newPrimary.value}&backup_name=${newBackup.value}`);ElMessage.success('创建成功');showCreate.value=false;load()}catch(e){ElMessage.error('创建失败')}}
onMounted(load)
</script>
