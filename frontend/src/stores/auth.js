import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as apiLogin, logout as apiLogout, getCurrentUser } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  // State
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(null)
  const loading = ref(false)

  // Getters
  const isAuthenticated = computed(() => !!token.value)
  const userRole = computed(() => user.value?.role || '')
  const userName = computed(() => user.value?.full_name || user.value?.username || '')
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isRegularUser = computed(() => user.value?.role === 'user')
  const isReadOnly = computed(() => user.value?.role === 'readonly')

  // Actions
  async function login(credentials) {
    loading.value = true
    try {
      const response = await apiLogin(credentials)
      // response 已经是后端返回的数据对象（经过拦截器处理）
      const { access_token, user: userData } = response
      
      token.value = access_token
      user.value = userData
      localStorage.setItem('token', access_token)
      
      return { success: true }
    } catch (error) {
      // 后端登录失败返回 {"detail": "..."} 格式
      const detail = error.response?.data?.detail
      const message = error.response?.data?.message
      let errorMsg = '登录失败'
      
      if (detail) {
        // 将英文错误信息翻译为中文
        const d = detail.toLowerCase()
        if (d.includes('invalid username or password')) {
          errorMsg = '用户名或密码错误'
        } else if (d.includes('disabled')) {
          errorMsg = '账户已被禁用'
        } else {
          errorMsg = detail
        }
      } else if (message) {
        errorMsg = message
      }
      
      return { 
        success: false, 
        message: errorMsg
      }
    } finally {
      loading.value = false
    }
  }

  async function logout() {
    try {
      await apiLogout()
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      token.value = ''
      user.value = null
      localStorage.removeItem('token')
    }
  }

  async function fetchCurrentUser() {
    if (!token.value) return

    try {
      const response = await getCurrentUser()
      // response 已经是用户数据对象（经过拦截器处理）
      user.value = response
    } catch (error) {
      console.error('Failed to fetch current user:', error)
      // If token is invalid, clear auth state
      if (error.response?.status === 401) {
        await logout()
      }
    }
  }

  function hasPermission(requiredRoles) {
    if (!requiredRoles || requiredRoles.length === 0) return true
    return requiredRoles.includes(user.value?.role)
  }

  return {
    // State
    token,
    user,
    loading,
    // Getters
    isAuthenticated,
    userRole,
    userName,
    isAdmin,
    isRegularUser,
    isReadOnly,
    // Actions
    login,
    logout,
    fetchCurrentUser,
    hasPermission
  }
})
