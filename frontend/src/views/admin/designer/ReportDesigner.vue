<template>
  <DesignerLayout
    title="报表设计器"
    :components="reportComponents"
    @save="(d) => $message.success('报表保存成功')"
    @publish="(d) => $message.success('报表发布成功')"
  />
</template>

<script setup>
import DesignerLayout from '@/designer/core/DesignerLayout.vue'

const reportComponents = [
  { type: 'data_table', label: '数据表格', icon: '📋', defaultProps: {} },
  { type: 'cross_table', label: '交叉表', icon: '📊', defaultProps: {} },
  { type: 'group_table', label: '分组表', icon: '📑', defaultProps: {} },
  { type: 'chart', label: '图表', icon: '📈', defaultProps: {} },
  { type: 'text_block', label: '文本块', icon: '📝', defaultProps: {} },
  { type: 'divider', label: '分隔线', icon: '➖', defaultProps: {} },
  { type: 'filter', label: '筛选器', icon: '🔍', defaultProps: {} },
  { type: 'parameter', label: '参数输入', icon: '⚙️', defaultProps: {} },
]
</script>
