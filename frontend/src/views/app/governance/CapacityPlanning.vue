<template>
  <div>
    <h3 style="margin-bottom:16px;">📊 容量规划</h3>
    <el-row :gutter="12" style="margin-bottom:16px;">
      <el-col :span="8"><el-card shadow="hover"><div class="stat-card"><div class="stat-num">{{ items.length }}</div><div class="stat-label">监控网段</div></div></el-card></el-col>
      <el-col :span="8"><el-card shadow="hover"><div class="stat-card"><div class="stat-num" style="color:#f56c6c;">{{ highRisk }}</div><div class="stat-label">高风险（3个月内耗尽）</div></div></el-card></el-col>
      <el-col :span="8"><el-card shadow="hover"><div class="stat-card"><div class="stat-num" style="color:#e6a23c;">{{ medRisk }}</div><div class="stat-label">中风险（6个月内耗尽）</div></div></el-card></el-col>
    </el-row>
    <el-table :data="items" v-loading="loading" stripe :default-sort="{prop:'predicted_exhaust_months',order:'ascending'}">
      <el-table-column prop="name" label="网段名称" width="140" />
      <el-table-column prop="cidr" label="CIDR" width="160" />
      <el-table-column label="使用率" width="160"><template #default="{row}"><el-progress :percentage="Math.round(row.usage_rate)" :color="row.usage_rate>90?'#f56c6c':row.usage_rate>70?'#e6a23c':'#409eff'" :stroke-width="14" :text-inside="true" /></template></el-table-column>
      <el-table-column prop="available" label="剩余IP" width="80" />
      <el-table-column label="预计耗尽" width="120" sortable prop="predicted_exhaust_months"><template #default="{row}">{{ row.predicted_exhaust_months > 24 ? '24+月' : row.predicted_exhaust_months + '个月' }}</template></el-table-column>
      <el-table-column label="风险" width="80"><template #default="{row}"><el-tag :type="{high:'danger',medium:'warning',low:'success'}[row.risk_level]" size="small">{{ {high:'高',medium:'中',low:'低'}[row.risk_level] }}</el-tag></template></el-table-column>
    </el-table>
  </div>
</template>
<script setup>
import { ref, computed, onMounted } from 'vue'
import request from '@/api/request'
const items=ref([]),loading=ref(false)
const highRisk=computed(()=>items.value.filter(i=>i.risk_level==='high').length)
const medRisk=computed(()=>items.value.filter(i=>i.risk_level==='medium').length)
async function load(){loading.value=true;try{const r=await request.get('/governance/capacity/overview');items.value=r.data?.items||[]}catch(e){}loading.value=false}
onMounted(load)
</script>
<style scoped>.stat-card{text-align:center;padding:8px;}.stat-num{font-size:28px;font-weight:700;}.stat-label{font-size:12px;color:#909399;margin-top:4px;}</style>
