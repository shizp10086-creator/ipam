<template>
  <div class="dashboard-container">
    <!-- 页面标题和刷新按钮 -->
    <div class="dashboard-header">
      <h2>仪表板</h2>
      <div class="header-actions">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          size="default"
          style="margin-right: 10px"
          @change="handleDateRangeChange"
        />
        <el-button 
          type="primary" 
          :icon="RefreshIcon" 
          @click="handleRefresh"
          :loading="loading"
        >
          刷新数据
        </el-button>
      </div>
    </div>

    <!-- Key Metrics - 关键指标卡片 -->
    <el-row :gutter="20" class="metrics-row">
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="metric-card" shadow="hover">
          <div class="metric-content">
            <el-icon class="metric-icon" color="#409eff"><Connection /></el-icon>
            <div class="metric-info">
              <div class="metric-value">{{ stats.total_ips || 0 }}</div>
              <div class="metric-label">总 IP 数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="metric-card" shadow="hover">
          <div class="metric-content">
            <el-icon class="metric-icon" color="#67c23a"><Check /></el-icon>
            <div class="metric-info">
              <div class="metric-value">{{ stats.used_ips || 0 }}</div>
              <div class="metric-label">已用 IP 数</div>
              <div class="metric-sub">
                <el-tag size="small" type="info">
                  使用率: {{ calculateUsageRate() }}%
                </el-tag>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="metric-card" shadow="hover">
          <div class="metric-content">
            <el-icon class="metric-icon" color="#e6a23c"><Monitor /></el-icon>
            <div class="metric-info">
              <div class="metric-value">{{ stats.total_devices || 0 }}</div>
              <div class="metric-label">设备总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="metric-card" shadow="hover">
          <div class="metric-content">
            <el-icon class="metric-icon" color="#f56c6c"><Grid /></el-icon>
            <div class="metric-info">
              <div class="metric-value">{{ stats.total_segments || 0 }}</div>
              <div class="metric-label">网段总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Charts - 图表区域 -->
    <el-row :gutter="20" class="charts-row">
      <el-col :xs="24" :md="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>网段使用率分布</span>
              <el-tooltip content="点击柱状图查看详情" placement="top">
                <el-icon><InfoFilled /></el-icon>
              </el-tooltip>
            </div>
          </template>
          <div ref="segmentChartRef" class="chart" v-loading="chartLoading"></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>IP 状态分布</span>
            </div>
          </template>
          <div ref="ipStatusChartRef" class="chart" v-loading="chartLoading"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 设备统计图表 -->
    <el-row :gutter="20" class="charts-row">
      <el-col :xs="24">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>设备数量趋势</span>
              <el-radio-group v-model="deviceTrendDays" size="small" @change="fetchCharts">
                <el-radio-button :label="7">最近7天</el-radio-button>
                <el-radio-button :label="30">最近30天</el-radio-button>
                <el-radio-button :label="90">最近90天</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <div ref="deviceTrendChartRef" class="chart-large" v-loading="chartLoading"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Recent Activities -->
    <el-row :gutter="20">
      <el-col :xs="24" :md="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>最近操作</span>
              <el-button text type="primary" @click="$router.push('/logs')">
                查看更多
              </el-button>
            </div>
          </template>
          <el-timeline>
            <el-timeline-item
              v-for="log in recentLogs"
              :key="log.id"
              :timestamp="formatDate(log.created_at)"
              placement="top"
            >
              <p>
                <el-tag size="small">{{ formatOperationType(log.operation_type) }}</el-tag>
                {{ log.username }} {{ formatOperationType(log.operation_type) }}了
                {{ formatResourceType(log.resource_type) }}
              </p>
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>未解决告警</span>
              <el-button text type="primary" @click="$router.push('/alerts')">
                查看更多
              </el-button>
            </div>
          </template>
          <el-empty v-if="alerts.length === 0" description="暂无告警" />
          <el-timeline v-else>
            <el-timeline-item
              v-for="alert in alerts"
              :key="alert.id"
              :timestamp="formatDate(alert.created_at)"
              placement="top"
              :type="alert.severity === 'critical' ? 'danger' : 'warning'"
            >
              <p>{{ alert.message }}</p>
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import { getStats, getCharts } from '@/api/dashboard'
import { getLogs } from '@/api/logs'
import { getAlerts } from '@/api/alerts'
import { formatDate, formatOperationType, formatResourceType } from '@/utils/formatters'
import { Connection, Check, Monitor, Grid, InfoFilled, Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const RefreshIcon = Refresh

const stats = ref({})
const recentLogs = ref([])
const alerts = ref([])
const loading = ref(false)
const chartLoading = ref(false)
const dateRange = ref(null)
const deviceTrendDays = ref(30)

const segmentChartRef = ref(null)
const ipStatusChartRef = ref(null)
const deviceTrendChartRef = ref(null)

let segmentChart = null
let ipStatusChart = null
let deviceTrendChart = null
let refreshInterval = null

// 计算使用率（修改后的需求）
// 使用率 = (已用 IP + 保留 IP + 在线 IP) / 总 IP × 100%
function calculateUsageRate() {
  if (!stats.value.total_ips || stats.value.total_ips === 0) {
    return 0
  }
  const usedIps = stats.value.used_ips || 0
  const reservedIps = stats.value.reserved_ips || 0
  const onlineIps = stats.value.online_ips || 0
  const rate = ((usedIps + reservedIps + onlineIps) / stats.value.total_ips * 100).toFixed(2)
  return rate
}

async function fetchStats() {
  try {
    const response = await getStats()
    stats.value = response.data
  } catch (error) {
    console.error('Failed to fetch stats:', error)
    ElMessage.error('获取统计数据失败')
  }
}

async function fetchCharts() {
  chartLoading.value = true
  try {
    const response = await getCharts({ days: deviceTrendDays.value })
    const data = response.data
    
    // 网段使用率图表
    if (segmentChart && data.segment_usage_distribution) {
      const segmentData = data.segment_usage_distribution
      segmentChart.setOption({
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'shadow' },
          formatter: (params) => {
            const item = params[0]
            return `${item.name}<br/>使用率: ${item.value}%<br/>已用: ${segmentData[item.dataIndex].used_ips}/${segmentData[item.dataIndex].total_ips}`
          }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '15%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: segmentData.map(item => item.name),
          axisLabel: { 
            rotate: 45,
            interval: 0
          }
        },
        yAxis: {
          type: 'value',
          max: 100,
          axisLabel: { formatter: '{value}%' }
        },
        series: [{
          name: '使用率',
          type: 'bar',
          data: segmentData.map(item => item.usage_rate),
          itemStyle: {
            color: (params) => {
              const value = params.value
              if (value >= 80) return '#f56c6c'
              if (value >= 60) return '#e6a23c'
              return '#67c23a'
            }
          },
          label: {
            show: true,
            position: 'top',
            formatter: '{c}%'
          }
        }]
      })

      // 添加点击事件
      segmentChart.off('click')
      segmentChart.on('click', (params) => {
        const segment = segmentData[params.dataIndex]
        ElMessage.info(`网段: ${segment.name}, 使用率: ${segment.usage_rate}%`)
      })
    }

    // IP 状态分布图表
    if (ipStatusChart && data.ip_status_distribution) {
      const ipStatus = data.ip_status_distribution
      ipStatusChart.setOption({
        tooltip: {
          trigger: 'item',
          formatter: '{b}: {c} ({d}%)'
        },
        legend: {
          orient: 'vertical',
          left: 'left',
          top: 'center'
        },
        series: [{
          name: 'IP 状态',
          type: 'pie',
          radius: ['40%', '70%'],
          center: ['60%', '50%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 10,
            borderColor: '#fff',
            borderWidth: 2
          },
          label: {
            show: true,
            formatter: '{b}: {c}\n({d}%)'
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 16,
              fontWeight: 'bold'
            }
          },
          data: [
            { 
              value: ipStatus.available || 0, 
              name: '空闲', 
              itemStyle: { color: '#67c23a' } 
            },
            { 
              value: ipStatus.used || 0, 
              name: '已用', 
              itemStyle: { color: '#e6a23c' } 
            },
            { 
              value: ipStatus.reserved || 0, 
              name: '保留', 
              itemStyle: { color: '#909399' } 
            }
          ]
        }]
      })
    }

    // 设备统计趋势图表
    if (deviceTrendChart && data.device_statistics) {
      const deviceStats = data.device_statistics
      deviceTrendChart.setOption({
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'cross'
          }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: deviceStats.dates || []
        },
        yAxis: {
          type: 'value',
          name: '设备数量'
        },
        series: [
          {
            name: '设备总数',
            type: 'line',
            smooth: true,
            data: deviceStats.counts || [],
            areaStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: 'rgba(64, 158, 255, 0.5)' },
                { offset: 1, color: 'rgba(64, 158, 255, 0.1)' }
              ])
            },
            itemStyle: {
              color: '#409eff'
            },
            lineStyle: {
              width: 2
            }
          }
        ]
      })
    }
  } catch (error) {
    console.error('Failed to fetch charts:', error)
    ElMessage.error('获取图表数据失败')
  } finally {
    chartLoading.value = false
  }
}

async function fetchRecentLogs() {
  try {
    const response = await getLogs({ page: 1, page_size: 5 })
    recentLogs.value = response.data.items || []
  } catch (error) {
    console.error('Failed to fetch logs:', error)
  }
}

async function fetchAlerts() {
  try {
    const response = await getAlerts({ is_resolved: false, page: 1, page_size: 5 })
    alerts.value = response.data.items || []
  } catch (error) {
    console.error('Failed to fetch alerts:', error)
  }
}

function initCharts() {
  if (segmentChartRef.value) {
    segmentChart = echarts.init(segmentChartRef.value)
  }
  if (ipStatusChartRef.value) {
    ipStatusChart = echarts.init(ipStatusChartRef.value)
  }
  if (deviceTrendChartRef.value) {
    deviceTrendChart = echarts.init(deviceTrendChartRef.value)
  }
}

function resizeCharts() {
  segmentChart?.resize()
  ipStatusChart?.resize()
  deviceTrendChart?.resize()
}

async function refreshData() {
  await Promise.all([
    fetchStats(),
    fetchCharts(),
    fetchRecentLogs(),
    fetchAlerts()
  ])
}

// 手动刷新
async function handleRefresh() {
  loading.value = true
  try {
    await refreshData()
    ElMessage.success('数据已刷新')
  } catch (error) {
    ElMessage.error('刷新失败')
  } finally {
    loading.value = false
  }
}

// 时间范围变化处理
function handleDateRangeChange(value) {
  if (value) {
    console.log('Date range changed:', value)
    // 这里可以根据时间范围重新获取数据
    // 目前后端 API 支持 days 参数，可以扩展支持具体日期范围
  }
}

onMounted(async () => {
  initCharts()
  await refreshData()
  
  // 自动刷新：每 5 分钟
  refreshInterval = setInterval(refreshData, 5 * 60 * 1000)
  
  // 处理窗口大小变化
  window.addEventListener('resize', resizeCharts)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
  segmentChart?.dispose()
  ipStatusChart?.dispose()
  deviceTrendChart?.dispose()
  window.removeEventListener('resize', resizeCharts)
})
</script>

<style scoped>
.dashboard-container {
  padding: 12px;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 0 4px;
}

.dashboard-header h2 {
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.header-actions {
  display: flex;
  align-items: center;
}

.metrics-row {
  margin-bottom: 12px;
}

.metric-card {
  cursor: pointer;
  transition: transform 0.3s, box-shadow 0.3s;
  height: 100%;
}

.metric-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.metric-content {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 10px 0;
}

.metric-icon {
  font-size: 40px;
  flex-shrink: 0;
}

.metric-info {
  flex: 1;
  min-width: 0;
}

.metric-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  line-height: 1.2;
}

.metric-label {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}

.metric-sub {
  margin-top: 6px;
}

.charts-row {
  margin-bottom: 12px;
}

.chart {
  height: 320px;
  width: 100%;
}

.chart-large {
  height: 380px;
  width: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .dashboard-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .header-actions {
    width: 100%;
    flex-direction: column;
    gap: 10px;
  }
  
  .metric-value {
    font-size: 24px;
  }
  
  .metric-icon {
    font-size: 32px;
  }
  
  .chart {
    height: 280px;
  }
  
  .chart-large {
    height: 300px;
  }
}
</style>
