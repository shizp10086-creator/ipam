<template>
  <div class="home">
    <el-container>
      <el-header>
        <h1>IPAM System - IP地址管理系统</h1>
      </el-header>
      <el-main>
        <el-card>
          <template #header>
            <div class="card-header">
              <span>欢迎使用 IPAM 系统</span>
            </div>
          </template>
          <div class="content">
            <p>系统正在初始化中...</p>
            <p>后端 API 地址: {{ apiBaseUrl }}</p>
            <el-button type="primary" @click="checkHealth">检查后端健康状态</el-button>
            <div v-if="healthStatus" class="health-status">
              <el-alert
                :title="healthStatus.message"
                :type="healthStatus.type"
                :closable="false"
                show-icon
              />
            </div>
          </div>
        </el-card>
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const healthStatus = ref(null)

const checkHealth = async () => {
  try {
    const response = await axios.get(`${apiBaseUrl}/health`)
    healthStatus.value = {
      message: `后端服务正常运行 - ${response.data.service} v${response.data.version}`,
      type: 'success'
    }
  } catch (error) {
    healthStatus.value = {
      message: `无法连接到后端服务: ${error.message}`,
      type: 'error'
    }
  }
}
</script>

<style scoped>
.home {
  height: 100%;
  background-color: #f0f2f5;
}

.el-header {
  background-color: #409eff;
  color: white;
  display: flex;
  align-items: center;
  padding: 0 20px;
}

.el-header h1 {
  font-size: 24px;
  margin: 0;
}

.el-main {
  padding: 20px;
}

.content {
  text-align: center;
}

.content p {
  margin: 10px 0;
  font-size: 16px;
}

.health-status {
  margin-top: 20px;
}
</style>
