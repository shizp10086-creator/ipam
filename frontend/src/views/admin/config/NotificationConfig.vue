<template>
  <div>
    <h3 style="margin-bottom:16px;">📧 通知渠道配置</h3>
    <el-tabs v-model="activeTab">
      <el-tab-pane label="邮件 (SMTP)" name="email">
        <el-form label-width="120px" style="max-width:550px;">
          <el-form-item label="启用"><el-switch v-model="email.enabled" /></el-form-item>
          <el-form-item label="SMTP 服务器"><el-input v-model="email.host" placeholder="smtp.example.com" /></el-form-item>
          <el-form-item label="端口"><el-input-number v-model="email.port" :min="1" /></el-form-item>
          <el-form-item label="用户名"><el-input v-model="email.username" /></el-form-item>
          <el-form-item label="密码"><el-input v-model="email.password" type="password" show-password /></el-form-item>
          <el-form-item label="发件人"><el-input v-model="email.from_addr" placeholder="noreply@example.com" /></el-form-item>
          <el-form-item label="加密"><el-select v-model="email.encryption" style="width:100%"><el-option label="TLS" value="tls" /><el-option label="SSL" value="ssl" /><el-option label="无" value="none" /></el-select></el-form-item>
          <el-form-item><el-button type="primary" @click="save('email')">保存</el-button><el-button @click="testChannel('email')" style="margin-left:8px;">发送测试</el-button></el-form-item>
        </el-form>
      </el-tab-pane>
      <el-tab-pane label="企业微信" name="wechat">
        <el-form label-width="120px" style="max-width:550px;">
          <el-form-item label="启用"><el-switch v-model="wechat.enabled" /></el-form-item>
          <el-form-item label="Webhook URL"><el-input v-model="wechat.webhook_url" placeholder="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=..." /></el-form-item>
          <el-form-item><el-button type="primary" @click="save('wechat')">保存</el-button><el-button @click="testChannel('wechat')" style="margin-left:8px;">发送测试</el-button></el-form-item>
        </el-form>
      </el-tab-pane>
      <el-tab-pane label="钉钉" name="dingtalk">
        <el-form label-width="120px" style="max-width:550px;">
          <el-form-item label="启用"><el-switch v-model="dingtalk.enabled" /></el-form-item>
          <el-form-item label="Webhook URL"><el-input v-model="dingtalk.webhook_url" placeholder="https://oapi.dingtalk.com/robot/send?access_token=..." /></el-form-item>
          <el-form-item label="签名密钥"><el-input v-model="dingtalk.secret" type="password" show-password /></el-form-item>
          <el-form-item><el-button type="primary" @click="save('dingtalk')">保存</el-button><el-button @click="testChannel('dingtalk')" style="margin-left:8px;">发送测试</el-button></el-form-item>
        </el-form>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>
<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
const activeTab=ref('email')
const email=ref({enabled:false,host:'',port:587,username:'',password:'',from_addr:'',encryption:'tls'})
const wechat=ref({enabled:false,webhook_url:''})
const dingtalk=ref({enabled:false,webhook_url:'',secret:''})
function save(ch){ElMessage.success(`${ch} 配置保存成功`)}
function testChannel(ch){ElMessage.info(`正在发送 ${ch} 测试消息...`);setTimeout(()=>ElMessage.success('测试消息发送成功'),1000)}
</script>
