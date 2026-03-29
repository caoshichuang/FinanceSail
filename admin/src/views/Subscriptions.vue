<template>
  <div class="subscriptions-container">
    <el-card class="header-card">
      <template #header>
        <div class="card-header">
          <span>🔔 Subscription Management</span>
          <el-button type="primary" @click="showAddDialog">
            <el-icon><Plus /></el-icon>
            Add Subscription
          </el-button>
        </div>
      </template>
    </el-card>

    <el-table :data="subscriptions" style="width: 100%; margin-top: 20px;">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="stock_code" label="Code" width="120" />
      <el-table-column prop="stock_name" label="Name" width="150" />
      <el-table-column prop="market" label="Market" width="100" />
      <el-table-column label="Rules" min-width="200">
        <template #default="scope">
          <el-tag 
            v-for="rule in parseRules(scope.row.rules)" 
            :key="rule.type"
            style="margin-right: 8px;"
          >
            {{ rule.type }}: {{ rule.threshold }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="Status" width="100">
        <template #default="scope">
          <el-tag :type="scope.row.is_active ? 'success' : 'info'">
            {{ scope.row.is_active ? 'Active' : 'Inactive' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="Created" width="180" />
      <el-table-column label="Actions" width="200" fixed="right">
        <template #default="scope">
          <el-button 
            type="primary" 
            size="small" 
            @click="editSubscription(scope.row)"
          >
            Edit
          </el-button>
          <el-button 
            type="danger" 
            size="small" 
            @click="deleteSubscription(scope.row)"
          >
            Delete
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- Add/Edit Dialog -->
    <el-dialog 
      v-model="dialogVisible" 
      :title="isEditing ? 'Edit Subscription' : 'Add Subscription'" 
      width="500px"
    >
      <el-form :model="form" label-width="100px">
        <el-form-item label="Stock Code">
          <el-input v-model="form.stock_code" placeholder="e.g., 600519" />
        </el-form-item>
        <el-form-item label="Stock Name">
          <el-input v-model="form.stock_name" placeholder="e.g., 贵州茅台" />
        </el-form-item>
        <el-form-item label="Market">
          <el-select v-model="form.market" placeholder="Select market">
            <el-option label="A股" value="A股" />
            <el-option label="港股" value="港股" />
            <el-option label="美股" value="美股" />
          </el-select>
        </el-form-item>
        <el-form-item label="Alert Rules">
          <div v-for="(rule, index) in form.rules" :key="index" style="margin-bottom: 10px;">
            <el-row :gutter="10">
              <el-col :span="10">
                <el-select v-model="rule.type" placeholder="Type">
                  <el-option label="Price Change %" value="change" />
                  <el-option label="Announcement" value="announce" />
                  <el-option label="Earnings" value="earning" />
                  <el-option label="Dividend" value="dividend" />
                </el-select>
              </el-col>
              <el-col :span="10">
                <el-input 
                  v-model="rule.threshold" 
                  placeholder="Threshold" 
                  :disabled="rule.type !== 'change'"
                />
              </el-col>
              <el-col :span="4">
                <el-button type="danger" @click="removeRule(index)">-</el-button>
              </el-col>
            </el-row>
          </div>
          <el-button type="primary" @click="addRule">+ Add Rule</el-button>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">Cancel</el-button>
        <el-button type="primary" @click="saveSubscription">Save</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import api from '../utils/api'

const subscriptions = ref([])
const dialogVisible = ref(false)
const isEditing = ref(false)
const editingId = ref(null)

const form = ref({
  stock_code: '',
  stock_name: '',
  market: 'A股',
  rules: [{ type: 'change', threshold: '5' }]
})

const parseRules = (rulesJson) => {
  if (!rulesJson) return []
  try {
    return JSON.parse(rulesJson)
  } catch {
    return []
  }
}

const fetchSubscriptions = async () => {
  try {
    const response = await api.get('/subscriptions/')
    subscriptions.value = response.data
  } catch (error) {
    console.error('Failed to fetch subscriptions:', error)
    ElMessage.error('Failed to load subscriptions')
  }
}

const showAddDialog = () => {
  isEditing.value = false
  editingId.value = null
  form.value = {
    stock_code: '',
    stock_name: '',
    market: 'A股',
    rules: [{ type: 'change', threshold: '5' }]
  }
  dialogVisible.value = true
}

const editSubscription = (row) => {
  isEditing.value = true
  editingId.value = row.id
  form.value = {
    stock_code: row.stock_code,
    stock_name: row.stock_name,
    market: row.market,
    rules: parseRules(row.rules)
  }
  if (form.value.rules.length === 0) {
    form.value.rules = [{ type: 'change', threshold: '5' }]
  }
  dialogVisible.value = true
}

const deleteSubscription = async (row) => {
  try {
    await ElMessageBox.confirm(
      `Are you sure you want to delete ${row.stock_name}?`,
      'Confirm',
      { type: 'warning' }
    )
    
    await api.delete(`/subscriptions/${row.id}`)
    ElMessage.success('Subscription deleted')
    fetchSubscriptions()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete subscription:', error)
      ElMessage.error('Failed to delete subscription')
    }
  }
}

const addRule = () => {
  form.value.rules.push({ type: 'change', threshold: '5' })
}

const removeRule = (index) => {
  form.value.rules.splice(index, 1)
}

const saveSubscription = async () => {
  try {
    const data = {
      ...form.value,
      rules: JSON.stringify(form.value.rules)
    }
    
    if (isEditing.value) {
      await api.put(`/subscriptions/${editingId.value}`, data)
      ElMessage.success('Subscription updated')
    } else {
      await api.post('/subscriptions/', data)
      ElMessage.success('Subscription created')
    }
    
    dialogVisible.value = false
    fetchSubscriptions()
  } catch (error) {
    console.error('Failed to save subscription:', error)
    ElMessage.error('Failed to save subscription')
  }
}

onMounted(() => {
  fetchSubscriptions()
})
</script>

<style scoped>
.subscriptions-container {
  padding: 20px;
}

.header-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 18px;
  font-weight: 600;
}
</style>