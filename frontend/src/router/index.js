/**
 * 路由配置 - 双入口单应用架构
 *
 * /admin/* — 管理员设计态（设计器/配置/插件/权限）
 * /app/*   — 用户运行态（IP管理/资产/告警/工单）
 *
 * 登录后根据角色自动跳转：
 * - admin → /admin/dashboard
 * - user/readonly → /app/dashboard
 */
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const routes = [
  // ==================== 公共页面 ====================
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  },

  // ==================== 管理员设计态 /admin ====================
  {
    path: '/admin',
    component: () => import('@/layouts/AdminLayout.vue'),
    meta: { requiresAuth: true, requiresRole: ['admin'] },
    children: [
      {
        path: '',
        redirect: '/admin/dashboard'
      },
      {
        path: 'dashboard',
        name: 'AdminDashboard',
        component: () => import('@/views/admin/AdminDashboard.vue'),
        meta: { title: '管理首页' }
      },
      // 设计器
      {
        path: 'designer/form',
        name: 'FormDesigner',
        component: () => import('@/views/admin/designer/FormDesigner.vue'),
        meta: { title: '表单设计器' }
      },
      {
        path: 'designer/workflow',
        name: 'WorkflowDesigner',
        component: () => import('@/views/admin/designer/WorkflowDesigner.vue'),
        meta: { title: '流程设计器' }
      },
      {
        path: 'designer/report',
        name: 'ReportDesigner',
        component: () => import('@/views/admin/designer/ReportDesigner.vue'),
        meta: { title: '报表设计器' }
      },
      {
        path: 'designer/dashboard',
        name: 'DashboardDesigner',
        component: () => import('@/views/admin/designer/DashboardDesigner.vue'),
        meta: { title: '仪表盘设计器' }
      },
      {
        path: 'designer/screen',
        name: 'ScreenDesigner',
        component: () => import('@/views/admin/designer/ScreenDesigner.vue'),
        meta: { title: '大屏设计器' }
      },
      {
        path: 'designer/ppt',
        name: 'PPTDesigner',
        component: () => import('@/views/admin/designer/PPTDesigner.vue'),
        meta: { title: 'PPT 设计器' }
      },
      {
        path: 'designer/page',
        name: 'PageDesigner',
        component: () => import('@/views/admin/designer/PageDesigner.vue'),
        meta: { title: '页面布局设计器' }
      },
      // 系统配置
      {
        path: 'config/system',
        name: 'SystemConfig',
        component: () => import('@/views/admin/config/SystemConfig.vue'),
        meta: { title: '配置中心' }
      },
      {
        path: 'config/notification',
        name: 'NotificationConfig',
        component: () => import('@/views/admin/config/NotificationConfig.vue'),
        meta: { title: '通知渠道' }
      },
      {
        path: 'config/scheduler',
        name: 'SchedulerConfig',
        component: () => import('@/views/admin/config/SchedulerConfig.vue'),
        meta: { title: '定时任务' }
      },
      // 管理功能
      {
        path: 'plugins',
        name: 'PluginManager',
        component: () => import('@/views/admin/PluginManager.vue'),
        meta: { title: '插件管理' }
      },
      {
        path: 'permissions',
        name: 'PermissionManager',
        component: () => import('@/views/admin/PermissionManager.vue'),
        meta: { title: '权限管理' }
      },
      {
        path: 'tenants',
        name: 'TenantManager',
        component: () => import('@/views/admin/TenantManager.vue'),
        meta: { title: '租户管理' }
      },
      {
        path: 'templates',
        name: 'TemplateManager',
        component: () => import('@/views/admin/TemplateManager.vue'),
        meta: { title: '模板库' }
      },
      {
        path: 'connectors',
        name: 'ConnectorManager',
        component: () => import('@/views/admin/ConnectorManager.vue'),
        meta: { title: '连接器' }
      },
      {
        path: 'automation',
        name: 'AutomationManager',
        component: () => import('@/views/admin/AutomationManager.vue'),
        meta: { title: '自动化工作流' }
      },
    ]
  },

  // ==================== 用户运行态 /app ====================
  {
    path: '/app',
    component: () => import('@/layouts/AppLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: '/app/dashboard'
      },
      {
        path: 'dashboard',
        name: 'AppDashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '运维仪表盘' }
      },
      // IPAM
      {
        path: 'ipam/segments',
        name: 'SegmentList',
        component: () => import('@/views/NetworkSegment/List.vue'),
        meta: { title: '网段管理' }
      },
      {
        path: 'ipam/segments/create',
        name: 'SegmentCreate',
        component: () => import('@/views/NetworkSegment/Form.vue'),
        meta: { title: '创建网段', requiresRole: ['admin'] }
      },
      {
        path: 'ipam/segments/:id/edit',
        name: 'SegmentEdit',
        component: () => import('@/views/NetworkSegment/Form.vue'),
        meta: { title: '编辑网段', requiresRole: ['admin'] }
      },
      {
        path: 'ipam/segments/:id',
        name: 'SegmentDetail',
        component: () => import('@/views/NetworkSegment/Detail.vue'),
        meta: { title: '网段详情' }
      },
      {
        path: 'ipam/ips',
        name: 'IPList',
        component: () => import('@/views/IPAddress/List.vue'),
        meta: { title: 'IP 地址管理' }
      },
      {
        path: 'ipam/ips/allocate',
        name: 'IPAllocate',
        component: () => import('@/views/IPAddress/Allocate.vue'),
        meta: { title: '分配 IP', requiresRole: ['admin', 'user'] }
      },
      {
        path: 'ipam/ips/:id',
        name: 'IPDetail',
        component: () => import('@/views/IPAddress/Detail.vue'),
        meta: { title: 'IP 详情' },
        props: route => ({ ipId: Number(route.params.id) })
      },
      {
        path: 'ipam/matrix/:segmentId',
        name: 'IPMatrix',
        component: () => import('@/views/IPAddress/Matrix.vue'),
        meta: { title: 'IP 矩阵视图' }
      },
      {
        path: 'ipam/scan',
        name: 'IPScanner',
        component: () => import('@/views/IPAddress/Scanner.vue'),
        meta: { title: 'Ping 扫描' }
      },
      // 资产管理
      {
        path: 'assets/devices',
        name: 'DeviceList',
        component: () => import('@/views/Device/List.vue'),
        meta: { title: '设备资产' }
      },
      {
        path: 'assets/devices/create',
        name: 'DeviceCreate',
        component: () => import('@/views/Device/Form.vue'),
        meta: { title: '创建设备', requiresRole: ['admin', 'user'] }
      },
      {
        path: 'assets/devices/:id',
        name: 'DeviceDetail',
        component: () => import('@/views/Device/Detail.vue'),
        meta: { title: '设备详情' }
      },
      {
        path: 'assets/terminals',
        name: 'TerminalList',
        component: () => import('@/views/app/terminals/List.vue'),
        meta: { title: '终端管理' }
      },
      {
        path: 'assets/inventory',
        name: 'InventoryList',
        component: () => import('@/views/app/inventory/List.vue'),
        meta: { title: '资产盘点' }
      },
      // DCIM
      {
        path: 'dcim/datacenters',
        name: 'DataCenterList',
        component: () => import('@/views/app/dcim/DataCenterList.vue'),
        meta: { title: '机房管理' }
      },
      {
        path: 'dcim/racks',
        name: 'RackList',
        component: () => import('@/views/app/dcim/RackList.vue'),
        meta: { title: '机架管理' }
      },
      {
        path: 'dcim/topology',
        name: 'Topology',
        component: () => import('@/views/app/dcim/Topology.vue'),
        meta: { title: '网络拓扑' }
      },
      // 告警
      {
        path: 'alerts',
        name: 'AlertList',
        component: () => import('@/views/Alert/List.vue'),
        meta: { title: '告警中心' }
      },
      // NAC 准入控制
      {
        path: 'nac/policies',
        name: 'NacPolicies',
        component: () => import('@/views/app/nac/Policies.vue'),
        meta: { title: '认证策略' }
      },
      {
        path: 'nac/sessions',
        name: 'NacSessions',
        component: () => import('@/views/app/nac/Sessions.vue'),
        meta: { title: '在线终端' }
      },
      {
        path: 'nac/auth-logs',
        name: 'NacAuthLogs',
        component: () => import('@/views/app/nac/AuthLogs.vue'),
        meta: { title: '认证日志' }
      },
      {
        path: 'nac/visitors',
        name: 'NacVisitors',
        component: () => import('@/views/app/nac/Visitors.vue'),
        meta: { title: '访客管理' }
      },
      // 工单
      {
        path: 'tickets',
        name: 'TicketList',
        component: () => import('@/views/app/tickets/List.vue'),
        meta: { title: '工单协作' }
      },
      // 报表
      {
        path: 'reports',
        name: 'ReportCenter',
        component: () => import('@/views/ComingSoon.vue'),
        meta: { title: '报表中心' }
      },
      // 日志
      {
        path: 'logs',
        name: 'LogList',
        component: () => import('@/views/Log/List.vue'),
        meta: { title: '操作日志' }
      },
      // 导入导出
      {
        path: 'import-export',
        name: 'ImportExport',
        component: () => import('@/views/ImportExport/Index.vue'),
        meta: { title: '导入导出', requiresRole: ['admin'] }
      },
      // 用户管理
      {
        path: 'users',
        name: 'UserList',
        component: () => import('@/views/User/List.vue'),
        meta: { title: '用户管理', requiresRole: ['admin'] }
      },
      // 个人设置
      {
        path: 'settings',
        name: 'UserSettings',
        component: () => import('@/views/ComingSoon.vue'),
        meta: { title: '个人设置' }
      },
    ]
  },

  // ==================== 兼容旧路由（重定向到 /app） ====================
  {
    path: '/',
    redirect: '/app/dashboard'
  },
  {
    path: '/segments',
    redirect: '/app/ipam/segments'
  },
  {
    path: '/ip/list',
    redirect: '/app/ipam/ips'
  },
  {
    path: '/devices',
    redirect: '/app/assets/devices'
  },
  {
    path: '/alerts',
    redirect: '/app/alerts'
  },
  {
    path: '/logs',
    redirect: '/app/logs'
  },

  // 404
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth !== false)
  const requiresRole = to.meta.requiresRole

  if (requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
    return
  }

  if (requiresRole && !requiresRole.includes(authStore.userRole)) {
    ElMessage.error('您没有权限访问此页面')
    next(from.path || '/app/dashboard')
    return
  }

  next()
})

// 登录后根据角色跳转
export function getDefaultRoute(role) {
  if (role === 'admin') return '/admin/dashboard'
  return '/app/dashboard'
}

// 页面标题
router.afterEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} - IT 智维平台` : 'IT 智维平台'
})

export default router
