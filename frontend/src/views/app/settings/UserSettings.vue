<template>
  <div>
    <h3 style="margin-bottom:16px;">⚙️ 个人设置</h3>
    <el-tabs v-model="activeTab">
      <el-tab-pane label="基本信息" name="profile">
        <el-form :model="profile" label-width="100px" style="max-width:500px;">
          <el-form-item label="用户名"><el-input v-model="profile.username" disabled /></el-form-item>
          <el-form-item label="显示名称"><el-input v-model="profile.display_name" /></el-form-item>
          <el-form-item label="邮箱"><el-input v-model="profile.email" /></el-form-item>
          <el-form-item label="手机号"><el-input v-model="profile.phone" /></el-form-item>
          <el-form-item label="部门"><el-input v-model="profile.department" /></el-form-item>
          <el-form-item><el-button type="primary" @click="saveProfile">保存</el-button></el-form-item>
        </el-form>
      </el-tab-pane>
      <el-tab-pane label="修改密码" name="password">
        <el-form :model="pwdForm" label-width="100px" style="max-width:500px;">
          <el-form-item label="当前密码"><el-input v-model="pwdForm.old_password" type="password" show-password /></el-form-item>
          <el-form-item label="新密码"><el-input v-model="pwdForm.new_password" type="password" show-password /></el-form-item>
          <el-form-item label="确认密码"><el-input v-model="pwdForm.confirm_password" type="password" show-password /></el-form-item>
          <el-form-item><el-button type="primary" @click="changePassword">修改密码</el-button></el-form-item>
        </el-form>
      </el-tab-pane>
      <el-tab-pane label="通知偏好" name="notification">
        <el-form label-width="120px" style="max-width:500px;">
          <el-form-item label="邮件通知"><el-switch v-model="notif.email" /></el-form-item>
          <el-form-item label="企业微信通知"><el-switch v-model="notif.wechat" /></el-form-item>
          <el-form-item label="钉钉通知"><el-switch v-model="notif.dingtalk" /></el-form-item>
          <el-form-item label="告警通知"><el-switch v-model="notif.alert" /></el-form-item>
          <el-form-item label="工单通知"><el-switch v-model="notif.ticket" /></el-form-item>
          <el-form-item><el-button type="primary" @click="saveNotif">保存偏好</el-button></el-form-item>
        </el-form>
      </el-tab-pane>
      <el-tab-pane label="界面设置" name="ui">
        <el-form label-width="100px" style="max-width:500px;">
          <el-form-item label="语言">
            <el-select v-model="uiSettings.language" style="width:200px;">
              <el-option label="简体中文" value="zh-CN" /><el-option label="English" value="en" />
            </el-select>
          </el-form-item>
          <el-form-item label="每页条数">
            <el-select v-model="uiSettings.pageSize" style="width:200px;">
              <el-option :label="10" :value="10" /><el-option :label="20" :value="20" />
              <el-option :label="50" :value="50" /><el-option :label="100" :value="100" />
            </el-select>
          </el-form-item>
          <el-form-item><el-button type="primary" @click="saveUI">保存</el-button></el-form-item>
        </el-form>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/api/request'
const activeTab=ref('profile')
const profile=ref({username:'',display_name:'',email:'',phone:'',department:''})
const pwdForm=ref({old_password:'',new_password:'',confirm_password:''})
const notif=ref({email:true,wechat:false,dingtalk:false,alert:true,ticket:true})
const uiSettings=ref({language:'zh-CN',pageSize:20})
async function loadProfile(){
  try{const r=await request.get('/auth/me');const d=r.data||{};profile.value={username:d.username||'',display_name:d.display_name||d.username||'',email:d.email||'',phone:d.phone||'',department:d.department||''}}catch(e){}
}
async function saveProfile(){try{await request.put('/users/me',profile.value);ElMessage.success('保存成功')}catch(e){ElMessage.error('保存失败')}}
async function changePassword(){
  if(!pwdForm.value.old_password||!pwdForm.value.new_password){ElMessage.warning('请填写密码');return}
  if(pwdForm.value.new_password!==pwdForm.value.confirm_password){ElMessage.warning('两次密码不一致');return}
  if(pwdForm.value.new_password.length<6){ElMessage.warning('密码至少6位');return}
  try{await request.post('/auth/change-password',pwdForm.value);ElMessage.success('密码修改成功');pwdForm.value={old_password:'',new_password:'',confirm_password:''}}catch(e){ElMessage.error('修改失败')}
}
function saveNotif(){localStorage.setItem('notif_prefs',JSON.stringify(notif.value));ElMessage.success('通知偏好已保存')}
function saveUI(){localStorage.setItem('ui_settings',JSON.stringify(uiSettings.value));ElMessage.success('界面设置已保存')}
onMounted(()=>{
  loadProfile()
  try{const n=JSON.parse(localStorage.getItem('notif_prefs'));if(n)Object.assign(notif.value,n)}catch(e){}
  try{const u=JSON.parse(localStorage.getItem('ui_settings'));if(u)Object.assign(uiSettings.value,u)}catch(e){}
})
</script>
