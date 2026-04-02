<template>
  <div class="ip-detail-container" v-loading="loading">
    <div v-if="ipDetail">
      <!-- 基本信息 -->
      <el-descriptions title="基本信息" :column="2" border>
        <template #extra>
          <el-button 
            v-if="canEdit" 
            type="primary" 
            :icon="Edit" 
            @click="showEditDialog"
          >
            编辑
          </el-button>
        </template>
        
        <el-descriptions-item label="IP 地址">
          <el-tag size="large">{{ ipDetail.ip_address }}</el-tag>
        </el-descriptions-item>
        
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(ipDetail.status)">
            {{ getStatusText(ipDetail.status) }}
          </el-tag>
        </el-descriptions-item>

        <el-descriptions-item label="所属网段">
          <span v-if="ipDetail.segment">
            {{ ipDetail.segment.name }} 
            ({{ ipDetail.segment.network }}/{{ ipDetail.segment.prefix_length }})
          </span>
        </el-descriptions-item>

        <el-descriptions-item label="在线状态">
          <el-tag v-if="ipDetail.is_online" type="success">在线</el-tag>
          <el-tag v-else-if="ipDetail.last_seen" type="info">离线</el-tag>
          <span v-else>未扫描</span>
        </el-descriptions-item>

        <el-descriptions-item label="分配时间">
          {{ ipDetail.allocated_at ? formatDateTime(ipDetail.allocated_at) : '-' }}
        </el-descriptions-item>

        <el-descriptions-item label="最后扫描时间">
          {{ ipDetail.last_seen ? formatDateTime(ipDetail.last_seen) : '-' }}
        </el-descriptions-item>

        <el-descriptions-item label="创建时间">
          {{ formatDateTime(ipDetail.created_at) }}
        </el-descriptions-item>

        <el-descriptions-item label="更新时间">
          {{ formatDateTime(ipDetail.updated_at) }}
        </el-descriptions-item>
      </el-descriptions>

      <!-- 关联设备信息 -->
      <el-descriptions
        v-if="ipDetail.device"
        title="关联设备信息"
        :column="2"
        border
        style="margin-top: 20px"
      >
        <el-descriptions-item label="设备名称">
          {{ ipDetail.device.name }}
        </el-descriptions-item>

        <el-descriptions-item label="MAC 地址">
          <el-tag>{{ ipDetail.device.mac_address }}</el-tag>
        </el-descriptions-item>

        <el-descriptions-item label="设备类型">
          {{ ipDetail.device.device_type || '-' }}
        </el-descriptions-item>

        <el-descriptions-item label="制造商">
          {{ ipDetail.device.manufacturer || '-' }}
        </el-descriptions-item>

        <el-descriptions-item label="型号">
          {{ ipDetail.device.model || '-' }}
        </el-descriptions-item>

        <el-descriptions-item label="责任人">
          {{ ipDetail.device.owner || '-' }}
        </el-descriptions-item>

        <el-descriptions-item label="部门">
          {{ ipDetail.device.department || '-' }}
        </el-descriptions-item>

        <el-descriptions-item label="位置">
          {{ ipDetail.device.location || '-' }}
        </el-descriptions-item>

        <el-descriptions-item label="描述" :span="2">
          {{ ipDetail.device.description || '-' }}
        </el-descriptions-item>
      </el-descriptions>

      <div v-else style="margin-top: 20px">
        <el-alert
          title="未关联设备"
          type="info"
          :closable="false"
        />
      </div>

      <!-- 操作历史 -->
      <div style="margin-top: 20px">
        <h3>操作历史</h3>
        <el-table
          :data="operationLogs"
          v-loading="logsLoading"
          stripe
          style="width: 100%; margin-top: 10px"
        >
          <el-table-column prop="operation_type" label="操作类型" width="120">
            <template #default="{ row }">
              <el-tag :type="getOperationType(row.operation_type)" size="small">
                {{ getOperationText(row.operation_type) }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column prop="username" label="操作人" width="150" />

          <el-table-column label="操作时间" width="180">
            <template #default="{ row }">
              {{ formatDateTime(row.created_at) }}
            </template>
          </el-table-column>

          <el-table-column prop="details" label="操作详情">
            <template #default="{ row }">
              <el-popover
                placement="top"
                :width="400"
                trigger="hover"
              >
                <template #reference>
                  <span style="cursor: pointer; color: #409eff">
                    查看详情
                  </span>
                </template>
                <pre style="max-height: 300px; overflow: auto">{{ formatJSON(row.details) }}</pre>
              </el-popover>
            </template>
          </el-table-column>

          <el-table-column prop="ip_address" label="客户端 IP" width="150" />
        </el-table>

        <el-pagination
          v-if="logsPagination.total > 10"
          v-model:current-page="logsPagination.page"
          v-model:page-size="logsPagination.page_size"
          :page-sizes="[10, 20, 50]"
          :total="logsPagination.total"
          layout="total, sizes, prev, pager, next"
          @size-change="loadOperationLogs"
          @current-change="loadOperationLogs"
          style="margin-top: 20px; justify-content: flex-end"
        />
      </div>
    </div>

    <!-- 编辑对话框 -->
    <el-dialog
      v-model="editDialogVisible"
      title="编辑 IP 地址"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="editFormRef"
        :model="editForm"
        :rules="editRules"
        label-width="120px"
      >
        <el-form-item label="IP 地址">
          <el-input v-model="ipDetail.ip_address" disabled />
        </el-form-item>

        <el-form-item label="状态" prop="status">
          <el-select v-model="editForm.status" placeholder="请选择状态" style="width: 100%">
            <el-option label="空闲" value="available" />
            <el-option label="已用" value="used" />
            <el-option label="保留" value="reserved" />
          </el-select>
        </el-form-item>

        <el-form-item label="关联设备" prop="device_id">
          <el-select
            v-model="editForm.device_id"
            placeholder="请选择设备（可选）"
            clearable
            filterable
            remote
            :remote-method="searchDevices"
            :loading="devicesLoading"
            style="width: 100%"
          >
            <el-option
              v-for="device in deviceOptions"
              :key="device.id"
              :label="`${device.name} (${device.mac_address})`"
              :value="device.id"
            />
          </el-select>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleUpdate" :loading="updating">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Edit } from '@element-plus/icons-vue'
import { getIP, updateIP } from '@/api/ip'
import { getDevices } from '@/api/device'
import { getLogs } from '@/api/logs'
import { formatDateTime } from '@/utils/formatters'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

const props = defineProps({
  ipId: {
    type: Number,
    required: true
  }
})

// 数据
const loading = ref(false)
const logsLoading = ref(false)
const ipDetail = ref(null)
const operationLogs = ref([])

// 编辑相关
const editDialogVisible = ref(false)
const editFormRef = ref(null)
const updating = ref(false)
const devicesLoading = ref(false)
const deviceOptions = ref([])

const editForm = reactive({
  status: '',
  device_id: null
})

const editRules = {
  status: [
    { required: true, message: '请选择状态', trigger: 'change' }
  ]
}

// 权限检查
const canEdit = computed(() => {
  return ['admin', 'user'].includes(authStore.userRole)
})

// 日志分页
const logsPagination = reactive({
  page: 1,
  page_size: 10,
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

// 获取操作类型
const getOperationType = (type) => {
  const typeMap = {
    allocate: 'success',
    release: 'warning',
    create: 'primary',
    update: 'info',
    delete: 'danger'
  }
  return typeMap[type] || 'info'
}

// 获取操作文本
const getOperationText = (type) => {
  const textMap = {
    allocate: '分配',
    release: '回收',
    create: '创建',
    update: '更新',
    delete: '删除'
  }
  return textMap[type] || type
}

// 格式化 JSON
const formatJSON = (jsonStr) => {
  try {
    if (typeof jsonStr === 'string') {
      return JSON.stringify(JSON.parse(jsonStr), null, 2)
    }
    return JSON.stringify(jsonStr, null, 2)
  } catch (error) {
    return jsonStr
  }
}

// 加载 IP 详情
const loadIPDetail = async () => {
  loading.value = true
  try {
    const res = await getIP(props.ipId)
    if (res.code === 200) {
      ipDetail.value = res.data
    }
  } catch (error) {
    ElMessage.error('加载 IP 详情失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 加载操作日志
const loadOperationLogs = async () => {
  logsLoading.value = true
  try {
    const res = await getLogs({
      resource_type: 'ip',
      resource_id: props.ipId,
      page: logsPagination.page,
      page_size: logsPagination.page_size
    })
    
    if (res.code === 200) {
      operationLogs.value = res.data.items || []
      logsPagination.total = res.data.total || 0
    }
  } catch (error) {
    console.error('加载操作日志失败:', error)
  } finally {
    logsLoading.value = false
  }
}

// 显示编辑对话框
const showEditDialog = () => {
  editForm.status = ipDetail.value.status
  editForm.device_id = ipDetail.value.device_id
  
  // 如果有关联设备，加载到选项中
  if (ipDetail.value.device) {
    deviceOptions.value = [ipDetail.value.device]
  }
  
  editDialogVisible.value = true
}

// 搜索设备
const searchDevices = async (query) => {
  if (!query) {
    deviceOptions.value = ipDetail.value.device ? [ipDetail.value.device] : []
    return
  }
  
  devicesLoading.value = true
  try {
    const res = await getDevices({ search: query, page_size: 20 })
    if (res.code === 200) {
      deviceOptions.value = res.data.items || []
    }
  } catch (error) {
    console.error('搜索设备失败:', error)
  } finally {
    devicesLoading.value = false
  }
}

// 更新 IP
const handleUpdate = async () => {
  if (!editFormRef.value) return
  
  await editFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    updating.value = true
    try {
      const res = await updateIP(props.ipId, {
        status: editForm.status,
        device_id: editForm.device_id || null
      })
      
      if (res.code === 200) {
        ElMessage.success('更新成功')
        editDialogVisible.value = false
        await loadIPDetail()
        await loadOperationLogs()
      }
    } catch (error) {
      ElMessage.error(error.response?.data?.message || '更新失败')
    } finally {
      updating.value = false
    }
  })
}

// 初始化
onMounted(() => {
  loadIPDetail()
  loadOperationLogs()
})
</script>

<style scoped>
.ip-detail-container {
  padding: 10px;
}

h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
}

pre {
  margin: 0;
  font-size: 12px;
  line-height: 1.5;
}
</style>
