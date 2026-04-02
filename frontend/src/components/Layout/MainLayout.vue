<template>
  <el-container class="main-layout">
    <el-aside :width="sidebarWidth" class="sidebar">
      <Sidebar />
    </el-aside>
    <el-container>
      <el-header class="header">
        <Header />
      </el-header>
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useAppStore } from '@/stores/app'
import Header from './Header.vue'
import Sidebar from './Sidebar.vue'

const appStore = useAppStore()

const sidebarWidth = computed(() => {
  return appStore.sidebarCollapsed ? '64px' : '200px'
})
</script>

<style scoped>
.main-layout {
  height: 100vh;
  width: 100%;
}

.sidebar {
  background-color: #304156;
  transition: width 0.3s;
  overflow-x: hidden;
}

.header {
  background-color: #fff;
  border-bottom: 1px solid #e6e6e6;
  padding: 0 20px;
  display: flex;
  align-items: center;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
}

.main-content {
  background-color: #f0f2f5;
  padding: 20px;
  overflow-y: auto;
}
</style>
