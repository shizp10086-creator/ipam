<template>
  <DesignerLayout
    title="流程设计器"
    :components="workflowComponents"
    @save="handleSave"
    @publish="handlePublish"
  >
    <template #preview="{ items }">
      <h3 style="margin-bottom: 16px;">流程预览</h3>
      <div class="flow-preview">
        <div v-for="(item, i) in items" :key="item.id" class="flow-node">
          <div class="node-box" :class="item.type">
            <span class="node-icon">{{ item.icon }}</span>
            <span>{{ item.label }}</span>
          </div>
          <div v-if="i < items.length - 1" class="flow-arrow">↓</div>
        </div>
      </div>
    </template>
  </DesignerLayout>
</template>

<script setup>
import { ElMessage } from 'element-plus'
import DesignerLayout from '@/designer/core/DesignerLayout.vue'

const workflowComponents = [
  { type: 'approver', label: '审批人', icon: '👤', defaultProps: {} },
  { type: 'countersign', label: '会签', icon: '👥', defaultProps: {} },
  { type: 'condition', label: '条件分支', icon: '🔀', defaultProps: {} },
  { type: 'parallel', label: '并行分支', icon: '⚡', defaultProps: {} },
  { type: 'subprocess', label: '子流程', icon: '📦', defaultProps: {} },
  { type: 'timer', label: '定时器', icon: '⏰', defaultProps: {} },
  { type: 'notification', label: '通知节点', icon: '📧', defaultProps: {} },
  { type: 'script', label: '脚本节点', icon: '⚙️', defaultProps: {} },
]

function handleSave(data) { ElMessage.success('流程保存成功') }
function handlePublish(data) { ElMessage.success('流程发布成功') }
</script>

<style scoped>
.flow-preview { display: flex; flex-direction: column; align-items: center; }
.flow-node { display: flex; flex-direction: column; align-items: center; }
.node-box {
  padding: 12px 24px; border: 2px solid #409eff; border-radius: 8px;
  display: flex; align-items: center; gap: 8px; background: #ecf5ff;
}
.node-box.condition { border-color: #e6a23c; background: #fdf6ec; }
.node-box.timer { border-color: #909399; background: #f4f4f5; }
.flow-arrow { color: #409eff; font-size: 20px; margin: 4px 0; }
</style>
