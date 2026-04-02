<template>
  <div>
    <h3 style="margin-bottom:16px;">🔐 权限管理</h3>
    <el-tabs v-model="activeTab">
      <el-tab-pane label="用户管理" name="users">
        <el-button type="primary" size="small" style="margin-bottom:12px;" @click="$router.push('/app/users')">管理用户 →</el-button>
        <p style="color:#909399;font-size:13px;">在用户管理页面创建/编辑用户、分配角色。</p>
      </el-tab-pane>
      <el-tab-pane label="角色管理" name="roles">
        <el-table :data="roles" stripe>
          <el-table-column prop="name" label="角色名称" width="140" />
          <el-table-column prop="code" label="角色编码" width="140" />
          <el-table-column label="类型" width="80"><template #default="{row}"><el-tag :type="row.system?'':'success'" size="small">{{ row.system?'系统':'自定义' }}</el-tag></template></el-table-column>
          <el-table-column prop="desc" label="权限说明" min-width="300" />
        </el-table>
      </el-tab-pane>
      <el-tab-pane label="LDAP/AD" name="ldap">
        <el-form label-width="120px" style="max-width:550px;">
          <el-form-item label="启用 LDAP"><el-switch v-model="ldap.enabled" /></el-form-item>
          <el-form-item label="服务器地址"><el-input v-model="ldap.server_url" placeholder="ldap://192.168.1.10:389" /></el-form-item>
          <el-form-item label="Base DN"><el-input v-model="ldap.base_dn" placeholder="dc=example,dc=com" /></el-form-item>
          <el-form-item label="绑定 DN"><el-input v-model="ldap.bind_dn" /></el-form-item>
          <el-form-item label="绑定密码"><el-input v-model="ldap.bind_password" type="password" show-password /></el-form-item>
          <el-form-item label="同步周期(h)"><el-input-number v-model="ldap.sync_interval_hours" :min="1" /></el-form-item>
          <el-form-item><el-button type="primary" @click="saveLdap">保存</el-button><el-button @click="testLdap" style="margin-left:8px;">测试连接</el-button><el-button @click="syncLdap" style="margin-left:8px;">立即同步</el-button></el-form-item>
        </el-form>
      </el-tab-pane>
      <el-tab-pane label="企业微信" name="wechat">
        <el-form label-width="120px" style="max-width:550px;">
          <el-form-item label="启用"><el-switch v-model="wechat.enabled" /></el-form-item>
          <el-form-item label="Corp ID"><el-input v-model="wechat.corp_id" /></el-form-item>
          <el-form-item label="Agent ID"><el-input v-model="wechat.agent_id" /></el-form-item>
          <el-form-item label="Secret"><el-input v-model="wechat.secret" type="password" show-password /></el-form-item>
          <el-form-item><el-button type="primary" @click="saveWechat">保存</el-button><el-button @click="syncOrg" style="margin-left:8px;">同步组织架构</el-button></el-form-item>
        </el-form>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>
<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/api/request'
const activeTab=ref('roles')
const roles=ref([
  {name:'管理员',code:'administrator',system:true,desc:'所有权限（创建/读取/更新/删除/配置/审批）'},
  {name:'普通用户',code:'regular_user',system:true,desc:'IP 分配/回收、设备管理、告警查看、工单提交'},
  {name:'只读用户',code:'readonly_user',system:true,desc:'仅查看数据，不能执行任何修改操作'},
])
const ldap=ref({enabled:false,server_url:'',base_dn:'',bind_dn:'',bind_password:'',sync_interval_hours:6})
const wechat=ref({enabled:false,corp_id:'',agent_id:'',secret:''})
async function saveLdap(){try{await request.post('/auth/ldap/config',ldap.value);ElMessage.success('LDAP 配置保存成功')}catch(e){ElMessage.error('保存失败')}}
async function testLdap(){try{const r=await request.post('/auth/ldap/test',ldap.value);ElMessage.success(r.message)}catch(e){ElMessage.error('连接失败')}}
async function syncLdap(){try{await request.post('/auth/ldap/sync');ElMessage.success('同步任务已加入队列')}catch(e){}}
async function saveWechat(){try{await request.post('/auth/wechat/config',wechat.value);ElMessage.success('企业微信配置保存成功')}catch(e){}}
async function syncOrg(){try{await request.post('/auth/wechat/sync-org');ElMessage.success('组织架构同步已加入队列')}catch(e){}}
</script>
