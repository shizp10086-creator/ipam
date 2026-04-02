<template>
  <DesignerLayout
    title="页面布局设计器"
    :components="pageComponents"
    @save="(d) => $message.success('页面布局保存成功')"
    @publish="(d) => $message.success('页面布局发布成功')"
  />
</template>

<script setup>
import DesignerLayout from '@/designer/core/DesignerLayout.vue'

const pageComponents = [
  { type: 'table', label: '表格', icon: '📋', defaultProps: {} },
  { type: 'form', label: '表单', icon: '📝', defaultProps: {} },
  { type: 'chart', label: '图表', icon: '📊', defaultProps: {} },
  { type: 'card', label: '卡片', icon: '🃏', defaultProps: {} },
  { type: 'tabs', label: '标签页', icon: '📑', defaultProps: {} },
  { type: 'button_group', label: '按钮组', icon: '🔘', defaultProps: {} },
  { type: 'search_bar', label: '搜索栏', icon: '🔍', defaultProps: {} },
  { type: 'stat_panel', label: '统计面板', icon: '📈', defaultProps: {} },
]
</script>
