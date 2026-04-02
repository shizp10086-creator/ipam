<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
      <h3>🧹 数据清洗</h3>
      <el-button type="primary" @click="runCleaning" :loading="running"><el-icon><Refresh /></el-icon> 执行清洗检查</el-button>
    </div>
    <el-alert v-if="result" :type="result.total_issues>0?'warning':'success'" :closable="false" style="margin-bottom:16px;">
      扫描完成：发现 {{ result.total_issues }} 个问题
    </el-alert>
    <el-table v-if="result && result.issues.length" :data="result.issues" stripe>
      <el-table-column label="严重程度" width="100"><template #default="{row}"><el-tag :type="{high:'danger',medium:'warning',low:'info'}[row.severity]" size="small">{{ {high:'高',medium:'中',low:'低'}[row.severity] }}</el-tag></template></el-table-column>
      <el-table-column label="问题类型" width="140"><template #default="{row}">{{ {duplicate_ip:'重复IP',usage_mismatch:'使用率异常',orphan_ip:'孤立IP'}[row.type]||row.type }}</template></el-table-column>
      <el-table-column prop="detail" label="详情" min-width="300" />
    </el-table>
    <el-empty v-if="result && result.issues.length===0" description="数据质量良好，未发现问题 ✅" />
    <el-empty v-if="!result" description="点击「执行清洗检查」开始扫描数据质量" />
  </div>
</template>
<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/api/request'
const result=ref(null),running=ref(false)
async function runCleaning(){running.value=true;try{const r=await request.post('/governance/data-cleaning/run');result.value=r.data;ElMessage.success(`扫描完成，发现 ${r.data.total_issues} 个问题`)}catch(e){ElMessage.error('扫描失败')}running.value=false}
</script>
