<template>
  <div class="rack-page">
    <!-- 顶部操作栏 -->
    <div class="page-header">
      <div class="header-left">
        <h3>机架管理</h3>
        <el-tag type="info" size="small">{{ racks.length }} 个机架</el-tag>
      </div>
      <div class="header-right">
        <el-select v-model="filterDc" placeholder="筛选机房" clearable size="default" style="width:180px;margin-right:8px;">
          <el-option v-for="dc in rooms" :key="dc.id" :label="dc.name" :value="dc.id" />
        </el-select>
        <el-radio-group v-model="viewMode" size="small" style="margin-right:8px;">
          <el-radio-button label="visual">可视化</el-radio-button>
          <el-radio-button label="table">表格</el-radio-button>
        </el-radio-group>
        <el-button type="primary" @click="showCreate=true"><el-icon><Plus /></el-icon> 新建机架</el-button>
      </div>
    </div>

    <!-- 可视化视图：机柜卡片 -->
    <div v-if="viewMode==='visual'" class="rack-visual-grid">
      <div v-for="rack in filteredRacks" :key="rack.id" class="rack-card" @click="selectRack(rack)">
        <!-- 机柜头部 -->
        <div class="rack-card-header">
          <span class="rack-name">{{ rack.name }}</span>
          <el-tag :type="getUsageColor(rack)" size="small">{{ Math.round((rack.used_u/rack.total_u)*100) }}%</el-tag>
        </div>
        <!-- 机柜正面可视化 -->
        <div class="rack-cabinet">
          <div class="cabinet-frame">
            <div v-for="u in rack.total_u" :key="u" class="cabinet-u"
              :class="getUClass(rack.id, rack.total_u - u + 1)">
              <span class="u-num">{{ rack.total_u - u + 1 }}</span>
            </div>
          </div>
        </div>
        <!-- 机柜底部统计 -->
        <div class="rack-card-footer">
          <div class="stat-item">
            <span class="stat-label">空间</span>
            <span class="stat-value">{{ rack.used_u }}/{{ rack.total_u }}U</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">功率</span>
            <span class="stat-value">{{ rack.current_power || 0 }}W</span>
          </div>
        </div>
      </div>
      <div v-if="filteredRacks.length===0" style="width:100%;text-align:center;padding:60px;color:#909399;">
        暂无机架数据
      </div>
    </div>

    <!-- 表格视图 -->
    <el-table v-else :data="filteredRacks" stripe v-loading="loading" @row-click="selectRack" style="cursor:pointer;">
      <el-table-column prop="name" label="机架名称" width="140" />
      <el-table-column label="空间使用率" width="200">
        <template #default="{row}">
          <el-progress :percentage="Math.round((row.used_u/row.total_u)*100)" :color="getProgressColor(row)" :stroke-width="14" :text-inside="true" />
        </template>
      </el-table-column>
      <el-table-column label="U 位" width="100">
        <template #default="{row}">{{ row.used_u }}/{{ row.total_u }}U</template>
      </el-table-column>
      <el-table-column label="功率使用率" width="200">
        <template #default="{row}">
          <el-progress v-if="row.rated_power" :percentage="Math.round(((row.current_power||0)/row.rated_power)*100)" :color="getProgressColor(row)" :stroke-width="14" :text-inside="true" />
          <span v-else style="color:#909399;">未设置</span>
        </template>
      </el-table-column>
      <el-table-column prop="rated_power" label="额定功率(W)" width="120" />
      <el-table-column prop="current_power" label="当前功耗(W)" width="120" />
      <el-table-column label="操作" width="100">
        <template #default="{row}">
          <el-button link size="small" type="primary" @click.stop="selectRack(row)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 机架详情抽屉 -->
    <el-drawer v-model="showDetail" :title="selectedRack?.name + ' — 机架详情'" size="680px" direction="rtl">
      <template v-if="selectedRack">
        <!-- 概览卡片 -->
        <el-row :gutter="12" style="margin-bottom:16px;">
          <el-col :span="6">
            <div class="overview-card">
              <div class="ov-value">{{ selectedRack.total_u }}</div>
              <div class="ov-label">总 U 数</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="overview-card">
              <div class="ov-value" style="color:#409eff;">{{ selectedRack.used_u }}</div>
              <div class="ov-label">已用 U</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="overview-card">
              <div class="ov-value" style="color:#67c23a;">{{ selectedRack.total_u - selectedRack.used_u }}</div>
              <div class="ov-label">空闲 U</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="overview-card">
              <div class="ov-value" :style="{color: (selectedRack.used_u/selectedRack.total_u)>0.8?'#f56c6c':'#303133'}">
                {{ Math.round((selectedRack.used_u/selectedRack.total_u)*100) }}%
              </div>
              <div class="ov-label">使用率</div>
            </div>
          </el-col>
        </el-row>

        <!-- 正面/背面切换 -->
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
          <el-radio-group v-model="rackFace" size="small">
            <el-radio-button label="front">正面</el-radio-button>
            <el-radio-button label="rear">背面</el-radio-button>
          </el-radio-group>
          <el-button size="small" type="primary" @click="showInstall=true">
            <el-icon><Plus /></el-icon> 设备上架
          </el-button>
        </div>

        <!-- U 位可视化（仿真机柜） -->
        <div class="rack-detail-cabinet">
          <div class="cabinet-ruler">
            <div v-for="u in selectedRack.total_u" :key="u" class="ruler-u">
              {{ selectedRack.total_u - u + 1 }}
            </div>
          </div>
          <div class="cabinet-body">
            <div v-for="u in selectedRack.total_u" :key="u" class="detail-u"
              :class="getDetailUClass(selectedRack.total_u - u + 1)"
              @click="handleUClick(selectedRack.total_u - u + 1)">
              <template v-if="getDeviceAtU(selectedRack.total_u - u + 1)">
                <div class="device-bar" :style="getDeviceBarStyle(selectedRack.total_u - u + 1)"
                  :class="'dtype-' + (getDeviceAtU(selectedRack.total_u - u + 1).device_type || 'server')">
                  <!-- 仿真设备面板 -->
                  <div class="device-faceplate">
                    <span class="device-leds">
                      <i class="led led-green"></i>
                      <i class="led led-green"></i>
                    </span>
                    <span class="device-type-icon">{{ deviceTypeIcon(getDeviceAtU(selectedRack.total_u - u + 1).device_type) }}</span>
                    <span class="device-name">{{ getDeviceAtU(selectedRack.total_u - u + 1).device_name }}</span>
                    <span class="device-ports" v-if="['switch','router'].includes(getDeviceAtU(selectedRack.total_u - u + 1).device_type)">
                      <i v-for="p in 8" :key="p" class="port-dot"></i>
                    </span>
                    <span class="device-u-badge">{{ getDeviceAtU(selectedRack.total_u - u + 1).u_size }}U</span>
                  </div>
                </div>
              </template>
              <template v-else>
                <div class="empty-slot">空闲</div>
              </template>
            </div>
          </div>
        </div>

        <!-- 已安装设备列表 -->
        <h4 style="margin:16px 0 8px;">已安装设备</h4>
        <el-table :data="installations" size="small" stripe>
          <el-table-column label="U 位" width="80">
            <template #default="{row}">U{{ row.start_u }}-U{{ row.start_u + row.u_size - 1 }}</template>
          </el-table-column>
          <el-table-column label="设备" min-width="160">
            <template #default="{row}">
              <span>{{ deviceTypeIcon(row.device_type) }} {{ row.device_name }}</span>
            </template>
          </el-table-column>
          <el-table-column label="类型" width="80">
            <template #default="{row}">
              <el-tag size="small" :type="deviceTagType(row.device_type)">{{ deviceTypeName(row.device_type) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="u_size" label="占用U" width="60" />
          <el-table-column prop="face" label="面" width="50" />
          <el-table-column label="功耗" width="70">
            <template #default="{row}">{{ row.power_consumption ? row.power_consumption + 'W' : '-' }}</template>
          </el-table-column>
          <el-table-column prop="pdu_port" label="PDU" width="80" />
          <el-table-column label="操作" width="60">
            <template #default="{row}">
              <el-popconfirm title="确定下架？" @confirm="uninstall(row.id)">
                <template #reference>
                  <el-button link size="small" type="danger">下架</el-button>
                </template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>
      </template>
    </el-drawer>

    <!-- 新建机架对话框 -->
    <el-dialog title="新建机架" v-model="showCreate" width="480px">
      <el-form :model="createForm" label-width="90px">
        <el-form-item label="机架名称" required><el-input v-model="createForm.name" placeholder="如 A-01" /></el-form-item>
        <el-form-item label="所属机房" required>
          <el-select v-model="createForm.datacenter_id" style="width:100%" placeholder="选择机房">
            <el-option v-for="dc in rooms" :key="dc.id" :label="dc.name" :value="dc.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="总 U 数"><el-input-number v-model="createForm.total_u" :min="1" :max="60" /></el-form-item>
        <el-form-item label="额定功率(W)"><el-input-number v-model="createForm.rated_power" :min="0" style="width:100%" /></el-form-item>
        <el-form-item label="承重(kg)"><el-input-number v-model="createForm.max_weight" :min="0" style="width:100%" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate=false">取消</el-button>
        <el-button type="primary" @click="createRack" :loading="saving">确定</el-button>
      </template>
    </el-dialog>

    <!-- 设备上架对话框 -->
    <el-dialog title="设备上架" v-model="showInstall" width="450px">
      <el-form :model="installForm" label-width="90px">
        <el-form-item label="设备ID" required><el-input-number v-model="installForm.device_id" :min="1" style="width:100%" /></el-form-item>
        <el-form-item label="起始U位" required><el-input-number v-model="installForm.start_u" :min="1" :max="selectedRack?.total_u" /></el-form-item>
        <el-form-item label="占用U数" required><el-input-number v-model="installForm.u_size" :min="1" :max="10" /></el-form-item>
        <el-form-item label="安装面">
          <el-radio-group v-model="installForm.face">
            <el-radio label="front">正面</el-radio>
            <el-radio label="rear">背面</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="功耗(W)"><el-input-number v-model="installForm.power_consumption" :min="0" style="width:100%" /></el-form-item>
        <el-form-item label="PDU端口"><el-input v-model="installForm.pdu_port" placeholder="如 A1-P3" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showInstall=false">取消</el-button>
        <el-button type="primary" @click="installDevice" :loading="installing">上架</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/api/request'

const racks = ref([]), rooms = ref([]), loading = ref(false)
const viewMode = ref('visual'), filterDc = ref(null)
const showCreate = ref(false), saving = ref(false)
const showDetail = ref(false), selectedRack = ref(null), rackFace = ref('front')
const showInstall = ref(false), installing = ref(false)
const installations = ref([]), rackUMap = ref({})

const createForm = ref({ name:'', datacenter_id:null, total_u:42, rated_power:5000, max_weight:null })
const installForm = ref({ device_id:null, start_u:1, u_size:1, face:'front', power_consumption:null, pdu_port:'' })

const filteredRacks = computed(() => {
  if (!filterDc.value) return racks.value
  return racks.value.filter(r => r.datacenter_id === filterDc.value)
})

// 机柜卡片中每个 U 的样式
const rackUMaps = ref({}) // rack_id -> u_map
function getUClass(rackId, u) {
  const map = rackUMaps.value[rackId]
  if (map && map[u]) return 'u-occupied'
  return 'u-empty'
}

function getUsageColor(rack) {
  const pct = rack.used_u / rack.total_u
  if (pct >= 0.9) return 'danger'
  if (pct >= 0.7) return 'warning'
  return 'success'
}

function getProgressColor(rack) {
  const pct = rack.used_u / rack.total_u
  if (pct >= 0.9) return '#f56c6c'
  if (pct >= 0.7) return '#e6a23c'
  return '#409eff'
}

// 详情视图中的 U 位
function getDetailUClass(u) {
  if (rackUMap.value[u]) return 'detail-u-occupied'
  return 'detail-u-empty'
}

function getDeviceAtU(u) {
  const info = rackUMap.value[u]
  if (!info) return null
  const inst = installations.value.find(i => i.id === info.installation_id)
  if (inst && u === inst.start_u) return inst // 只在起始 U 位显示设备信息
  return null
}

function getDeviceBarStyle(u) {
  const inst = installations.value.find(i => i.id === rackUMap.value[u]?.installation_id && i.start_u === u)
  if (!inst) return {}
  return { height: `${inst.u_size * 28 - 2}px` }
}

function handleUClick(u) {
  if (!rackUMap.value[u]) {
    installForm.value.start_u = u
    showInstall.value = true
  }
}

function deviceTypeIcon(type) {
  const icons = {
    server: '🖥️', switch: '🔲', router: '🌐', firewall: '🛡️',
    ups: '🔋', pdu: '⚡', storage: '💾', ap: '📡', other: '📦'
  }
  return icons[type] || icons.server
}

function deviceTypeName(type) {
  const names = {
    server: '服务器', switch: '交换机', router: '路由器', firewall: '防火墙',
    ups: 'UPS', pdu: 'PDU', storage: '存储', ap: 'AP', other: '其他'
  }
  return names[type] || type || '服务器'
}

function deviceTagType(type) {
  const types = { server: '', switch: 'success', router: 'warning', firewall: 'danger', ups: 'info', storage: '' }
  return types[type] || ''
}

async function loadRacks() {
  loading.value = true
  try {
    const r = await request.get('/dcim/racks')
    racks.value = r.data?.items || []
  } catch(e) {}
  loading.value = false
}

async function loadRooms() {
  try {
    const r = await request.get('/dcim/datacenters?dc_type=room')
    rooms.value = r.data?.items || []
  } catch(e) {}
}

async function selectRack(rack) {
  try {
    const r = await request.get(`/dcim/racks/${rack.id}`)
    selectedRack.value = r.data
    rackUMap.value = r.data?.u_map || {}
    installations.value = r.data?.installations || []
    showDetail.value = true
  } catch(e) { ElMessage.error('加载失败') }
}

async function createRack() {
  if (!createForm.value.name || !createForm.value.datacenter_id) { ElMessage.warning('请填写完整'); return }
  saving.value = true
  try {
    await request.post('/dcim/racks', createForm.value)
    ElMessage.success('创建成功'); showCreate.value = false; loadRacks()
    createForm.value = { name:'', datacenter_id:null, total_u:42, rated_power:5000, max_weight:null }
  } catch(e) { ElMessage.error('创建失败') }
  saving.value = false
}

async function installDevice() {
  if (!installForm.value.device_id) { ElMessage.warning('请填写设备ID'); return }
  installing.value = true
  try {
    await request.post('/dcim/racks/install', { rack_id: selectedRack.value.id, ...installForm.value })
    ElMessage.success('上架成功')
    showInstall.value = false
    selectRack(selectedRack.value) // 刷新详情
    loadRacks() // 刷新列表
  } catch(e) { ElMessage.error(e.response?.data?.message || '上架失败') }
  installing.value = false
}

async function uninstall(installationId) {
  try {
    await request.post(`/dcim/racks/uninstall/${installationId}`)
    ElMessage.success('下架成功')
    selectRack(selectedRack.value)
    loadRacks()
  } catch(e) { ElMessage.error('下架失败') }
}

onMounted(() => { loadRacks(); loadRooms() })
</script>

<style scoped>
.rack-page { height: 100%; }
.page-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; }
.header-left { display:flex; align-items:center; gap:12px; }
.header-right { display:flex; align-items:center; }

/* 可视化网格 */
.rack-visual-grid { display:flex; flex-wrap:wrap; gap:16px; }
.rack-card {
  width: 160px; background:#fff; border:1px solid #e4e7ed; border-radius:8px;
  cursor:pointer; transition:all 0.2s; overflow:hidden;
}
.rack-card:hover { border-color:#409eff; box-shadow:0 4px 12px rgba(64,158,255,0.15); transform:translateY(-2px); }
.rack-card-header { padding:8px 10px; display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #f0f0f0; }
.rack-name { font-weight:600; font-size:13px; }

/* 机柜缩略图 */
.rack-cabinet { padding:6px 10px; }
.cabinet-frame { border:2px solid #606266; border-radius:3px; background:#1d1e1f; padding:1px; }
.cabinet-u { height:3px; margin:0.5px 1px; border-radius:1px; }
.u-occupied { background:#409eff; }
.u-empty { background:#3a3b3c; }
.u-num { display:none; }

.rack-card-footer { padding:6px 10px; display:flex; justify-content:space-between; border-top:1px solid #f0f0f0; }
.stat-item { text-align:center; }
.stat-label { display:block; font-size:10px; color:#909399; }
.stat-value { display:block; font-size:12px; font-weight:600; color:#303133; }

/* 概览卡片 */
.overview-card { background:#f5f7fa; border-radius:8px; padding:12px; text-align:center; }
.ov-value { font-size:24px; font-weight:700; color:#303133; }
.ov-label { font-size:12px; color:#909399; margin-top:4px; }

/* 详情机柜视图 */
.rack-detail-cabinet { display:flex; border:2px solid #303133; border-radius:6px; background:#1d1e1f; overflow:hidden; }
.cabinet-ruler { width:30px; background:#263238; flex-shrink:0; }
.ruler-u { height:28px; display:flex; align-items:center; justify-content:center; font-size:10px; color:#78909c; border-bottom:1px solid #37474f; }
.cabinet-body { flex:1; }
.detail-u { height:28px; border-bottom:1px solid #2c2d2e; position:relative; display:flex; align-items:center; }
.detail-u-empty { background:#2a2b2c; cursor:pointer; }
.detail-u-empty:hover { background:#3a3b3c; }
.detail-u-occupied { background:#1a3a5c; }
.empty-slot { color:#555; font-size:10px; padding-left:8px; }
.device-bar {
  position:absolute; left:2px; right:2px; top:1px;
  border-radius:3px; display:flex; align-items:center;
  color:#fff; font-size:11px; z-index:1; overflow:hidden;
}
/* 设备类型颜色 */
.dtype-server .device-faceplate { background:linear-gradient(135deg, #37474f 0%, #263238 100%); }
.dtype-switch .device-faceplate { background:linear-gradient(135deg, #1565c0 0%, #0d47a1 100%); }
.dtype-router .device-faceplate { background:linear-gradient(135deg, #2e7d32 0%, #1b5e20 100%); }
.dtype-firewall .device-faceplate { background:linear-gradient(135deg, #c62828 0%, #b71c1c 100%); }
.dtype-ups .device-faceplate { background:linear-gradient(135deg, #f57f17 0%, #e65100 100%); }
.dtype-pdu .device-faceplate { background:linear-gradient(135deg, #6a1b9a 0%, #4a148c 100%); }
.dtype-storage .device-faceplate { background:linear-gradient(135deg, #00838f 0%, #006064 100%); }
.dtype-ap .device-faceplate { background:linear-gradient(135deg, #558b2f 0%, #33691e 100%); }

.device-faceplate {
  width:100%; height:100%; display:flex; align-items:center; gap:4px; padding:0 6px;
  border-radius:3px; border:1px solid rgba(255,255,255,0.15);
  background:linear-gradient(135deg, #37474f 0%, #263238 100%);
}
.device-leds { display:flex; gap:2px; flex-shrink:0; }
.led { width:4px; height:4px; border-radius:50%; display:inline-block; }
.led-green { background:#4caf50; box-shadow:0 0 3px #4caf50; }
.device-type-icon { font-size:13px; flex-shrink:0; }
.device-name { flex:1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; font-size:11px; }
.device-ports { display:flex; gap:1px; flex-shrink:0; }
.port-dot { width:3px; height:6px; background:rgba(255,255,255,0.4); border-radius:1px; display:inline-block; }
.device-u-badge {
  font-size:9px; background:rgba(0,0,0,0.3); padding:1px 4px; border-radius:2px; flex-shrink:0;
}
.device-icon { font-size:14px; }
.device-u-info { font-size:10px; opacity:0.8; flex-shrink:0; }
</style>
