<template>
  <div class="admin-layout">
    <!-- 顶栏 -->
    <div class="admin-header">
      <div class="header-left">
        <span class="logo">🛠️ IT 智维平台</span>
        <span class="mode-badge">设计态</span>
      </div>
      <div class="header-right">
        <el-button
          type="primary"
          link
          @click="switchToApp"
        >
          <el-icon><Monitor /></el-icon>
          切换到运行态
        </el-button>
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

    <div class="admin-body">
      <!-- 侧边栏 -->
      <div class="admin-sidebar" :class="{ collapsed: sidebarCollapsed }">
        <el-menu
          :default-active="activeMenu"
          :collapse="sidebarCollapsed"
          router
          class="admin-menu"
        >
          <el-menu-item index="/admin/dashboard">
            <el-icon><Odometer /></el-icon>
            <span>管理首页</span>
          </el-menu-item>

          <el-sub-menu index="designer">
            <template #title>
              <el-icon><Edit /></el-icon>
              <span>设计器</span>
            </template>
            <el-menu-item index="/admin/designer/form">表单设计器</el-menu-item>
            <el-menu-item index="/admin/designer/workflow">流程设计器</el-menu-item>
            <el-menu-item index="/admin/designer/report">报表设计器</el-menu-item>
            <el-menu-item index="/admin/designer/dashboard">仪表盘设计器</el-menu-item>
            <el-menu-item index="/admin/designer/screen">大屏设计器</el-menu-item>
            <el-menu-item index="/admin/designer/ppt">PPT 设计器</el-menu-item>
            <el-menu-item index="/admin/designer/page">页面布局设计器</el-menu-item>
          </el-sub-menu>

          <el-sub-menu index="config">
            <template #title>
              <el-icon><Setting /></el-icon>
              <span>系统配置</span>
            </template>
            <el-menu-item index="/admin/config/system">配置中心</el-menu-item>
            <el-menu-item index="/admin/config/notification">通知渠道</el-menu-item>
            <el-menu-item index="/admin/config/scheduler">定时任务</el-menu-item>
          </el-sub-menu>

          <el-menu-item index="/admin/plugins">
            <el-icon><Connection /></el-icon>
            <span>插件管理</span>
          </el-menu-item>

          <el-menu-item index="/admin/permissions">
            <el-icon><Lock /></el-icon>
            <span>权限管理</span>
          </el-menu-item>

          <el-menu-item index="/admin/tenants">
            <el-icon><OfficeBuilding /></el-icon>
            <span>租户管理</span>
          </el-menu-item>

          <el-menu-item index="/admin/templates">
            <el-icon><Document /></el-icon>
            <span>模板库</span>
          </el-menu-item>

          <el-menu-item index="/admin/connectors">
            <el-icon><Link /></el-icon>
            <span>连接器</span>
          </el-menu-item>

          <el-menu-item index="/admin/automation">
            <el-icon><Cpu /></el-icon>
            <span>自动化工作流</span>
          </el-menu-item>
        </el-menu>

        <div class="sidebar-toggle" @click="sidebarCollapsed = !sidebarCollapsed">
          <el-icon>
            <DArrowLeft v-if="!sidebarCollapsed" />
            <DArrowRight v-else />
          </el-icon>
        </div>
      </div>

      <!-- 内容区 -->
      <div class="admin-content">
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
const activeMenu = computed(() => route.path)
const userName = computed(() => authStore.user?.full_name || authStore.user?.username || '管理员')
const userInitial = computed(() => userName.value.charAt(0))

function switchToApp() {
  router.push('/app/dashboard')
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.admin-layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.admin-header {
  height: 50px;
  background: #1d1e1f;
  color: #fff;
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

.logo {
  font-size: 16px;
  font-weight: 600;
}

.mode-badge {
  background: #e6a23c;
  color: #fff;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #fff;
  cursor: pointer;
}

.admin-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.admin-sidebar {
  width: 220px;
  background: #263238;
  transition: width 0.3s;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.admin-sidebar.collapsed {
  width: 64px;
}

.admin-menu {
  flex: 1;
  border-right: none;
  background: #263238;
  --el-menu-bg-color: #263238;
  --el-menu-text-color: #b0bec5;
  --el-menu-active-color: #409eff;
  --el-menu-hover-bg-color: #37474f;
}

.sidebar-toggle {
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #b0bec5;
  border-top: 1px solid #37474f;
}

.admin-content {
  flex: 1;
  overflow: auto;
  background: #f5f7fa;
  padding: 16px;
}
</style>
