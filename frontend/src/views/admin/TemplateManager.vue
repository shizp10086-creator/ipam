<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
      <h3>📄 模板库</h3>
      <el-button type="primary" @click="showCreate=true"><el-icon><Plus /></el-icon> 新建模板</el-button>
    </div>
    <el-tabs v-model="activeTab">
      <el-tab-pane label="表单模板" name="form" />
      <el-tab-pane label="报表模板" name="report" />
      <el-tab-pane label="仪表盘模板" name="dashboard" />
      <el-tab-pane label="大屏模板" name="screen" />
      <el-tab-pane label="PPT 模板" name="ppt" />
    </el-tabs>
    <el-table :data="filtered" v-loading="loading" stripe>
      <el-table-column prop="name" label="模板名称" min-width="200" />
      <el-table-column label="类型" width="100">
        <template #default="{row}"><el-tag size="small">{{ typeMap[row.config_type]||row.config_type }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="version" label="版本" width="80" />
      <el-table-column label="状态" width="80">
        <template #default="{row}"><el-tag :type="row.status==='published'?'success':'info'" size="small">{{ row.status==='published'?'已发布':'草稿' }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="170" />
      <el-table-column label="操作" width="120">
        <template #default="{row}">
          <el-button link size="small" @click="preview(row)">预览</el-button>
          <el-popconfirm title="确定删除？" @confirm="remove(row.id)">
            <template #reference><el-button link size="small" type="danger">删除</el-button></template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>
    <el-dialog title="新建模板" v-model="showCreate" width="480px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="类型">
          <el-select v-model="form.config_type" style="width:100%">
            <el-option label="表单" value="form" /><el-option label="报表" value="report" />
            <el-option label="仪表盘" value="dashboard" /><el-option label="大屏" value="screen" />
            <el-option label="PPT" value="ppt" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="showCreate=false">取消</el-button><el-button type="primary" @click="create">创建</el-button></template>
    </el-dialog>
  </div>
</template>
<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/api/request'
const items=ref([]),loading=ref(false),showCreate=ref(false),activeTab=ref('form')
const form=ref({name:'',config_type:'form',description:''})
const typeMap={form:'表单',report:'报表',dashboard:'仪表盘',screen:'大屏',ppt:'PPT'}
const filtered=computed(()=>items.value.filter(i=>i.config_type===activeTab.value))
async function load(){loading.value=true;try{const r=await request.get('/designer/configs?limit=200');items.value=r.data?.items||[]}catch(e){}loading.value=false}
async function create(){if(!form.value.name){ElMessage.warning('请输入名称');return};try{await request.post('/designer/configs',{...form.value,config_data:{},status:'draft'});ElMessage.success('创建成功');showCreate.value=false;load()}catch(e){}}
async function remove(id){try{await request.delete(`/designer/configs/${id}`);ElMessage.success('已删除');load()}catch(e){}}
function preview(row){ElMessage.info(`预览模板: ${row.name}`)}
onMounted(load)
</script>
