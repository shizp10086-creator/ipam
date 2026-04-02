<template>
  <div class="import-export-container">
    <!-- Excel 模板下载 -->
    <el-card class="section-card">
      <template #header>
        <span>Excel 模板下载</span>
      </template>
      <el-alert
        title="使用说明"
        type="info"
        :closable="false"
        class="info-alert"
      >
        <p>1. 下载 Excel 模板文件</p>
        <p>2. 按照模板格式填写数据</p>
        <p>3. 上传填写好的 Excel 文件进行导入</p>
      </el-alert>
      <el-button 
        type="primary" 
        :icon="Download" 
        @click="handleDownloadTemplate"
        :loading="downloadingTemplate"
      >
        下载 Excel 模板
      </el-button>
    </el-card>

    <!-- Excel 导入 -->
    <el-card class="section-card">
      <template #header>
        <span>Excel 导入</span>
      </template>
      
      <el-upload
        ref="uploadRef"
        class="upload-demo"
        drag
        :action="uploadAction"
        :headers="uploadHeaders"
        :on-success="handleUploadSuccess"
        :on-error="handleUploadError"
        :before-upload="beforeUpload"
        :on-progress="handleUploadProgress"
        accept=".xlsx,.xls"
        :auto-upload="true"
        :limit="1"
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">
          将文件拖到此处，或<em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            只能上传 xlsx/xls 文件，且不超过 10MB
          </div>
        </template>
      </el-upload>

      <!-- 上传进度 -->
      <el-progress 
        v-if="uploading" 
        :percentage="uploadProgress" 
        :status="uploadStatus"
        class="upload-progress"
      />

      <!-- 导入结果 -->
      <el-alert
        v-if="importResult"
        :title="importResult.success ? '导入成功' : '导入失败'"
        :type="importResult.success ? 'success' : 'error'"
        :closable="false"
        class="result-alert"
      >
        <div v-if="importResult.success">
          <p>成功导入 {{ importResult.success_count }} 条记录</p>
          <p v-if="importResult.failed_count > 0">
            失败 {{ importResult.failed_count }} 条记录
          </p>
        </div>
        <div v-else>
          <p>{{ importResult.message }}</p>
        </div>
      </el-alert>

      <!-- 错误详情 -->
      <el-collapse v-if="importResult && importResult.errors && importResult.errors.length > 0" class="error-collapse">
        <el-collapse-item title="查看错误详情" name="1">
          <el-table :data="importResult.errors" border stripe max-height="300">
            <el-table-column prop="row" label="行号" width="80" align="center" />
            <el-table-column prop="field" label="字段" width="120" />
            <el-table-column prop="value" label="值" width="150" show-overflow-tooltip />
            <el-table-column prop="error" label="错误信息" min-width="200" show-overflow-tooltip />
          </el-table>
        </el-collapse-item>
      </el-collapse>
    </el-card>

    <!-- Excel 导出 -->
    <el-card class="section-card">
      <template #header>
        <span>Excel 导出</span>
      </template>

      <el-form :inline="true" :model="exportForm" class="export-form">
        <el-form-item label="导出类型">
          <el-select v-model="exportForm.type" placeholder="请选择" style="width: 200px">
            <el-option label="网段数据" value="segments" />
            <el-option label="IP 地址数据" value="ips" />
            <el-option label="设备数据" value="devices" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="网段筛选" v-if="exportForm.type === 'ips'">
          <el-select v-model="exportForm.segment_id" placeholder="全部网段" clearable style="width: 200px">
            <el-option 
              v-for="segment in segments" 
              :key="segment.id" 
              :label="`${segment.name} (${segment.network}/${segment.prefix_length})`" 
              :value="segment.id" 
            />
          </el-select>
        </el-form-item>

        <el-form-item label="状态筛选" v-if="exportForm.type === 'ips'">
          <el-select v-model="exportForm.status" placeholder="全部状态" clearable style="width: 150px">
            <el-option label="空闲" value="available" />
            <el-option label="已用" value="used" />
            <el-option label="保留" value="reserved" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button 
            type="success" 
            :icon="Download" 
            @click="handleExport"
            :loading="exporting"
            :disabled="!exportForm.type"
          >
            导出数据
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Download, UploadFilled } from '@element-plus/icons-vue'
import * as importExportApi from '@/api/importExport'
import * as networkApi from '@/api/network'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const uploadRef = ref(null)
const downloadingTemplate = ref(false)
const uploading = ref(false)
const uploadProgress = ref(0)
const uploadStatus = ref('')
const importResult = ref(null)
const exporting = ref(false)
const segments = ref([])

const exportForm = reactive({
  type: 'ips',
  segment_id: null,
  status: ''
})

// 上传配置
const uploadAction = `${import.meta.env.VITE_API_BASE_URL}/import-export/import`
const uploadHeaders = {
  'Authorization': `Bearer ${authStore.token}`
}

// 下载模板
async function handleDownloadTemplate() {
  downloadingTemplate.value = true
  try {
    const response = await importExportApi.downloadTemplate()
    
    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', 'ipam_template.xlsx')
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('模板下载成功')
  } catch (error) {
    ElMessage.error('模板下载失败')
  } finally {
    downloadingTemplate.value = false
  }
}

// 上传前检查
function beforeUpload(file) {
  const isExcel = file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' || 
                  file.type === 'application/vnd.ms-excel'
  const isLt10M = file.size / 1024 / 1024 < 10

  if (!isExcel) {
    ElMessage.error('只能上传 Excel 文件！')
    return false
  }
  if (!isLt10M) {
    ElMessage.error('文件大小不能超过 10MB！')
    return false
  }
  
  uploading.value = true
  uploadProgress.value = 0
  uploadStatus.value = ''
  importResult.value = null
  
  return true
}

// 上传进度
function handleUploadProgress(event) {
  uploadProgress.value = Math.round(event.percent)
}

// 上传成功
function handleUploadSuccess(response) {
  uploading.value = false
  uploadProgress.value = 100
  uploadStatus.value = 'success'
  
  if (response.code === 200 || response.code === 201) {
    importResult.value = {
      success: true,
      success_count: response.data.success_count || 0,
      failed_count: response.data.failed_count || 0,
      errors: response.data.errors || []
    }
    ElMessage.success('导入完成')
  } else {
    importResult.value = {
      success: false,
      message: response.message || '导入失败'
    }
  }
  
  // 清空上传列表
  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
}

// 上传失败
function handleUploadError(error) {
  uploading.value = false
  uploadStatus.value = 'exception'
  
  try {
    const response = JSON.parse(error.message)
    importResult.value = {
      success: false,
      message: response.detail || '导入失败'
    }
  } catch {
    importResult.value = {
      success: false,
      message: '导入失败，请检查文件格式'
    }
  }
  
  ElMessage.error('导入失败')
}

// 导出数据
async function handleExport() {
  exporting.value = true
  try {
    const params = {
      type: exportForm.type
    }
    
    if (exportForm.type === 'ips') {
      if (exportForm.segment_id) {
        params.segment_id = exportForm.segment_id
      }
      if (exportForm.status) {
        params.status = exportForm.status
      }
    }
    
    const response = await importExportApi.exportData(params)
    
    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response]))
    const link = document.createElement('a')
    link.href = url
    
    const filename = `ipam_${exportForm.type}_${new Date().getTime()}.xlsx`
    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('导出成功')
  } catch (error) {
    ElMessage.error('导出失败')
  } finally {
    exporting.value = false
  }
}

// 加载网段列表
async function loadSegments() {
  try {
    const response = await networkApi.getSegments({ page_size: 1000 })
    segments.value = response.data.items || response.data
  } catch (error) {
    console.error('加载网段列表失败', error)
  }
}

onMounted(() => {
  loadSegments()
})
</script>

<style scoped>
.import-export-container {
  padding: 8px;
}

.section-card {
  margin-bottom: 16px;
}

.info-alert {
  margin-bottom: 16px;
}

.info-alert p {
  margin: 4px 0;
}

.upload-demo {
  margin-top: 16px;
}

.upload-progress {
  margin-top: 16px;
}

.result-alert {
  margin-top: 16px;
}

.result-alert p {
  margin: 4px 0;
}

.error-collapse {
  margin-top: 16px;
}

.export-form {
  margin-top: 16px;
}
</style>
