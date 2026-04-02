<template>
  <div class="segment-list-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>网段管理</span>
          <el-button 
            v-if="canCreate" 
            type="primary" 
            :icon="Plus" 
            @click="handleCreate"
          >
            创建网段
          </el-button>
        </div>
      </template>

      <!-- 搜索和筛选区域 - 添加背景色和分隔 -->
      <div class="search-section">
        <el-form :inline="true" :model="searchForm" class="search-form">
          <el-form-item label="网段名称">
            <el-input 
              v-model="searchForm.name" 
              placeholder="请输入网段名称" 
              clearable 
              @keyup.enter="handleSearch"
              style="width: 200px"
            />
          </el-form-item>
          <el-form-item label="网络地址">
            <el-input 
              v-model="searchForm.network" 
              placeholder="如 192.168.1.0" 
              clearable 
              @keyup.enter="handleSearch"
              style="width: 200px"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
            <el-button :icon="Refresh" @click="handleReset">重置</el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 表格 - 优化列宽和行高 -->
      <el-table 
        :data="segments" 
        v-loading="loading" 
        border 
        stripe
        :row-class-name="getRowClassName"
        @sort-change="handleSortChange"
        class="segment-table"
      >
        <el-table-column prop="id" label="ID" width="80" sortable="custom" align="center" />
        <el-table-column prop="company" label="所属公司" min-width="120" show-overflow-tooltip />
        <el-table-column prop="name" label="网段名称" min-width="150" sortable="custom" show-overflow-tooltip />
        <el-table-column label="CIDR" min-width="200">
          <template #default="{ row }">
            <div class="cidr-cell">
              <el-tag size="default">{{ row.network }}/{{ row.prefix_length }}</el-tag>
              <el-icon 
                class="copy-icon" 
                @click="copyToClipboard(`${row.network}/${row.prefix_length}`)"
                title="复制 CIDR"
              >
                <DocumentCopy />
              </el-icon>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="gateway" label="网关" min-width="160" show-overflow-tooltip>
          <template #default="{ row }">
            <div class="gateway-cell" v-if="row.gateway">
              <span>{{ row.gateway }}</span>
              <el-icon 
                class="copy-icon" 
                @click="copyToClipboard(row.gateway)"
                title="复制网关"
              >
                <DocumentCopy />
              </el-icon>
            </div>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column label="使用率" width="150" sortable="custom" prop="usage_rate">
          <template #default="{ row }">
            <div class="usage-cell">
              <el-progress 
                :percentage="getUsagePercentage(row)" 
                :color="getUsageColor(row)"
                :stroke-width="20"
                :text-inside="true"
                :format="() => `${getUsagePercentage(row)}%`"
              />
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="usage_threshold" label="告警阈值" width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ row.usage_threshold }}%</el-tag>
          </template>
        </el-table-column>
        <el-table-column 
          v-if="showDescriptionColumn" 
          prop="description" 
          label="描述" 
          min-width="200" 
          show-overflow-tooltip 
        />
        <el-table-column prop="created_at" label="创建时间" width="180" sortable="custom">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right" align="center">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button 
                size="small" 
                :icon="View" 
                @click="handleView(row)"
                class="action-btn action-btn-icon"
                circle
                title="详情"
              />
              <el-button 
                v-if="canEdit" 
                size="small" 
                :icon="Edit" 
                @click="handleEdit(row)"
                class="action-btn"
              >
                编辑
              </el-button>
              <el-button 
                v-if="canDelete" 
                size="small" 
                type="danger" 
                :icon="Delete" 
                @click="handleDelete(row)"
                class="action-btn action-btn-delete"
              >
                删除
              </el-button>
            </div>
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
        @size-change="fetchSegments"
        @current-change="fetchSegments"
        class="pagination"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh, View, Edit, Delete, DocumentCopy } from '@element-plus/icons-vue'
import * as networkApi from '@/api/network'
import { formatDate } from '@/utils/formatters'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const segments = ref([])
const showDescriptionColumn = ref(true)

const searchForm = reactive({
  name: '',
  network: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const sortParams = reactive({
  sort_by: '',
  sort_order: ''
})

// 权限检查
const canCreate = computed(() => authStore.userRole === 'admin')
const canEdit = computed(() => authStore.userRole === 'admin')
const canDelete = computed(() => authStore.userRole === 'admin')

// 响应式布局 - 根据屏幕宽度调整列显示
function handleResize() {
  const width = window.innerWidth
  showDescriptionColumn.value = width >= 1200
}

// 获取网段列表
async function fetchSegments() {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      include_stats: true,  // 包含统计信息
      ...searchForm,
      ...sortParams
    }
    
    // 移除空值参数
    Object.keys(params).forEach(key => {
      if (params[key] === '' || params[key] === null || params[key] === undefined) {
        delete params[key]
      }
    })
    
    const response = await networkApi.getSegments(params)
    segments.value = response.data.items || response.data
    pagination.total = response.data.total || segments.value.length
  } catch (error) {
    ElMessage.error('获取网段列表失败')
  } finally {
    loading.value = false
  }
}

// 计算使用率百分比
// 使用率 = (已用 IP + 保留 IP + 在线 IP) / 总 IP × 100%
function getUsagePercentage(row) {
  if (!row.total_ips || row.total_ips === 0) return 0
  const used = row.used_ips || 0
  const reserved = row.reserved_ips || 0
  const online = row.online_ips || 0
  const total = row.total_ips
  return Math.round(((used + reserved + online) / total) * 100)
}

// 根据使用率获取颜色（渐变色）
function getUsageColor(row) {
  const percentage = getUsagePercentage(row)
  
  if (percentage < 30) {
    return '#52c41a' // 绿色 - 低使用率
  } else if (percentage < 70) {
    return '#faad14' // 黄色 - 中等使用率
  } else {
    return '#f5222d' // 红色 - 高使用率
  }
}

// 获取行类名（用于 hover 效果）
function getRowClassName({ rowIndex }) {
  return 'table-row'
}

// 复制到剪贴板
function copyToClipboard(text) {
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(() => {
      ElMessage.success('已复制到剪贴板')
    }).catch(() => {
      fallbackCopy(text)
    })
  } else {
    fallbackCopy(text)
  }
}

// 降级复制方法
function fallbackCopy(text) {
  const textarea = document.createElement('textarea')
  textarea.value = text
  textarea.style.position = 'fixed'
  textarea.style.opacity = '0'
  document.body.appendChild(textarea)
  textarea.select()
  try {
    document.execCommand('copy')
    ElMessage.success('已复制到剪贴板')
  } catch (err) {
    ElMessage.error('复制失败，请手动复制')
  }
  document.body.removeChild(textarea)
}

// 搜索
function handleSearch() {
  pagination.page = 1
  fetchSegments()
}

// 重置
function handleReset() {
  searchForm.name = ''
  searchForm.network = ''
  pagination.page = 1
  sortParams.sort_by = ''
  sortParams.sort_order = ''
  fetchSegments()
}

// 排序变化
function handleSortChange({ prop, order }) {
  if (order) {
    sortParams.sort_by = prop
    sortParams.sort_order = order === 'ascending' ? 'asc' : 'desc'
  } else {
    sortParams.sort_by = ''
    sortParams.sort_order = ''
  }
  fetchSegments()
}

// 创建网段
function handleCreate() {
  router.push({ name: 'SegmentCreate' })
}

// 查看详情
function handleView(row) {
  router.push({ name: 'SegmentDetail', params: { id: row.id } })
}

// 编辑网段
function handleEdit(row) {
  router.push({ name: 'SegmentEdit', params: { id: row.id } })
}

// 删除网段
function handleDelete(row) {
  ElMessageBox.confirm(
    `确定要删除网段 "${row.name}" (${row.network}/${row.prefix_length}) 吗？如果网段内有已分配的 IP，删除将失败。`,
    '提示',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      await networkApi.deleteSegment(row.id)
      ElMessage.success('删除网段成功')
      fetchSegments()
    } catch (error) {
      // 错误已由拦截器处理
    }
  }).catch(() => {})
}

onMounted(() => {
  fetchSegments()
  handleResize()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.segment-list-container {
  padding: 8px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* 搜索区域样式 - 添加背景色和分隔 */
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

/* 表格样式优化 */
.segment-table {
  margin-top: 0;
}

/* 表格行样式 - 增加行高和 hover 效果 */
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

:deep(.table-row) {
  transition: all 0.3s ease;
}

:deep(.table-row:hover) {
  background-color: #f5f7fa !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

/* CIDR 单元格样式 */
.cidr-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.copy-icon {
  cursor: pointer;
  color: #909399;
  font-size: 14px;
  transition: all 0.3s;
  opacity: 0;
}

.cidr-cell:hover .copy-icon,
.gateway-cell:hover .copy-icon {
  opacity: 1;
}

.copy-icon:hover {
  color: #409eff;
  transform: scale(1.2);
}

/* 网关单元格样式 */
.gateway-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 使用率单元格样式 - 优化布局 */
.usage-cell {
  display: flex;
  align-items: center;
  padding: 0 4px;
}

:deep(.usage-cell .el-progress) {
  flex: 1;
}

:deep(.el-progress__text) {
  font-size: 11px !important;
  font-weight: 600;
  color: #fff !important;
}

/* 操作按钮样式 - 优化间距和 hover 效果 */
.action-buttons {
  display: flex;
  gap: 4px;
  justify-content: center;
  align-items: center;
}

.action-btn {
  padding: 4px 10px;
  transition: all 0.3s;
}

.action-btn-icon {
  padding: 4px;
  width: 26px;
  height: 26px;
}

.action-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.3);
}

.action-btn-delete {
  opacity: 0.7;
}

:deep(.table-row:hover) .action-btn-delete {
  opacity: 1;
}

.action-btn-delete:hover {
  box-shadow: 0 2px 8px rgba(245, 34, 45, 0.3);
}

.text-muted {
  color: #909399;
}

.pagination {
  margin-top: 12px;
  justify-content: flex-end;
}

/* 响应式布局 */
@media (max-width: 1200px) {
  .search-form :deep(.el-form-item) {
    margin-bottom: 12px;
  }
}

@media (max-width: 768px) {
  .segment-list-container {
    padding: 8px;
  }
  
  .search-section {
    padding: 12px;
  }
  
  .search-form {
    display: flex;
    flex-direction: column;
  }
  
  .search-form :deep(.el-form-item) {
    width: 100%;
    margin-right: 0;
  }
  
  .search-form :deep(.el-input) {
    width: 100% !important;
  }
  
  :deep(.el-table__body td) {
    padding: 10px 0;
  }
  
  .action-buttons {
    flex-direction: column;
    gap: 4px;
  }
  
  .action-btn {
    width: 100%;
  }
}
</style>
