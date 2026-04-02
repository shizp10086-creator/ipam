<template>
  <div>
    <h3 style="margin-bottom:16px;">📖 IT 服务目录</h3>
    <el-row :gutter="16">
      <el-col :span="8" v-for="cat in categories" :key="cat.name">
        <el-card shadow="hover" style="margin-bottom:16px;">
          <template #header><span style="font-weight:600;">{{ cat.icon }} {{ cat.name }}</span></template>
          <div v-for="svc in cat.services" :key="svc.title" class="svc-item" @click="applyService(svc)">
            <div class="svc-title">{{ svc.title }}</div>
            <div class="svc-desc">{{ svc.desc }}</div>
            <div class="svc-meta">预计处理: {{ svc.sla }} | {{ svc.approval ? '需审批' : '免审批' }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>
<script setup>
import { useRouter } from 'vue-router'
const router = useRouter()
const categories = [
  { name: '网络服务', icon: '🌐', services: [
    { title: 'IP 地址申请', desc: '申请新的内网/公网 IP', sla: '2小时', approval: true, type: 'ip_apply' },
    { title: 'IP 地址变更', desc: '修改 IP 绑定关系', sla: '1小时', approval: true, type: 'ip_change' },
    { title: 'IP 地址回收', desc: '归还不再使用的 IP', sla: '30分钟', approval: false, type: 'ip_recycle' },
    { title: 'VLAN 变更', desc: '调整终端所在 VLAN', sla: '2小时', approval: true, type: 'change_request' },
  ]},
  { name: '设备服务', icon: '💻', services: [
    { title: '设备领用', desc: '申请领用 IT 设备', sla: '1天', approval: true, type: 'device_onboard' },
    { title: '设备报修', desc: '报告设备故障', sla: '4小时', approval: false, type: 'device_repair' },
    { title: '设备归还', desc: '归还不再使用的设备', sla: '1天', approval: false, type: 'other' },
  ]},
  { name: '账号服务', icon: '🔑', services: [
    { title: '权限申请', desc: '申请系统功能权限', sla: '4小时', approval: true, type: 'permission_apply' },
    { title: '网络准入', desc: '申请网络接入权限', sla: '2小时', approval: true, type: 'other' },
    { title: '访客网络', desc: '为访客申请临时网络', sla: '30分钟', approval: true, type: 'other' },
  ]},
]
function applyService(svc) { router.push({ path: '/app/tickets', query: { create: svc.type } }) }
</script>
<style scoped>
.svc-item{padding:10px 0;border-bottom:1px solid #f0f0f0;cursor:pointer;transition:background 0.2s;}
.svc-item:hover{background:#f5f7fa;}
.svc-item:last-child{border-bottom:none;}
.svc-title{font-weight:600;font-size:14px;color:#303133;}
.svc-desc{font-size:12px;color:#909399;margin-top:2px;}
.svc-meta{font-size:11px;color:#c0c4cc;margin-top:4px;}
</style>
