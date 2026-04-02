<template>
  <div class="device-list-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>设备管理</span>
          <el-button 
            v-if="canCreate" 
            type="primary" 
            :icon="Plus" 
            @click="handleCreate"
          >
            创建设备
          </el-button>
        </div>
      </template>

      <!-- 搜索区域 -->
      <div class="search-section">
        <el-form :inline="true" :model="searchForm" class="search-form">
          <el-form-item label="设备名称">
            <el-input 
              v-model="searchForm.name" 
              placeholder="请输入设备名称" 
              clearable 
              @keyup.enter="handleSearch"
              style="width: 200px"
            />
          </el-form-item>
          <el-form-item label="MAC 地址">
            <el-input 
              v-model="searchForm.mac_address" 
              placeholder="如 00:11:22:33:44:55" 
              clearable 
              @keyup.enter="handleSearch"
              style="width: 200px"
            />
          </el-form-item>
          <el-form-item label="责任人">
            <el-input 
              v-model="searchForm.owner" 
              placeholder="请输入责任人" 
              clearable 
              @keyup.enter="handleSearch"
              style="width: 150px"
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
        :data="devices" 
        v-loading="loading" 
        border 
        stripe
        @sort-change="handleSortChange"
        class="device-table"
      >
        <el-table-column prop="id" label="ID" width="80" sortable="custom" align="center" />
        <el-table-column prop="name" label="设备名称" min-width="150" sortable="custom" show-overflow-tooltip />
        <el-table-column prop="mac_address" label="MAC 地址" width="160" show-overflow-tooltip>
          <template #default="{ row }">
            <el-tag size="default">{{ row.mac_address }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="device_type" label="设备类型" width="120" show-overflow-tooltip />
        <el-table-column prop="manufacturer" label="制造商" width="120" show-overflow-tooltip />
        <el-table-column prop="model" label="型号" width="120" show-overflow-tooltip />
        <el-table-column prop="owner" label="责任人" width="100" show-overflow-tooltip />
        <el-table-column prop="department" label="部门" width="120" show-overflow-tooltip />
        <el-table-column prop="location" label="位置" width="120" show-overflow-tooltip />
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
        @size-change="fetchDevices"
        @current-change="fetchDevices"
        class="pagination"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh, View, Edit, Delete } from '@element-plus/icons-vue'
import * as deviceApi from '@/api/device'
import { formatDate } from '@/utils/formatters'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const devices = ref([])

const searchForm = reactive({
  name: '',
  mac_address: '',
  owner: ''
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

// 获取设备列表
async function fetchDevices() {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      ...searchForm,
      ...sortParams
    }
    
    // 移除空值参数
    Object.keys(params).forEach(key => {
      if (params[key] === '' || params[key] === null || params[key] === undefined) {
        delete params[key]
      }
    })
    
    const response = await deviceApi.getDevices(params)
    devices.value = response.data.items || response.data
    pagination.total = response.data.total || devices.value.length
  } catch (error) {
    ElMessage.error('获取设备列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索
function handleSearch() {
  pagination.page = 1
  fetchDevices()
}

// 重置
function handleReset() {
  searchForm.name = ''
  searchForm.mac_address = ''
  searchForm.owner = ''
  pagination.page = 1
  sortParams.sort_by = ''
  sortParams.sort_order = ''
  fetchDevices()
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
  fetchDevices()
}

// 创建设备
function handleCreate() {
  router.push({ name: 'DeviceCreate' })
}

// 查看详情
function handleView(row) {
  router.push({ name: 'DeviceDetail', params: { id: row.id } })
}

// 编辑设备
function handleEdit(row) {
  router.push({ name: 'DeviceEdit', params: { id: row.id } })
}

// 删除设备
function handleDelete(row) {
  ElMessageBox.confirm(
    `确定要删除设备 "${row.name}" 吗？删除设备将自动回收其关联的所有 IP 地址。`,
    '提示',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      await deviceApi.deleteDevice(row.id)
      ElMessage.success('删除设备成功')
      fetchDevices()
    } catch (error) {
      // 错误已由拦截器处理
    }
  }).catch(() => {})
}

onMounted(() => {
  fetchDevices()
})
</script>

<style scoped>
.device-list-container {
  padding: 8px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
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

.device-table {
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

.action-btn-delete:hover {
  opacity: 1;
  box-shadow: 0 2px 8px rgba(245, 34, 45, 0.3);
}

.pagination {
  margin-top: 12px;
  justify-content: flex-end;
}
</style>
