# 前端视图组件模板

本文档提供了实现剩余前端视图的模板和指南。所有模板都遵循相同的模式，可以快速复制和修改。

## 通用列表页面模板

```vue
<template>
  <div class="list-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>标题</span>
          <el-button type="primary" :icon="Plus" @click="handleCreate">
            创建
          </el-button>
        </div>
      </template>

      <!-- 搜索表单 -->
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="搜索">
          <el-input v-model="searchForm.keyword" placeholder="请输入关键词" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 数据表格 -->
      <el-table :data="list" v-loading="loading" border stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <!-- 其他列 -->
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" :icon="Edit" @click="handleEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" :icon="Delete" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="fetchList"
        @current-change="fetchList"
        class="pagination"
      />
    </el-card>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
      @close="resetForm"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="100px"
      >
        <!-- 表单项 -->
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh, Edit, Delete } from '@element-plus/icons-vue'
import * as api from '@/api/xxx'

const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const currentId = ref(null)
const formRef = ref(null)

const list = ref([])
const searchForm = reactive({
  keyword: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const form = reactive({
  // 表单字段
})

const dialogTitle = computed(() => isEdit.value ? '编辑' : '创建')

const formRules = {
  // 验证规则
}

async function fetchList() {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      ...searchForm
    }
    const response = await api.getList(params)
    list.value = response.data.items
    pagination.total = response.data.total
  } catch (error) {
    ElMessage.error('获取列表失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  pagination.page = 1
  fetchList()
}

function handleReset() {
  Object.keys(searchForm).forEach(key => {
    searchForm[key] = ''
  })
  pagination.page = 1
  fetchList()
}

function handleCreate() {
  isEdit.value = false
  dialogVisible.value = true
}

function handleEdit(row) {
  isEdit.value = true
  currentId.value = row.id
  Object.assign(form, row)
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    submitting.value = true

    if (isEdit.value) {
      await api.update(currentId.value, form)
      ElMessage.success('更新成功')
    } else {
      await api.create(form)
      ElMessage.success('创建成功')
    }

    dialogVisible.value = false
    fetchList()
  } catch (error) {
    // Error handled by interceptor
  } finally {
    submitting.value = false
  }
}

function handleDelete(row) {
  ElMessageBox.confirm(`确定要删除吗？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await api.delete(row.id)
      ElMessage.success('删除成功')
      fetchList()
    } catch (error) {
      // Error handled by interceptor
    }
  }).catch(() => {})
}

function resetForm() {
  if (formRef.value) {
    formRef.value.resetFields()
  }
  Object.keys(form).forEach(key => {
    form[key] = ''
  })
}

onMounted(() => {
  fetchList()
})
</script>

<style scoped>
.list-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-form {
  margin-bottom: 20px;
}

.pagination {
  margin-top: 20px;
  justify-content: flex-end;
}
</style>
```

## 网段管理实现指南

### NetworkSegment/List.vue
- 显示网段列表（名称、CIDR、网关、使用率）
- 使用率用进度条显示
- 搜索：按名称、网络地址
- 操作：创建、编辑、删除、查看详情

### NetworkSegment/Form.vue
- 表单字段：name, network, prefix_length, gateway, description, usage_threshold
- CIDR 验证：使用正则表达式验证格式
- 网关验证：验证 IP 格式

### NetworkSegment/Detail.vue
- 显示网段基本信息
- 显示统计数据（总IP、已用IP、使用率）
- 显示该网段下的 IP 列表

## IP 地址管理实现指南

### IPAddress/List.vue
- 显示 IP 列表（IP地址、状态、关联设备、网段）
- 状态用不同颜色的标签显示
- 筛选：按网段、状态
- 操作：分配、回收、保留、查看详情

### IPAddress/Allocate.vue
- 表单：选择网段、输入IP、选择设备
- IP 格式验证
- 调用冲突检测 API
- 显示冲突错误信息

### IPAddress/Detail.vue
- 显示 IP 基本信息
- 显示关联设备信息
- 显示历史操作记录（从日志API获取）

### IPAddress/Scanner.vue
- 选择要扫描的网段
- 显示扫描进度（进度条）
- 显示扫描结果（在线/离线IP列表）
- 高亮未注册的在线IP

## 设备管理实现指南

### Device/List.vue
- 显示设备列表（名称、MAC、类型、责任人）
- 模糊搜索：按名称、MAC、责任人
- 操作：创建、编辑、删除、查看详情

### Device/Form.vue
- 表单字段：name, mac_address, device_type, manufacturer, model, owner, department, location, description
- MAC 地址验证：格式 AA:BB:CC:DD:EE:FF 或 AA-BB-CC-DD-EE-FF

### Device/Detail.vue
- 显示设备完整信息
- 显示关联的所有 IP 地址
- 删除按钮（带确认）

## 操作日志实现指南

### Log/List.vue
- 显示日志列表（操作人、操作类型、资源类型、时间）
- 筛选：按操作人、操作类型、时间范围
- 只读，不可编辑删除
- 点击查看详情（显示完整的 JSON 详情）

## 告警管理实现指南

### Alert/List.vue
- 显示告警列表（网段、类型、严重程度、使用率、时间）
- 区分已解决和未解决（不同颜色）
- 筛选：按网段、是否解决
- 操作：解决告警

## 导入导出实现指南

### ImportExport/Index.vue
- 下载模板按钮
- 文件上传组件（el-upload）
- 显示导入结果和错误报告
- 导出按钮（可选择导出范围）

## 表单验证示例

### CIDR 格式验证
```javascript
const cidrValidator = (rule, value, callback) => {
  const cidrRegex = /^(\d{1,3}\.){3}\d{1,3}\/\d{1,2}$/
  if (!cidrRegex.test(value)) {
    callback(new Error('请输入有效的 CIDR 格式（如 192.168.1.0/24）'))
  } else {
    callback()
  }
}
```

### IP 地址验证
```javascript
const ipValidator = (rule, value, callback) => {
  const ipRegex = /^(\d{1,3}\.){3}\d{1,3}$/
  if (!ipRegex.test(value)) {
    callback(new Error('请输入有效的 IP 地址'))
  } else {
    const parts = value.split('.')
    if (parts.some(part => parseInt(part) > 255)) {
      callback(new Error('IP 地址每段不能超过 255'))
    } else {
      callback()
    }
  }
}
```

### MAC 地址验证
```javascript
const macValidator = (rule, value, callback) => {
  const macRegex = /^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$/
  if (!macRegex.test(value)) {
    callback(new Error('请输入有效的 MAC 地址（如 AA:BB:CC:DD:EE:FF）'))
  } else {
    callback()
  }
}
```

## ECharts 图表示例

### 柱状图（网段使用率）
```javascript
const option = {
  tooltip: {
    trigger: 'axis',
    axisPointer: { type: 'shadow' }
  },
  xAxis: {
    type: 'category',
    data: segments.map(s => s.name)
  },
  yAxis: {
    type: 'value',
    max: 100,
    axisLabel: { formatter: '{value}%' }
  },
  series: [{
    name: '使用率',
    type: 'bar',
    data: segments.map(s => s.usage_rate),
    itemStyle: {
      color: (params) => {
        const value = params.value
        if (value >= 80) return '#f56c6c'
        if (value >= 60) return '#e6a23c'
        return '#67c23a'
      }
    }
  }]
}
```

### 饼图（IP 状态分布）
```javascript
const option = {
  tooltip: {
    trigger: 'item',
    formatter: '{b}: {c} ({d}%)'
  },
  legend: {
    orient: 'vertical',
    left: 'left'
  },
  series: [{
    name: 'IP 状态',
    type: 'pie',
    radius: '50%',
    data: [
      { value: available, name: '空闲', itemStyle: { color: '#67c23a' } },
      { value: used, name: '已用', itemStyle: { color: '#e6a23c' } },
      { value: reserved, name: '保留', itemStyle: { color: '#909399' } }
    ]
  }]
}
```

## 响应式设计

使用 Element Plus 的响应式栅格系统：

```vue
<el-row :gutter="20">
  <el-col :xs="24" :sm="12" :md="8" :lg="6">
    <!-- 内容 -->
  </el-col>
</el-row>
```

- xs: <768px (手机)
- sm: ≥768px (平板)
- md: ≥992px (小屏电脑)
- lg: ≥1200px (大屏电脑)

## 主题切换

在 App.vue 中添加 CSS 变量：

```css
:root[data-theme="light"] {
  --bg-color: #ffffff;
  --text-color: #303133;
}

:root[data-theme="dark"] {
  --bg-color: #1a1a1a;
  --text-color: #ffffff;
}
```

## 快速开发建议

1. 复制 `User/List.vue` 作为基础模板
2. 修改 API 调用
3. 修改表格列定义
4. 修改表单字段
5. 添加特定的验证规则
6. 测试 CRUD 操作

每个页面的开发时间应该在 30-60 分钟内完成。
