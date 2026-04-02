<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
      <h3>🔢 IP 矩阵视图 — {{ segmentInfo.cidr || `网段 #${segmentId}` }}</h3>
      <div style="display:flex;gap:8px;align-items:center;">
        <span style="font-size:12px;color:#909399;">
          <span style="display:inline-block;width:12px;height:12px;background:#67c23a;border-radius:2px;vertical-align:middle;margin-right:2px;"></span>空闲
          <span style="display:inline-block;width:12px;height:12px;background:#f56c6c;border-radius:2px;vertical-align:middle;margin:0 2px 0 8px;"></span>已用
          <span style="display:inline-block;width:12px;height:12px;background:#e6a23c;border-radius:2px;vertical-align:middle;margin:0 2px 0 8px;"></span>保留
          <span style="display:inline-block;width:12px;height:12px;background:#409eff;border-radius:2px;vertical-align:middle;margin:0 2px 0 8px;"></span>临时
        </span>
        <el-button size="small" @click="load"><el-icon><Refresh /></el-icon> 刷新</el-button>
      </div>
    </div>
    <div style="margin-bottom:12px;display:flex;gap:16px;">
      <el-tag>总数 {{ ips.length }}</el-tag>
      <el-tag type="success">空闲 {{ countByStatus('available') }}</el-tag>
      <el-tag type="danger">已用 {{ countByStatus('used') }}</el-tag>
      <el-tag type="warning">保留 {{ countByStatus('reserved') }}</el-tag>
      <el-tag type="">临时 {{ countByStatus('temporary') }}</el-tag>
    </div>
    <div v-loading="loading" class="matrix-grid">
      <el-tooltip v-for="ip in ips" :key="ip.ip_address" :content="tipContent(ip)" placement="top" :show-after="200">
        <div class="matrix-cell" :style="{background:colorMap[ip.status]||'#dcdfe6'}" @click="handleClick(ip)">
          {{ ip.ip_address?.split('.').pop() || ip.ip_address }}
        </div>
      </el-tooltip>
    </div>
    <el-drawer v-model="showDetail" :title="selected?.ip_address" size="360px">
      <template v-if="selected">
        <el-descriptions :column="1" border size="small">
          <el-descriptions-item label="IP 地址">{{ selected.ip_address }}</el-descriptions-item>
          <el-descriptions-item label="状态"><el-tag :type="tagType(selected.status)" size="small">{{ statusMap[selected.status] }}</el-tag></el-descriptions-item>
          <el-descriptions-item label="设备">{{ selected.device_name||'-' }}</el-descriptions-item>
          <el-descriptions-item label="使用人">{{ selected.owner||'-' }}</el-descriptions-item>
          <el-descriptions-item label="描述">{{ selected.description||'-' }}</el-descriptions-item>
        </el-descriptions>
        <div style="margin-top:16px;display:flex;gap:8px;">
          <el-button v-if="selected.status==='available'" type="primary" size="small" @click="allocate(selected)">分配</el-button>
          <el-button v-if="selected.status==='used'" type="warning" size="small" @click="release(selected)">回收</el-button>
          <el-button v-if="selected.status==='available'" size="small" @click="reserve(selected)">标记保留</el-button>
        </div>
      </template>
    </el-drawer>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '@/api/request'
const route=useRoute(),router=useRouter()
const segmentId=route.params.segmentId
const ips=ref([]),loading=ref(false),showDetail=ref(false),selected=ref(null)
const segmentInfo=ref({cidr:''})
const colorMap={available:'#67c23a',used:'#f56c6c',reserved:'#e6a23c',temporary:'#409eff',conflict:'#ff0000'}
const statusMap={available:'空闲',used:'已用',reserved:'保留',temporary:'临时',conflict:'冲突'}
function tagType(s){return {available:'success',used:'danger',reserved:'warning',temporary:'',conflict:'danger'}[s]||'info'}
function countByStatus(s){return ips.value.filter(i=>i.status===s).length}
function tipContent(ip){return `${ip.ip_address} [${statusMap[ip.status]||ip.status}]${ip.device_name?' - '+ip.device_name:''}`}
function handleClick(ip){selected.value=ip;showDetail.value=true}
async function load(){
  loading.value=true
  try{
    try{const sr=await request.get(`/segments/${segmentId}`);segmentInfo.value=sr.data||{}}catch(e){}
    const r=await request.get(`/ips?segment_id=${segmentId}&page_size=1024`)
    ips.value=r.data?.items||r.data||[]
  }catch(e){}
  loading.value=false
}
async function allocate(ip){router.push({name:'IPAllocate',query:{ip:ip.ip_address,segment_id:segmentId}})}
async function release(ip){try{await request.post('/ips/release',{ip_address:ip.ip_address});ElMessage.success('已回收');load()}catch(e){}}
async function reserve(ip){try{await request.put(`/ips/${ip.id}`,{status:'reserved'});ElMessage.success('已标记保留');load()}catch(e){}}
onMounted(load)
</script>
<style scoped>
.matrix-grid{display:flex;flex-wrap:wrap;gap:4px;}
.matrix-cell{width:44px;height:32px;display:flex;align-items:center;justify-content:center;border-radius:4px;font-size:11px;color:#fff;cursor:pointer;transition:transform .15s,box-shadow .15s;font-weight:500;}
.matrix-cell:hover{transform:scale(1.15);box-shadow:0 2px 8px rgba(0,0,0,.2);z-index:1;}
</style>
