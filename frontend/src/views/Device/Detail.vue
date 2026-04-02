<template>
  <div class="device-detail-container">
    <el-card v-loading="loading">
      <template #header>
        <div class="card-header">
          <span>设备详情</span>
          <div>
            <el-button 
              v-if="canEdit" 
              type="primary" 
              :icon="Edit" 
              @click="handleEdit"
            >
              编辑
            </el-button>
            <el-button @click="handleBack">返回</el-button>
          </div>
        </div>
      </template>

      <div class="device-info" v-if="device">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="设备 ID">
            {{ device.id }}
          </el-descriptions-item>
          <el-descriptions-item label="设备名称">
            {{ device.name }}
          </el-descriptions-item>
          <el-descriptions-item label="MAC 地址">
            <el-tag>{{ device.mac_address }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="设备类型">
            {{ device.device_type || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="制造商">
            {{ device.manufacturer || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="型号">
            {{ device.model || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="责任人">
            {{ device.owner || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="部门">
            {{ device.department || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="位置" :span="2">
            {{ device.location || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">
            {{ device.description || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ formatDate(device.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="更新时间">
            {{ formatDate(device.updated_at) }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-card>

    <!-- 关联的 IP 地址 -->
    <el-card class="ip-list-card" v-loading="ipLoading">
      <template #header>
        <span>关联的 IP 地址</span>
      </template>

      <el-table :data="ipAddresses" border stripe v-if="ipAddresses.length > 0">
        <el-table-column prop="ip_address" label="IP 地址" width="150" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="网段" min-width="200">
          <template #default="{ row }">
            {{ row.segment?.name || '-' }}
            <span v-if="row.segment" class="text-muted">
              ({{ row.segment.network }}/{{ row.segment.prefix_length }})
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="allocated_at" label="分配时间" width="180">
          <template #default="{ row }">
            {{ row.allocated_at ? formatDate(row.allocated_at) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" align="center">
          <template #default="{ row }">
            <el-button 
              size="small" 
              @click="viewIP(row)"
            >
              查看
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-else description="该设备暂无关联的 IP 地址" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Edit } from '@element-plus/icons-vue'
import * as deviceApi from '@/api/device'
import { formatDate } from '@/utils/formatters'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const loading = ref(false)
const ipLoading = ref(false)
const device = ref(null)
const ipAddresses = ref([])

const canEdit = computed(() => authStore.userRole === 'admin')

// 获取设备详情
async function fetchDevice() {
  loading.value = true
  try {
    const response = await deviceApi.getDevice(route.params.id)
    device.value = response.data
  } catch (error) {
    ElMessage.error('获取设备详情失败')
    handleBack()
  } finally {
    loading.value = false
  }
}

// 获取设备关联的 IP 地址
async function fetchDeviceIPs() {
  ipLoading.value = true
  try {
    const response = await deviceApi.getDeviceIPs(route.params.id)
    ipAddresses.value = response.data || []
  } catch (error) {
    ElMessage.error('获取设备 IP 列表失败')
  } finally {
    ipLoading.value = false
  }
}

// 获取状态类型
function getStatusType(status) {
  const typeMap = {
    'available': 'success',
    'used': 'warning',
    'reserved': 'info'
  }
  return typeMap[status] || 'info'
}

// 获取状态文本
function getStatusText(status) {
  const textMap = {
    'available': '空闲',
    'used': '已用',
    'reserved': '保留'
  }
  return textMap[status] || status
}

// 查看 IP 详情
function viewIP(ip) {
  router.push({ name: 'IPDetail', params: { id: ip.id } })
}

// 编辑设备
function handleEdit() {
  router.push({ name: 'DeviceEdit', params: { id: route.params.id } })
}

// 返回列表
function handleBack() {
  router.push({ name: 'DeviceList' })
}

onMounted(() => {
  fetchDevice()
  fetchDeviceIPs()
})
</script>

<style scoped>
.device-detail-container {
  padding: 8px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.device-info {
  margin-bottom: 20px;
}

.ip-list-card {
  margin-top: 16px;
}

.text-muted {
  color: #909399;
  font-size: 12px;
}
</style>
