<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
      <h3>💻 终端管理</h3>
      <div style="display:flex;gap:8px;">
        <el-tag type="success">在线 {{ stats.online }}</el-tag>
        <el-tag type="info">离线 {{ stats.offline }}</el-tag>
        <el-tag>合规率 {{ stats.compliance_rate }}%</el-tag>
      </div>
    </div>
    <div style="margin-bottom:12px;display:flex;gap:8px;flex-wrap:wrap;">
      <el-input v-model="search" placeholder="搜索主机名/IP/MAC/用户" clearable style="width:240px;" @keyup.enter="load" @clear="load" />
      <el-select v-model="filterType" placeholder="类型" clearable style="width:120px;" @change="load">
        <el-option label="PC" value="pc" /><el-option label="笔记本" value="laptop" />
        <el-option label="打印机" value="printer" /><el-option label="手机" value="mobile" />
        <el-option label="IoT" value="iot" /><el-option label="其他" value="other" />
      </el-select>
      <el-select v-model="filterOnline" placeholder="在线状态" clearable style="width:120px;" @change="load">
        <el-option label="在线" :value="true" /><el-option label="离线" :value="false" />
      </el-select>
      <el-select v-model="filterCompliance" placeholder="合规状态" clearable style="width:120px;" @change="load">
        <el-option label="合规" value="compliant" /><el-option label="不合规" value="non_compliant" />
        <el-option label="未检查" value="unknown" />
      </el-select>
      <el-select v-model="filterApproval" placeholder="审核状态" clearable style="width:120px;" @change="load">
        <el-option label="已纳管" value="approved" /><el-option label="待审核" value="pending" />
        <el-option label="已拉黑" value="blacklisted" />
      </el-select>
    </div>
    <el-table :data="items" v-loading="loading" stripe>
      <el-table-column prop="hostname" label="主机名" min-width="140" />
      <el-table-column prop="ip_address" label="IP 地址" width="140" />
      <el-table-column prop="mac_address" label="MAC 地址" width="150" />
      <el-table-column label="类型" width="80"><template #default="{row}"><el-tag size="small">{{ row.terminal_type }}</el-tag></template></el-table-column>
      <el-table-column prop="os_type" label="操作系统" width="100" />
      <el-table-column label="在线" width="60">
        <template #default="{row}"><el-tag :type="row.is_online?'success':'info'" size="small">{{ row.is_online?'在线':'离线' }}</el-tag></template>
      </el-table-column>
      <el-table-column label="合规" width="70">
        <template #default="{row}">
          <el-tag :type="{compliant:'success',non_compliant:'danger',unknown:'info'}[row.compliance_status]" size="small">{{ row.compliance_score }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="user_name" label="使用人" width="80" />
      <el-table-column prop="user_department" label="部门" width="100" />
      <el-table-column label="审核" width="80">
        <template #default="{row}">
          <el-tag :type="{approved:'success',pending:'warning',blacklisted:'danger'}[row.approval_status]" size="small">
            {{ {approved:'已纳管',pending:'待审核',blacklisted:'已拉黑'}[row.approval_status] }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="140">
        <template #default="{row}">
          <el-button link size="small" @click="viewProfile(row)">画像</el-button>
          <el-button v-if="row.approval_status==='pending'" link size="small" type="success" @click="approve(row.id,'approved')">纳管</el-button>
          <el-button v-if="row.approval_status==='pending'" link size="small" type="danger" @click="approve(row.id,'blacklisted')">拉黑</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-drawer v-model="showProfile" :title="profile?.basic?.hostname||'终端画像'" size="480px">
      <template v-if="profile">
        <h4>基本信息</h4>
        <el-descriptions :column="2" border size="small" style="margin-bottom:16px;">
          <el-descriptions-item label="主机名">{{ profile.basic.hostname }}</el-descriptions-item>
          <el-descriptions-item label="IP">{{ profile.basic.ip_address }}</el-descriptions-item>
          <el-descriptions-item label="MAC">{{ profile.basic.mac_address }}</el-descriptions-item>
          <el-descriptions-item label="类型">{{ profile.basic.terminal_type }}</el-descriptions-item>
          <el-descriptions-item label="操作系统">{{ profile.basic.os_type }} {{ profile.basic.os_version }}</el-descriptions-item>
          <el-descriptions-item label="厂商">{{ profile.basic.manufacturer }}</el-descriptions-item>
        </el-descriptions>
        <h4>硬件信息</h4>
        <el-descriptions :column="2" border size="small" style="margin-bottom:16px;">
          <el-descriptions-item label="CPU">{{ profile.hardware.cpu }}</el-descriptions-item>
          <el-descriptions-item label="内存">{{ profile.hardware.memory_gb }} GB</el-descriptions-item>
          <el-descriptions-item label="磁盘">{{ profile.hardware.disk_gb }} GB</el-descriptions-item>
        </el-descriptions>
        <h4>安全状态</h4>
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="合规评分"><el-tag :type="profile.security.compliance_score>=80?'success':'danger'" size="small">{{ profile.security.compliance_score }}</el-tag></el-descriptions-item>
          <el-descriptions-item label="杀毒软件"><el-tag :type="profile.security.antivirus?'success':'danger'" size="small">{{ profile.security.antivirus?'已安装':'未安装' }}</el-tag></el-descriptions-item>
          <el-descriptions-item label="防火墙"><el-tag :type="profile.security.firewall?'success':'danger'" size="small">{{ profile.security.firewall?'已开启':'未开启' }}</el-tag></el-descriptions-item>
          <el-descriptions-item label="系统补丁"><el-tag :type="profile.security.os_patched?'success':'danger'" size="small">{{ profile.security.os_patched?'已更新':'未更新' }}</el-tag></el-descriptions-item>
        </el-descriptions>
      </template>
    </el-drawer>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/api/request'
const items=ref([]),loading=ref(false),showProfile=ref(false),profile=ref(null)
const stats=ref({online:0,offline:0,compliance_rate:0})
const search=ref(''),filterType=ref(null),filterOnline=ref(null),filterCompliance=ref(null),filterApproval=ref(null)
async function load(){
  loading.value=true
  try{
    let u='/asset/terminals?limit=50'
    if(search.value)u+=`&search=${search.value}`
    if(filterType.value)u+=`&terminal_type=${filterType.value}`
    if(filterOnline.value!==null&&filterOnline.value!==undefined&&filterOnline.value!=='')u+=`&is_online=${filterOnline.value}`
    if(filterCompliance.value)u+=`&compliance=${filterCompliance.value}`
    if(filterApproval.value)u+=`&approval=${filterApproval.value}`
    const r=await request.get(u)
    items.value=r.data?.items||[]
    if(r.data?.stats)stats.value=r.data.stats
  }catch(e){}
  loading.value=false
}
async function viewProfile(row){try{const r=await request.get(`/asset/terminals/${row.id}`);profile.value=r.data;showProfile.value=true}catch(e){}}
async function approve(id,action){try{await request.put(`/asset/terminals/${id}/approve?action=${action}`);ElMessage.success(action==='approved'?'已纳管':'已拉黑');load()}catch(e){}}
onMounted(load)
</script>
