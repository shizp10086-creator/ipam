<template>
  <div class="device-form-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ isEdit ? '编辑设备' : '创建设备' }}</span>
          <el-button @click="handleBack">返回</el-button>
        </div>
      </template>

      <el-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        label-width="120px"
        class="device-form"
      >
        <el-form-item label="设备名称" prop="name">
          <el-input 
            v-model="formData.name" 
            placeholder="请输入设备名称"
            maxlength="100"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="MAC 地址" prop="mac_address">
          <el-input 
            v-model="formData.mac_address" 
            placeholder="如 00:11:22:33:44:55"
            maxlength="17"
          />
        </el-form-item>

        <el-form-item label="设备类型" prop="device_type">
          <el-select v-model="formData.device_type" placeholder="请选择设备类型" style="width: 100%">
            <el-option label="服务器" value="Server" />
            <el-option label="交换机" value="Switch" />
            <el-option label="路由器" value="Router" />
            <el-option label="防火墙" value="Firewall" />
            <el-option label="打印机" value="Printer" />
            <el-option label="电脑" value="PC" />
            <el-option label="笔记本" value="Laptop" />
            <el-option label="其他" value="Other" />
          </el-select>
        </el-form-item>

        <el-form-item label="制造商">
          <el-input 
            v-model="formData.manufacturer" 
            placeholder="请输入制造商"
            maxlength="100"
          />
        </el-form-item>

        <el-form-item label="型号">
          <el-input 
            v-model="formData.model" 
            placeholder="请输入型号"
            maxlength="100"
          />
        </el-form-item>

        <el-form-item label="责任人">
          <el-input 
            v-model="formData.owner" 
            placeholder="请输入责任人"
            maxlength="50"
          />
        </el-form-item>

        <el-form-item label="部门">
          <el-input 
            v-model="formData.department" 
            placeholder="请输入部门"
            maxlength="100"
          />
        </el-form-item>

        <el-form-item label="位置">
          <el-input 
            v-model="formData.location" 
            placeholder="请输入位置"
            maxlength="200"
          />
        </el-form-item>

        <el-form-item label="描述">
          <el-input 
            v-model="formData.description" 
            type="textarea"
            :rows="4"
            placeholder="请输入设备描述"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">
            {{ isEdit ? '更新' : '创建' }}
          </el-button>
          <el-button @click="handleBack">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as deviceApi from '@/api/device'

const router = useRouter()
const route = useRoute()

const formRef = ref(null)
const submitting = ref(false)
const isEdit = ref(false)

const formData = reactive({
  name: '',
  mac_address: '',
  device_type: '',
  manufacturer: '',
  model: '',
  owner: '',
  department: '',
  location: '',
  description: ''
})

// MAC 地址验证
const validateMacAddress = (rule, value, callback) => {
  if (!value) {
    callback(new Error('请输入 MAC 地址'))
    return
  }
  
  // MAC 地址格式：XX:XX:XX:XX:XX:XX 或 XX-XX-XX-XX-XX-XX
  const macPattern = /^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$/
  if (!macPattern.test(value)) {
    callback(new Error('MAC 地址格式不正确，应为 XX:XX:XX:XX:XX:XX'))
  } else {
    callback()
  }
}

const rules = {
  name: [
    { required: true, message: '请输入设备名称', trigger: 'blur' },
    { min: 2, max: 100, message: '长度在 2 到 100 个字符', trigger: 'blur' }
  ],
  mac_address: [
    { required: true, validator: validateMacAddress, trigger: 'blur' }
  ],
  device_type: [
    { required: true, message: '请选择设备类型', trigger: 'change' }
  ]
}

// 加载设备数据（编辑模式）
async function loadDevice() {
  const deviceId = route.params.id
  if (!deviceId) return
  
  try {
    const response = await deviceApi.getDevice(deviceId)
    const device = response.data
    
    Object.keys(formData).forEach(key => {
      if (device[key] !== undefined) {
        formData[key] = device[key]
      }
    })
  } catch (error) {
    ElMessage.error('加载设备信息失败')
    handleBack()
  }
}

// 提交表单
async function handleSubmit() {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    try {
      if (isEdit.value) {
        await deviceApi.updateDevice(route.params.id, formData)
        ElMessage.success('更新设备成功')
      } else {
        await deviceApi.createDevice(formData)
        ElMessage.success('创建设备成功')
      }
      handleBack()
    } catch (error) {
      // 错误已由拦截器处理
    } finally {
      submitting.value = false
    }
  })
}

// 返回列表
function handleBack() {
  router.push({ name: 'DeviceList' })
}

onMounted(() => {
  isEdit.value = !!route.params.id
  if (isEdit.value) {
    loadDevice()
  }
})
</script>

<style scoped>
.device-form-container {
  padding: 8px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.device-form {
  max-width: 600px;
  margin: 0 auto;
}
</style>
