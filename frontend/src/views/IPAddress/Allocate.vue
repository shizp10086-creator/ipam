<template>
  <div class="ip-allocate-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>分配 IP 地址</span>
          <el-button @click="handleBack">
            <el-icon><Back /></el-icon>
            返回
          </el-button>
        </div>
      </template>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="120px"
        style="max-width: 600px"
      >
        <el-form-item label="选择网段" prop="segment_id">
          <el-select
            v-model="form.segment_id"
            placeholder="请选择网段"
            style="width: 100%"
            @change="handleSegmentChange"
          >
            <el-option
              v-for="segment in segments"
              :key="segment.id"
              :label="`${segment.name} (${segment.network}/${segment.prefix_length})`"
              :value="segment.id"
            >
              <div style="display: flex; justify-content: space-between">
                <span>{{ segment.name }}</span>
                <span style="color: #8492a6; font-size: 13px">
                  {{ segment.network }}/{{ segment.prefix_length }}
                </span>
              </div>
            </el-option>
          </el-select>
        </el-form-item>

        <el-form-item v-if="selectedSegment" label="网段信息">
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="网段名称">
              {{ selectedSegment.name }}
            </el-descriptions-item>
            <el-descriptions-item label="网段地址">
              {{ selectedSegment.network }}/{{ selectedSegment.prefix_length }}
            </el-descriptions-item>
            <el-descriptions-item label="网关">
              {{ selectedSegment.gateway || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="使用率">
              <el-progress
                :percentage="calculateUsageRate(selectedSegment)"
                :color="getUsageColor(calculateUsageRate(selectedSegment))"
              />
            </el-descriptions-item>
          </el-descriptions>
        </el-form-item>

        <el-form-item label="IP 地址" prop="ip_address">
          <el-input
            v-model="form.ip_address"
            placeholder="请输入 IP 地址，例如：192.168.1.10"
            @blur="handleIPBlur"
          >
            <template #append>
              <el-button
                :loading="checkingConflict"
                @click="handleCheckConflict"
              >
                检测冲突
              </el-button>
            </template>
          </el-input>
          <div v-if="conflictResult" style="margin-top: 5px">
            <el-alert
              v-if="conflictResult.has_conflict"
              :title="conflictResult.message"
              type="error"
              :closable="false"
            >
              <template v-if="conflictResult.conflict_type === 'logical'">
                <p>逻辑冲突：该 IP 已在数据库中被标记为使用或保留</p>
                <p v-if="conflictResult.details">
                  {{ conflictResult.details }}
                </p>
              </template>
              <template v-else-if="conflictResult.conflict_type === 'physical'">
                <p>物理冲突：该 IP 在网络中已被其他设备使用</p>
                <p v-if="conflictResult.details">
                  {{ conflictResult.details }}
                </p>
              </template>
            </el-alert>
            <el-alert
              v-else
              title="未检测到冲突，可以分配"
              type="success"
              :closable="false"
            />
          </div>
        </el-form-item>

        <el-form-item label="选择设备" prop="device_id">
          <el-select
            v-model="form.device_id"
            placeholder="请选择设备"
            filterable
            style="width: 100%"
          >
            <el-option
              v-for="device in devices"
              :key="device.id"
              :label="`${device.name} (${device.mac_address})`"
              :value="device.id"
            >
              <div style="display: flex; justify-content: space-between">
                <span>{{ device.name }}</span>
                <span style="color: #8492a6; font-size: 13px">
                  {{ device.mac_address }}
                </span>
              </div>
            </el-option>
          </el-select>
        </el-form-item>

        <el-form-item v-if="selectedDevice" label="设备信息">
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="设备名称">
              {{ selectedDevice.name }}
            </el-descriptions-item>
            <el-descriptions-item label="MAC 地址">
              {{ selectedDevice.mac_address }}
            </el-descriptions-item>
            <el-descriptions-item label="设备类型">
              {{ selectedDevice.device_type || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="责任人">
              {{ selectedDevice.owner || '-' }}
            </el-descriptions-item>
          </el-descriptions>
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            @click="handleSubmit"
            :loading="submitting"
            :disabled="conflictResult && conflictResult.has_conflict"
          >
            分配 IP
          </el-button>
          <el-button @click="handleReset">重置</el-button>
          <el-button @click="handleBack">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Back } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { allocateIP, checkConflict } from '@/api/ip'
import { getSegments } from '@/api/network'
import { getDevices } from '@/api/device'

const router = useRouter()
const formRef = ref(null)

// 数据
const segments = ref([])
const devices = ref([])
const submitting = ref(false)
const checkingConflict = ref(false)
const conflictResult = ref(null)

// 表单数据
const form = reactive({
  segment_id: null,
  ip_address: '',
  device_id: null
})

// 选中的网段和设备
const selectedSegment = computed(() => {
  return segments.value.find(s => s.id === form.segment_id)
})

const selectedDevice = computed(() => {
  return devices.value.find(d => d.id === form.device_id)
})

// IP 地址验证规则
const validateIP = (rule, value, callback) => {
  if (!value) {
    callback(new Error('请输入 IP 地址'))
    return
  }
  
  // IP 地址格式验证
  const ipPattern = /^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/
  if (!ipPattern.test(value)) {
    callback(new Error('IP 地址格式不正确'))
    return
  }
  
  const parts = value.split('.')
  for (let part of parts) {
    const num = parseInt(part)
    if (num < 0 || num > 255) {
      callback(new Error('IP 地址每段必须在 0-255 之间'))
      return
    }
  }
  
  callback()
}

// 表单验证规则
const rules = {
  segment_id: [
    { required: true, message: '请选择网段', trigger: 'change' }
  ],
  ip_address: [
    { required: true, validator: validateIP, trigger: 'blur' }
  ],
  device_id: [
    { required: true, message: '请选择设备', trigger: 'change' }
  ]
}

// 计算使用率
const calculateUsageRate = (segment) => {
  if (!segment || !segment.total_ips) return 0
  const used = segment.used_ips || 0
  const total = segment.total_ips || 1
  return Math.round((used / total) * 100)
}

// 获取使用率颜色
const getUsageColor = (rate) => {
  if (rate < 60) return '#67c23a'
  if (rate < 80) return '#e6a23c'
  return '#f56c6c'
}

// 加载网段列表
const loadSegments = async () => {
  try {
    const res = await getSegments()
    if (res.code === 200) {
      segments.value = res.data.items || res.data
    }
  } catch (error) {
    ElMessage.error('加载网段列表失败')
    console.error(error)
  }
}

// 加载设备列表
const loadDevices = async () => {
  try {
    const res = await getDevices({ page_size: 1000 })
    if (res.code === 200) {
      devices.value = res.data.items || res.data
    }
  } catch (error) {
    ElMessage.error('加载设备列表失败')
    console.error(error)
  }
}

// 网段变化
const handleSegmentChange = () => {
  // 清空冲突检测结果
  conflictResult.value = null
}

// IP 输入失焦
const handleIPBlur = () => {
  // 清空之前的冲突检测结果
  conflictResult.value = null
}

// 检测冲突
const handleCheckConflict = async () => {
  if (!form.ip_address) {
    ElMessage.warning('请先输入 IP 地址')
    return
  }

  // 验证 IP 格式
  const ipPattern = /^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/
  if (!ipPattern.test(form.ip_address)) {
    ElMessage.error('IP 地址格式不正确')
    return
  }

  checkingConflict.value = true
  try {
    const res = await checkConflict({
      ip_address: form.ip_address,
      segment_id: form.segment_id
    })
    
    if (res.code === 200) {
      conflictResult.value = res.data
      
      if (res.data.has_conflict) {
        ElMessage.warning('检测到 IP 冲突')
      } else {
        ElMessage.success('未检测到冲突')
      }
    }
  } catch (error) {
    ElMessage.error('冲突检测失败')
    console.error(error)
  } finally {
    checkingConflict.value = false
  }
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    // 检查是否有冲突
    if (conflictResult.value && conflictResult.value.has_conflict) {
      ElMessage.error('存在 IP 冲突，无法分配')
      return
    }

    // 如果没有进行冲突检测，先检测
    if (!conflictResult.value) {
      ElMessage.warning('请先进行冲突检测')
      return
    }

    submitting.value = true
    try {
      const res = await allocateIP({
        ip_address: form.ip_address,
        segment_id: form.segment_id,
        device_id: form.device_id
      })

      if (res.code === 200 || res.code === 201) {
        ElMessage.success('IP 分配成功')
        router.push('/ip/list')
      }
    } catch (error) {
      ElMessage.error(error.response?.data?.message || '分配失败')
      console.error(error)
    } finally {
      submitting.value = false
    }
  })
}

// 重置表单
const handleReset = () => {
  formRef.value?.resetFields()
  conflictResult.value = null
}

// 返回
const handleBack = () => {
  router.back()
}

// 初始化
onMounted(() => {
  loadSegments()
  loadDevices()
})
</script>

<style scoped>
.ip-allocate-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
