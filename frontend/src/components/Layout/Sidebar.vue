<template>
  <div class="sidebar-container">
    <div class="logo">
      <el-icon v-if="!appStore.sidebarCollapsed" class="logo-icon"><Monitor /></el-icon>
      <span v-if="!appStore.sidebarCollapsed" class="logo-text">IPAM 系统</span>
      <el-icon v-else class="logo-icon-collapsed"><Monitor /></el-icon>
    </div>

    <el-menu
      :default-active="activeMenu"
      :collapse="appStore.sidebarCollapsed"
      :collapse-transition="false"
      background-color="#304156"
      text-color="#bfcbd9"
      active-text-color="#409eff"
      router
    >
      <el-menu-item index="/">
        <el-icon><DataBoard /></el-icon>
        <template #title>仪表板</template>
      </el-menu-item>

      <el-menu-item index="/segments">
        <el-icon><Grid /></el-icon>
        <template #title>网段管理</template>
      </el-menu-item>

      <el-menu-item index="/ip/list">
        <el-icon><Connection /></el-icon>
        <template #title>IP 地址</template>
      </el-menu-item>

      <el-menu-item index="/devices">
        <el-icon><Monitor /></el-icon>
        <template #title>设备管理</template>
      </el-menu-item>

      <el-menu-item index="/ip/scanner">
        <el-icon><Search /></el-icon>
        <template #title>IP 扫描</template>
      </el-menu-item>

      <el-menu-item index="/logs">
        <el-icon><Document /></el-icon>
        <template #title>操作日志</template>
      </el-menu-item>

      <el-menu-item index="/alerts">
        <el-icon><Bell /></el-icon>
        <template #title>告警管理</template>
      </el-menu-item>

      <el-menu-item v-if="authStore.isAdmin" index="/import-export">
        <el-icon><Upload /></el-icon>
        <template #title>导入导出</template>
      </el-menu-item>

      <el-menu-item v-if="authStore.isAdmin" index="/users">
        <el-icon><User /></el-icon>
        <template #title>用户管理</template>
      </el-menu-item>
    </el-menu>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useAppStore } from '@/stores/app'
import {
  Monitor,
  DataBoard,
  Grid,
  Connection,
  Search,
  Document,
  Bell,
  Upload,
  User
} from '@element-plus/icons-vue'

const route = useRoute()
const authStore = useAuthStore()
const appStore = useAppStore()

const activeMenu = computed(() => {
  const { path } = route
  // Handle special cases
  if (path.startsWith('/segments')) return '/segments'
  if (path.startsWith('/ip') && !path.includes('scanner')) return '/ip/list'
  if (path.startsWith('/devices')) return '/devices'
  return path
})
</script>

<style scoped>
.sidebar-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #2b3a4b;
  color: #fff;
  font-size: 18px;
  font-weight: bold;
  gap: 10px;
}

.logo-icon {
  font-size: 24px;
}

.logo-icon-collapsed {
  font-size: 28px;
}

.logo-text {
  white-space: nowrap;
}

.el-menu {
  border-right: none;
  flex: 1;
}

.el-menu:not(.el-menu--collapse) {
  width: 200px;
}
</style>
