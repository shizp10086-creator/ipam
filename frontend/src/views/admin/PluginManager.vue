<template>
  <div>
    <h3 style="margin-bottom:16px;">🧩 插件管理</h3>
    <el-tabs v-model="activeTab">
      <el-tab-pane label="已安装" name="installed">
        <el-table :data="installed" stripe>
          <el-table-column prop="name" label="插件名称" width="160" />
          <el-table-column prop="version" label="版本" width="80" />
          <el-table-column prop="description" label="描述" min-width="250" />
          <el-table-column label="状态" width="80"><template #default="{row}"><el-tag :type="row.enabled?'success':'info'" size="small">{{ row.enabled?'启用':'禁用' }}</el-tag></template></el-table-column>
          <el-table-column label="操作" width="120"><template #default="{row}"><el-button link size="small" @click="row.enabled=!row.enabled">{{ row.enabled?'禁用':'启用' }}</el-button></template></el-table-column>
        </el-table>
      </el-tab-pane>
      <el-tab-pane label="插件市场" name="market">
        <el-row :gutter="16">
          <el-col :span="8" v-for="p in market" :key="p.name">
            <el-card shadow="hover" style="margin-bottom:12px;">
              <div style="display:flex;justify-content:space-between;align-items:center;">
                <div><div style="font-weight:600;">{{ p.name }}</div><div style="font-size:12px;color:#909399;">{{ p.desc }}</div></div>
                <el-button size="small" type="primary">安装</el-button>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>
<script setup>
import { ref } from 'vue'
const activeTab=ref('installed')
const installed=ref([
  {name:'IPAM 核心',version:'2.0.0',description:'IP 地址管理、网段管理、冲突检测',enabled:true},
  {name:'DCIM 机房管理',version:'1.0.0',description:'机房、机架、U 位管理',enabled:true},
  {name:'NAC 准入控制',version:'1.0.0',description:'RADIUS 认证、策略引擎',enabled:true},
  {name:'数据采集引擎',version:'1.0.0',description:'SNMP/Ping/Syslog/NetFlow 采集',enabled:true},
  {name:'AI 智能分析',version:'1.0.0',description:'AI 对话、智能搜索、预警',enabled:true},
])
const market=ref([
  {name:'VMware 集成',desc:'自动同步 vCenter 虚拟机 IP'},
  {name:'K8s 容器管理',desc:'纳管 Pod/Service IP'},
  {name:'阿里云集成',desc:'同步 VPC/EIP 资源'},
  {name:'华为云集成',desc:'同步华为云网络资源'},
  {name:'Modbus 工控采集',desc:'PLC/传感器数据采集'},
  {name:'MQTT IoT 采集',desc:'物联网设备数据采集'},
])
</script>
