import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('@/components/Layout/MainLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '仪表板' }
      },
      // 网段管理
      {
        path: 'segments',
        name: 'SegmentList',
        component: () => import('@/views/NetworkSegment/List.vue'),
        meta: { title: '网段管理' }
      },
      {
        path: 'segments/create',
        name: 'SegmentCreate',
        component: () => import('@/views/NetworkSegment/Form.vue'),
        meta: { title: '创建网段', requiresRole: ['admin'] }
      },
      {
        path: 'segments/:id/edit',
        name: 'SegmentEdit',
        component: () => import('@/views/NetworkSegment/Form.vue'),
        meta: { title: '编辑网段', requiresRole: ['admin'] }
      },
      {
        path: 'segments/:id',
        name: 'SegmentDetail',
        component: () => import('@/views/NetworkSegment/Detail.vue'),
        meta: { title: '网段详情' }
      },
      // IP 地址管理
      {
        path: 'ip/list',
        name: 'IPList',
        component: () => import('@/views/IPAddress/List.vue'),
        meta: { title: 'IP 地址管理' }
      },
      {
        path: 'ip/allocate',
        name: 'IPAllocate',
        component: () => import('@/views/IPAddress/Allocate.vue'),
        meta: { title: '分配 IP', requiresRole: ['admin', 'user'] }
      },
      {
        path: 'ip/:id',
        name: 'IPDetail',
        component: () => import('@/views/IPAddress/Detail.vue'),
        meta: { title: 'IP 详情' },
        props: route => ({ ipId: Number(route.params.id) })
      },
      {
        path: 'ip/scanner',
        name: 'IPScanner',
        component: () => import('@/views/IPAddress/Scanner.vue'),
        meta: { title: 'IP 扫描' }
      },
      {
        path: 'ip/test-scanner',
        name: 'TestScanner',
        component: () => import('@/views/IPAddress/Scanner.vue'),
        meta: { title: 'IP 扫描测试' }
      },
      {
        path: 'ips/scanner',
        redirect: '/ip/scanner'
      },
      // 设备管理
      {
        path: 'devices',
        name: 'DeviceList',
        component: () => import('@/views/Device/List.vue'),
        meta: { title: '设备管理' }
      },
      {
        path: 'devices/create',
        name: 'DeviceCreate',
        component: () => import('@/views/Device/Form.vue'),
        meta: { title: '创建设备', requiresRole: ['admin', 'user'] }
      },
      {
        path: 'devices/:id/edit',
        name: 'DeviceEdit',
        component: () => import('@/views/Device/Form.vue'),
        meta: { title: '编辑设备', requiresRole: ['admin', 'user'] }
      },
      {
        path: 'devices/:id',
        name: 'DeviceDetail',
        component: () => import('@/views/Device/Detail.vue'),
        meta: { title: '设备详情' }
      },
      // 操作日志
      {
        path: 'logs',
        name: 'LogList',
        component: () => import('@/views/Log/List.vue'),
        meta: { title: '操作日志' }
      },
      // 告警管理
      {
        path: 'alerts',
        name: 'AlertList',
        component: () => import('@/views/Alert/List.vue'),
        meta: { title: '告警管理' }
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
      }
    ]
  },
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

// Navigation guard for authentication
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth !== false)
  const requiresRole = to.meta.requiresRole

  if (requiresAuth && !authStore.isAuthenticated) {
    // Redirect to login if not authenticated
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else if (requiresRole && !requiresRole.includes(authStore.userRole)) {
    // Check role permissions
    ElMessage.error('您没有权限访问此页面')
    next(from.path || '/')
  } else {
    next()
  }
})

// Set page title
router.afterEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} - IPAM 系统` : 'IPAM 系统'
})

export default router
