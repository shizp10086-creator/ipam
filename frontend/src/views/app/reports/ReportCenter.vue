<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
      <h3>📊 报表中心</h3>
      <div style="display:flex;gap:8px;">
        <el-date-picker v-model="dateRange" type="daterange" range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期" style="width:280px;" size="default" @change="load" />
        <el-button type="primary" @click="exportReport">导出报表</el-button>
      </div>
    </div>
    <el-tabs v-model="activeTab" @tab-change="load">
      <el-tab-pane label="IP 资源报表" name="ip" />
      <el-tab-pane label="设备资产报表" name="device" />
      <el-tab-pane label="告警统计报表" name="alert" />
      <el-tab-pane label="工单统计报表" name="ticket" />
      <el-tab-pane label="准入审计报表" name="nac" />
      <el-tab-pane label="自定义报表" name="custom" />
    </el-tabs>
    <div v-loading="loading">
      <!-- IP 资源报表 -->
      <template v-if="activeTab==='ip'">
        <div style="display:flex;gap:16px;margin-bottom:16px;">
          <el-card style="flex:1;text-align:center;"><div style="font-size:28px;font-weight:bold;color:#409eff;">{{ ipStats.total_segments }}</div><div style="color:#909399;font-size:13px;">网段总数</div></el-card>
          <el-card style="flex:1;text-align:center;"><div style="font-size:28px;font-weight:bold;color:#67c23a;">{{ ipStats.total_ips }}</div><div style="color:#909399;font-size:13px;">IP 总数</div></el-card>
          <el-card style="flex:1;text-align:center;"><div style="font-size:28px;font-weight:bold;color:#f56c6c;">{{ ipStats.used_ips }}</div><div style="color:#909399;font-size:13px;">已分配</div></el-card>
          <el-card style="flex:1;text-align:center;"><div style="font-size:28px;font-weight:bold;color:#e6a23c;">{{ ipStats.usage_rate }}%</div><div style="color:#909399;font-size:13px;">使用率</div></el-card>
        </div>
        <el-table :data="ipDetails" stripe>
          <el-table-column prop="name" label="网段名称" min-width="160" />
          <el-table-column prop="cidr" label="CIDR" width="160" />
          <el-table-column prop="total" label="总 IP" width="80" />
          <el-table-column prop="used" label="已用" width="80" />
          <el-table-column prop="available" label="可用" width="80" />
          <el-table-column label="使用率" width="120"><template #default="{row}"><el-progress :percentage="row.usage_rate||0" :stroke-width="6" /></template></el-table-column>
        </el-table>
      </template>
      <!-- 设备资产报表 -->
      <template v-if="activeTab==='device'">
        <div style="display:flex;gap:16px;margin-bottom:16px;">
          <el-card style="flex:1;text-align:center;"><div style="font-size:28px;font-weight:bold;color:#409eff;">{{ deviceStats.total }}</div><div style="color:#909399;font-size:13px;">设备总数</div></el-card>
          <el-card style="flex:1;text-align:center;"><div style="font-size:28px;font-weight:bold;color:#67c23a;">{{ deviceStats.online }}</div><div style="color:#909399;font-size:13px;">在线</div></el-card>
          <el-card style="flex:1;text-align:center;"><div style="font-size:28px;font-weight:bold;color:#e6a23c;">{{ deviceStats.types }}</div><div style="color:#909399;font-size:13px;">设备类型</div></el-card>
        </div>
        <el-table :data="deviceDetails" stripe>
          <el-table-column prop="device_type" label="设备类型" width="140" />
          <el-table-column prop="count" label="数量" width="80" />
          <el-table-column prop="online" label="在线" width="80" />
          <el-table-column label="在线率" width="120"><template #default="{row}"><el-progress :percentage="row.online_rate||0" :stroke-width="6" /></template></el-table-column>
        </el-table>
      </template>
      <!-- 告警统计报表 -->
      <template v-if="activeTab==='alert'">
        <el-table :data="alertDetails" stripe>
          <el-table-column prop="level" label="告警级别" width="100"><template #default="{row}"><el-tag :type="{critical:'danger',warning:'warning',info:'info'}[row.level]" size="small">{{ row.level }}</el-tag></template></el-table-column>
          <el-table-column prop="count" label="数量" width="80" />
          <el-table-column prop="acknowledged" label="已确认" width="80" />
          <el-table-column prop="resolved" label="已恢复" width="80" />
          <el-table-column label="处理率" width="120"><template #default="{row}"><el-progress :percentage="row.resolve_rate||0" :stroke-width="6" /></template></el-table-column>
        </el-table>
      </template>
      <!-- 工单统计报表 -->
      <template v-if="activeTab==='ticket'">
        <el-table :data="ticketDetails" stripe>
          <el-table-column prop="ticket_type" label="工单类型" width="140" />
          <el-table-column prop="total" label="总数" width="80" />
          <el-table-column prop="completed" label="已完成" width="80" />
          <el-table-column prop="avg_hours" label="平均处理时长(h)" width="140" />
          <el-table-column label="完成率" width="120"><template #default="{row}"><el-progress :percentage="row.complete_rate||0" :stroke-width="6" /></template></el-table-column>
        </el-table>
      </template>
      <!-- 准入审计报表 -->
      <template v-if="activeTab==='nac'">
        <el-table :data="nacDetails" stripe>
          <el-table-column prop="auth_method" label="认证方式" width="140" />
          <el-table-column prop="total" label="认证次数" width="100" />
          <el-table-column prop="success" label="成功" width="80" />
          <el-table-column prop="failed" label="失败" width="80" />
          <el-table-column label="成功率" width="120"><template #default="{row}"><el-progress :percentage="row.success_rate||0" :stroke-width="6" /></template></el-table-column>
        </el-table>
      </template>
      <!-- 自定义报表 -->
      <template v-if="activeTab==='custom'">
        <el-table :data="customReports" stripe>
          <el-table-column prop="name" label="报表名称" min-width="200" />
          <el-table-column prop="type" label="类型" width="100" />
          <el-table-column prop="schedule" label="生成周期" width="100" />
          <el-table-column prop="last_generated" label="上次生成" width="170" />
          <el-table-column label="操作" width="120">
            <template #default="{row}"><el-button link size="small" @click="viewReport(row)">查看</el-button><el-button link size="small" @click="downloadReport(row)">下载</el-button></template>
          </el-table-column>
        </el-table>
      </template>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/api/request'
const activeTab=ref('ip'),loading=ref(false),dateRange=ref(null)
const ipStats=ref({total_segments:0,total_ips:0,used_ips:0,usage_rate:0}),ipDetails=ref([])
const deviceStats=ref({total:0,online:0,types:0}),deviceDetails=ref([])
const alertDetails=ref([]),ticketDetails=ref([]),nacDetails=ref([]),customReports=ref([])
async function load(){
  loading.value=true
  try{
    if(activeTab.value==='ip'){
      const r=await request.get('/dashboard/stats');const d=r.data||{}
      ipStats.value={total_segments:d.total_segments||0,total_ips:d.total_ips||0,used_ips:d.used_ips||0,usage_rate:d.total_ips?Math.round(d.used_ips/d.total_ips*100):0}
      try{const sr=await request.get('/segments?limit=100');ipDetails.value=(sr.data?.items||[]).map(s=>({name:s.name,cidr:`${s.network}/${s.prefix_length}`,total:s.total_ips||0,used:s.used_ips||0,available:(s.total_ips||0)-(s.used_ips||0),usage_rate:s.total_ips?Math.round(s.used_ips/s.total_ips*100):0}))}catch(e){}
    }else if(activeTab.value==='device'){
      try{const r=await request.get('/dashboard/stats');deviceStats.value={total:r.data?.total_devices||0,online:0,types:0}}catch(e){}
    }else if(activeTab.value==='alert'){
      alertDetails.value=[{level:'critical',count:0,acknowledged:0,resolved:0,resolve_rate:0},{level:'warning',count:0,acknowledged:0,resolved:0,resolve_rate:0},{level:'info',count:0,acknowledged:0,resolved:0,resolve_rate:0}]
      try{const r=await request.get('/alerts?limit=200');const items=r.data?.items||[];alertDetails.value.forEach(a=>{const f=items.filter(i=>i.severity===a.level);a.count=f.length;a.acknowledged=f.filter(i=>i.acknowledged).length;a.resolved=f.filter(i=>i.status==='resolved').length;a.resolve_rate=a.count?Math.round(a.resolved/a.count*100):0})}catch(e){}
    }else if(activeTab.value==='ticket'){
      try{const r=await request.get('/tickets/tickets?limit=200');const items=r.data?.items||[];const types=[...new Set(items.map(i=>i.ticket_type))];ticketDetails.value=types.map(t=>{const f=items.filter(i=>i.ticket_type===t);return{ticket_type:t,total:f.length,completed:f.filter(i=>i.status==='completed').length,avg_hours:'-',complete_rate:f.length?Math.round(f.filter(i=>i.status==='completed').length/f.length*100):0}})}catch(e){}
    }else if(activeTab.value==='nac'){
      nacDetails.value=[{auth_method:'802.1X',total:0,success:0,failed:0,success_rate:0},{auth_method:'MAC',total:0,success:0,failed:0,success_rate:0},{auth_method:'Portal',total:0,success:0,failed:0,success_rate:0}]
    }else if(activeTab.value==='custom'){
      try{const r=await request.get('/designer/configs?config_type=report&limit=50');customReports.value=(r.data?.items||[]).map(i=>({...i,type:'自定义',schedule:'-',last_generated:i.updated_at}))}catch(e){}
    }
  }catch(e){}
  loading.value=false
}
function exportReport(){ElMessage.success('报表导出功能已触发')}
function viewReport(row){ElMessage.info(`查看报表: ${row.name}`)}
function downloadReport(row){ElMessage.info(`下载报表: ${row.name}`)}
onMounted(load)
</script>
