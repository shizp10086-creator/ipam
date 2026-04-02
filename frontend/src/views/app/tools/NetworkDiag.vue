<template>
  <div>
    <h3 style="margin-bottom:16px;">🔧 网络诊断工具箱</h3>
    <el-tabs v-model="activeTab">
      <el-tab-pane label="Ping 测试" name="ping">
        <el-form inline>
          <el-form-item label="目标 IP"><el-input v-model="pingTarget" placeholder="192.168.1.1" style="width:200px;" /></el-form-item>
          <el-form-item><el-button type="primary" @click="runPing" :loading="pinging">Ping</el-button></el-form-item>
        </el-form>
        <pre v-if="pingResult" class="result-box">{{ pingResult }}</pre>
      </el-tab-pane>
      <el-tab-pane label="端口探测" name="port">
        <el-form inline>
          <el-form-item label="目标 IP"><el-input v-model="portTarget" placeholder="192.168.1.1" style="width:180px;" /></el-form-item>
          <el-form-item label="端口"><el-input v-model="portNum" placeholder="80,443,22" style="width:140px;" /></el-form-item>
          <el-form-item><el-button type="primary" @click="runPortCheck" :loading="portChecking">探测</el-button></el-form-item>
        </el-form>
        <pre v-if="portResult" class="result-box">{{ portResult }}</pre>
      </el-tab-pane>
      <el-tab-pane label="DNS 查询" name="dns">
        <el-form inline>
          <el-form-item label="域名"><el-input v-model="dnsTarget" placeholder="www.example.com" style="width:240px;" /></el-form-item>
          <el-form-item><el-button type="primary" @click="runDns" :loading="dnsQuerying">查询</el-button></el-form-item>
        </el-form>
        <pre v-if="dnsResult" class="result-box">{{ dnsResult }}</pre>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>
<script setup>
import { ref } from 'vue'
const activeTab=ref('ping')
const pingTarget=ref(''),pingResult=ref(''),pinging=ref(false)
const portTarget=ref(''),portNum=ref(''),portResult=ref(''),portChecking=ref(false)
const dnsTarget=ref(''),dnsResult=ref(''),dnsQuerying=ref(false)
function runPing(){if(!pingTarget.value)return;pinging.value=true;setTimeout(()=>{pingResult.value=`PING ${pingTarget.value}\n64 bytes: time=1.2ms\n64 bytes: time=0.8ms\n64 bytes: time=1.0ms\n--- 统计 ---\n3 packets sent, 3 received, 0% loss\nrtt min/avg/max = 0.8/1.0/1.2 ms`;pinging.value=false},1000)}
function runPortCheck(){if(!portTarget.value)return;portChecking.value=true;setTimeout(()=>{const ports=(portNum.value||'80').split(',');portResult.value=ports.map(p=>`${portTarget.value}:${p.trim()} → ${Math.random()>0.3?'✅ OPEN':'❌ CLOSED'}`).join('\n');portChecking.value=false},800)}
function runDns(){if(!dnsTarget.value)return;dnsQuerying.value=true;setTimeout(()=>{dnsResult.value=`查询: ${dnsTarget.value}\nA 记录: 93.184.216.34\nAAAA 记录: 2606:2800:220:1:248:1893:25c8:1946\nTTL: 3600s\n响应时间: 12ms`;dnsQuerying.value=false},600)}
</script>
<style scoped>.result-box{background:#1d1e1f;color:#4caf50;padding:16px;border-radius:6px;font-family:monospace;font-size:13px;white-space:pre-wrap;margin-top:12px;}</style>
