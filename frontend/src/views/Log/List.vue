<template>
  <div class="log-list-container">
    <el-card>
      <template #header>
        <span>操作日志</span>
      </template>

      <!-- 筛选区域 -->
      <div class="search-section">
        <el-form :inline="true" :model="searchForm" class="search-form">
          <el-form-item label="操作人">
            <el-input 
              v-model="searchForm.username" 
              placeholder="请输入操作人" 
              clearable 
              style="width: 150px"
            />
          </el-form-item>
          <el-form-item label="操作类型">
            <el-select v-model="searchForm.operation_type" placeholder="请选择" clearable style="width: 150px">
              <el-option label="创建" value="create" />
              <el-option label="更新" value="update" />
              <el-option label="删除" value="delete" />
              <el-option label="分配" value="allocate" />
              <el-option label="回收" value="release" />
              <el-option label="扫描" value="scan" />
            </el-select>
          </el-form-item>
          <el-form-item label="资源类型">
            <el-select v-model="searchForm.resource_type" placeholder="请选择" clearable style="width: 150px">
              <el-option label="网段" value="segment" />
              <el-option label="IP 地址" value="ip" />
              <el-option label="设备" value="device" />
              <el-option label="用户" value="user" />
            </el-select>
          </el-form-item>
          <el-form-item label="时间范围">
            <el-date-picker
              v-model="dateRange"
              type="datetimerange"
              range-separator="至"
              start-placeholder="开始时间"
              end-placeholder="结束时间"
              style="width: 360px"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
            <el-button :icon="Refresh" @click="handleReset">重置</el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 表格 -->
      <el-table 
        :data="logs" 
        v-loading="loading" 
        border 
        stripe
        class="log-table"
      >
        <el-table-column prop="id" label="ID" width="80" align="center" />
        <el-table-column prop="username" label="操作人" width="120" />
        <el-table-column prop="user_role" label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="getRoleType(row.user_role)" size="small">
              {{ getRoleText(row.user_role) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="operation_type" label="操作类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getOperationType(row.operation_type)" size="small">
              {{ getOperationText(row.operation_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="resource_type" label="资源类型" width="100">
          <template #default="{ row }">
            {{ getResourceText(row.resource_type) }}
          </template>
        </el-table-column>
        <el-table-column prop="resource_id" label="资源 ID" width="100" align="center" />
        <el-table-column prop="details" label="操作详情" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            {{ formatDetails(row.details) }}
          </template>
        </el-table-column>
        <el-table-column prop="client_ip" label="客户端 IP" width="140" />
        <el-table-column prop="created_at" label="操作时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" align="center">
          <template #default="{ row }">
            <el-button 
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
        @size-change="fetchLogs"
        @current-change="fetchLogs"
        class="pagination"
      />
    </el-card>

    <!-- 日志详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="日志详情"
      width="600px"
    >
      <el-descriptions :column="1" border v-if="currentLog">
        <el-descriptions-item label="日志 ID">
          {{ currentLog.id }}
        </el-descriptions-item>
        <el-descriptions-item label="操作人">
          {{ currentLog.username }}
        </el-descriptions-item>
        <el-descriptions-item label="用户角色">
          {{ getRoleText(currentLog.user_role) }}
        </el-descriptions-item>
        <el-descriptions-item label="操作类型">
          {{ getOperationText(currentLog.operation_type) }}
        </el-descriptions-item>
        <el-descriptions-item label="资源类型">
          {{ getResourceText(currentLog.resource_type) }}
        </el-descriptions-item>
        <el-descriptions-item label="资源 ID">
          {{ currentLog.resource_id }}
        </el-descriptions-item>
        <el-descriptions-item label="客户端 IP">
          {{ currentLog.client_ip || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="操作时间">
          {{ formatDate(currentLog.created_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="操作详情">
          <pre class="details-json">{{ formatDetailsJSON(currentLog.details) }}</pre>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh } from '@element-plus/icons-vue'
import * as logApi from '@/api/log'
import { formatDate } from '@/utils/formatters'

const loading = ref(false)
const logs = ref([])
const dateRange = ref([])
const detailDialogVisible = ref(false)
const currentLog = ref(null)

const searchForm = reactive({
  username: '',
  operation_type: '',
  resource_type: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

// 获取日志列表
async function fetchLogs() {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      ...searchForm
    }
    
    // 添加时间范围
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_time = dateRange.value[0].toISOString()
      params.end_time = dateRange.value[1].toISOString()
    }
    
    // 移除空值参数
    Object.keys(params).forEach(key => {
      if (params[key] === '' || params[key] === null || params[key] === undefined) {
        delete params[key]
      }
    })
    
    const response = await logApi.getLogs(params)
    logs.value = response.data.items || response.data
    pagination.total = response.data.total || logs.value.length
  } catch (error) {
    ElMessage.error('获取日志列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索
function handleSearch() {
  pagination.page = 1
  fetchLogs()
}

// 重置
function handleReset() {
  searchForm.username = ''
  searchForm.operation_type = ''
  searchForm.resource_type = ''
  dateRange.value = []
  pagination.page = 1
  fetchLogs()
}

// 查看详情
function handleView(row) {
  currentLog.value = row
  detailDialogVisible.value = true
}

// 获取角色类型
function getRoleType(role) {
  const typeMap = {
    'admin': 'danger',
    'user': 'warning',
    'readonly': 'info'
  }
  return typeMap[role] || 'info'
}

// 获取角色文本
function getRoleText(role) {
  const textMap = {
    'admin': '管理员',
    'user': '普通用户',
    'readonly': '只读用户'
  }
  return textMap[role] || role
}

// 获取操作类型
function getOperationType(type) {
  const typeMap = {
    'create': 'success',
    'update': 'warning',
    'delete': 'danger',
    'allocate': 'primary',
    'release': 'info',
    'scan': ''
  }
  return typeMap[type] || 'info'
}

// 获取操作文本
function getOperationText(type) {
  const textMap = {
    'create': '创建',
    'update': '更新',
    'delete': '删除',
    'allocate': '分配',
    'release': '回收',
    'scan': '扫描'
  }
  return textMap[type] || type
}

// 获取资源文本
function getResourceText(type) {
  const textMap = {
    'segment': '网段',
    'ip': 'IP 地址',
    'device': '设备',
    'user': '用户'
  }
  return textMap[type] || type
}

// 格式化详情（简短显示）
function formatDetails(details) {
  if (!details) return '-'
  if (typeof details === 'string') return details
  
  try {
    const obj = typeof details === 'object' ? details : JSON.parse(details)
    // 提取关键信息
    if (obj.name) return `名称: ${obj.name}`
    if (obj.ip_address) return `IP: ${obj.ip_address}`
    if (obj.cidr) return `CIDR: ${obj.cidr}`
    return JSON.stringify(obj).substring(0, 50) + '...'
  } catch {
    return String(details).substring(0, 50)
  }
}

// 格式化详情（JSON 显示）
function formatDetailsJSON(details) {
  if (!details) return '-'
  try {
    const obj = typeof details === 'object' ? details : JSON.parse(details)
    return JSON.stringify(obj, null, 2)
  } catch {
    return String(details)
  }
}

onMounted(() => {
  fetchLogs()
})
</script>

<style scoped>
.log-list-container {
  padding: 8px;
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

.log-table {
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

.pagination {
  margin-top: 12px;
  justify-content: flex-end;
}

.details-json {
  background-color: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  font-size: 12px;
  line-height: 1.5;
  max-height: 400px;
  overflow-y: auto;
}
</style>
