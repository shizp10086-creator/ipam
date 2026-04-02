<template>
  <div class="alert-list-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>告警管理</span>
          <el-badge :value="unresolvedCount" :max="99" class="badge">
            <el-button :icon="Bell" @click="fetchAlerts">刷新</el-button>
          </el-badge>
        </div>
      </template>

      <!-- 筛选区域 -->
      <div class="search-section">
        <el-form :inline="true" :model="searchForm" class="search-form">
          <el-form-item label="状态">
            <el-select v-model="searchForm.is_resolved" placeholder="请选择" clearable style="width: 120px">
              <el-option label="未解决" :value="false" />
              <el-option label="已解决" :value="true" />
            </el-select>
          </el-form-item>
          <el-form-item label="严重程度">
            <el-select v-model="searchForm.severity" placeholder="请选择" clearable style="width: 120px">
              <el-option label="警告" value="warning" />
              <el-option label="严重" value="critical" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
            <el-button :icon="Refresh" @click="handleReset">重置</el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 表格 -->
      <el-table 
        :data="alerts" 
        v-loading="loading" 
        border 
        stripe
        class="alert-table"
      >
        <el-table-column prop="id" label="ID" width="80" align="center" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_resolved ? 'success' : 'danger'" size="small">
              {{ row.is_resolved ? '已解决' : '未解决' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="alert_type" label="告警类型" width="120">
          <template #default="{ row }">
            使用率告警
          </template>
        </el-table-column>
        <el-table-column prop="severity" label="严重程度" width="100">
          <template #default="{ row }">
            <el-tag :type="getSeverityType(row.severity)" size="small">
              {{ getSeverityText(row.severity) }}
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
        <el-table-column prop="current_usage" label="当前使用率" width="120" align="center">
          <template #default="{ row }">
            <span :style="{ color: getUsageColor(row.current_usage) }">
              {{ row.current_usage }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="message" label="告警消息" min-width="200" show-overflow-tooltip />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" align="center" fixed="right">
          <template #default="{ row }">
            <el-button 
              v-if="!row.is_resolved && canResolve"
              size="small" 
              type="success"
              @click="handleResolve(row)"
            >
              解决
            </el-button>
            <el-button 
              v-else
              size="small" 
              @click="handleView(row)"
            >
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="fetchAlerts"
        @current-change="fetchAlerts"
        class="pagination"
      />
    </el-card>

    <!-- 告警详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="告警详情"
      width="600px"
    >
      <el-descriptions :column="1" border v-if="currentAlert">
        <el-descriptions-item label="告警 ID">
          {{ currentAlert.id }}
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="currentAlert.is_resolved ? 'success' : 'danger'">
            {{ currentAlert.is_resolved ? '已解决' : '未解决' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="告警类型">
          使用率告警
        </el-descriptions-item>
        <el-descriptions-item label="严重程度">
          <el-tag :type="getSeverityType(currentAlert.severity)">
            {{ getSeverityText(currentAlert.severity) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="网段">
          {{ currentAlert.segment?.name || '-' }}
          <span v-if="currentAlert.segment">
            ({{ currentAlert.segment.network }}/{{ currentAlert.segment.prefix_length }})
          </span>
        </el-descriptions-item>
        <el-descriptions-item label="当前使用率">
          <span :style="{ color: getUsageColor(currentAlert.current_usage) }">
            {{ currentAlert.current_usage }}%
          </span>
        </el-descriptions-item>
        <el-descriptions-item label="告警阈值">
          {{ currentAlert.threshold }}%
        </el-descriptions-item>
        <el-descriptions-item label="告警消息">
          {{ currentAlert.message }}
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ formatDate(currentAlert.created_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="解决时间" v-if="currentAlert.resolved_at">
          {{ formatDate(currentAlert.resolved_at) }}
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Bell } from '@element-plus/icons-vue'
import * as alertApi from '@/api/alert'
import { formatDate } from '@/utils/formatters'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const loading = ref(false)
const alerts = ref([])
const detailDialogVisible = ref(false)
const currentAlert = ref(null)

const searchForm = reactive({
  is_resolved: undefined,
  severity: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const canResolve = computed(() => authStore.userRole === 'admin')

// 未解决告警数量
const unresolvedCount = computed(() => {
  return alerts.value.filter(alert => !alert.is_resolved).length
})

// 获取告警列表
async function fetchAlerts() {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      ...searchForm
    }
    
    // 移除空值参数
    Object.keys(params).forEach(key => {
      if (params[key] === '' || params[key] === null || params[key] === undefined) {
        delete params[key]
      }
    })
    
    const response = await alertApi.getAlerts(params)
    alerts.value = response.data.items || response.data
    pagination.total = response.data.total || alerts.value.length
  } catch (error) {
    ElMessage.error('获取告警列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索
function handleSearch() {
  pagination.page = 1
  fetchAlerts()
}

// 重置
function handleReset() {
  searchForm.is_resolved = undefined
  searchForm.severity = ''
  pagination.page = 1
  fetchAlerts()
}

// 查看详情
function handleView(row) {
  currentAlert.value = row
  detailDialogVisible.value = true
}

// 解决告警
function handleResolve(row) {
  ElMessageBox.confirm(
    `确定要解决此告警吗？`,
    '提示',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      await alertApi.resolveAlert(row.id)
      ElMessage.success('告警已解决')
      fetchAlerts()
    } catch (error) {
      // 错误已由拦截器处理
    }
  }).catch(() => {})
}

// 获取严重程度类型
function getSeverityType(severity) {
  const typeMap = {
    'warning': 'warning',
    'critical': 'danger'
  }
  return typeMap[severity] || 'info'
}

// 获取严重程度文本
function getSeverityText(severity) {
  const textMap = {
    'warning': '警告',
    'critical': '严重'
  }
  return textMap[severity] || severity
}

// 获取使用率颜色
function getUsageColor(usage) {
  if (usage < 70) return '#faad14'
  return '#f5222d'
}

onMounted(() => {
  fetchAlerts()
})
</script>

<style scoped>
.alert-list-container {
  padding: 8px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.badge {
  margin-left: 12px;
}

.search-section {
  background-color: #f8f9fa;
  padding: 12px;
  margin: -20px -20px 12px -20px;
  border-bottom: 1px solid #e8e8e8;
  border-radius: 4px 4px 0 0;
}

.search-form {
  margin-bottom: 0;
}

.alert-table {
  margin-top: 0;
}

:deep(.el-table) {
  font-size: 14px;
}

:deep(.el-table__header) {
  background-color: #f0f2f5;
}

:deep(.el-table__header th) {
  background-color: #f0f2f5;
  color: #303133;
  font-weight: 600;
  padding: 8px 0;
}

:deep(.el-table__body td) {
  padding: 8px 0;
}

.text-muted {
  color: #909399;
  font-size: 12px;
}

.pagination {
  margin-top: 12px;
  justify-content: flex-end;
}
</style>
