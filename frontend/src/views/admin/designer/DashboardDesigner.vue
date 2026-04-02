<template>
  <DesignerLayout
    title="仪表盘设计器"
    :components="dashboardComponents"
    @save="handleSave"
    @publish="handlePublish"
  >
    <template #preview="{ items }">
      <h3 style="margin-bottom: 16px;">仪表盘预览</h3>
      <el-row :gutter="16">
        <el-col :span="item.type === 'stat_card' ? 6 : 12" v-for="item in items" :key="item.id">
          <el-card shadow="hover" style="margin-bottom: 16px;">
            <template #header>{{ item.label }}</template>
            <div v-if="item.type === 'stat_card'" style="text-align:center;font-size:28px;font-weight:700;color:#409eff;">
              --
            </div>
            <div v-else-if="item.type === 'bar_chart'" style="height:200px;display:flex;align-items:center;justify-content:center;color:#909399;">
              📊 柱状图区域
            </div>
            <div v-else-if="item.type === 'line_chart'" style="height:200px;display:flex;align-items:center;justify-content:center;color:#909399;">
              📈 折线图区域
            </div>
            <div v-else-if="item.type === 'pie_chart'" style="height:200px;display:flex;align-items:center;justify-content:center;color:#909399;">
              🥧 饼图区域
            </div>
            <div v-else-if="item.type === 'table'" style="color:#909399;">
              📋 表格区域
            </div>
            <div v-else style="color:#909399;">{{ item.type }}</div>
          </el-card>
        </el-col>
      </el-row>
    </template>
  </DesignerLayout>
</template>

<script setup>
import { ElMessage } from 'element-plus'
import DesignerLayout from '@/designer/core/DesignerLayout.vue'

const dashboardComponents = [
  { type: 'stat_card', label: '数字卡片', icon: '🔢', defaultProps: {} },
  { type: 'bar_chart', label: '柱状图', icon: '📊', defaultProps: {} },
  { type: 'line_chart', label: '折线图', icon: '📈', defaultProps: {} },
  { type: 'pie_chart', label: '饼图', icon: '🥧', defaultProps: {} },
  { type: 'table', label: '表格', icon: '📋', defaultProps: {} },
  { type: 'gauge', label: '仪表盘', icon: '⏱️', defaultProps: {} },
  { type: 'heatmap', label: '热力图', icon: '🌡️', defaultProps: {} },
  { type: 'topology', label: '拓扑图', icon: '🔗', defaultProps: {} },
  { type: 'map', label: '地图', icon: '🗺️', defaultProps: {} },
  { type: 'filter', label: '全局筛选器', icon: '🔍', defaultProps: {} },
]

function handleSave(data) {
  ElMessage.success('仪表盘保存成功')
}
function handlePublish(data) {
  ElMessage.success('仪表盘发布成功')
}
</script>
