<template>
  <div class="global-search">
    <el-popover
      :visible="showResults"
      placement="bottom-start"
      :width="600"
      trigger="manual"
      popper-class="search-popover"
    >
      <template #reference>
        <el-input
          v-model="searchQuery"
          placeholder="搜索网段、IP、设备..."
          :prefix-icon="Search"
          clearable
          @input="handleSearch"
          @focus="handleFocus"
          @blur="handleBlur"
          @keyup.enter="handleEnter"
          class="search-input"
        />
      </template>

      <div class="search-results" v-loading="loading">
        <!-- 无结果 -->
        <el-empty v-if="!loading && searched && totalResults === 0" description="未找到匹配结果" :image-size="80" />

        <!-- 有结果 -->
        <div v-if="totalResults > 0" class="results-container">
          <!-- 网段结果 -->
          <div v-if="results.segments && results.segments.length > 0" class="result-section">
            <div class="section-title">
              <el-icon><Network /></el-icon>
              <span>网段 ({{ results.segments.length }})</span>
            </div>
            <div
              v-for="item in results.segments"
              :key="`segment-${item.id}`"
              class="result-item"
              @click="navigateTo('segment', item.id)"
            >
              <div class="item-main">
                <span class="item-name">{{ item.name }}</span>
                <el-tag size="small">{{ item.cidr }}</el-tag>
              </div>
              <div class="item-desc" v-if="item.description">{{ item.description }}</div>
            </div>
          </div>

          <!-- IP 地址结果 -->
          <div v-if="results.ips && results.ips.length > 0" class="result-section">
            <div class="section-title">
              <el-icon><Connection /></el-icon>
              <span>IP 地址 ({{ results.ips.length }})</span>
            </div>
            <div
              v-for="item in results.ips"
              :key="`ip-${item.id}`"
              class="result-item"
              @click="navigateTo('ip', item.id)"
            >
              <div class="item-main">
                <span class="item-name">{{ item.ip_address }}</span>
                <el-tag :type="getStatusType(item.status)" size="small">
                  {{ getStatusText(item.status) }}
                </el-tag>
                <el-tag v-if="item.is_online" type="success" size="small">在线</el-tag>
              </div>
              <div class="item-desc" v-if="item.segment_name">
                网段: {{ item.segment_name }} ({{ item.segment_cidr }})
              </div>
            </div>
          </div>

          <!-- 设备结果 -->
          <div v-if="results.devices && results.devices.length > 0" class="result-section">
            <div class="section-title">
              <el-icon><Monitor /></el-icon>
              <span>设备 ({{ results.devices.length }})</span>
            </div>
            <div
              v-for="item in results.devices"
              :key="`device-${item.id}`"
              class="result-item"
              @click="navigateTo('device', item.id)"
            >
              <div class="item-main">
                <span class="item-name">{{ item.name }}</span>
                <el-tag size="small">{{ item.mac_address }}</el-tag>
              </div>
              <div class="item-desc">
                <span v-if="item.device_type">{{ item.device_type }}</span>
                <span v-if="item.owner"> · {{ item.owner }}</span>
                <span v-if="item.location"> · {{ item.location }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-popover>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Search, Grid, Link, Monitor } from '@element-plus/icons-vue'
import { globalSearch } from '@/api/search'
import { debounce } from 'lodash-es'

const router = useRouter()

const searchQuery = ref('')
const loading = ref(false)
const showResults = ref(false)
const searched = ref(false)
const results = ref({
  segments: [],
  ips: [],
  devices: []
})

const totalResults = computed(() => {
  return (results.value.segments?.length || 0) +
         (results.value.ips?.length || 0) +
         (results.value.devices?.length || 0)
})

// 防抖搜索
const handleSearch = debounce(async () => {
  const query = searchQuery.value.trim()
  
  if (!query) {
    showResults.value = false
    searched.value = false
    return
  }
  
  if (query.length < 2) {
    return
  }
  
  loading.value = true
  searched.value = true
  showResults.value = true
  
  try {
    const response = await globalSearch(query, 10)
    results.value = {
      segments: response.data.segments || [],
      ips: response.data.ips || [],
      devices: response.data.devices || []
    }
  } catch (error) {
    console.error('Search error:', error)
  } finally {
    loading.value = false
  }
}, 300)

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

// 导航到详情页
function navigateTo(type, id) {
  showResults.value = false
  searchQuery.value = ''
  
  const routeMap = {
    'segment': { name: 'SegmentDetail', params: { id } },
    'ip': { name: 'IPDetail', params: { id } },
    'device': { name: 'DeviceDetail', params: { id } }
  }
  
  if (routeMap[type]) {
    router.push(routeMap[type])
  }
}

// 处理焦点
function handleFocus() {
  if (searchQuery.value && searched.value) {
    showResults.value = true
  }
}

// 处理失焦
function handleBlur() {
  // 延迟关闭，以便点击结果项
  setTimeout(() => {
    showResults.value = false
  }, 200)
}

// 处理回车
function handleEnter() {
  if (totalResults.value === 1) {
    // 如果只有一个结果，直接跳转
    if (results.value.segments.length === 1) {
      navigateTo('segment', results.value.segments[0].id)
    } else if (results.value.ips.length === 1) {
      navigateTo('ip', results.value.ips[0].id)
    } else if (results.value.devices.length === 1) {
      navigateTo('device', results.value.devices[0].id)
    }
  }
}
</script>

<style scoped>
.global-search {
  width: 300px;
}

.search-input {
  width: 100%;
}

.search-results {
  max-height: 500px;
  overflow-y: auto;
}

.results-container {
  padding: 8px 0;
}

.result-section {
  margin-bottom: 16px;
}

.result-section:last-child {
  margin-bottom: 0;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  font-size: 13px;
  font-weight: 600;
  color: #606266;
  background-color: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 4px;
}

.result-item {
  padding: 10px 12px;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s;
}

.result-item:hover {
  background-color: #f5f7fa;
}

.item-main {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.item-name {
  font-weight: 500;
  color: #303133;
}

.item-desc {
  font-size: 12px;
  color: #909399;
  margin-left: 0;
}
</style>

<style>
.search-popover {
  padding: 8px !important;
}
</style>
