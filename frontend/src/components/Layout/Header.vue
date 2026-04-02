<template>
  <div class="header-container">
    <div class="left-section">
      <el-icon class="menu-icon" @click="toggleSidebar">
        <Fold v-if="!appStore.sidebarCollapsed" />
        <Expand v-else />
      </el-icon>
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
        <el-breadcrumb-item v-if="currentRoute.meta.title">
          {{ currentRoute.meta.title }}
        </el-breadcrumb-item>
      </el-breadcrumb>
    </div>

    <div class="right-section">
      <!-- 全局搜索 -->
      <GlobalSearch />
      
      <!-- 未解决告警通知 -->
      <el-badge :value="unresolvedAlerts" :hidden="unresolvedAlerts === 0" class="alert-badge">
        <el-icon class="icon-button" @click="goToAlerts">
          <Bell />
        </el-icon>
      </el-badge>

      <!-- 主题切换 -->
      <el-icon class="icon-button" @click="toggleTheme">
        <Sunny v-if="appStore.theme === 'light'" />
        <Moon v-else />
      </el-icon>

      <!-- 用户菜单 -->
      <el-dropdown @command="handleCommand">
        <div class="user-info">
          <el-avatar :size="32" :icon="UserFilled" />
          <span class="username">{{ authStore.userName }}</span>
          <el-icon><ArrowDown /></el-icon>
        </div>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item disabled>
              <el-tag :type="roleTagType" size="small">{{ roleText }}</el-tag>
            </el-dropdown-item>
            <el-dropdown-item divided command="profile">
              <el-icon><User /></el-icon>
              个人信息
            </el-dropdown-item>
            <el-dropdown-item command="changePassword">
              <el-icon><Lock /></el-icon>
              修改密码
            </el-dropdown-item>
            <el-dropdown-item divided command="logout">
              <el-icon><SwitchButton /></el-icon>
              退出登录
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useAppStore } from '@/stores/app'
import { ElMessageBox, ElMessage } from 'element-plus'
import { getAlerts } from '@/api/alerts'
import GlobalSearch from '@/components/GlobalSearch.vue'
import {
  Fold,
  Expand,
  Bell,
  Sunny,
  Moon,
  UserFilled,
  ArrowDown,
  User,
  Lock,
  SwitchButton
} from '@element-plus/icons-vue'

const router = useRouter()
const currentRoute = useRoute()
const authStore = useAuthStore()
const appStore = useAppStore()

const unresolvedAlerts = ref(0)

const roleText = computed(() => {
  const roleMap = {
    admin: '管理员',
    user: '普通用户',
    readonly: '只读用户'
  }
  return roleMap[authStore.userRole] || authStore.userRole
})

const roleTagType = computed(() => {
  const typeMap = {
    admin: 'danger',
    user: 'success',
    readonly: 'info'
  }
  return typeMap[authStore.userRole] || 'info'
})

function toggleSidebar() {
  appStore.toggleSidebar()
}

function toggleTheme() {
  appStore.toggleTheme()
}

function goToAlerts() {
  router.push({ name: 'AlertList' })
}

async function fetchUnresolvedAlerts() {
  try {
    const response = await getAlerts({ is_resolved: false, page_size: 1 })
    unresolvedAlerts.value = response.data.total || 0
  } catch (error) {
    console.error('Failed to fetch alerts:', error)
  }
}

function handleCommand(command) {
  switch (command) {
    case 'profile':
      // TODO: Navigate to profile page
      ElMessage.info('个人信息功能开发中')
      break
    case 'changePassword':
      // TODO: Show change password dialog
      ElMessage.info('修改密码功能开发中')
      break
    case 'logout':
      handleLogout()
      break
  }
}

function handleLogout() {
  ElMessageBox.confirm('确定要退出登录吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    await authStore.logout()
    router.push({ name: 'Login' })
    ElMessage.success('已退出登录')
  }).catch(() => {
    // User cancelled
  })
}

onMounted(() => {
  fetchUnresolvedAlerts()
  // Refresh alerts every 5 minutes
  setInterval(fetchUnresolvedAlerts, 5 * 60 * 1000)
})
</script>

<style scoped>
.header-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  height: 100%;
}

.left-section {
  display: flex;
  align-items: center;
  gap: 20px;
}

.menu-icon {
  font-size: 20px;
  cursor: pointer;
  transition: color 0.3s;
}

.menu-icon:hover {
  color: #409eff;
}

.right-section {
  display: flex;
  align-items: center;
  gap: 20px;
}

.icon-button {
  font-size: 20px;
  cursor: pointer;
  transition: color 0.3s;
}

.icon-button:hover {
  color: #409eff;
}

.alert-badge {
  cursor: pointer;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 5px 10px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.user-info:hover {
  background-color: #f5f7fa;
}

.username {
  font-size: 14px;
  color: #303133;
}
</style>
