<template>
  <div class="distribution-container">
    <el-card class="header-card">
      <template #header>
        <div class="card-header">
          <span>📤 Distribution Management</span>
        </div>
      </template>
      <p class="description">
        Distribute content to multiple platforms: Xiaohongshu, WeChat Official Account, and Toutiao.
      </p>
    </el-card>

    <el-table :data="contents" style="width: 100%; margin-top: 20px;">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="market" label="Market" width="120" />
      <el-table-column prop="content_type" label="Type" width="120" />
      <el-table-column prop="title" label="Title" min-width="200" show-overflow-tooltip />
      <el-table-column prop="created_at" label="Created" width="180" />
      <el-table-column label="Status" width="120">
        <template #default="scope">
          <el-tag :type="getStatusType(scope.row.status)">
            {{ scope.row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="Actions" width="300" fixed="right">
        <template #default="scope">
          <el-button 
            type="primary" 
            size="small" 
            @click="distributeToXiaohongshu(scope.row)"
          >
            Xiaohongshu
          </el-button>
          <el-button 
            type="success" 
            size="small" 
            @click="distributeToWechat(scope.row)"
          >
            WeChat
          </el-button>
          <el-button 
            type="warning" 
            size="small" 
            @click="distributeToToutiao(scope.row)"
          >
            Toutiao
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- Xiaohongshu Dialog -->
    <el-dialog v-model="xiaohongshuDialogVisible" title="Xiaohongshu Distribution" width="600px">
      <div v-if="xiaohongshuData">
        <h4>Title (max 20 chars)</h4>
        <el-input v-model="xiaohongshuData.formatted_content.title" readonly />
        
        <h4 style="margin-top: 16px;">Content</h4>
        <el-input 
          v-model="xiaohongshuData.formatted_content.full_content" 
          type="textarea" 
          :rows="6" 
          readonly 
        />
        
        <h4 style="margin-top: 16px;">Instructions</h4>
        <el-input 
          v-model="xiaohongshuData.instructions" 
          type="textarea" 
          :rows="10" 
          readonly 
        />
        
        <div v-if="xiaohongshuData.warnings && xiaohongshuData.warnings.length > 0">
          <h4 style="margin-top: 16px;">Warnings</h4>
          <el-alert 
            v-for="(warning, index) in xiaohongshuData.warnings" 
            :key="index"
            :title="warning" 
            type="warning" 
            show-icon 
            style="margin-bottom: 8px;"
          />
        </div>
      </div>
      <template #footer>
        <el-button @click="xiaohongshuDialogVisible = false">Close</el-button>
        <el-button type="primary" @click="copyXiaohongshuContent">Copy Content</el-button>
      </template>
    </el-dialog>

    <!-- WeChat Dialog -->
    <el-dialog v-model="wechatDialogVisible" title="WeChat Distribution" width="600px">
      <div v-if="wechatData">
        <el-alert 
          :title="wechatData.message" 
          :type="wechatData.success ? 'success' : 'error'" 
          show-icon 
        />
        
        <div v-if="wechatData.success && wechatData.data">
          <h4 style="margin-top: 16px;">Status</h4>
          <el-tag :type="wechatData.data.status === 'publishing' ? 'warning' : 'success'">
            {{ wechatData.data.status }}
          </el-tag>
          
          <div v-if="wechatData.data.status === 'draft'">
            <p style="margin-top: 16px;">
              Draft has been created in WeChat Official Account backend. 
              Please log in to publish manually.
            </p>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="wechatDialogVisible = false">Close</el-button>
      </template>
    </el-dialog>

    <!-- Toutiao Dialog -->
    <el-dialog v-model="toutiaoDialogVisible" title="Toutiao Distribution" width="600px">
      <div v-if="toutiaoData">
        <el-alert 
          :title="toutiaoData.message" 
          :type="toutiaoData.success ? 'success' : 'error'" 
          show-icon 
        />
        
        <div v-if="toutiaoData.success && toutiaoData.data">
          <h4 style="margin-top: 16px;">Status</h4>
          <el-tag :type="toutiaoData.data.status === 'published' ? 'success' : 'warning'">
            {{ toutiaoData.data.status }}
          </el-tag>
          
          <div v-if="toutiaoData.data.status === 'draft'">
            <p style="margin-top: 16px;">
              Article has been created. 
              Please log in to Toutiao backend to publish manually.
            </p>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="toutiaoDialogVisible = false">Close</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../utils/api'

const contents = ref([])
const xiaohongshuDialogVisible = ref(false)
const wechatDialogVisible = ref(false)
const toutiaoDialogVisible = ref(false)
const xiaohongshuData = ref(null)
const wechatData = ref(null)
const toutiaoData = ref(null)

const getStatusType = (status) => {
  const types = {
    generated: 'info',
    sent: 'success',
    published: 'success',
    failed: 'danger',
  }
  return types[status] || 'info'
}

const fetchContents = async () => {
  try {
    const response = await api.get('/content/')
    contents.value = response.data
  } catch (error) {
    console.error('Failed to fetch contents:', error)
    ElMessage.error('Failed to load contents')
  }
}

const distributeToXiaohongshu = async (content) => {
  try {
    const response = await api.post(`/distribution/xiaohongshu/${content.id}`)
    xiaohongshuData.value = response.data.data
    xiaohongshuDialogVisible.value = true
  } catch (error) {
    console.error('Failed to distribute to Xiaohongshu:', error)
    ElMessage.error('Failed to distribute to Xiaohongshu')
  }
}

const distributeToWechat = async (content) => {
  try {
    const response = await api.post(`/distribution/wechat/${content.id}`)
    wechatData.value = response.data
    wechatDialogVisible.value = true
  } catch (error) {
    console.error('Failed to distribute to WeChat:', error)
    ElMessage.error('Failed to distribute to WeChat')
  }
}

const distributeToToutiao = async (content) => {
  try {
    const response = await api.post(`/distribution/toutiao/${content.id}`)
    toutiaoData.value = response.data
    toutiaoDialogVisible.value = true
  } catch (error) {
    console.error('Failed to distribute to Toutiao:', error)
    ElMessage.error('Failed to distribute to Toutiao')
  }
}

const copyXiaohongshuContent = async () => {
  try {
    await navigator.clipboard.writeText(xiaohongshuData.value.formatted_content.full_content)
    ElMessage.success('Content copied to clipboard!')
  } catch (error) {
    ElMessage.error('Failed to copy content')
  }
}

onMounted(() => {
  fetchContents()
})
</script>

<style scoped>
.distribution-container {
  padding: 20px;
}

.header-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
}

.description {
  color: #909399;
  margin: 0;
}

h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}
</style>