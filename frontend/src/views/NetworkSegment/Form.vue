<template>
  <div class="segment-form-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ isEdit ? '编辑网段' : '创建网段' }}</span>
          <el-button :icon="Back" @click="handleBack">返回</el-button>
        </div>
      </template>

      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="120px"
        style="max-width: 800px"
      >
        <el-form-item label="网段名称" prop="name">
          <el-input 
            v-model="form.name" 
            placeholder="请输入网段名称，如：办公网段"
            maxlength="100"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="所属公司" prop="company">
          <el-input 
            v-model="form.company" 
            placeholder="请输入所属公司（可选）"
            maxlength="100"
            show-word-limit
            clearable
          />
        </el-form-item>

        <el-form-item label="网络地址" prop="network">
          <el-input 
            v-model="form.network" 
            placeholder="请输入网络地址，如：192.168.1.0"
            :disabled="isEdit"
          >
            <template #append>
              <span style="padding: 0 10px">/</span>
            </template>
          </el-input>
          <div class="form-tip">
            网络地址是网段的起始地址（如 192.168.1.0）
          </div>
        </el-form-item>

        <el-form-item label="前缀长度" prop="prefix_length">
          <el-input-number 
            v-model="form.prefix_length" 
            :min="8" 
            :max="30" 
            :disabled="isEdit"
          />
          <div class="form-tip">
            前缀长度决定网段大小（如 24 表示 /24，即 256 个 IP）
          </div>
        </el-form-item>

        <el-form-item label="CIDR 预览">
          <el-tag v-if="form.network && form.prefix_length" type="info" size="large">
            {{ form.network }}/{{ form.prefix_length }}
          </el-tag>
          <span v-else class="form-tip">请先输入网络地址和前缀长度</span>
        </el-form-item>

        <el-form-item label="网关地址" prop="gateway">
          <el-input 
            v-model="form.gateway" 
            placeholder="请输入网关地址（可选），如：192.168.1.1"
          />
          <div class="form-tip">
            网关地址通常是网段的第一个可用 IP
          </div>
        </el-form-item>

        <el-form-item label="使用率阈值" prop="usage_threshold">
          <el-input-number 
            v-model="form.usage_threshold" 
            :min="1" 
            :max="100" 
          />
          <span style="margin-left: 10px">%</span>
          <div class="form-tip">
            当网段使用率达到此阈值时，系统将生成告警
          </div>
        </el-form-item>

        <el-form-item label="描述" prop="description">
          <el-input 
            v-model="form.description" 
            type="textarea" 
            :rows="4"
            placeholder="请输入网段描述信息（可选）"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="submitting" @click="handleSubmit">
            {{ isEdit ? '更新' : '创建' }}
          </el-button>
          <el-button @click="handleBack">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Back } from '@element-plus/icons-vue'
import * as networkApi from '@/api/network'

const router = useRouter()
const route = useRoute()

const formRef = ref(null)
const submitting = ref(false)
const isEdit = computed(() => !!route.params.id)

const form = reactive({
  name: '',
  company: '',
  network: '',
  prefix_length: 24,
  gateway: '',
  usage_threshold: 80,
  description: ''
})

// CIDR 格式验证函数
const validateCIDR = (rule, value, callback) => {
  if (!value) {
    return callback(new Error('请输入网络地址'))
  }
  
  // IPv4 地址格式验证
  const ipv4Regex = /^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/
  const match = value.match(ipv4Regex)
  
  if (!match) {
    return callback(new Error('请输入有效的 IPv4 地址'))
  }
  
  // 检查每个八位组是否在 0-255 范围内
  for (let i = 1; i <= 4; i++) {
    const octet = parseInt(match[i])
    if (octet < 0 || octet > 255) {
      return callback(new Error('IP 地址的每个部分必须在 0-255 之间'))
    }
  }
  
  callback()
}

// 网关地址验证函数
const validateGateway = (rule, value, callback) => {
  if (!value) {
    return callback() // 网关是可选的
  }
  
  // IPv4 地址格式验证
  const ipv4Regex = /^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/
  const match = value.match(ipv4Regex)
  
  if (!match) {
    return callback(new Error('请输入有效的 IPv4 地址'))
  }
  
  // 检查每个八位组是否在 0-255 范围内
  for (let i = 1; i <= 4; i++) {
    const octet = parseInt(match[i])
    if (octet < 0 || octet > 255) {
      return callback(new Error('IP 地址的每个部分必须在 0-255 之间'))
    }
  }
  
  callback()
}

const formRules = {
  name: [
    { required: true, message: '请输入网段名称', trigger: 'blur' },
    { min: 2, max: 100, message: '网段名称长度在 2 到 100 个字符', trigger: 'blur' }
  ],
  network: [
    { required: true, validator: validateCIDR, trigger: 'blur' }
  ],
  prefix_length: [
    { required: true, message: '请输入前缀长度', trigger: 'change' },
    { type: 'number', min: 8, max: 30, message: '前缀长度必须在 8 到 30 之间', trigger: 'change' }
  ],
  gateway: [
    { validator: validateGateway, trigger: 'blur' }
  ],
  usage_threshold: [
    { required: true, message: '请输入使用率阈值', trigger: 'change' },
    { type: 'number', min: 1, max: 100, message: '阈值必须在 1 到 100 之间', trigger: 'change' }
  ],
  description: [
    { max: 500, message: '描述不能超过 500 个字符', trigger: 'blur' }
  ]
}

// 加载网段数据（编辑模式）
async function loadSegment() {
  if (!isEdit.value) return
  
  try {
    const response = await networkApi.getSegment(route.params.id)
    const segment = response.data
    
    Object.assign(form, {
      name: segment.name,
      network: segment.network,
      prefix_length: segment.prefix_length,
      gateway: segment.gateway || '',
      usage_threshold: segment.usage_threshold || 80,
      description: segment.description || ''
    })
  } catch (error) {
    ElMessage.error('加载网段信息失败')
    handleBack()
  }
}

// 提交表单
async function handleSubmit() {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    submitting.value = true

    const data = {
      name: form.name,
      network: form.network,
      prefix_length: form.prefix_length,
      gateway: form.gateway || null,
      usage_threshold: form.usage_threshold,
      description: form.description || null
    }

    if (isEdit.value) {
      await networkApi.updateSegment(route.params.id, data)
      ElMessage.success('更新网段成功')
    } else {
      await networkApi.createSegment(data)
      ElMessage.success('创建网段成功')
    }

    handleBack()
  } catch (error) {
    // 错误已由拦截器处理
  } finally {
    submitting.value = false
  }
}

// 返回列表
function handleBack() {
  router.push({ name: 'SegmentList' })
}

onMounted(() => {
  loadSegment()
})
</script>

<style scoped>
.segment-form-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
  line-height: 1.5;
}
</style>
