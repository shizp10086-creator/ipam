<template>
  <div class="designer-layout">
    <!-- 顶部工具栏 -->
    <div class="designer-toolbar">
      <div class="toolbar-left">
        <el-button @click="$router.back()" link>
          <el-icon><ArrowLeft /></el-icon> 返回
        </el-button>
        <el-divider direction="vertical" />
        <span class="designer-title">{{ title }}</span>
        <el-tag v-if="isDraft" type="info" size="small">草稿</el-tag>
        <el-tag v-else type="success" size="small">已发布</el-tag>
      </div>
      <div class="toolbar-center">
        <el-button-group>
          <el-button :type="mode === 'design' ? 'primary' : ''" size="small" @click="mode = 'design'">
            <el-icon><Edit /></el-icon> 设计
          </el-button>
          <el-button :type="mode === 'preview' ? 'primary' : ''" size="small" @click="mode = 'preview'">
            <el-icon><View /></el-icon> 预览
          </el-button>
        </el-button-group>
      </div>
      <div class="toolbar-right">
        <el-tooltip content="撤销 (Ctrl+Z)">
          <el-button size="small" :disabled="!canUndo" @click="undo">
            <el-icon><RefreshLeft /></el-icon>
          </el-button>
        </el-tooltip>
        <el-tooltip content="重做 (Ctrl+Y)">
          <el-button size="small" :disabled="!canRedo" @click="redo">
            <el-icon><RefreshRight /></el-icon>
          </el-button>
        </el-tooltip>
        <el-divider direction="vertical" />
        <el-button size="small" @click="handleSave">
          <el-icon><FolderOpened /></el-icon> 保存
        </el-button>
        <el-button size="small" type="primary" @click="handlePublish">
          <el-icon><Upload /></el-icon> 发布
        </el-button>
      </div>
    </div>

    <!-- 主体区域 -->
    <div class="designer-body" v-if="mode === 'design'">
      <!-- 左侧：组件面板 -->
      <div class="designer-sidebar-left">
        <div class="sidebar-title">组件</div>
        <slot name="component-panel">
          <div class="component-list">
            <div
              v-for="comp in components"
              :key="comp.type"
              class="component-item"
              draggable="true"
              @dragstart="onDragStart($event, comp)"
            >
              <span class="comp-icon">{{ comp.icon }}</span>
              <span class="comp-label">{{ comp.label }}</span>
            </div>
          </div>
        </slot>
      </div>

      <!-- 中央：画布 -->
      <div
        class="designer-canvas"
        @dragover.prevent
        @drop="onDrop"
        @click.self="selectedItem = null"
      >
        <div v-if="canvasItems.length === 0" class="canvas-empty">
          <el-icon :size="48"><Plus /></el-icon>
          <p>从左侧拖拽组件到这里</p>
        </div>
        <div
          v-for="(item, index) in canvasItems"
          :key="item.id"
          class="canvas-item"
          :class="{ selected: selectedItem?.id === item.id }"
          @click.stop="selectedItem = item"
        >
          <slot name="canvas-item" :item="item" :index="index">
            <div class="item-header">
              <span>{{ item.label || item.type }}</span>
              <el-button link size="small" type="danger" @click.stop="removeItem(index)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
            <div class="item-body">
              <component :is="getPreviewComponent(item)" v-bind="item.props" />
            </div>
          </slot>
        </div>
      </div>

      <!-- 右侧：属性面板 -->
      <div class="designer-sidebar-right">
        <div class="sidebar-title">属性</div>
        <div v-if="!selectedItem" class="prop-empty">
          <p>点击画布中的组件查看属性</p>
        </div>
        <div v-else class="prop-form">
          <slot name="property-panel" :item="selectedItem" :update="updateItemProp">
            <el-form label-position="top" size="small">
              <el-form-item label="标签">
                <el-input v-model="selectedItem.label" @input="markDirty" />
              </el-form-item>
              <el-form-item label="字段名">
                <el-input v-model="selectedItem.field" @input="markDirty" />
              </el-form-item>
              <el-form-item label="必填">
                <el-switch v-model="selectedItem.required" @change="markDirty" />
              </el-form-item>
              <el-form-item label="占位提示">
                <el-input v-model="selectedItem.placeholder" @input="markDirty" />
              </el-form-item>
            </el-form>
          </slot>
        </div>
      </div>
    </div>

    <!-- 预览模式 -->
    <div class="designer-preview" v-else>
      <div class="preview-container">
        <slot name="preview" :items="canvasItems">
          <div class="preview-hint">预览模式 — 展示真实渲染效果</div>
          <div v-for="item in canvasItems" :key="item.id" class="preview-item">
            <component :is="getPreviewComponent(item)" v-bind="item.props" />
          </div>
        </slot>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  title: { type: String, default: '设计器' },
  components: { type: Array, default: () => [] },
  initialItems: { type: Array, default: () => [] },
  configId: { type: Number, default: null },
})

const emit = defineEmits(['save', 'publish'])

const mode = ref('design')
const canvasItems = ref([...props.initialItems])
const selectedItem = ref(null)
const isDraft = ref(true)
const dirty = ref(false)

// 撤销/重做
const history = ref([JSON.stringify([])])
const historyIndex = ref(0)
const canUndo = computed(() => historyIndex.value > 0)
const canRedo = computed(() => historyIndex.value < history.value.length - 1)

function pushHistory() {
  const snapshot = JSON.stringify(canvasItems.value)
  history.value = history.value.slice(0, historyIndex.value + 1)
  history.value.push(snapshot)
  historyIndex.value = history.value.length - 1
}

function undo() {
  if (!canUndo.value) return
  historyIndex.value--
  canvasItems.value = JSON.parse(history.value[historyIndex.value])
  selectedItem.value = null
}

function redo() {
  if (!canRedo.value) return
  historyIndex.value++
  canvasItems.value = JSON.parse(history.value[historyIndex.value])
  selectedItem.value = null
}

function markDirty() {
  dirty.value = true
}

// 拖拽
let dragData = null

function onDragStart(event, comp) {
  dragData = comp
  event.dataTransfer.effectAllowed = 'copy'
}

function onDrop(event) {
  if (!dragData) return
  const newItem = {
    id: Date.now().toString(),
    type: dragData.type,
    label: dragData.label,
    icon: dragData.icon,
    field: `field_${canvasItems.value.length + 1}`,
    required: false,
    placeholder: '',
    props: { ...(dragData.defaultProps || {}) },
  }
  canvasItems.value.push(newItem)
  pushHistory()
  markDirty()
  dragData = null
}

function removeItem(index) {
  canvasItems.value.splice(index, 1)
  selectedItem.value = null
  pushHistory()
  markDirty()
}

function updateItemProp(key, value) {
  if (selectedItem.value) {
    selectedItem.value[key] = value
    markDirty()
  }
}

function getPreviewComponent(item) {
  // 返回对应的预览组件名，默认用 div 占位
  const map = {
    'input': 'el-input',
    'textarea': 'el-input',
    'number': 'el-input-number',
    'select': 'el-select',
    'date': 'el-date-picker',
    'switch': 'el-switch',
  }
  return map[item.type] || 'div'
}

function handleSave() {
  emit('save', {
    items: canvasItems.value,
    configId: props.configId,
  })
  dirty.value = false
}

function handlePublish() {
  emit('publish', {
    items: canvasItems.value,
    configId: props.configId,
  })
  isDraft.value = false
}

// 快捷键
function onKeydown(e) {
  if ((e.ctrlKey || e.metaKey) && e.key === 'z') {
    e.preventDefault()
    if (e.shiftKey) redo()
    else undo()
  }
  if ((e.ctrlKey || e.metaKey) && e.key === 'y') {
    e.preventDefault()
    redo()
  }
  if ((e.ctrlKey || e.metaKey) && e.key === 's') {
    e.preventDefault()
    handleSave()
  }
}

onMounted(() => document.addEventListener('keydown', onKeydown))
onUnmounted(() => document.removeEventListener('keydown', onKeydown))
</script>

<style scoped>
.designer-layout {
  height: calc(100vh - 50px);
  display: flex;
  flex-direction: column;
  background: #f0f2f5;
}

.designer-toolbar {
  height: 44px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 12px;
  flex-shrink: 0;
}
.toolbar-left, .toolbar-center, .toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}
.designer-title {
  font-weight: 600;
  font-size: 14px;
}

.designer-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.designer-sidebar-left {
  width: 240px;
  background: #fff;
  border-right: 1px solid #e4e7ed;
  overflow-y: auto;
  flex-shrink: 0;
}
.designer-sidebar-right {
  width: 280px;
  background: #fff;
  border-left: 1px solid #e4e7ed;
  overflow-y: auto;
  flex-shrink: 0;
}
.sidebar-title {
  padding: 12px 16px;
  font-weight: 600;
  font-size: 13px;
  color: #303133;
  border-bottom: 1px solid #f0f0f0;
}

.component-list {
  padding: 8px;
}
.component-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  margin-bottom: 4px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  cursor: grab;
  font-size: 13px;
  transition: all 0.2s;
}
.component-item:hover {
  border-color: #409eff;
  background: #ecf5ff;
}
.comp-icon { font-size: 16px; }

.designer-canvas {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  min-height: 0;
}
.canvas-empty {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #c0c4cc;
  border: 2px dashed #dcdfe6;
  border-radius: 8px;
}
.canvas-item {
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  margin-bottom: 8px;
  transition: all 0.2s;
}
.canvas-item.selected {
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}
.canvas-item:hover {
  border-color: #409eff;
}
.item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 12px;
  background: #fafafa;
  border-bottom: 1px solid #f0f0f0;
  font-size: 12px;
  color: #606266;
}
.item-body {
  padding: 12px;
}

.prop-empty {
  padding: 24px 16px;
  text-align: center;
  color: #c0c4cc;
  font-size: 13px;
}
.prop-form {
  padding: 12px 16px;
}

.designer-preview {
  flex: 1;
  overflow-y: auto;
  display: flex;
  justify-content: center;
  padding: 24px;
}
.preview-container {
  width: 100%;
  max-width: 800px;
  background: #fff;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
}
.preview-hint {
  text-align: center;
  color: #909399;
  margin-bottom: 16px;
  font-size: 13px;
}
.preview-item {
  margin-bottom: 16px;
}
</style>
