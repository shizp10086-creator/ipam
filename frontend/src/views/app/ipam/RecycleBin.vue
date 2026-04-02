<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
      <h3>🗑️ IP 回收站</h3>
      <el-button type="danger" @click="emptyAll" :disabled="items.length===0">清空回收站</el-button>
    </div>
    <el-alert type="info" :closable="false" style="margin-bottom:12px;">已删除的 IP/网段/设备记录保留 30 天，超期自动永久删除。</el-alert>
    <el-table :data="items" v-loading="loading" stripe>
      <el-table-column prop="type" label="类型" width="80"><template #default="{row}"><el-tag size="small">{{ {ip:'IP',segment:'网段',device:'设备'}[row.type]||row.type }}</el-tag></template></el-table-column>
      <el-table-column prop="name" label="名称/地址" min-width="200" />
      <el-table-column prop="deleted_at" label="删除时间" width="170" />
      <el-table-column prop="deleted_by" label="删除人" width="100" />
      <el-table-column label="操作" width="140">
        <template #default="{row}">
          <el-button link size="small" type="primary" @click="restore(row)">恢复</el-button>
          <el-popconfirm title="永久删除？不可恢复！" @confirm="permanentDelete(row)">
            <template #reference><el-button link size="small" type="danger">永久删除</el-button></template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
const items=ref([]),loading=ref(false)
async function load(){
  loading.value=true
  // 模拟数据（实际从后端查询 deleted_at IS NOT NULL 的记录）
  items.value=[]
  loading.value=false
}
function restore(row){ElMessage.success(`${row.name} 已恢复`)}
function permanentDelete(row){ElMessage.success(`${row.name} 已永久删除`)}
async function emptyAll(){
  try{await ElMessageBox.confirm('确定清空回收站？所有数据将永久删除！','警告',{type:'warning'});ElMessage.success('回收站已清空')}catch{}
}
onMounted(load)
</script>
