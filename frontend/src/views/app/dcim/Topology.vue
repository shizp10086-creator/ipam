<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
      <h3>网络拓扑</h3>
      <div>
        <el-radio-group v-model="layout" size="small">
          <el-radio-button label="tree">树形</el-radio-button>
          <el-radio-button label="star">星形</el-radio-button>
        </el-radio-group>
        <el-button size="small" @click="loadTopology" style="margin-left:8px;">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
      </div>
    </div>

    <el-card v-loading="loading">
      <!-- 拓扑图区域 -->
      <div class="topo-container" ref="topoRef">
        <div v-if="devices.length === 0" style="text-align:center;padding:60px;color:#909399;">
          <p>暂无设备数据，请先在设备管理中添加网络设备</p>
        </div>

        <!-- 树形布局 -->
        <div v-else-if="layout === 'tree'" class="topo-tree">
          <!-- 核心层 -->
          <div class="topo-level">
            <div class="level-label">核心层</div>
            <div class="level-nodes">
              <div v-for="d in coreDevices" :key="d.id" class="topo-node core"
                @click="showDetail(d)" :class="{online: d.is_online, offline: !d.is_online}">
                <div class="node-icon">🔲</div>
                <div class="node-name">{{ d.name || d.ip_address }}</div>
                <div class="node-status">{{ d.is_online ? '在线' : '离线' }}</div>
              </div>
            </div>
          </div>
          <div class="topo-connector">│</div>
          <!-- 汇聚层 -->
          <div class="topo-level">
            <div class="level-label">汇聚层</div>
            <div class="level-nodes">
              <div v-for="d in aggDevices" :key="d.id" class="topo-node agg"
                @click="showDetail(d)" :class="{online: d.is_online, offline: !d.is_online}">
                <div class="node-icon">🔳</div>
                <div class="node-name">{{ d.name || d.ip_address }}</div>
                <div class="node-status">{{ d.is_online ? '在线' : '离线' }}</div>
              </div>
            </div>
          </div>
          <div class="topo-connector">│</div>
          <!-- 接入层 -->
          <div class="topo-level">
            <div class="level-label">接入层</div>
            <div class="level-nodes">
              <div v-for="d in accessDevices" :key="d.id" class="topo-node access"
                @click="showDetail(d)" :class="{online: d.is_online, offline: !d.is_online}">
                <div class="node-icon">📡</div>
                <div class="node-name">{{ d.name || d.ip_address }}</div>
                <div class="node-status">{{ d.is_online ? '在线' : '离线' }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 星形布局 -->
        <div v-else class="topo-star">
          <div class="star-center">
            <div class="topo-node core online" style="width:100px;height:100px;">
              <div class="node-icon" style="font-size:32px;">🔲</div>
              <div class="node-name">核心</div>
            </div>
          </div>
          <div class="star-ring">
            <div v-for="(d, i) in devices.slice(0, 12)" :key="d.id"
              class="topo-node access" :class="{online: d.is_online, offline: !d.is_online}"
              :style="starPosition(i, Math.min(devices.length, 12))"
              @click="showDetail(d)">
              <div class="node-icon">📡</div>
              <div class="node-name">{{ d.name || d.ip_address }}</div>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 设备详情弹窗 -->
    <el-drawer v-model="showDrawer" :title="detailDevice?.name || '设备详情'" size="400px">
      <el-descriptions :column="1" border v-if="detailDevice">
        <el-descriptions-item label="设备名称">{{ detailDevice.name }}</el-descriptions-item>
        <el-descriptions-item label="IP 地址">{{ detailDevice.ip_address || '-' }}</el-descriptions-item>
        <el-descriptions-item label="MAC 地址">{{ detailDevice.mac_address || '-' }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="detailDevice.is_online ? 'success' : 'danger'" size="small">
            {{ detailDevice.is_online ? '在线' : '离线' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="设备类型">{{ detailDevice.device_type || '-' }}</el-descriptions-item>
        <el-descriptions-item label="厂商">{{ detailDevice.manufacturer || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/api/request'

const layout = ref('tree')
const loading = ref(false)
const devices = ref([])
const showDrawer = ref(false)
const detailDevice = ref(null)

// 按设备类型简单分层（实际应根据设备角色/标签分层）
const coreDevices = computed(() => devices.value.filter((_, i) => i < 2))
const aggDevices = computed(() => devices.value.filter((_, i) => i >= 2 && i < 6))
const accessDevices = computed(() => devices.value.filter((_, i) => i >= 6))

async function loadTopology() {
  loading.value = true
  try {
    const r = await request.get('/devices/')
    devices.value = r.data?.items || r.data || []
  } catch (e) {
    ElMessage.error('加载设备数据失败')
  }
  loading.value = false
}

function showDetail(d) {
  detailDevice.value = d
  showDrawer.value = true
}

function starPosition(index, total) {
  const angle = (index / total) * 2 * Math.PI - Math.PI / 2
  const radius = 180
  const x = Math.cos(angle) * radius
  const y = Math.sin(angle) * radius
  return { transform: `translate(${x}px, ${y}px)` }
}

onMounted(loadTopology)
</script>

<style scoped>
.topo-container { min-height: 500px; position: relative; }
.topo-tree { display: flex; flex-direction: column; align-items: center; padding: 24px; }
.topo-level { display: flex; align-items: center; gap: 16px; }
.level-label { writing-mode: vertical-lr; color: #909399; font-size: 12px; width: 20px; }
.level-nodes { display: flex; gap: 16px; flex-wrap: wrap; justify-content: center; }
.topo-connector { color: #dcdfe6; font-size: 24px; text-align: center; }
.topo-node {
  width: 80px; padding: 8px; border-radius: 8px; text-align: center; cursor: pointer;
  border: 2px solid #e4e7ed; transition: all 0.2s; background: #fff;
}
.topo-node:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
.topo-node.online { border-color: #67c23a; }
.topo-node.offline { border-color: #f56c6c; background: #fef0f0; }
.topo-node.core { border-width: 3px; }
.node-icon { font-size: 24px; margin-bottom: 4px; }
.node-name { font-size: 11px; color: #303133; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.node-status { font-size: 10px; color: #909399; }
.topo-star { position: relative; height: 500px; display: flex; align-items: center; justify-content: center; }
.star-center { z-index: 2; }
.star-ring { position: absolute; }
.star-ring .topo-node { position: absolute; left: -40px; top: -30px; }
</style>
