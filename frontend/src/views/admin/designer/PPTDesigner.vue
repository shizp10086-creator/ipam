<template>
  <DesignerLayout
    title="PPT 设计器"
    :components="pptComponents"
    @save="(d) => $message.success('PPT 保存成功')"
    @publish="(d) => $message.success('PPT 导出成功')"
  />
</template>

<script setup>
import DesignerLayout from '@/designer/core/DesignerLayout.vue'

const pptComponents = [
  { type: 'title', label: '标题', icon: '📌', defaultProps: {} },
  { type: 'text', label: '文本块', icon: '📝', defaultProps: {} },
  { type: 'chart', label: '图表', icon: '📊', defaultProps: {} },
  { type: 'table', label: '表格', icon: '📋', defaultProps: {} },
  { type: 'image', label: '图片', icon: '🖼️', defaultProps: {} },
  { type: 'stat_card', label: '数字卡片', icon: '🔢', defaultProps: {} },
  { type: 'timeline', label: '时间线', icon: '📅', defaultProps: {} },
  { type: 'comparison', label: '对比图', icon: '⚖️', defaultProps: {} },
]
</script>
