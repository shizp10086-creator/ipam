<template>
  <div class="segment-detail-container">
    <!-- 基本信息卡片 -->
    <el-card v-loading="loading">
      <template #header>
        <div class="card-header">
          <span>网段详情</span>
          <div>
            <el-button 
              v-if="canEdit" 
              type="primary" 
              :icon="Edit" 
              @click="handleEdit"
            >
              编辑
            </el-button>
            <el-button :icon="Back" @click="handleBack">返回</el-button>
          </div>
        </div>
      </template>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="网段 ID">
          {{ segment.id }}
        </el-descriptions-item>
        <el-descriptions-item label="网段名称">
          {{ segment.name }}
        </el-descriptions-item>
        <el-descriptions-item label="所属公司">
          {{ segment.company || '未设置' }}
        </el-descriptions-item>
        <el-descriptions-item label="CIDR">
          <el-tag type="info" size="large">
            {{ segment.network }}/{{ segment.prefix_length }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="网关地址">
          {{ segment.gateway || '未设置' }}
        </el-descriptions-item>
        <el-descriptions-item label="使用率阈值">
          {{ segment.usage_threshold }}%
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ formatDate(segment.created_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">
          {{ segment.description || '无' }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 统计信息卡片 -->
    <el-card v-loading="statsLoading" class="stats-card">
      <template #header>
        <div class="card-header">
          <span>统计信息</span>
          <el-button :icon="Refresh" @click="loadStats">刷新</el-button>
        </div>
      </template>

      <el-row :gutter="20" class="stats-row">
        <el-col :span="4">
          <div class="stat-item">
            <div class="stat-label">总 IP 数</div>
            <div class="stat-value">{{ stats.total_ips || 0 }}</div>
          </div>
        </el-col>
        <el-col :span="4">
          <div class="stat-item clickable" @click="filterByStatus('used')">
            <div class="stat-label">已用 IP</div>
            <div class="stat-value" style="color: #409eff">
              {{ stats.used_ips || 0 }}
            </div>
          </div>
        </el-col>
        <el-col :span="4">
          <div class="stat-item">
            <div class="stat-label">可用 IP</div>
            <div class="stat-value" style="color: #67c23a">
              {{ stats.available_ips || 0 }}
            </div>
            <div class="stat-hint">计算值</div>
          </div>
        </el-col>
        <el-col :span="4">
          <div class="stat-item clickable" @click="filterByStatus('reserved')">
            <div class="stat-label">保留 IP</div>
            <div class="stat-value" style="color: #e6a23c">
              {{ stats.reserved_ips || 0 }}
            </div>
          </div>
        </el-col>
        <el-col :span="4">
          <div class="stat-item clickable" @click="filterByOnlineStatus(true)">
            <div class="stat-label">在线 IP</div>
            <div class="stat-value" style="color: #67c23a">
              {{ stats.online_ips || 0 }}
            </div>
          </div>
        </el-col>
        <el-col :span="4">
          <div class="stat-item clickable" @click="filterByOnlineStatus(false)">
            <div class="stat-label">离线 IP</div>
            <div class="stat-value" style="color: #909399">
              {{ stats.offline_ips || 0 }}
            </div>
          </div>
        </el-col>
      </el-row>

      <el-divider />

      <div class="usage-section">
        <div class="usage-label">
          <span>使用率</span>
          <span class="usage-percentage">{{ stats.usage_rate || 0 }}%</span>
        </div>
        <el-progress 
          :percentage="stats.usage_rate || 0" 
          :color="getUsageColor()"
          :stroke-width="20"
        />
        <div class="usage-tip" v-if="stats.usage_rate >= segment.usage_threshold">
          <el-alert
            title="警告：网段使用率已达到或超过告警阈值！"
            type="warning"
            :closable="false"
            show-icon
          />
        </div>
      </div>
    </el-card>

    <!-- IP 地址列表卡片 -->
    <el-card class="ip-list-card">
      <template #header>
        <div class="card-header">
          <span>
            IP 地址列表 [v2.0]
            <el-tag 
              v-if="ipFilter.status" 
              type="primary" 
              size="small" 
              closable 
              @close="clearStatusFilter"
              style="margin-left: 10px"
            >
              状态: {{ getStatusText(ipFilter.status) }}
            </el-tag>
            <el-tag 
              v-if="ipFilter.is_online !== null" 
              type="success" 
              size="small" 
              closable 
              @close="clearOnlineFilter"
              style="margin-left: 10px"
            >
              {{ ipFilter.is_online ? '在线' : '离线' }}
            </el-tag>
          </span>
          <div>
            <el-button 
              v-if="canEdit && selectedIPs.length > 0"
              type="warning"
              @click="showBatchUpdateDialog"
              style="margin-right: 10px;"
            >
              批量更新状态 ({{ selectedIPs.length }})
            </el-button>
            <el-button 
              type="primary" 
              @click="handleScanSegment"
              style="margin-right: 10px;"
            >
              <el-icon><Search /></el-icon>
              扫描网段
            </el-button>
            <el-select 
              v-model="ipFilter.status" 
              placeholder="筛选状态" 
              clearable
              style="width: 150px; margin-right: 10px"
              @change="loadIPs"
            >
              <el-option label="空闲" value="available" />
              <el-option label="已用" value="used" />
              <el-option label="保留" value="reserved" />
            </el-select>
            <el-button :icon="Refresh" @click="loadIPs">刷新列表</el-button>
          </div>
        </div>
      </template>

      <el-table 
        :data="ipAddresses" 
        v-loading="ipLoading" 
        border 
        stripe
        max-height="500"
        @selection-change="handleSelectionChange"
      >
        <el-table-column 
          v-if="canEdit"
          type="selection" 
          width="55" 
        />
        <el-table-column prop="ip_address" label="IP 地址" width="150" />
        <el-table-column label="状态" width="150">
          <template #default="{ row }">
            <el-select
              v-if="canEdit"
              v-model="row.status"
              size="small"
              @change="handleStatusChange(row)"
              style="width: 100px"
            >
              <el-option label="空闲" value="available">
                <el-tag type="success" size="small">空闲</el-tag>
              </el-option>
              <el-option label="已用" value="used">
                <el-tag type="primary" size="small">已用</el-tag>
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
        <el-table-column label="关联设备" min-width="280">
          <template #default="{ row }">
            <el-select
              v-if="canEdit"
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
                {{ row.device.name }} ({{ row.device.mac_address }})
              </span>
              <span v-else class="text-muted">未关联</span>
            </span>
          </template>
        </el-table-column>
        <el-table-column label="在线状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.last_seen" :type="row.is_online ? 'success' : 'info'" size="small">
              {{ row.is_online ? '在线' : '离线' }}
            </el-tag>
            <span v-else class="text-muted">未扫描</span>
          </template>
        </el-table-column>
        <el-table-column prop="last_seen" label="最后扫描" width="180">
          <template #default="{ row }">
            {{ row.last_seen ? formatDate(row.last_seen) : '未扫描' }}
          </template>
        </el-table-column>
        <el-table-column prop="allocated_at" label="分配时间" width="180">
          <template #default="{ row }">
            {{ row.allocated_at ? formatDate(row.allocated_at) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button 
              size="small" 
              :icon="View" 
              @click="handleViewIP(row)"
            >
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- IP 列表分页 -->
      <el-pagination
        v-model:current-page="ipPagination.page"
        v-model:page-size="ipPagination.pageSize"
        :total="ipPagination.total"
        :page-sizes="[20, 50, 100, 200]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="loadIPs"
        @current-change="loadIPs"
        class="pagination"
      />
    </el-card>

    <!-- IP 详情对话框 -->
    <el-dialog
      v-model="ipDetailDialogVisible"
      title="IP 地址详情"
      width="900px"
      :close-on-click-modal="false"
    >
      <IPDetail v-if="ipDetailDialogVisible" :ip-id="currentIPId" />
    </el-dialog>

    <!-- 批量更新状态对话框 -->
    <el-dialog
      v-model="batchUpdateDialogVisible"
      title="批量更新 IP 状态"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form label-width="100px">
        <el-form-item label="选中数量">
          <el-tag type="info">{{ selectedIPs.length }} 个 IP</el-tag>
        </el-form-item>
        <el-form-item label="目标状态">
          <el-radio-group v-model="batchUpdateStatus">
            <el-radio label="available">
              <el-tag type="success">空闲</el-tag>
            </el-radio>
            <el-radio label="used">
              <el-tag type="primary">已用</el-tag>
            </el-radio>
            <el-radio label="reserved">
              <el-tag type="warning">保留</el-tag>
            </el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="batchUpdateDialogVisible = false">取消</el-button>
        <el-button 
          type="primary" 
          @click="handleBatchUpdate"
          :loading="batchUpdating"
        >
          确定更新
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Back, Edit, Refresh, View, Search } from '@element-plus/icons-vue'
import * as networkApi from '@/api/network'
import * as ipApi from '@/api/ip'
import { getDevices } from '@/api/device'
import { formatDate } from '@/utils/formatters'
import { useAuthStore } from '@/stores/auth'
import IPDetail from '@/views/IPAddress/Detail.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const loading = ref(false)
const statsLoading = ref(false)
const ipLoading = ref(false)

const segment = ref({})
const stats = ref({})
const ipAddresses = ref([])
const devices = ref([])
const ipDetailDialogVisible = ref(false)
const currentIPId = ref(null)
const selectedIPs = ref([])
const batchUpdateDialogVisible = ref(false)
const batchUpdateStatus = ref('available')
const batchUpdating = ref(false)

const ipFilter = reactive({
  status: '',
  is_online: null  // null=全部, true=在线, false=离线
})

const ipPagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const canEdit = computed(() => authStore.userRole === 'admin')

// 加载网段基本信息
async function loadSegment() {
  loading.value = true
  try {
    const response = await networkApi.getSegment(route.params.id)
    segment.value = response.data
  } catch (error) {
    ElMessage.error('加载网段信息失败')
    handleBack()
  } finally {
    loading.value = false
  }
}

// 加载统计信息
async function loadStats() {
  statsLoading.value = true
  try {
    const response = await networkApi.getSegmentStats(route.params.id)
    stats.value = response.data
  } catch (error) {
    ElMessage.error('加载统计信息失败')
  } finally {
    statsLoading.value = false
  }
}

// 加载 IP 地址列表
async function loadIPs() {
  ipLoading.value = true
  try {
    const params = {
      segment_id: parseInt(route.params.id),
      page: ipPagination.page,
      page_size: ipPagination.pageSize
    }
    
    if (ipFilter.status) {
      params.status = ipFilter.status
    }
    
    if (ipFilter.is_online !== null) {
      params.is_online = ipFilter.is_online
    }
    
    const response = await ipApi.getIPs(params)
    
    // 处理响应数据
    if (response.code === 200 && response.data) {
      ipAddresses.value = response.data.items || []
      ipPagination.total = response.data.total || 0
    } else {
      ipAddresses.value = []
      ipPagination.total = 0
    }
  } catch (error) {
    console.error('Failed to load IPs:', error)
    ElMessage.error('加载 IP 地址列表失败')
    ipAddresses.value = []
    ipPagination.total = 0
  } finally {
    ipLoading.value = false
  }
}

// 加载设备列表
async function loadDevices() {
  try {
    const response = await getDevices({ page: 1, page_size: 1000 })
    if (response.code === 200) {
      devices.value = response.data.items || []
    }
  } catch (error) {
    console.error('加载设备列表失败:', error)
  }
}

// 处理状态变更
async function handleStatusChange(row) {
  try {
    const response = await ipApi.updateIP(row.id, { status: row.status })
    if (response.code === 200) {
      ElMessage.success('状态更新成功')
      loadIPs()
      loadStats() // 刷新统计信息
    }
  } catch (error) {
    ElMessage.error('状态更新失败')
    console.error(error)
    loadIPs() // 恢复原状态
  }
}

// 处理设备变更
async function handleDeviceChange(row) {
  try {
    const response = await ipApi.updateIP(row.id, { device_id: row.device_id })
    if (response.code === 200) {
      ElMessage.success('关联设备更新成功')
      loadIPs()
    }
  } catch (error) {
    ElMessage.error('关联设备更新失败')
    console.error(error)
    loadIPs() // 恢复原设备
  }
}

// 获取使用率颜色
function getUsageColor() {
  const percentage = stats.value.usage_rate || 0
  const threshold = segment.value.usage_threshold || 80
  
  if (percentage >= threshold) {
    return '#f56c6c' // 红色
  } else if (percentage >= threshold * 0.8) {
    return '#e6a23c' // 橙色
  } else {
    return '#67c23a' // 绿色
  }
}

// 获取状态类型
function getStatusType(status) {
  const typeMap = {
    available: 'success',
    used: 'primary',
    reserved: 'warning'
  }
  return typeMap[status] || 'info'
}

// 获取状态文本
function getStatusText(status) {
  const textMap = {
    available: '空闲',
    used: '已用',
    reserved: '保留'
  }
  return textMap[status] || status
}

// 编辑网段
function handleEdit() {
  router.push({ name: 'SegmentEdit', params: { id: route.params.id } })
}

// 查看 IP 详情
function handleViewIP(row) {
  currentIPId.value = row.id
  ipDetailDialogVisible.value = true
}

// 返回列表
function handleBack() {
  router.push({ name: 'SegmentList' })
}

// 扫描网段
function handleScanSegment() {
  router.push({
    name: 'IPScanner',
    query: { segment_id: route.params.id }
  })
}

// 处理选择变化
function handleSelectionChange(selection) {
  selectedIPs.value = selection
}

// 显示批量更新对话框
function showBatchUpdateDialog() {
  if (selectedIPs.value.length === 0) {
    ElMessage.warning('请先选择要更新的 IP 地址')
    return
  }
  batchUpdateDialogVisible.value = true
}

// 批量更新状态
async function handleBatchUpdate() {
  if (!batchUpdateStatus.value) {
    ElMessage.warning('请选择目标状态')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要将选中的 ${selectedIPs.value.length} 个 IP 地址状态更新为"${getStatusText(batchUpdateStatus.value)}"吗？`,
      '确认批量更新',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    batchUpdating.value = true
    
    const ipIds = selectedIPs.value.map(ip => ip.id)
    const response = await ipApi.batchUpdateIPStatus({
      ip_ids: ipIds,
      status: batchUpdateStatus.value
    })

    if (response.code === 200) {
      const { success_count, failed_count } = response.data
      
      if (failed_count === 0) {
        ElMessage.success(`批量更新成功：${success_count} 个 IP 已更新`)
      } else {
        ElMessage.warning(`批量更新完成：${success_count} 个成功，${failed_count} 个失败`)
      }
      
      batchUpdateDialogVisible.value = false
      selectedIPs.value = []
      loadIPs()
      loadStats()
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量更新失败')
      console.error(error)
    }
  } finally {
    batchUpdating.value = false
  }
}

// 按状态筛选
function filterByStatus(status) {
  ipFilter.status = status
  ipFilter.is_online = null  // 清除在线状态筛选
  ipPagination.page = 1  // 重置到第一页
  loadIPs()
  
  // 滚动到 IP 列表
  const ipListCard = document.querySelector('.ip-list-card')
  if (ipListCard) {
    ipListCard.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

// 按在线状态筛选
function filterByOnlineStatus(isOnline) {
  ipFilter.is_online = isOnline
  ipFilter.status = ''  // 清除状态筛选
  ipPagination.page = 1  // 重置到第一页
  loadIPs()
  
  // 滚动到 IP 列表
  const ipListCard = document.querySelector('.ip-list-card')
  if (ipListCard) {
    ipListCard.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

// 清除状态筛选
function clearStatusFilter() {
  ipFilter.status = ''
  ipPagination.page = 1
  loadIPs()
}

// 清除在线状态筛选
function clearOnlineFilter() {
  ipFilter.is_online = null
  ipPagination.page = 1
  loadIPs()
}

onMounted(() => {
  loadSegment()
  loadStats()
  loadDevices()
  loadIPs()
})
</script>

<style scoped>
.segment-detail-container {
  padding: 12px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stats-card {
  margin-top: 12px;
}

.stats-row {
  margin-bottom: 12px;
}

.stat-item {
  text-align: center;
  padding: 12px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.stat-item.clickable {
  cursor: pointer;
  transition: all 0.3s;
}

.stat-item.clickable:hover {
  background-color: #e8eaf0;
  transform: translateY(-2px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.stat-label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 6px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.stat-hint {
  font-size: 11px;
  color: #c0c4cc;
  margin-top: 4px;
}

.usage-section {
  padding: 0 12px;
}

.usage-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 15px;
  font-weight: bold;
}

.usage-percentage {
  font-size: 20px;
  color: #409eff;
}

.usage-tip {
  margin-top: 10px;
}

.ip-list-card {
  margin-top: 12px;
}

.text-muted {
  color: #909399;
}

.pagination {
  margin-top: 12px;
  justify-content: flex-end;
}
</style>
