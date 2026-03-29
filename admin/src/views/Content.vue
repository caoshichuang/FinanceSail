<template>
  <div class="content-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>内容管理</span>
          <el-space>
            <el-select v-model="filter.market" placeholder="市场" clearable style="width: 120px">
              <el-option label="美股" value="美股" />
              <el-option label="A股" value="A股" />
              <el-option label="港股" value="港股" />
            </el-select>
            <el-button @click="loadContent">刷新</el-button>
          </el-space>
        </div>
      </template>
      
      <el-table :data="contents" v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="market" label="市场" width="80" />
        <el-table-column prop="content_type" label="类型" width="100" />
        <el-table-column prop="title" label="标题" show-overflow-tooltip />
        <el-table-column prop="created_at" label="生成时间" width="180" />
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button size="small" @click="showDetail(row)">查看</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 内容详情对话框 -->
    <el-dialog v-model="detailDialogVisible" title="内容详情" width="800px">
      <div v-if="currentContent">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="ID">{{ currentContent.id }}</el-descriptions-item>
          <el-descriptions-item label="市场">{{ currentContent.market }}</el-descriptions-item>
          <el-descriptions-item label="类型">{{ currentContent.content_type }}</el-descriptions-item>
          <el-descriptions-item label="生成时间">{{ currentContent.created_at }}</el-descriptions-item>
        </el-descriptions>
        
        <h4 style="margin: 16px 0 8px">标题</h4>
        <p>{{ currentContent.title }}</p>
        
        <h4 style="margin: 16px 0 8px">内容</h4>
        <el-input
          v-model="currentContent.content"
          type="textarea"
          :rows="15"
          readonly
        />
        
        <h4 style="margin: 16px 0 8px">标签</h4>
        <p>{{ currentContent.tags }}</p>
      </div>
      <template #footer>
        <el-button @click="copyContent">复制内容</el-button>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { contentApi } from '../utils/api'

const contents = ref([])
const loading = ref(false)
const detailDialogVisible = ref(false)
const currentContent = ref(null)
const filter = reactive({
  market: ''
})

const loadContent = async () => {
  loading.value = true
  try {
    const params = {}
    if (filter.market) params.market = filter.market
    contents.value = await contentApi.list(params)
  } catch (error) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

const showDetail = (row) => {
  currentContent.value = { ...row }
  detailDialogVisible.value = true
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定删除此内容？', '提示')
    await contentApi.delete(row.id)
    ElMessage.success('删除成功')
    loadContent()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

const copyContent = () => {
  navigator.clipboard.writeText(currentContent.value.content)
  ElMessage.success('已复制到剪贴板')
}

onMounted(loadContent)
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
