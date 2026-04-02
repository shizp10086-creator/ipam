<template>
  <div class="scanner-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>IP 扫描</span>
          <el-button @click="handleBack">
            <el-icon><Back /></el-icon>
            返回
          </el-button>
        </div>
      </template>

      <!-- 扫描配置 -->
      <el-form
        ref="formRef"
        :model="scanForm"
        :rules="rules"
        label-width="120px"
        style="max-width: 600px"
      >
        <el-form-item label="选择网段" prop="segment_id">
          <el-select
            v-model="scanForm.segment_id"
            placeholder="请选择要扫描的网段"
            style="width: 100%"
            filterable
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
            <el-descriptions-item label="预计扫描 IP 数">
              {{ calculateTotalIPs(selectedSegment) }}
            </el-descriptions-item>
            <el-descriptions-item label="预计耗时">
              约 {{ estimateDuration(selectedSegment) }} 秒
            </el-descriptions-item>
          </el-descriptions>
        </el-form-item>

        <el-form-item label="扫描类型" prop="scan_type">
          <el-radio-group v-model="scanForm.scan_type">
            <el-radio label="ping">Ping 扫描</el-radio>
            <el-radio label="arp" disabled>ARP 扫描（暂不支持）</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="超时时间">
          <el-input-number
            v-model="scanForm.timeout"
            :min="1"
            :max="10"
            :step="1"
          />
          <span style="margin-left: 10px; color: #909399">秒</span>
        </el-form-item>

        <el-form-item label="最大并发数">
          <el-input-number
            v-model="scanForm.max_concurrent"
            :min="10"
            :max="200"
            :step="10"
          />
          <span style="margin-left: 10px; color: #909399">个</span>
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            @click="handleStartScan"
            :loading="scanning"
            :disabled="!scanForm.segment_id"
          >
            <el-icon v-if="!scanning"><Search /></el-icon>
            {{ scanning ? '扫描中...' : '开始扫描' }}
          </el-button>
          <el-button @click="handleReset" :disabled="scanning">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 扫描进度 -->
      <div v-if="scanning || scanResult" class="scan-progress">
        <el-divider />
        <h3>扫描进度</h3>
        
        <div v-if="scanning" class="progress-info">
          <el-progress
            :percentage="scanProgress"
            :status="scanProgress === 100 ? 'success' : undefined"
            :stroke-width="20"
          />
          <div class="progress-text">
            <span>正在扫描网段 {{ selectedSegment?.name }}...</span>
            <span>请稍候，预计需要 {{ estimateDuration(selectedSegment) }} 秒</span>
          </div>
        </div>

        <!-- 扫描结果 -->
        <div v-if="scanResult" class="scan-result">
          <el-alert
            :title="`扫描完成！耗时 ${scanResult.duration?.toFixed(2)} 秒`"
            type="success"
            :closable="false"
            show-icon
            style="margin-bottom: 20px"
          />

          <el-row :gutter="20" class="stats-row">
            <el-col :span="6">
              <div class="stat-card">
                <div class="stat-label">总 IP 数</div>
                <div class="stat-value">{{ scanResult.total_ips || 0 }}</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="stat-card online">
                <div class="stat-label">在线 IP</div>
                <div class="stat-value">{{ scanResult.online_ips || 0 }}</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="stat-card offline">
                <div class="stat-label">离线 IP</div>
                <div class="stat-value">
                  {{ (scanResult.total_ips || 0) - (scanResult.online_ips || 0) }}
                </div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="stat-card warning">
                <div class="stat-label">未注册在线 IP</div>
                <div class="stat-value">
                  {{ scanResult.report?.unregistered_online_ips?.length || 0 }}
                </div>
              </div>
            </el-col>
          </el-row>

          <!-- 未注册的在线 IP -->
          <div v-if="scanResult.report?.unregistered_online_ips?.length > 0" class="unregistered-ips">
            <h4>未注册的在线 IP</h4>
            <el-alert
              title="发现未注册的在线 IP，这些 IP 可能存在安全风险"
              type="warning"
              :closable="false"
              show-icon
              style="margin-bottom: 10px"
            />
            <el-table
              :data="scanResult.report.unregistered_online_ips"
              border
              stripe
              max-height="300"
            >
              <el-table-column prop="ip_address" label="IP 地址" width="150" />
              <el-table-column label="响应时间" width="120">
                <template #default="{ row }">
                  {{ row.response_time?.toFixed(2) }} ms
                </template>
              </el-table-column>
              <el-table-column label="操作">
                <template #default="{ row }">
                  <el-button
                    type="primary"
                    size="small"
                    @click="handleAllocateIP(row.ip_address)"
                  >
                    分配此 IP
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>

          <!-- 操作按钮 -->
          <div class="result-actions">
            <el-button type="primary" @click="handleViewSegmentDetail">
              查看网段详情
            </el-button>
            <el-button @click="handleScanAgain">再次扫描</el-button>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 扫描历史 -->
    <el-card style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <span>扫描历史</span>
          <el-button @click="loadScanHistory">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>

      <el-table
        :data="scanHistory"
        v-loading="historyLoading"
        stripe
        style="width: 100%"
      >
        <el-table-column label="网段" width="250">
          <template #default="{ row }">
            <span v-if="row.segment">
              {{ row.segment.name }} ({{ row.segment.network }}/{{ row.segment.prefix_length }})
            </span>
          </template>
        </el-table-column>

        <el-table-column prop="scan_type" label="扫描类型" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ row.scan_type.toUpperCase() }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column label="扫描结果" width="200">
          <template #default="{ row }">
            <span>总数: {{ row.total_ips }}</span>
            <span style="margin-left: 10px; color: #67c23a">
              在线: {{ row.online_ips }}
            </span>
          </template>
        </el-table-column>

        <el-table-column label="耗时" width="100">
          <template #default="{ row }">
            {{ row.duration?.toFixed(2) }} 秒
          </template>
        </el-table-column>

        <el-table-column label="扫描时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              link
              @click="handleViewHistory(row)"
            >
              查看详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-if="historyPagination.total > 10"
        v-model:current-page="historyPagination.page"
        v-model:page-size="historyPagination.page_size"
        :page-sizes="[10, 20, 50]"
        :total="historyPagination.total"
        layout="total, sizes, prev, pager, next"
        @size-change="loadScanHistory"
        @current-change="loadScanHistory"
        style="margin-top: 20px; justify-content: flex-end"
      />
    </el-card>

    <!-- 扫描历史详情 Drawer -->
    <el-drawer v-model="showHistoryDetail" title="扫描历史详情" size="500px">
      <template v-if="historyDetail">
        <el-descriptions :column="2" border size="small" style="margin-bottom:16px;">
          <el-descriptions-item label="网段">{{ historyDetail.segment_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="状态"><el-tag :type="historyDetail.status==='completed'?'success':'warning'" size="small">{{ historyDetail.status==='completed'?'已完成':'进行中' }}</el-tag></el-descriptions-item>
          <el-descriptions-item label="总 IP 数">{{ historyDetail.total_ips }}</el-descriptions-item>
          <el-descriptions-item label="在线数"><span style="color:#67c23a;font-weight:bold;">{{ historyDetail.online_ips }}</span></el-descriptions-item>
          <el-descriptions-item label="耗时">{{ historyDetail.duration?.toFixed(2) }} 秒</el-descriptions-item>
          <el-descriptions-item label="扫描时间">{{ formatDateTime(historyDetail.created_at) }}</el-descriptions-item>
        </el-descriptions>
        <h4 style="margin-bottom:8px;">扫描结果明细</h4>
        <el-table :data="historyDetail.results||[]" stripe size="small" max-height="400">
          <el-table-column prop="ip_address" label="IP 地址" width="140" />
          <el-table-column label="状态" width="80">
            <template #default="{row}"><el-tag :type="row.is_online?'success':'info'" size="small">{{ row.is_online?'在线':'离线' }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="response_time" label="响应时间" width="100">
            <template #default="{row}">{{ row.response_time ? row.response_time.toFixed(1)+'ms' : '-' }}</template>
          </el-table-column>
          <el-table-column prop="hostname" label="主机名" min-width="120" />
        </el-table>
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Back, Search, Refresh } from '@element-plus/icons-vue'
import { scanSegment, getScanHistory } from '@/api/ip'
import { getSegments } from '@/api/network'
import { formatDateTime } from '@/utils/formatters'

const router = useRouter()
const route = useRoute()
const formRef = ref(null)

// 数据
const segments = ref([])
const scanning = ref(false)
const scanProgress = ref(0)
const scanResult = ref(null)
const scanHistory = ref([])
const historyLoading = ref(false)

// 扫描表单
const scanForm = reactive({
  segment_id: null,
  scan_type: 'ping',
  timeout: 2,
  max_concurrent: 50
})

// 历史记录分页
const historyPagination = reactive({
  page: 1,
  page_size: 10,
  total: 0
})

// 表单验证规则
const rules = {
  segment_id: [
    { required: true, message: '请选择网段', trigger: 'change' }
  ]
}

// 选中的网段
const selectedSegment = computed(() => {
  return segments.value.find(s => s.id === scanForm.segment_id)
})

// 计算总 IP 数
const calculateTotalIPs = (segment) => {
  if (!segment) return 0
  return Math.pow(2, 32 - segment.prefix_length) - 2
}

// 估算扫描时间
const estimateDuration = (segment) => {
  if (!segment) return 0
  const totalIPs = calculateTotalIPs(segment)
  const concurrent = scanForm.max_concurrent
  const timeout = scanForm.timeout
  // 估算：总IP数 / 并发数 * 超时时间 * 0.3（经验系数）
  return Math.ceil((totalIPs / concurrent) * timeout * 0.3)
}

// 加载网段列表
const loadSegments = async () => {
  try {
    console.log('开始加载网段列表...')
    const res = await getSegments()
    console.log('网段列表响应:', res)
    if (res.code === 200) {
      segments.value = res.data.items || res.data
      console.log('网段列表加载成功:', segments.value)
    } else {
      console.error('网段列表响应码不是200:', res)
      ElMessage.error(`加载网段列表失败: ${res.message || '未知错误'}`)
    }
  } catch (error) {
    console.error('加载网段列表异常:', error)
    ElMessage.error('加载网段列表失败: ' + (error.message || '网络错误'))
  }
}

// 加载扫描历史
const loadScanHistory = async () => {
  historyLoading.value = true
  try {
    const res = await getScanHistory({
      page: historyPagination.page,
      page_size: historyPagination.page_size
    })
    
    if (res.code === 200) {
      scanHistory.value = res.data.items || []
      historyPagination.total = res.data.total || 0
    }
  } catch (error) {
    console.error('加载扫描历史失败:', error)
  } finally {
    historyLoading.value = false
  }
}

// 网段变化
const handleSegmentChange = () => {
  scanResult.value = null
  scanProgress.value = 0
}

// 开始扫描
const handleStartScan = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    scanning.value = true
    scanProgress.value = 0
    scanResult.value = null

    // 模拟进度更新
    const progressInterval = setInterval(() => {
      if (scanProgress.value < 90) {
        scanProgress.value += 10
      }
    }, 500)

    try {
      const scanData = {
        segment_id: scanForm.segment_id,
        scan_type: scanForm.scan_type,
        timeout: scanForm.timeout,
        max_concurrent: scanForm.max_concurrent
      }
      console.log('开始扫描，请求数据:', scanData)
      
      const res = await scanSegment(scanData)
      console.log('扫描响应:', res)

      clearInterval(progressInterval)
      scanProgress.value = 100

      if (res.code === 200) {
        scanResult.value = res.data
        console.log('扫描结果:', scanResult.value)
        ElMessage.success('扫描完成')
        // 刷新扫描历史
        loadScanHistory()
      } else {
        console.error('扫描响应码不是200:', res)
        ElMessage.error(`扫描失败: ${res.message || '未知错误'}`)
      }
    } catch (error) {
      clearInterval(progressInterval)
      console.error('扫描异常:', error)
      const errorMsg = error.response?.data?.detail || error.response?.data?.message || error.message || '未知错误'
      ElMessage.error('扫描失败: ' + errorMsg)
    } finally {
      scanning.value = false
    }
  })
}

// 重置表单
const handleReset = () => {
  formRef.value?.resetFields()
  scanResult.value = null
  scanProgress.value = 0
}

// 再次扫描
const handleScanAgain = () => {
  scanResult.value = null
  scanProgress.value = 0
  handleStartScan()
}

// 查看网段详情
const handleViewSegmentDetail = () => {
  if (scanForm.segment_id) {
    router.push(`/segments/${scanForm.segment_id}`)
  }
}

// 分配 IP
const handleAllocateIP = (ipAddress) => {
  router.push({
    path: '/ip/allocate',
    query: { ip: ipAddress, segment_id: scanForm.segment_id }
  })
}

// 查看历史详情
const showHistoryDetail = ref(false)
const historyDetail = ref(null)
const handleViewHistory = async (row) => {
  historyDetail.value = { ...row, results: [] }
  showHistoryDetail.value = true
  try {
    const r = await getScanHistory({ scan_id: row.id })
    if (r.data?.results) {
      historyDetail.value.results = r.data.results
    }
  } catch (e) {
    // 如果没有详细结果 API，展示基本信息即可
  }
}

// 返回
const handleBack = () => {
  router.back()
}

// 初始化
onMounted(() => {
  loadSegments()
  loadScanHistory()
  
  // 如果 URL 中有 segment_id 参数，自动选中该网段
  const segmentIdFromQuery = route.query.segment_id
  if (segmentIdFromQuery) {
    scanForm.segment_id = parseInt(segmentIdFromQuery)
  }
})
</script>

<style scoped>
.scanner-container {
  padding: 12px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.scan-progress {
  margin-top: 12px;
}

.progress-info {
  margin: 12px 0;
}

.progress-text {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  color: #606266;
  font-size: 13px;
}

.scan-result {
  margin-top: 12px;
}

.stats-row {
  margin: 12px 0;
}

.stat-card {
  text-align: center;
  padding: 12px;
  background-color: #f5f7fa;
  border-radius: 4px;
  border-left: 4px solid #409eff;
}

.stat-card.online {
  border-left-color: #67c23a;
}

.stat-card.offline {
  border-left-color: #909399;
}

.stat-card.warning {
  border-left-color: #e6a23c;
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

.unregistered-ips {
  margin-top: 12px;
}

.unregistered-ips h4 {
  margin: 0 0 8px 0;
  font-size: 15px;
  font-weight: 500;
}

.result-actions {
  margin-top: 12px;
  text-align: center;
}

h3 {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 500;
}
</style>
