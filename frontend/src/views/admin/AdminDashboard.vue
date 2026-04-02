<template>
  <div class="admin-dashboard">
    <h2>管理后台</h2>
    <p style="color: #909399; margin-bottom: 24px;">系统配置与低代码设计器入口</p>

    <el-row :gutter="16">
      <el-col :span="6" v-for="item in designerCards" :key="item.title">
        <el-card shadow="hover" class="designer-card" @click="$router.push(item.path)">
          <div class="card-icon">{{ item.icon }}</div>
          <div class="card-title">{{ item.title }}</div>
          <div class="card-desc">{{ item.desc }}</div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
const designerCards = [
  { icon: '📝', title: '表单设计器', desc: '拖拽创建业务表单', path: '/admin/designer/form' },
  { icon: '🔄', title: '流程设计器', desc: '可视化编排审批流程', path: '/admin/designer/workflow' },
  { icon: '📊', title: '报表设计器', desc: '拖拽设计数据报表', path: '/admin/designer/report' },
  { icon: '📈', title: '仪表盘设计器', desc: '自定义数据看板', path: '/admin/designer/dashboard' },
  { icon: '🖥️', title: '大屏设计器', desc: '设计数字化大屏', path: '/admin/designer/screen' },
  { icon: '📑', title: 'PPT 设计器', desc: 'AI 生成工作汇报', path: '/admin/designer/ppt' },
  { icon: '🧩', title: '页面布局', desc: '自定义页面组件排列', path: '/admin/designer/page' },
  { icon: '⚙️', title: '系统配置', desc: '配置中心与参数管理', path: '/admin/config/system' },
]
</script>

<style scoped>
.designer-card {
  cursor: pointer;
  text-align: center;
  margin-bottom: 16px;
  transition: transform 0.2s;
}
.designer-card:hover {
  transform: translateY(-4px);
}
.card-icon {
  font-size: 36px;
  margin-bottom: 8px;
}
.card-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}
.card-desc {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
