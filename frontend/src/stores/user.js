import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as userApi from '@/api/users'

export const useUserStore = defineStore('user', () => {
  // State
  const users = ref([])
  const currentUser = ref(null)
  const loading = ref(false)
  const total = ref(0)

  // Actions
  async function fetchUsers(params = {}) {
    loading.value = true
    try {
      const response = await userApi.getUsers(params)
      users.value = response.data.items
      total.value = response.data.total
      return { success: true }
    } catch (error) {
      return { 
        success: false, 
        message: error.response?.data?.message || '获取用户列表失败' 
      }
    } finally {
      loading.value = false
    }
  }

  async function fetchUser(id) {
    loading.value = true
    try {
      const response = await userApi.getUser(id)
      currentUser.value = response.data
      return { success: true, data: response.data }
    } catch (error) {
      return { 
        success: false, 
        message: error.response?.data?.message || '获取用户详情失败' 
      }
    } finally {
      loading.value = false
    }
  }

  async function createUser(userData) {
    loading.value = true
    try {
      const response = await userApi.createUser(userData)
      return { success: true, data: response.data }
    } catch (error) {
      return { 
        success: false, 
        message: error.response?.data?.message || '创建用户失败' 
      }
    } finally {
      loading.value = false
    }
  }

  async function updateUser(id, userData) {
    loading.value = true
    try {
      const response = await userApi.updateUser(id, userData)
      return { success: true, data: response.data }
    } catch (error) {
      return { 
        success: false, 
        message: error.response?.data?.message || '更新用户失败' 
      }
    } finally {
      loading.value = false
    }
  }

  async function deleteUser(id) {
    loading.value = true
    try {
      await userApi.deleteUser(id)
      return { success: true }
    } catch (error) {
      return { 
        success: false, 
        message: error.response?.data?.message || '删除用户失败' 
      }
    } finally {
      loading.value = false
    }
  }

  async function changePassword(id, passwordData) {
    loading.value = true
    try {
      await userApi.changePassword(id, passwordData)
      return { success: true }
    } catch (error) {
      return { 
        success: false, 
        message: error.response?.data?.message || '修改密码失败' 
      }
    } finally {
      loading.value = false
    }
  }

  return {
    // State
    users,
    currentUser,
    loading,
    total,
    // Actions
    fetchUsers,
    fetchUser,
    createUser,
    updateUser,
    deleteUser,
    changePassword
  }
})
