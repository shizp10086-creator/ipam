<template>
  <div class="user-list-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>用户管理</span>
          <el-button type="primary" :icon="Plus" @click="handleCreate">
            创建用户
          </el-button>
        </div>
      </template>

      <!-- Search and Filter -->
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="用户名">
          <el-input v-model="searchForm.username" placeholder="请输入用户名" clearable />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="searchForm.role" placeholder="请选择角色" clearable>
            <el-option label="管理员" value="admin" />
            <el-option label="普通用户" value="user" />
            <el-option label="只读用户" value="readonly" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- Table -->
      <el-table :data="users" v-loading="loading" border stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="full_name" label="姓名" />
        <el-table-column prop="email" label="邮箱" />
        <el-table-column prop="role" label="角色" width="120">
          <template #default="{ row }">
            <el-tag :type="getRoleType(row.role)">{{ getRoleText(row.role) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? '激活' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button size="small" :icon="Edit" @click="handleEdit(row)">编辑</el-button>
            <el-button size="small" :icon="Key" @click="handleChangePassword(row)">改密</el-button>
            <el-button size="small" type="danger" :icon="Delete" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- Pagination -->
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="fetchUsers"
        @current-change="fetchUsers"
        class="pagination"
      />
    </el-card>

    <!-- Create/Edit Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
      @close="resetForm"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" :disabled="isEdit" />
        </el-form-item>
        <el-form-item label="姓名" prop="full_name">
          <el-input v-model="form.full_name" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role" style="width: 100%">
            <el-option label="管理员" value="admin" />
            <el-option label="普通用户" value="user" />
            <el-option label="只读用户" value="readonly" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="!isEdit" label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>
        <el-form-item label="状态" prop="is_active">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- Change Password Dialog -->
    <el-dialog
      v-model="passwordDialogVisible"
      title="修改密码"
      width="500px"
      @close="resetPasswordForm"
    >
      <el-form
        ref="passwordFormRef"
        :model="passwordForm"
        :rules="passwordRules"
        label-width="100px"
      >
        <el-form-item label="新密码" prop="new_password">
          <el-input v-model="passwordForm.new_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm_password">
          <el-input v-model="passwordForm.confirm_password" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="passwordDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmitPassword">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh, Edit, Delete, Key } from '@element-plus/icons-vue'
import * as userApi from '@/api/users'
import { formatDate } from '@/utils/formatters'

const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const passwordDialogVisible = ref(false)
const isEdit = ref(false)
const currentUserId = ref(null)
const formRef = ref(null)
const passwordFormRef = ref(null)

const users = ref([])
const searchForm = reactive({
  username: '',
  role: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const form = reactive({
  username: '',
  full_name: '',
  email: '',
  role: 'user',
  password: '',
  is_active: true
})

const passwordForm = reactive({
  new_password: '',
  confirm_password: ''
})

const dialogTitle = computed(() => isEdit.value ? '编辑用户' : '创建用户')

const formRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度在 3 到 50 个字符', trigger: 'blur' }
  ],
  full_name: [
    { required: true, message: '请输入姓名', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少 6 个字符', trigger: 'blur' }
  ]
}

const passwordRules = {
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少 6 个字符', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.new_password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

function getRoleType(role) {
  const typeMap = { admin: 'danger', user: 'success', readonly: 'info' }
  return typeMap[role] || 'info'
}

function getRoleText(role) {
  const textMap = { admin: '管理员', user: '普通用户', readonly: '只读用户' }
  return textMap[role] || role
}

async function fetchUsers() {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      ...searchForm
    }
    const response = await userApi.getUsers(params)
    users.value = response.data.items
    pagination.total = response.data.total
  } catch (error) {
    ElMessage.error('获取用户列表失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  pagination.page = 1
  fetchUsers()
}

function handleReset() {
  searchForm.username = ''
  searchForm.role = ''
  pagination.page = 1
  fetchUsers()
}

function handleCreate() {
  isEdit.value = false
  dialogVisible.value = true
}

function handleEdit(row) {
  isEdit.value = true
  currentUserId.value = row.id
  Object.assign(form, {
    username: row.username,
    full_name: row.full_name,
    email: row.email,
    role: row.role,
    is_active: row.is_active
  })
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    submitting.value = true

    if (isEdit.value) {
      await userApi.updateUser(currentUserId.value, form)
      ElMessage.success('更新用户成功')
    } else {
      await userApi.createUser(form)
      ElMessage.success('创建用户成功')
    }

    dialogVisible.value = false
    fetchUsers()
  } catch (error) {
    // Error handled by interceptor
  } finally {
    submitting.value = false
  }
}

function handleChangePassword(row) {
  currentUserId.value = row.id
  passwordDialogVisible.value = true
}

async function handleSubmitPassword() {
  if (!passwordFormRef.value) return
  
  try {
    await passwordFormRef.value.validate()
    submitting.value = true

    await userApi.changePassword(currentUserId.value, {
      new_password: passwordForm.new_password
    })
    
    ElMessage.success('修改密码成功')
    passwordDialogVisible.value = false
  } catch (error) {
    // Error handled by interceptor
  } finally {
    submitting.value = false
  }
}

function handleDelete(row) {
  ElMessageBox.confirm(`确定要删除用户 "${row.username}" 吗？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await userApi.deleteUser(row.id)
      ElMessage.success('删除用户成功')
      fetchUsers()
    } catch (error) {
      // Error handled by interceptor
    }
  }).catch(() => {})
}

function resetForm() {
  if (formRef.value) {
    formRef.value.resetFields()
  }
  Object.assign(form, {
    username: '',
    full_name: '',
    email: '',
    role: 'user',
    password: '',
    is_active: true
  })
}

function resetPasswordForm() {
  if (passwordFormRef.value) {
    passwordFormRef.value.resetFields()
  }
  Object.assign(passwordForm, {
    new_password: '',
    confirm_password: ''
  })
}

onMounted(() => {
  fetchUsers()
})
</script>

<style scoped>
.user-list-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-form {
  margin-bottom: 20px;
}

.pagination {
  margin-top: 20px;
  justify-content: flex-end;
}
</style>
