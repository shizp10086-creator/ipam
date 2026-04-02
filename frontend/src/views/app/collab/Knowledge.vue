<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
      <h3>📚 知识库</h3>
      <el-button type="primary" @click="showCreate=true"><el-icon><Plus /></el-icon> 新建文章</el-button>
    </div>
    <div style="margin-bottom:12px;display:flex;gap:8px;">
      <el-select v-model="filterCat" placeholder="分类" clearable style="width:140px;" @change="load">
        <el-option label="故障案例" value="故障案例" /><el-option label="配置手册" value="配置手册" />
        <el-option label="运维规范" value="运维规范" /><el-option label="FAQ" value="FAQ" />
      </el-select>
      <el-input v-model="search" placeholder="搜索标题/内容" clearable style="width:240px;" @keyup.enter="load" @clear="load" />
    </div>
    <el-table :data="items" v-loading="loading" stripe @row-click="viewArticle">
      <el-table-column prop="title" label="标题" min-width="250" />
      <el-table-column prop="category" label="分类" width="100"><template #default="{row}"><el-tag size="small">{{ row.category||'未分类' }}</el-tag></template></el-table-column>
      <el-table-column prop="author_name" label="作者" width="80" />
      <el-table-column prop="view_count" label="浏览" width="60" />
      <el-table-column prop="created_at" label="创建时间" width="170" />
    </el-table>
    <el-dialog title="新建知识文章" v-model="showCreate" width="600px">
      <el-form :model="form" label-width="60px">
        <el-form-item label="标题"><el-input v-model="form.title" /></el-form-item>
        <el-form-item label="分类"><el-select v-model="form.category" style="width:100%"><el-option label="故障案例" value="故障案例" /><el-option label="配置手册" value="配置手册" /><el-option label="运维规范" value="运维规范" /><el-option label="FAQ" value="FAQ" /></el-select></el-form-item>
        <el-form-item label="内容"><el-input v-model="form.content" type="textarea" :rows="6" /></el-form-item>
        <el-form-item label="标签"><el-input v-model="tagsInput" placeholder="逗号分隔" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="showCreate=false">取消</el-button><el-button type="primary" @click="create">发布</el-button></template>
    </el-dialog>
    <el-drawer v-model="showDetail" :title="detailArticle?.title" size="500px">
      <div v-if="detailArticle" style="white-space:pre-wrap;">{{ detailArticle.content }}</div>
    </el-drawer>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/api/request'
const items=ref([]),loading=ref(false),showCreate=ref(false),showDetail=ref(false),detailArticle=ref(null)
const filterCat=ref(null),search=ref(''),tagsInput=ref('')
const form=ref({title:'',content:'',category:'FAQ',tags:[]})
async function load(){loading.value=true;try{let u='/collab/knowledge?limit=50';if(filterCat.value)u+=`&category=${filterCat.value}`;if(search.value)u+=`&search=${search.value}`;const r=await request.get(u);items.value=r.data?.items||[]}catch(e){}loading.value=false}
async function create(){if(!form.value.title||!form.value.content){ElMessage.warning('请填写标题和内容');return};form.value.tags=tagsInput.value.split(',').map(t=>t.trim()).filter(Boolean);try{await request.post('/collab/knowledge',form.value);ElMessage.success('发布成功');showCreate.value=false;load()}catch(e){ElMessage.error('发布失败')}}
async function viewArticle(row){try{const r=await request.get(`/collab/knowledge/${row.id}`);detailArticle.value=r.data;showDetail.value=true}catch(e){}}
onMounted(load)
</script>
