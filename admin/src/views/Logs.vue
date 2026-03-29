<template>
  <div class="logs-page">
    <el-tabs v-model="activeTab">
      <el-tab-pane label="系统状态" name="status">
        <el-card v-loading="loadingStatus">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="CPU使用率">{{ systemStatus.cpu_percent }}%</el-descriptions-item>
            <el-descriptions-item label="内存使用率">{{ systemStatus.memory?.percent }}%</el-descriptions-item>
            <el-descriptions-item label="磁盘使用率">{{ systemStatus.disk?.percent }}%</el-descriptions-item>
            <el-descriptions-item label="Python版本">{{ systemStatus.python_version }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="应用日志" name="app">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>应用日志</span>
              <el-button @click="loadAppLog" :loading="loadingApp">刷新</el-button>
            </div>
          </template>
          <el-input
            v-model="appLog"
            type="textarea"
            :rows="20"
            readonly
            class="log-textarea"
          />
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="错误日志" name="error">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>错误日志</span>
              <el-button @click="loadErrorLog" :loading="loadingError">刷新</el-button>
            </div>
          </template>
          <el-input
            v-model="errorLog"
            type="textarea"
            :rows="20"
            readonly
            class="log-textarea error-log"
          />
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="定时任务" name="jobs">
        <el-card v-loading="loadingJobs">
          <el-table :data="jobs">
            <el-table-column prop="id" label="任务ID" />
            <el-table-column prop="name" label="任务名称" />
            <el-table-column prop="trigger" label="触发器" />
            <el-table-column prop="next_run" label="下次执行" />
          </el-table>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { logsApi } from '../utils/api'

const activeTab = ref('status')
const loadingStatus = ref(false)
const loadingApp = ref(false)
const loadingError = ref(false)
const loadingJobs = ref(false)

const systemStatus = ref({})
const appLogLines = ref([])
const errorLogLines = ref([])
const jobs = ref([])

const appLog = computed(() => appLogLines.value.join('\n'))
const errorLog = computed(() => errorLogLines.value.join('\n'))

const loadSystemStatus = async () => {
  loadingStatus.value = true
  try {
    systemStatus.value = await logsApi.getSystemStatus()
  } catch (error) {
    ElMessage.error('加载系统状态失败')
  } finally {
    loadingStatus.value = false
  }
}

const loadAppLog = async () => {
  loadingApp.value = true
  try {
    const res = await logsApi.getAppLog(200)
    appLogLines.value = res.lines
  } catch (error) {
    ElMessage.error('加载日志失败')
  } finally {
    loadingApp.value = false
  }
}

const loadErrorLog = async () => {
  loadingError.value = true
  try {
    const res = await logsApi.getErrorLog(200)
    errorLogLines.value = res.lines
  } catch (error) {
    ElMessage.error('加载日志失败')
  } finally {
    loadingError.value = false
  }
}

const loadJobs = async () => {
  loadingJobs.value = true
  try {
    jobs.value = await logsApi.getJobs()
  } catch (error) {
    ElMessage.error('加载任务状态失败')
  } finally {
    loadingJobs.value = false
  }
}

onMounted(() => {
  loadSystemStatus()
  loadAppLog()
  loadErrorLog()
  loadJobs()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.log-textarea :deep(.el-textarea__inner) {
  font-family: monospace;
  font-size: 12px;
}

.error-log :deep(.el-textarea__inner) {
  color: #f56c6c;
}
</style>
