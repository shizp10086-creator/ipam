<template>
  <div class="app-layout">
    <!-- 模拟预览提示条 -->
    <div v-if="isSimulating" class="simulate-bar">
      ⚠️ 当前正在模拟【{{ simulateRole }} - {{ simulateUser }}】的视角
      <el-button size="small" type="warning" @click="exitSimulate">退出模拟</el-button>
    </div>

    <!-- 顶栏 -->
    <div class="app-header">
      <div class="header-left">
        <el-icon class="menu-toggle" @click="sidebarCollapsed = !sidebarCollapsed">
          <Fold v-if="!sidebarCollapsed" />
          <Expand v-else />
        </el-icon>
        <span class="logo">IT 智维平台</span>
      </div>
      <div class="header-center">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索 IP / 设备 / 网段 / 工单..."
          prefix-icon="Search"
          clearable
          class="global-search"
          @keyup.enter="handleSearch"
        />
      </div>
      <div class="header-right">
        <!-- 告警铃铛 -->
        <el-badge :value="alertCount" :hidden="alertCount === 0" class="alert-badge">
          <el-icon class="header-icon" @click="$router.push('/app/alerts')">
            <Bell />
          </el-icon>
        </el-badge>
        <!-- 管理员切换按钮 -->
        <el-button
          v-if="isAdmin"
          type="primary"
          link
          @click="switchToAdmin"
        >
          <el-icon><Setting /></el-icon>
          设计态
        </el-button>
        <!-- 用户菜单 -->
        <el-dropdown trigger="click">
          <span class="user-info">
            <el-avatar :size="28">{{ userInitial }}</el-avatar>
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
      <!-- 侧边栏 -->
      <div class="app-sidebar" :class="{ collapsed: sidebarCollapsed }">
        <el-menu
          :default-active="activeMenu"
          :collapse="sidebarCollapsed"
          router
          class="app-menu"
        >
          <el-menu-item index="/app/dashboard">
            <el-icon><Odometer /></el-icon>
            <span>运维仪表盘</span>
          </el-menu-item>

          <el-sub-menu index="ipam">
            <template #title>
              <el-icon><Connection /></el-icon>
              <span>IP 管理</span>
            </template>
            <el-menu-item index="/app/ipam/segments">网段管理</el-menu-item>
            <el-menu-item index="/app/ipam/ips">IP 地址</el-menu-item>
            <el-menu-item index="/app/ipam/scan">Ping 扫描</el-menu-item>
          </el-sub-menu>

          <el-sub-menu index="assets">
            <template #title>
              <el-icon><Box /></el-icon>
              <span>资产管理</span>
            </template>
            <el-menu-item index="/app/assets/devices">设备资产</el-menu-item>
            <el-menu-item index="/app/assets/terminals">终端管理</el-menu-item>
            <el-menu-item index="/app/assets/inventory">资产盘点</el-menu-item>
          </el-sub-menu>

          <el-sub-menu index="dcim">
            <template #title>
              <el-icon><OfficeBuilding /></el-icon>
              <span>机房管理</span>
            </template>
            <el-menu-item index="/app/dcim/datacenters">机房</el-menu-item>
            <el-menu-item index="/app/dcim/racks">机架</el-menu-item>
            <el-menu-item index="/app/dcim/topology">网络拓扑</el-menu-item>
          </el-sub-menu>

          <el-sub-menu index="nac">
            <template #title>
              <el-icon><Lock /></el-icon>
              <span>准入控制</span>
            </template>
            <el-menu-item index="/app/nac/policies">认证策略</el-menu-item>
            <el-menu-item index="/app/nac/sessions">在线终端</el-menu-item>
            <el-menu-item index="/app/nac/auth-logs">认证日志</el-menu-item>
            <el-menu-item index="/app/nac/visitors">访客管理</el-menu-item>
          </el-sub-menu>

          <el-menu-item index="/app/alerts">
            <el-icon><Bell /></el-icon>
            <span>告警中心</span>
            <el-badge v-if="alertCount > 0" :value="alertCount" class="menu-badge" />
          </el-menu-item>

          <el-menu-item index="/app/tickets">
            <el-icon><Tickets /></el-icon>
            <span>工单协作</span>
          </el-menu-item>

          <el-menu-item index="/app/reports">
            <el-icon><DataAnalysis /></el-icon>
            <span>报表中心</span>
          </el-menu-item>

          <el-menu-item index="/app/logs">
            <el-icon><Document /></el-icon>
            <span>操作日志</span>
          </el-menu-item>

          <el-menu-item index="/app/import-export">
            <el-icon><Upload /></el-icon>
            <span>导入导出</span>
          </el-menu-item>
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
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const sidebarCollapsed = ref(false)
const searchKeyword = ref('')
const alertCount = ref(0)
const isSimulating = ref(false)
const simulateRole = ref('')
const simulateUser = ref('')

const activeMenu = computed(() => route.path)
const userName = computed(() => authStore.user?.full_name || authStore.user?.username || '用户')
const userInitial = computed(() => userName.value.charAt(0))
const isAdmin = computed(() => authStore.userRole === 'admin')

function switchToAdmin() {
  router.push('/admin/dashboard')
}

function handleSearch() {
  if (searchKeyword.value.trim()) {
    router.push({ path: '/app/search', query: { q: searchKeyword.value } })
  }
}

function exitSimulate() {
  isSimulating.value = false
  simulateRole.value = ''
  simulateUser.value = ''
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
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

.app-header {
  height: 50px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.menu-toggle {
  font-size: 20px;
  cursor: pointer;
  color: #606266;
}

.logo {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.header-center {
  flex: 1;
  max-width: 480px;
  margin: 0 24px;
}

.global-search {
  width: 100%;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-icon {
  font-size: 20px;
  cursor: pointer;
  color: #606266;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: #303133;
}

.app-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.app-sidebar {
  width: 220px;
  background: #fff;
  border-right: 1px solid #e4e7ed;
  transition: width 0.3s;
  flex-shrink: 0;
  overflow-y: auto;
}

.app-sidebar.collapsed {
  width: 64px;
}

.app-menu {
  border-right: none;
}

.app-content {
  flex: 1;
  overflow: auto;
  background: #f5f7fa;
  padding: 16px;
}

.menu-badge {
  margin-left: 8px;
}
</style>
