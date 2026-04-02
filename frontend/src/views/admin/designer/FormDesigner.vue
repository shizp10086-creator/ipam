<template>
  <DesignerLayout
    title="表单设计器"
    :components="formComponents"
    @save="handleSave"
    @publish="handlePublish"
  >
    <!-- 自定义属性面板 -->
    <template #property-panel="{ item, update }">
      <el-form label-position="top" size="small" v-if="item">
        <el-form-item label="标签名称">
          <el-input v-model="item.label" />
        </el-form-item>
        <el-form-item label="字段标识">
          <el-input v-model="item.field" />
        </el-form-item>
        <el-form-item label="占位提示">
          <el-input v-model="item.placeholder" />
        </el-form-item>
        <el-form-item label="必填">
          <el-switch v-model="item.required" />
        </el-form-item>
        <el-form-item label="默认值">
          <el-input v-model="item.defaultValue" />
        </el-form-item>
        <el-form-item v-if="item.type === 'select'" label="选项（每行一个）">
          <el-input type="textarea" :rows="4" v-model="item.optionsText" />
        </el-form-item>
      </el-form>
    </template>

    <!-- 自定义预览 -->
    <template #preview="{ items }">
      <h3 style="margin-bottom: 16px;">表单预览</h3>
      <el-form label-position="top">
        <el-form-item
          v-for="item in items"
          :key="item.id"
          :label="item.label"
          :required="item.required"
        >
          <el-input v-if="item.type === 'input'" :placeholder="item.placeholder" />
          <el-input v-else-if="item.type === 'textarea'" type="textarea" :rows="3" :placeholder="item.placeholder" />
          <el-input-number v-else-if="item.type === 'number'" />
          <el-select v-else-if="item.type === 'select'" :placeholder="item.placeholder" style="width:100%">
            <el-option v-for="opt in (item.optionsText || '').split('\n').filter(Boolean)" :key="opt" :label="opt" :value="opt" />
          </el-select>
          <el-date-picker v-else-if="item.type === 'date'" style="width:100%" />
          <el-switch v-else-if="item.type === 'switch'" />
          <el-upload v-else-if="item.type === 'upload'" action="#" :auto-upload="false">
            <el-button size="small">选择文件</el-button>
          </el-upload>
          <div v-else style="color:#909399">{{ item.type }} 组件</div>
        </el-form-item>
      </el-form>
    </template>
  </DesignerLayout>
</template>

<script setup>
import { ElMessage } from 'element-plus'
import DesignerLayout from '@/designer/core/DesignerLayout.vue'

const formComponents = [
  { type: 'input', label: '单行文本', icon: '📝', defaultProps: {} },
  { type: 'textarea', label: '多行文本', icon: '📄', defaultProps: {} },
  { type: 'number', label: '数字', icon: '🔢', defaultProps: {} },
  { type: 'select', label: '下拉选择', icon: '📋', defaultProps: {} },
  { type: 'date', label: '日期', icon: '📅', defaultProps: {} },
  { type: 'switch', label: '开关', icon: '🔘', defaultProps: {} },
  { type: 'upload', label: '附件上传', icon: '📎', defaultProps: {} },
  { type: 'divider', label: '分割线', icon: '➖', defaultProps: {} },
  { type: 'text', label: '说明文字', icon: '💬', defaultProps: {} },
]

function handleSave(data) {
  console.log('保存表单设计:', data)
  ElMessage.success('保存成功')
}

function handlePublish(data) {
  console.log('发布表单:', data)
  ElMessage.success('发布成功')
}
</script>
