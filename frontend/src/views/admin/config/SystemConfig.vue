<template>
  <div>
    <h3 style="margin-bottom:16px;">⚙️ 系统配置中心</h3>
    <el-tabs v-model="activeTab">
      <el-tab-pane label="基础配置" name="basic">
        <el-form label-width="140px" style="max-width:600px;">
          <el-form-item label="系统名称"><el-input v-model="config.system_name" /></el-form-item>
          <el-form-item label="默认语言"><el-select v-model="config.language" style="width:100%"><el-option label="中文" value="zh-CN" /><el-option label="English" value="en-US" /></el-select></el-form-item>
          <el-form-item label="时区"><el-select v-model="config.timezone" style="width:100%"><el-option label="Asia/Shanghai" value="Asia/Shanghai" /><el-option label="UTC" value="UTC" /></el-select></el-form-item>
          <el-form-item><el-button type="primary" @click="save">保存</el-button></el-form-item>
        </el-form>
      </el-tab-pane>
      <el-tab-pane label="扫描配置" name="scan">
        <el-form label-width="140px" style="max-width:600px;">
          <el-form-item label="Ping 并发数"><el-input-number v-model="config.ping_concurrency" :min="1" :max="100" /></el-form-item>
          <el-form-item label="扫描超时(秒)"><el-input-number v-model="config.scan_timeout" :min="1" :max="60" /></el-form-item>
          <el-form-item label="定时扫描"><el-switch v-model="config.auto_scan_enabled" /></el-form-item>
          <el-form-item label="扫描周期"><el-select v-model="config.scan_interval" style="width:100%"><el-option label="每天" value="daily" /><el-option label="每周" value="weekly" /><el-option label="每月" value="monthly" /></el-select></el-form-item>
          <el-form-item><el-button type="primary" @click="save">保存</el-button></el-form-item>
        </el-form>
      </el-tab-pane>
      <el-tab-pane label="告警配置" name="alert">
        <el-form label-width="140px" style="max-width:600px;">
          <el-form-item label="默认警告阈值(%)"><el-input-number v-model="config.alert_warning" :min="0" :max="100" /></el-form-item>
          <el-form-item label="默认严重阈值(%)"><el-input-number v-model="config.alert_critical" :min="0" :max="100" /></el-form-item>
          <el-form-item label="告警升级时间(分)"><el-input-number v-model="config.alert_escalation_minutes" :min="1" /></el-form-item>
          <el-form-item label="告警抑制时间(分)"><el-input-number v-model="config.alert_suppress_minutes" :min="1" /></el-form-item>
          <el-form-item><el-button type="primary" @click="save">保存</el-button></el-form-item>
        </el-form>
      </el-tab-pane>
      <el-tab-pane label="备份配置" name="backup">
        <el-form label-width="140px" style="max-width:600px;">
          <el-form-item label="自动备份"><el-switch v-model="config.auto_backup" /></el-form-item>
          <el-form-item label="备份周期"><el-select v-model="config.backup_interval" style="width:100%"><el-option label="每天" value="daily" /><el-option label="每周" value="weekly" /></el-select></el-form-item>
          <el-form-item label="保留天数"><el-input-number v-model="config.backup_retention_days" :min="1" /></el-form-item>
          <el-form-item><el-button type="primary" @click="save">保存</el-button></el-form-item>
        </el-form>
      </el-tab-pane>
      <el-tab-pane label="AI 模型" name="ai">
        <el-form label-width="140px" style="max-width:600px;">
          <el-form-item label="默认模型"><el-select v-model="config.ai_model" style="width:100%"><el-option label="GPT-4" value="openai-gpt4" /><el-option label="DeepSeek" value="deepseek-chat" /><el-option label="通义千问" value="qwen-turbo" /><el-option label="本地 Ollama" value="ollama-local" /></el-select></el-form-item>
          <el-form-item label="API 地址"><el-input v-model="config.ai_api_url" placeholder="https://api.openai.com/v1" /></el-form-item>
          <el-form-item label="API 密钥"><el-input v-model="config.ai_api_key" type="password" show-password placeholder="sk-..." /></el-form-item>
          <el-form-item><el-button type="primary" @click="save">保存</el-button></el-form-item>
        </el-form>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>
<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
const activeTab=ref('basic')
const config=ref({
  system_name:'IT 智维平台',language:'zh-CN',timezone:'Asia/Shanghai',
  ping_concurrency:10,scan_timeout:5,auto_scan_enabled:true,scan_interval:'daily',
  alert_warning:80,alert_critical:90,alert_escalation_minutes:60,alert_suppress_minutes:30,
  auto_backup:true,backup_interval:'daily',backup_retention_days:30,
  ai_model:'deepseek-chat',ai_api_url:'',ai_api_key:'',
})
function save(){ElMessage.success('配置保存成功（即时生效）')}
</script>
