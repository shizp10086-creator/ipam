<template>
  <DesignerLayout
    title="大屏设计器"
    :components="screenComponents"
    @save="(d) => $message.success('大屏保存成功')"
    @publish="(d) => $message.success('大屏发布成功')"
  />
</template>

<script setup>
import DesignerLayout from '@/designer/core/DesignerLayout.vue'

const screenComponents = [
  { type: 'stat_card', label: '指标卡片', icon: '🔢', defaultProps: {} },
  { type: 'bar_chart', label: '柱状图', icon: '📊', defaultProps: {} },
  { type: 'line_chart', label: '折线图', icon: '📈', defaultProps: {} },
  { type: 'pie_chart', label: '饼图', icon: '🥧', defaultProps: {} },
  { type: 'map', label: '地图', icon: '🗺️', defaultProps: {} },
  { type: 'topology', label: '拓扑图', icon: '🔗', defaultProps: {} },
  { type: 'heatmap', label: '热力图', icon: '🌡️', defaultProps: {} },
  { type: 'scroll_list', label: '滚动列表', icon: '📜', defaultProps: {} },
  { type: 'clock', label: '时钟', icon: '🕐', defaultProps: {} },
  { type: 'countdown', label: '倒计时', icon: '⏳', defaultProps: {} },
  { type: 'video', label: '视频监控', icon: '📹', defaultProps: {} },
]
</script>
