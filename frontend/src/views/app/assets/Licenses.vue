<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
      <h3>📜 软件许可证</h3>
      <el-button type="primary" @click="showCreate=true"><el-icon><Plus /></el-icon> 添加许可证</el-button>
    </div>
    <el-table :data="items" v-loading="loading" stripe>
      <el-table-column prop="software_name" label="软件名称" min-width="160" />
      <el-table-column prop="version" label="版本" width="80" />
      <el-table-column label="类型" width="80"><template #default="{row}"><el-tag size="small">{{ {perpetual:'永久',subscription:'订阅',oem:'OEM'}[row.license_type]||row.license_type }}</el-tag></template></el-table-column>
      <el-table-column label="使用量" width="120"><template #default="{row}">{{ row.used_count||0 }}/{{ row.total_count }}</template></el-table-column>
      <el-table-column prop="vendor" label="供应商" width="120" />
      <el-table-column prop="expire_date" label="到期日" width="110" />
      <el-table-column prop="cost" label="费用" width="100" />
    </el-table>
    <el-dialog title="添加软件许可证" v-model="showCreate" width="480px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="软件名称"><el-input v-model="form.software_name" /></el-form-item>
        <el-form-item label="版本"><el-input v-model="form.version" /></el-form-item>
        <el-form-item label="类型"><el-select v-model="form.license_type" style="width:100%"><el-option label="永久" value="perpetual" /><el-option label="订阅" value="subscription" /><el-option label="OEM" value="oem" /></el-select></el-form-item>
        <el-form-item label="数量"><el-input-number v-model="form.total_count" :min="1" style="width:100%" /></el-form-item>
        <el-form-item label="供应商"><el-input v-model="form.vendor" /></el-form-item>
        <el-form-item label="到期日"><el-date-picker v-model="form.expire_date" type="date" style="width:100%" value-format="YYYY-MM-DD" /></el-form-item>
        <el-form-item label="费用"><el-input-number v-model="form.cost" :min="0" style="width:100%" /></el-form-item>
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
const form=ref({software_name:'',version:'',license_type:'perpetual',total_count:1,vendor:'',expire_date:'',cost:null})
async function load(){loading.value=true;try{const r=await request.get('/assets/licenses');items.value=r.data?.items||[]}catch(e){}loading.value=false}
async function create(){if(!form.value.software_name){ElMessage.warning('请输入软件名称');return};try{await request.post('/assets/licenses',form.value);ElMessage.success('添加成功');showCreate.value=false;load()}catch(e){ElMessage.error('添加失败')}}
onMounted(load)
</script>
