<template>
  <div class="coming-soon-container">
    <el-card>
      <div class="content">
        <el-icon class="icon"><Tools /></el-icon>
        <h2>功能开发中</h2>
        <p>{{ message }}</p>
        <el-button type="primary" @click="$router.push('/')">返回首页</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { Tools } from '@element-plus/icons-vue'

const route = useRoute()

const message = computed(() => {
  return route.meta.title ? `${route.meta.title}功能正在开发中，敬请期待！` : '此功能正在开发中，敬请期待！'
})
</script>

<style scoped>
.coming-soon-container {
  padding: 20px;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 60vh;
}

.content {
  text-align: center;
  padding: 40px;
}

.icon {
  font-size: 80px;
  color: #409eff;
  margin-bottom: 20px;
}

h2 {
  font-size: 28px;
  color: #303133;
  margin-bottom: 15px;
}

p {
  font-size: 16px;
  color: #606266;
  margin-bottom: 30px;
}
</style>
