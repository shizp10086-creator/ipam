<template>
  <div>
    <h3 style="margin-bottom:16px;">🏢 租户管理</h3>
    <div style="display:flex;gap:12px;margin-bottom:16px;align-items:center;">
      <el-input v-model="searchKey" placeholder="搜索租户名称/编码" clearable style="width:260px;" @keyup.enter="load" />
      <el-select v-model="statusFilter" placeholder="状态" clearable style="width:120px;" @change="load">
        <el-option label="启用" value="active" /><el-option label="禁用" value="disabled" />
      </el-select>
      <el-button type="primary" @click="load">查询</el-button>
      <el-button type="primary" @click="openCreate">新建租户</el-button>
    </div>
    <el-table :data="list" v-loading="loading" stripe border>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="name" label="租户名称" min-width="140" />
      <el-table-column prop="code" label="编码" width="140" />
      <el-table-column label="状态" width="90">
        <template #default="{row}">
          <el-tag :type="row.status==='active'?'success':'danger'" size="small">{{ row.status==='active'?'启用':'禁用' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="contact_name" label="联系人" width="110" />
      <el-table-column prop="contact_email" label="邮箱" min-width="180" />
      <el-table-column prop="contact_phone" label="电话" width="130" />
      <el-table-column prop="created_at" label="创建时间" width="170" />
      <el-table-column label="操作" width="150">
        <template #default="{row}">
          <el-button link size="small" @click="openEdit(row)">编辑</el-button>
          <el-popconfirm v-if="row.id!==1" title="确定删除该租户？" @confirm="remove(row.id)">
            <template #reference><el-button link size="small" type="danger">删除</el-button></template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog :title="editId?'编辑租户':'新建租户'" v-model="showDialog" width="500px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item v-if="!editId" label="编码"><el-input v-model="form.code" placeholder="字母/数字/下划线/横线" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" :rows="2" /></el-form-item>
        <el-form-item v-if="editId" label="状态">
          <el-select v-model="form.status" style="width:100%">
            <el-option label="启用" value="active" /><el-option label="禁用" value="disabled" />
          </el-select>
        </el-form-item>
        <el-form-item label="联系人"><el-input v-model="form.contact_name" /></el-form-item>
        <el-form-item label="邮箱"><el-input v-model="form.contact_email" /></el-form-item>
        <el-form-item label="电话"><el-input v-model="form.contact_phone" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog=false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/api/request'

const list=ref([]),loading=ref(false),showDialog=ref(false),editId=ref(null)
const searchKey=ref(''),statusFilter=ref(null)
const form=ref({name:'',code:'',description:'',status:'active',contact_name:'',contact_email:'',contact_phone:''})

async function load(){
  loading.value=true
  try{
    let url='/tenants?limit=200'
    if(statusFilter.value)url+=`&status=${statusFilter.value}`
    if(searchKey.value)url+=`&search=${searchKey.value}`
    const r=await request.get(url)
    list.value=r.data?.items||[]
  }catch(e){}
  loading.value=false
}
function openCreate(){editId.value=null;form.value={name:'',code:'',description:'',status:'active',contact_name:'',contact_email:'',contact_phone:''};showDialog.value=true}
function openEdit(row){editId.value=row.id;form.value={name:row.name,code:row.code,description:row.description||'',status:row.status,contact_name:row.contact_name||'',contact_email:row.contact_email||'',contact_phone:row.contact_phone||''};showDialog.value=true}
async function save(){
  if(!form.value.name){ElMessage.warning('请输入租户名称');return}
  try{
    if(editId.value){await request.put(`/tenants/${editId.value}`,form.value);ElMessage.success('更新成功')}
    else{if(!form.value.code){ElMessage.warning('请输入编码');return};await request.post('/tenants',form.value);ElMessage.success('创建成功')}
    showDialog.value=false;load()
  }catch(e){}
}
async function remove(id){try{await request.delete(`/tenants/${id}`);ElMessage.success('删除成功');load()}catch(e){}}
onMounted(load)
</script>
