import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

// Create axios instance
const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor - 添加 JWT token
request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
request.interceptors.response.use(
  (response) => {
    // Return the data directly
    return response.data
  },
  (error) => {
    if (error.response) {
      const { status, data } = error.response
      
      // 将后端英文错误信息转换为中文
      const translateError = (msg) => {
        if (!msg) return null
        const m = msg.toLowerCase()
        if (m.includes('database')) return '数据库错误，请稍后重试'
        if (m.includes('not found')) return '请求的资源不存在'
        if (m.includes('already exists')) return '数据已存在，请勿重复添加'
        if (m.includes('constraint')) return '数据约束冲突，请检查输入'
        if (m.includes('connection')) return '服务连接失败，请稍后重试'
        if (m.includes('timeout')) return '请求超时，请稍后重试'
        if (m.includes('permission') || m.includes('forbidden')) return '没有权限执行此操作'
        if (m.includes('invalid')) return '输入数据无效，请检查后重试'
        if (m.includes('failed')) return '操作失败，请稍后重试'
        return null
      }
      
      switch (status) {
        case 401:
          ElMessage.error('登录已过期，请重新登录')
          localStorage.removeItem('token')
          router.push({ name: 'Login', query: { redirect: router.currentRoute.value.fullPath } })
          break
        case 403:
          ElMessage.error(translateError(data.message) || data.message || '没有权限访问此资源')
          break
        case 404:
          ElMessage.error(translateError(data.detail || data.message) || '请求的资源不存在')
          break
        case 409:
          ElMessage.error(translateError(data.detail || data.message) || '数据已存在，请勿重复添加')
          break
        case 422:
          if (data.errors && Array.isArray(data.errors)) {
            const errorMsg = data.errors.map(e => e.message).join('; ')
            ElMessage.error(errorMsg)
          } else {
            ElMessage.error(data.message || '数据验证失败，请检查输入')
          }
          break
        case 500: {
          const raw = data.detail || data.message || ''
          ElMessage.error(translateError(raw) || '服务器内部错误，请稍后重试')
          break
        }
        case 503:
          ElMessage.error('服务暂时不可用，请稍后重试')
          break
        default:
          ElMessage.error(translateError(data.message) || data.message || `请求失败 (${status})`)
      }
    } else if (error.request) {
      ElMessage.error('无法连接到服务器，请检查网络连接')
    } else {
      ElMessage.error('请求配置错误')
    }
    
    return Promise.reject(error)
  }
)

export default request
