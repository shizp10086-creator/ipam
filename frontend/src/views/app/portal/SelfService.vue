<template>
  <div>
    <h3 style="margin-bottom:16px;">🏠 员工自助门户</h3>
    <el-row :gutter="16">
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header><span>💻 我的设备</span></template>
          <p style="color:#909399;font-size:13px;">查看我领用的设备、IP 地址</p>
          <el-button type="primary" link @click="$router.push('/app/assets/devices')">查看设备 →</el-button>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header><span>🌐 我的网络</span></template>
          <p style="color:#909399;font-size:13px;">查看我的 IP、网络连接状态</p>
          <el-button type="primary" link @click="$router.push('/app/ipam/ips')">查看 IP →</el-button>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header><span>📋 我的工单</span></template>
          <p style="color:#909399;font-size:13px;">查看我提交的工单进度</p>
          <el-button type="primary" link @click="$router.push('/app/tickets')">查看工单 →</el-button>
        </el-card>
      </el-col>
    </el-row>
    <el-divider />
    <h4>快捷申请</h4>
    <el-row :gutter="16" style="margin-top:12px;">
      <el-col :span="6" v-for="svc in services" :key="svc.title">
        <el-card shadow="hover" class="svc-card" @click="applyService(svc)">
          <div style="text-align:center;">
            <div style="font-size:32px;">{{ svc.icon }}</div>
            <div style="font-weight:600;margin-top:8px;">{{ svc.title }}</div>
            <div style="font-size:12px;color:#909399;">{{ svc.desc }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>
<script setup>
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
const router = useRouter()
const services = [
  { icon: '🌐', title: 'IP 申请', desc: '申请新的 IP 地址', type: 'ip_apply' },
  { icon: '💻', title: '设备领用', desc: '申请领用 IT 设备', type: 'device_onboard' },
  { icon: '🔑', title: '权限申请', desc: '申请系统权限', type: 'permission_apply' },
  { icon: '🔧', title: '故障报修', desc: '报告设备/网络故障', type: 'incident' },
]
function applyService(svc) {
  router.push({ path: '/app/tickets', query: { create: svc.type } })
}
</script>
<style scoped>.svc-card{cursor:pointer;transition:transform 0.2s;}.svc-card:hover{transform:translateY(-4px);}</style>
