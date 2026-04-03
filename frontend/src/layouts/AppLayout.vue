<template>
  <div class="app-layout">
    <!-- 模拟预览提示条 -->
    <div v-if="isSimulating" class="simulate-bar">
      ⚠️ 当前正在模拟【{{ simulateRole }} - {{ simulateUser }}】的视角
      <el-button size="small" type="warning" @click="exitSimulate">退出模拟</el-button>
    </div>

    <!-- 顶栏：Logo + 一级导航 + 右侧工具 -->
    <div class="app-header">
      <div class="header-left">
        <span class="logo">IT 智维平台</span>
      </div>
      <div class="header-nav">
        <div
          v-for="item in topMenus"
          :key="item.key"
          class="nav-item"
          :class="{ active: activeTopMenu === item.key }"
          @click="handleTopMenuClick(item)"
        >
          <el-icon :size="16"><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </div>
      </div>
      <div class="header-right">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索 IP / 设备 / 网段..."
          prefix-icon="Search"
          clearable
          class="global-search"
          @keyup.enter="handleSearch"
        />
        <el-badge :value="alertCount" :hidden="alertCount === 0" class="alert-badge">
          <el-icon class="header-icon" @click="$router.push('/app/alerts')"><Bell /></el-icon>
        </el-badge>
        <el-button v-if="isAdmin" type="primary" link @click="switchToAdmin">
          <el-icon><Setting /></el-icon> 设计态
        </el-button>
        <el-dropdown trigger="click">
          <span class="user-info">
            <el-avatar :size="26">{{ userInitial }}</el-avatar>
            <span>{{ userName }}</span>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="$router.push('/app/settings')">个人设置</el-dropdown-item>
              <el-dropdown-item divided @click="handleLogout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <div class="app-body">
      <!-- 左侧二级菜单 -->
      <div v-if="currentSubMenus.length > 0" class="app-sidebar">
        <el-menu :default-active="activeMenu" router class="side-menu">
          <template v-for="item in currentSubMenus" :key="item.index">
            <el-menu-item :index="item.index">
              <span>{{ item.label }}</span>
              <el-badge v-if="item.badge" :value="item.badge" class="menu-badge" />
            </el-menu-item>
          </template>
        </el-menu>
      </div>

      <!-- 内容区 -->
      <div class="app-content">
        <router-view />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import {
  Odometer, Connection, Box, OfficeBuilding, Lock, Bell, Tickets,
  DataAnalysis, Document, Upload, Coin, ChatDotRound, Reading,
  TrendCharts, Tools, User, Setting
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const searchKeyword = ref('')
const alertCount = ref(0)
const isSimulating = ref(false)
const simulateRole = ref('')
const simulateUser = ref('')

const activeMenu = computed(() => route.path)
const userName = computed(() => authStore.user?.full_name || authStore.user?.username || '用户')
const userInitial = computed(() => userName.value.charAt(0))
const isAdmin = computed(() => authStore.userRole === 'admin')

// 一级菜单定义
const topMenus = [
  { key: 'home', label: '首页', icon: Odometer, path: '/app/dashboard' },
  { key: 'ipam', label: 'IP 管理', icon: Connection },
  { key: 'assets', label: '资产管理', icon: Box },
  { key: 'dcim', label: '机房管理', icon: OfficeBuilding },
  { key: 'nac', label: '准入控制', icon: Lock },
  { key: 'ops', label: '运维中心', icon: Tickets },
  { key: 'data', label: '数据分析', icon: DataAnalysis },
  { key: 'tools', label: '工具', icon: Tools },
]

// 二级菜单映射
const subMenuMap = {
  home: [],
  ipam: [
    { index: '/app/ipam/segments', label: '网段管理' },
    { index: '/app/ipam/ips', label: 'IP 地址' },
    { index: '/app/ipam/scan', label: 'Ping 扫描' },
    { index: '/app/ipam/heatmap', label: '使用率热力图' },
    { index: '/app/ipam/recycle', label: '回收站' },
  ],
  assets: [
    { index: '/app/assets/devices', label: '设备资产' },
    { index: '/app/assets/terminals', label: '终端管理' },
    { index: '/app/assets/inventory', label: '资产盘点' },
    { index: '/app/assets/licenses', label: '软件许可' },
    { index: '/app/assets/contracts', label: '合同管理' },
  ],
  dcim: [
    { index: '/app/dcim/datacenters', label: '机房' },
    { index: '/app/dcim/racks', label: '机架' },
    { index: '/app/dcim/topology', label: '网络拓扑' },
  ],
  nac: [
    { index: '/app/nac/radius-users', label: 'RADIUS 用户' },
    { index: '/app/nac/mac-auth', label: 'MAC 白名单' },
    { index: '/app/nac/nas-devices', label: 'NAS 设备' },
    { index: '/app/nac/policies', label: '认证策略' },
    { index: '/app/nac/sessions', label: '在线终端' },
    { index: '/app/nac/auth-logs', label: '认证日志' },
    { index: '/app/nac/visitors', label: '访客管理' },
  ],
  ops: [
    { index: '/app/alerts', label: '告警中心' },
    { index: '/app/tickets', label: '工单协作' },
    { index: '/app/logs', label: '操作日志' },
    { index: '/app/collab/knowledge', label: '知识库' },
    { index: '/app/collab/duty', label: '值班排班' },
    { index: '/app/collab/changes', label: '变更窗口' },
    { index: '/app/portal', label: '自助门户' },
  ],
  data: [
    { index: '/app/reports', label: '报表中心' },
    { index: '/app/value', label: 'IT 价值量化' },
    { index: '/app/ai', label: 'AI 助手' },
    { index: '/app/governance/cleaning', label: '数据清洗' },
    { index: '/app/governance/capacity', label: '容量规划' },
    { index: '/app/import-export', label: '导入导出' },
  ],
  tools: [
    { index: '/app/tools/diag', label: '网络诊断' },
    { index: '/app/tools/catalog', label: '服务目录' },
    { index: '/app/users', label: '用户管理' },
    { index: '/app/settings', label: '个人设置' },
  ],
}

// 路径前缀 → 一级菜单 key 映射（优先级从上到下）
const pathPrefixMap = [
  ['/app/ipam', 'ipam'],
  ['/app/assets', 'assets'],
  ['/app/dcim', 'dcim'],
  ['/app/nac', 'nac'],
  ['/app/alerts', 'ops'],
  ['/app/tickets', 'ops'],
  ['/app/collab', 'ops'],
  ['/app/portal', 'ops'],
  ['/app/logs', 'ops'],
  ['/app/reports', 'data'],
  ['/app/value', 'data'],
  ['/app/ai', 'data'],
  ['/app/governance', 'data'],
  ['/app/import-export', 'data'],
  ['/app/tools', 'tools'],
  ['/app/users', 'tools'],
  ['/app/settings', 'tools'],
]

function resolveTopMenu(path) {
  for (const [prefix, key] of pathPrefixMap) {
    if (path.startsWith(prefix)) return key
  }
  return 'home'
}

const activeTopMenu = ref(resolveTopMenu(route.path))
const currentSubMenus = computed(() => subMenuMap[activeTopMenu.value] || [])

watch(() => route.path, (p) => {
  activeTopMenu.value = resolveTopMenu(p)
})

function handleTopMenuClick(item) {
  activeTopMenu.value = item.key
  if (item.path) {
    router.push(item.path)
  } else {
    const subs = subMenuMap[item.key]
    if (subs && subs.length > 0) {
      router.push(subs[0].index)
    }
  }
}

function switchToAdmin() { router.push('/admin/dashboard') }
function handleSearch() {
  if (searchKeyword.value.trim()) {
    router.push({ path: '/app/search', query: { q: searchKeyword.value } })
  }
}
function exitSimulate() { isSimulating.value = false }
function handleLogout() { authStore.logout(); router.push('/login') }
</script>

<style scoped>
.app-layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.simulate-bar {
  height: 36px;
  background: #e6a23c;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  font-size: 13px;
  flex-shrink: 0;
}

/* ===== 顶栏 ===== */
.app-header {
  height: 52px;
  background: #1d1e2c;
  display: flex;
  align-items: center;
  padding: 0 16px;
  flex-shrink: 0;
  gap: 8px;
}

.header-left {
  display: flex;
  align-items: center;
  margin-right: 24px;
}

.logo {
  font-size: 16px;
  font-weight: 700;
  color: #fff;
  white-space: nowrap;
}

/* 一级横向导航 */
.header-nav {
  display: flex;
  align-items: center;
  gap: 2px;
  flex: 1;
  overflow-x: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 14px;
  border-radius: 6px;
  color: rgba(255,255,255,.7);
  font-size: 13px;
  cursor: pointer;
  white-space: nowrap;
  transition: all .2s;
}

.nav-item:hover {
  color: #fff;
  background: rgba(255,255,255,.1);
}

.nav-item.active {
  color: #fff;
  background: #409eff;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-left: auto;
  flex-shrink: 0;
}

.global-search {
  width: 200px;
}

.global-search :deep(.el-input__wrapper) {
  background: rgba(255,255,255,.12);
  border: none;
  box-shadow: none;
}

.global-search :deep(.el-input__inner) {
  color: #fff;
}

.global-search :deep(.el-input__inner::placeholder) {
  color: rgba(255,255,255,.5);
}

.global-search :deep(.el-input__prefix .el-icon) {
  color: rgba(255,255,255,.5);
}

.header-icon {
  font-size: 18px;
  cursor: pointer;
  color: rgba(255,255,255,.8);
}

.header-icon:hover {
  color: #fff;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  color: rgba(255,255,255,.85);
  font-size: 13px;
}

/* ===== 主体 ===== */
.app-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* 左侧二级菜单 */
.app-sidebar {
  width: 180px;
  background: #fff;
  border-right: 1px solid #e4e7ed;
  flex-shrink: 0;
  overflow-y: auto;
}

.side-menu {
  border-right: none;
  padding-top: 8px;
}

.side-menu .el-menu-item {
  height: 40px;
  line-height: 40px;
  font-size: 13px;
}

.side-menu .el-menu-item.is-active {
  background: #ecf5ff;
  color: #409eff;
  font-weight: 600;
}

.menu-badge {
  margin-left: 6px;
}

/* 内容区 */
.app-content {
  flex: 1;
  overflow: auto;
  background: #f5f7fa;
  padding: 16px;
}
</style>
