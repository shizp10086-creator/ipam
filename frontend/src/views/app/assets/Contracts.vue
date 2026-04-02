<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
      <h3>📄 合同管理</h3>
      <el-button type="primary" @click="showCreate=true"><el-icon><Plus /></el-icon> 添加合同</el-button>
    </div>
    <el-table :data="items" v-loading="loading" stripe>
      <el-table-column prop="contract_no" label="合同编号" width="140" />
      <el-table-column label="类型" width="80"><template #default="{row}"><el-tag size="small">{{ {purchase:'采购',maintenance:'维保',lease:'租赁',subscription:'订阅'}[row.contract_type]||row.contract_type }}</el-tag></template></el-table-column>
      <el-table-column prop="vendor" label="供应商" width="140" />
      <el-table-column prop="amount" label="金额" width="100" />
      <el-table-column prop="start_date" label="开始日期" width="110" />
      <el-table-column prop="end_date" label="到期日期" width="110" />
      <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
    </el-table>
    <el-dialog title="添加合同" v-model="showCreate" width="480px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="合同编号"><el-input v-model="form.contract_no" /></el-form-item>
        <el-form-item label="类型"><el-select v-model="form.contract_type" style="width:100%"><el-option label="采购" value="purchase" /><el-option label="维保" value="maintenance" /><el-option label="租赁" value="lease" /><el-option label="订阅" value="subscription" /></el-select></el-form-item>
        <el-form-item label="供应商"><el-input v-model="form.vendor" /></el-form-item>
        <el-form-item label="金额"><el-input-number v-model="form.amount" :min="0" style="width:100%" /></el-form-item>
        <el-form-item label="开始日期"><el-date-picker v-model="form.start_date" type="date" style="width:100%" value-format="YYYY-MM-DD" /></el-form-item>
        <el-form-item label="到期日期"><el-date-picker v-model="form.end_date" type="date" style="width:100%" value-format="YYYY-MM-DD" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" /></el-form-item>
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
const form=ref({contract_no:'',contract_type:'purchase',vendor:'',amount:null,start_date:'',end_date:'',description:''})
async function load(){loading.value=true;try{const r=await request.get('/assets/contracts');items.value=r.data?.items||[]}catch(e){}loading.value=false}
async function create(){if(!form.value.contract_no){ElMessage.warning('请输入合同编号');return};try{await request.post('/assets/contracts',form.value);ElMessage.success('添加成功');showCreate.value=false;load()}catch(e){ElMessage.error('添加失败')}}
onMounted(load)
</script>
