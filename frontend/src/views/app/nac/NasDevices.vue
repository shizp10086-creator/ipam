<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
      <h3>🔌 NAS 设备管理（交换机/AC 注册）</h3>
      <el-button type="primary" @click="showCreate=true"><el-icon><Plus /></el-icon> 注册设备</el-button>
    </div>
    <el-alert type="info" :closable="false" style="margin-bottom:16px;">
      华为交换机/无线 AC 需要在此注册为 RADIUS 客户端，FreeRADIUS 才能接受其认证请求。注册后 FreeRADIUS 自动从数据库加载，无需重启。
    </el-alert>
    <el-table :data="items" v-loading="loading" stripe>
      <el-table-column prop="name" label="设备名称" width="160" />
      <el-table-column prop="ip_address" label="管理 IP" width="140" />
      <el-table-column prop="secret" label="共享密钥" width="120" />
      <el-table-column label="设备类型" width="100">
        <template #default="{row}"><el-tag size="small">{{ {huawei:'华为',h3c:'华三',ruijie:'锐捷',cisco:'思科',other:'其他'}[row.nas_type]||row.nas_type }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="description" label="描述" min-width="200" />
    </el-table>
    <el-dialog title="注册 NAS 设备" v-model="showCreate" width="480px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="设备名称" required><el-input v-model="form.name" placeholder="如 SW-Core-01" /></el-form-item>
        <el-form-item label="管理 IP" required><el-input v-model="form.ip_address" placeholder="交换机管理 IP" /></el-form-item>
        <el-form-item label="共享密钥" required><el-input v-model="form.secret" placeholder="RADIUS 共享密钥（与交换机配置一致）" show-password /></el-form-item>
        <el-form-item label="设备类型">
          <el-select v-model="form.nas_type" style="width:100%">
            <el-option label="华为" value="huawei" /><el-option label="华三" value="h3c" />
            <el-option label="锐捷" value="ruijie" /><el-option label="思科" value="cisco" /><el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate=false">取消</el-button>
        <el-button type="primary" @click="create">注册</el-button>
      </template>
    </el-dialog>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/api/request'
const items=ref([]),loading=ref(false),showCreate=ref(false)
const form=ref({name:'',ip_address:'',secret:'',nas_type:'huawei',description:''})
async function load(){
  loading.value=true
  try{const r=await request.get('/nac/radius/nas');items.value=r.data?.items||[]}catch(e){}
  loading.value=false
}
async function create(){
  if(!form.value.name||!form.value.ip_address||!form.value.secret){ElMessage.warning('请填写完整');return}
  try{
    await request.post('/nac/radius/nas',form.value)
    ElMessage.success('NAS 设备注册成功');showCreate.value=false;load()
  }catch(e){ElMessage.error(e.response?.data?.message||'注册失败')}
}
onMounted(load)
</script>
