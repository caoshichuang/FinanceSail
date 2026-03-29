<template>
  <div class="users-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>用户管理</span>
          <el-button type="primary" @click="showAddDialog">添加用户</el-button>
        </div>
      </template>
      
      <el-table :data="users" v-loading="loading">
        <el-table-column prop="email" label="邮箱" />
        <el-table-column prop="name" label="昵称" />
        <el-table-column prop="expire_date" label="到期时间" />
        <el-table-column label="状态">
          <template #default="{ row }">
            <el-tag :type="row.is_expired ? 'danger' : 'success'">
              {{ row.is_expired ? '已过期' : '有效' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="订阅数">
          <template #default="{ row }">
            {{ row.stocks?.length || 0 }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250">
          <template #default="{ row }">
            <el-button size="small" @click="showSubscriptions(row)">订阅管理</el-button>
            <el-button size="small" type="success" @click="showRenewDialog(row)">续费</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 添加用户对话框 -->
    <el-dialog v-model="addDialogVisible" title="添加用户" width="400px">
      <el-form :model="addForm" label-width="80px">
        <el-form-item label="邮箱" required>
          <el-input v-model="addForm.email" />
        </el-form-item>
        <el-form-item label="昵称">
          <el-input v-model="addForm.name" />
        </el-form-item>
        <el-form-item label="到期天数">
          <el-input-number v-model="addForm.expire_days" :min="1" :max="365" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleAdd">确定</el-button>
      </template>
    </el-dialog>

    <!-- 续费对话框 -->
    <el-dialog v-model="renewDialogVisible" title="续费" width="300px">
      <el-form label-width="80px">
        <el-form-item label="用户">
          <span>{{ currentUser?.email }}</span>
        </el-form-item>
        <el-form-item label="续费天数">
          <el-input-number v-model="renewDays" :min="1" :max="365" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="renewDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleRenew">确定</el-button>
      </template>
    </el-dialog>

    <!-- 订阅管理对话框 -->
    <el-dialog v-model="subDialogVisible" title="订阅管理" width="600px">
      <div style="margin-bottom: 16px">
        <el-input v-model="newStock" placeholder="输入股票代码或名称" style="width: 300px; margin-right: 8px" />
        <el-button type="primary" @click="handleAddSubscription">添加订阅</el-button>
      </div>
      
      <el-table :data="currentUser?.stocks || []">
        <el-table-column prop="code" label="代码" />
        <el-table-column prop="name" label="名称" />
        <el-table-column label="操作">
          <template #default="{ row }">
            <el-button size="small" type="danger" @click="handleDeleteSubscription(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { usersApi } from '../utils/api'

const users = ref([])
const loading = ref(false)
const addDialogVisible = ref(false)
const renewDialogVisible = ref(false)
const subDialogVisible = ref(false)
const currentUser = ref(null)
const newStock = ref('')
const renewDays = ref(30)

const addForm = reactive({
  email: '',
  name: '',
  expire_days: 30
})

const loadUsers = async () => {
  loading.value = true
  try {
    users.value = await usersApi.list()
  } catch (error) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

const showAddDialog = () => {
  addForm.email = ''
  addForm.name = ''
  addForm.expire_days = 30
  addDialogVisible.value = true
}

const handleAdd = async () => {
  try {
    await usersApi.create(addForm)
    ElMessage.success('添加成功')
    addDialogVisible.value = false
    loadUsers()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '添加失败')
  }
}

const showRenewDialog = (user) => {
  currentUser.value = user
  renewDays.value = 30
  renewDialogVisible.value = true
}

const handleRenew = async () => {
  try {
    await usersApi.renew(currentUser.value.email, renewDays.value)
    ElMessage.success('续费成功')
    renewDialogVisible.value = false
    loadUsers()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '续费失败')
  }
}

const handleDelete = async (user) => {
  try {
    await ElMessageBox.confirm(`确定删除用户 ${user.email}？`, '提示')
    await usersApi.delete(user.email)
    ElMessage.success('删除成功')
    loadUsers()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

const showSubscriptions = (user) => {
  currentUser.value = user
  newStock.value = ''
  subDialogVisible.value = true
}

const handleAddSubscription = async () => {
  if (!newStock.value) {
    ElMessage.warning('请输入股票代码或名称')
    return
  }
  try {
    await usersApi.addSubscription(currentUser.value.email, { stock_code_or_name: newStock.value })
    ElMessage.success('添加成功')
    newStock.value = ''
    loadUsers()
    // 刷新当前用户数据
    const updatedUsers = await usersApi.list()
    currentUser.value = updatedUsers.find(u => u.email === currentUser.value.email)
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '添加失败')
  }
}

const handleDeleteSubscription = async (stock) => {
  try {
    await usersApi.deleteSubscription(currentUser.value.email, stock.code || stock.name)
    ElMessage.success('删除成功')
    loadUsers()
    const updatedUsers = await usersApi.list()
    currentUser.value = updatedUsers.find(u => u.email === currentUser.value.email)
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '删除失败')
  }
}

onMounted(loadUsers)
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
