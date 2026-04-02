<template>
  <div>
    <h3 style="margin-bottom:16px;">🌡️ IP 使用率热力图</h3>
    <el-row :gutter="8" class="heatmap-grid">
      <el-col :span="4" v-for="seg in segments" :key="seg.id">
        <div class="heat-cell" :style="{background: getHeatColor(seg.usage_rate)}" @click="$router.push(`/app/ipam/segments/${seg.id}`)">
          <div class="heat-name">{{ seg.name }}</div>
          <div class="heat-cidr">{{ seg.cidr || `${seg.network}/${seg.prefix_length}` }}</div>
          <div class="heat-rate">{{ Math.round(seg.usage_rate||0) }}%</div>
          <div class="heat-detail">{{ seg.used_ips||0 }}/{{ seg.total_ips||0 }}</div>
        </div>
      </el-col>
    </el-row>
    <div style="margin-top:16px;display:flex;align-items:center;gap:8px;">
      <span style="font-size:12px;color:#909399;">使用率：</span>
      <div style="width:200px;height:12px;border-radius:6px;background:linear-gradient(to right,#67c23a,#e6a23c,#f56c6c);"></div>
      <span style="font-size:12px;color:#909399;">0% → 100%</span>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import request from '@/api/request'
const segments = ref([])
function getHeatColor(rate) {
  const r = Math.min(rate||0, 100)
  if (r < 50) return `rgba(103,194,58,${0.2+r/100})`
  if (r < 80) return `rgba(230,162,60,${0.3+r/200})`
  return `rgba(245,108,108,${0.4+r/250})`
}
async function load() {
  try { const r = await request.get('/segments?include_stats=true&page_size=100'); segments.value = r.data?.items || [] } catch(e) {}
}
onMounted(load)
</script>
<style scoped>
.heatmap-grid{flex-wrap:wrap;}
.heat-cell{padding:12px 8px;border-radius:8px;text-align:center;margin-bottom:8px;cursor:pointer;transition:transform 0.2s;min-height:90px;}
.heat-cell:hover{transform:scale(1.05);}
.heat-name{font-size:12px;font-weight:600;color:#fff;text-shadow:0 1px 2px rgba(0,0,0,0.3);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.heat-cidr{font-size:10px;color:rgba(255,255,255,0.8);}
.heat-rate{font-size:20px;font-weight:700;color:#fff;margin:4px 0;}
.heat-detail{font-size:10px;color:rgba(255,255,255,0.7);}
</style>
