<template>
  <div class="ip-list-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>IP 地址管理</span>
          <div>
            <el-button type="primary" @click="handleAllocate" v-if="canWrite">
              <el-icon><Plus /></el-icon>
              分配 IP
            </el-button>
          </div>
        </div>
      </template>

      <!-- 搜索筛选区域 -->
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="网段">
          <el-select
            v-model="searchForm.segment_id"
            placeholder="选择网段"
            clearable
            style="width: 200px"
          >
            <el-option
              v-for="segment in segments"
              :key="segment.id"
              :label="`${segment.name} (${segment.network}/${segment.prefix_length})`"
              :value="segment.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="状态">
          <el-select
            v-model="searchForm.status"
            placeholder="选择状态"
            clearable
            style="width: 150px"
          >
            <el-option label="空闲" value="available" />
            <el-option label="已用" value="used" />
            <el-option label="保留" value="reserved" />
          </el-select>
        </el-form-item>

        <el-form-item label="IP 地址">
          <el-input
            v-model="searchForm.ip_address"
            placeholder="输入 IP 地址"
            clearable
            style="width: 200px"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>

      <!-- IP 地址列表表格 -->
      <el-table
        :data="ipList"
        v-loading="loading"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="ip_address" label="IP 地址" width="150" />
        
        <el-table-column label="状态" width="150">
          <template #default="{ row }">
            <el-select
              v-if="canWrite"
              v-model="row.status"
              size="small"
              @change="handleStatusChange(row)"
              style="width: 100px"
            >
              <el-option label="空闲" value="available">
                <el-tag type="success" size="small">空闲</el-tag>
              </el-option>
              <el-option label="已用" value="used">
                <el-tag type="danger" size="small">已用</el-tag>
              </el-option>
              <el-option label="保留" value="reserved">
                <el-tag type="warning" size="small">保留</el-tag>
              </el-option>
            </el-select>
            <el-tag v-else :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="网段" width="200">
          <template #default="{ row }">
            <span v-if="row.segment">
              {{ row.segment.name }} ({{ row.segment.network }}/{{ row.segment.prefix_length }})
            </span>
          </template>
        </el-table-column>

        <el-table-column label="关联设备" width="280">
          <template #default="{ row }">
            <el-select
              v-if="canWrite"
              v-model="row.device_id"
              size="small"
              clearable
              filterable
              placeholder="选择设备"
              @change="handleDeviceChange(row)"
              style="width: 260px"
            >
              <el-option
                v-for="device in devices"
                :key="device.id"
                :label="`${device.name} (${device.mac_address})`"
                :value="device.id"
              >
                <span>{{ device.name }}</span>
                <span style="float: right; color: #8492a6; font-size: 12px">
                  {{ device.mac_address }}
                </span>
              </el-option>
            </el-select>
            <span v-else>
              <span v-if="row.device">
                {{ row.device.name }}
                <el-tag size="small" style="margin-left: 5px">
                  {{ row.device.mac_address }}
                </el-tag>
              </span>
              <span v-else style="color: #909399">-</span>
            </span>
          </template>
        </el-table-column>

        <el-table-column label="在线状态" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.last_seen" :type="row.is_online ? 'success' : 'info'" size="small">
              {{ row.is_online ? '在线' : '离线' }}
            </el-tag>
            <span v-else style="color: #909399">未扫描</span>
          </template>
        </el-table-column>

        <el-table-column label="最后扫描" width="180">
          <template #default="{ row }">
            {{ row.last_seen ? formatDateTime(row.last_seen) : '-' }}
          </template>
        </el-table-column>

        <el-table-column label="分配时间" width="180">
          <template #default="{ row }">
            {{ row.allocated_at ? formatDateTime(row.allocated_at) : '-' }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              link
              @click="handleViewDetail(row)"
            >
              详情
            </el-button>

            <el-button
              v-if="row.status === 'available' && canWrite"
              type="warning"
              size="small"
              link
              @click="handleReserve(row)"
            >
              保留
            </el-button>

            <el-button
              v-if="row.status === 'reserved' && canWrite"
              type="success"
              size="small"
              link
              @click="handleCancelReserve(row)"
            >
              取消保留
            </el-button>

            <el-button
              v-if="row.status === 'used' && canWrite"
              type="danger"
              size="small"
              link
              @click="handleRelease(row)"
            >
              回收
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.page_size"
        :page-sizes="[10, 20, 50, 100]"
        :total="pagination.total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
        style="margin-top: 20px; justify-content: flex-end"
      />
    </el-card>

    <!-- IP 详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="IP 地址详情"
      width="800px"
    >
      <IPDetail v-if="detailDialogVisible" :ip-id="currentIPId" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh } from '@element-plus/icons-vue'
import { getIPs, updateIP, releaseIP } from '@/api/ip'
import { getSegments } from '@/api/network'
import { getDevices } from '@/api/device'
import { formatDateTime } from '@/utils/formatters'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
import IPDetail from './Detail.vue'

const router = useRouter()
const authStore = useAuthStore()

// 权限检查
const canWrite = computed(() => {
  const role = authStore.userRole
  console.log('当前用户角色:', role)
  console.log('canWrite:', role === 'admin' || role === 'user')
  return role === 'admin' || role === 'user'
})

// 数据
const loading = ref(false)
const ipList = ref([])
const segments = ref([])
const devices = ref([])
const detailDialogVisible = ref(false)
const currentIPId = ref(null)

// 搜索表单
const searchForm = reactive({
  segment_id: null,
  status: null,
  ip_address: ''
})

// 分页
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

// 获取状态类型
const getStatusType = (status) => {
  const typeMap = {
    available: 'success',
    used: 'danger',
    reserved: 'warning'
  }
  return typeMap[status] || 'info'
}

// 获取状态文本
const getStatusText = (status) => {
  const textMap = {
    available: '空闲',
    used: '已用',
    reserved: '保留'
  }
  return textMap[status] || status
}

// 加载网段列表
const loadSegments = async () => {
  try {
    const res = await getSegments()
    if (res.code === 200) {
      segments.value = res.data.items || res.data
    }
  } catch (error) {
    console.error('加载网段列表失败:', error)
  }
}

// 加载设备列表
const loadDevices = async () => {
  try {
    const res = await getDevices({ page: 1, page_size: 1000 })
    console.log('设备列表响应:', res)
    if (res.code === 200) {
      devices.value = res.data.items || []
      console.log('设备列表数量:', devices.value.length)
    }
  } catch (error) {
    console.error('加载设备列表失败:', error)
  }
}

// 加载 IP 列表
const loadIPList = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.page_size,
      ...searchForm
    }
    
    // 移除空值
    Object.keys(params).forEach(key => {
      if (params[key] === null || params[key] === '') {
        delete params[key]
      }
    })

    const res = await getIPs(params)
    console.log('IP列表响应:', res)
    if (res.code === 200) {
      ipList.value = res.data.items || []
      pagination.total = res.data.total || 0
      console.log('IP列表数量:', ipList.value.length)
      if (ipList.value.length > 0) {
        console.log('第一个IP示例:', ipList.value[0])
      }
    }
  } catch (error) {
    ElMessage.error('加载 IP 列表失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  loadIPList()
}

// 重置
const handleReset = () => {
  searchForm.segment_id = null
  searchForm.status = null
  searchForm.ip_address = ''
  pagination.page = 1
  loadIPList()
}

// 分页变化
const handleSizeChange = () => {
  pagination.page = 1
  loadIPList()
}

const handlePageChange = () => {
  loadIPList()
}

// 处理状态变更
const handleStatusChange = async (row) => {
  try {
    const res = await updateIP(row.id, { status: row.status })
    if (res.code === 200) {
      ElMessage.success('状态更新成功')
      loadIPList()
    }
  } catch (error) {
    ElMessage.error('状态更新失败')
    console.error(error)
    // 恢复原状态
    loadIPList()
  }
}

// 处理设备变更
const handleDeviceChange = async (row) => {
  try {
    const res = await updateIP(row.id, { device_id: row.device_id })
    if (res.code === 200) {
      ElMessage.success('关联设备更新成功')
      loadIPList()
    }
  } catch (error) {
    ElMessage.error('关联设备更新失败')
    console.error(error)
    // 恢复原设备
    loadIPList()
  }
}

// 分配 IP
const handleAllocate = () => {
  router.push('/ip/allocate')
}

// 查看详情
const handleViewDetail = (row) => {
  currentIPId.value = row.id
  detailDialogVisible.value = true
}

// 保留 IP
const handleReserve = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要保留 IP 地址 ${row.ip_address} 吗？`,
      '确认保留',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const res = await updateIP(row.id, { status: 'reserved' })
    if (res.code === 200) {
      ElMessage.success('保留成功')
      loadIPList()
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('保留失败')
      console.error(error)
    }
  }
}

// 取消保留
const handleCancelReserve = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要取消保留 IP 地址 ${row.ip_address} 吗？`,
      '确认取消保留',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const res = await updateIP(row.id, { status: 'available' })
    if (res.code === 200) {
      ElMessage.success('取消保留成功')
      loadIPList()
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('取消保留失败')
      console.error(error)
    }
  }
}

// 回收 IP
const handleRelease = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要回收 IP 地址 ${row.ip_address} 吗？回收后将解除与设备的关联。`,
      '确认回收',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const res = await releaseIP({ ip_id: row.id })
    if (res.code === 200) {
      ElMessage.success('回收成功')
      loadIPList()
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('回收失败')
      console.error(error)
    }
  }
}

// 初始化
onMounted(() => {
  loadSegments()
  loadDevices()
  loadIPList()
})
</script>

<style scoped>
.ip-list-container {
  padding: 12px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-form {
  margin-bottom: 12px;
}
</style>
