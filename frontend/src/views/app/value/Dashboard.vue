<template>
  <div>
    <h3 style="margin-bottom:16px;">💰 IT 价值量化</h3>
    <!-- 核心指标 -->
    <el-row :gutter="16" style="margin-bottom:20px;">
      <el-col :span="6"><el-card shadow="hover" class="value-card green"><div class="vc-num">{{ eff.total_saved_hours||0 }}h</div><div class="vc-label">本月节省工时</div><div class="vc-sub">折合 ¥{{ eff.cost_saved_yuan||0 }}</div></el-card></el-col>
      <el-col :span="6"><el-card shadow="hover" class="value-card blue"><div class="vc-num">¥{{ (cost.total_monthly||0).toLocaleString() }}</div><div class="vc-label">本月成本节省</div></el-card></el-col>
      <el-col :span="6"><el-card shadow="hover" class="value-card orange"><div class="vc-num">¥{{ ((risk.total_monthly||0)/10000).toFixed(0) }}万</div><div class="vc-label">风险规避价值</div></el-card></el-col>
      <el-col :span="6"><el-card shadow="hover" class="value-card gold"><div class="vc-num">{{ roi.roi_percentage||0 }}%</div><div class="vc-label">投资回报率 ROI</div><div class="vc-sub">回收期 {{ roi.payback_months||0 }} 个月</div></el-card></el-col>
    </el-row>
    <el-tabs v-model="activeTab">
      <el-tab-pane label="效率提升" name="efficiency">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="IP 分配效率">基线 {{ eff.ip_allocation?.baseline_minutes }}分钟 → 现在 {{ eff.ip_allocation?.current_minutes }}分钟，提升 {{ eff.ip_allocation?.improvement }}%</el-descriptions-item>
          <el-descriptions-item label="故障发现(MTTD)">基线 {{ eff.mttd?.baseline_minutes }}分钟 → 现在 {{ eff.mttd?.current_seconds }}秒，提升 {{ eff.mttd?.improvement }}%</el-descriptions-item>
          <el-descriptions-item label="故障修复(MTTR)">基线 {{ eff.mttr?.baseline_hours }}小时 → 现在 {{ eff.mttr?.current_minutes }}分钟，提升 {{ eff.mttr?.improvement }}%</el-descriptions-item>
          <el-descriptions-item label="工单处理">平均 {{ eff.ticket?.avg_hours }}小时，SLA 达标 {{ eff.ticket?.sla_rate }}%</el-descriptions-item>
        </el-descriptions>
      </el-tab-pane>
      <el-tab-pane label="成本节省" name="cost">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="闲置资产回收">发现 {{ cost.idle_assets?.count }} 台，价值 ¥{{ (cost.idle_assets?.value||0).toLocaleString() }}，已回收 {{ cost.idle_assets?.recovered }} 台</el-descriptions-item>
          <el-descriptions-item label="IP 资源优化">回收 {{ cost.ip_optimization?.recovered_ips }} 个 IP，月省 ¥{{ cost.ip_optimization?.monthly_saving }}</el-descriptions-item>
          <el-descriptions-item label="许可证优化">超量 {{ cost.license?.over_licensed }} 个，年省 ¥{{ (cost.license?.annual_saving||0).toLocaleString() }}</el-descriptions-item>
          <el-descriptions-item label="能耗优化">低负载服务器 {{ cost.energy?.low_usage_servers }} 台，年省 ¥{{ cost.energy?.annual_saving }}</el-descriptions-item>
          <el-descriptions-item label="故障避免">避免 {{ cost.incident_avoided?.count }} 次，避免损失 ¥{{ (cost.incident_avoided?.total_avoided||0).toLocaleString() }}</el-descriptions-item>
        </el-descriptions>
      </el-tab-pane>
      <el-tab-pane label="风险规避" name="risk">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="非法接入防护">阻止 {{ risk.illegal_access?.blocked }} 次，规避 ¥{{ (risk.illegal_access?.total_avoided||0).toLocaleString() }}</el-descriptions-item>
          <el-descriptions-item label="违规软件检测">发现 {{ risk.illegal_software?.found }} 款涉及 {{ risk.illegal_software?.terminals }} 台终端</el-descriptions-item>
          <el-descriptions-item label="预警避免故障">预警 {{ risk.predictive_alerts?.total }} 条，避免 {{ risk.predictive_alerts?.prevented }} 次故障</el-descriptions-item>
          <el-descriptions-item label="合规审计">自动生成 {{ risk.compliance?.reports_generated }} 份报表，通过率 {{ risk.compliance?.pass_rate }}%</el-descriptions-item>
        </el-descriptions>
      </el-tab-pane>
      <el-tab-pane label="部门排行" name="dept">
        <el-table :data="depts" stripe>
          <el-table-column prop="department" label="部门" width="120" />
          <el-table-column label="综合评分" width="100"><template #default="{row}"><el-tag :type="row.score>=85?'success':row.score>=70?'':'danger'" size="small">{{ row.score }}分</el-tag></template></el-table-column>
          <el-table-column label="IP 闲置率" width="100"><template #default="{row}">{{ row.ip_idle_rate }}%</template></el-table-column>
          <el-table-column label="设备利用率" width="100"><template #default="{row}">{{ row.device_usage }}%</template></el-table-column>
          <el-table-column label="合规率" width="100"><template #default="{row}">{{ row.compliance }}%</template></el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import request from '@/api/request'
const activeTab=ref('efficiency'),eff=ref({}),cost=ref({}),risk=ref({}),roi=ref({}),depts=ref([])
async function load(){
  try{
    const [r1,r2,r3,r4,r5]=await Promise.all([
      request.get('/value/efficiency'),request.get('/value/cost-saving'),
      request.get('/value/risk-avoidance'),request.get('/value/roi'),
      request.get('/value/department-ranking'),
    ])
    eff.value=r1.data||{};cost.value=r2.data||{};risk.value=r3.data||{};roi.value=r4.data||{};depts.value=r5.data?.items||[]
  }catch(e){}
}
onMounted(load)
</script>
<style scoped>
.value-card{text-align:center;padding:8px 0;}
.value-card.green{border-top:3px solid #67c23a;}.value-card.blue{border-top:3px solid #409eff;}
.value-card.orange{border-top:3px solid #e6a23c;}.value-card.gold{border-top:3px solid #f7ba2a;}
.vc-num{font-size:26px;font-weight:700;color:#303133;}.vc-label{font-size:13px;color:#909399;margin-top:4px;}
.vc-sub{font-size:11px;color:#c0c4cc;margin-top:2px;}
</style>
