<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header>今日生成</template>
          <div class="stat-value">{{ stats.today_count || 0 }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header>总内容数</template>
          <div class="stat-value">{{ stats.total_count || 0 }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header>有效用户</template>
          <div class="stat-value">{{ users.length }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header>系统状态</template>
          <div class="stat-value status-ok">正常运行</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>快捷操作</span>
          </template>
          <el-space wrap>
            <el-button type="primary" @click="triggerUS" :loading="loading.us">
              生成美股总结
            </el-button>
            <el-button type="primary" @click="triggerAShare" :loading="loading.aShare">
              生成A股总结
            </el-button>
            <el-button type="primary" @click="triggerIPO" :loading="loading.ipo">
              生成IPO分析
            </el-button>
            <el-button type="primary" @click="triggerHot" :loading="loading.hot">
              生成热点个股
            </el-button>
          </el-space>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>定时任务</span>
          </template>
          <el-table :data="jobs" size="small">
            <el-table-column prop="name" label="任务" />
            <el-table-column prop="next_run" label="下次执行" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { contentApi, usersApi, logsApi } from '../utils/api'

const stats = ref({})
const users = ref([])
const jobs = ref([])
const loading = reactive({
  us: false,
  aShare: false,
  ipo: false,
  hot: false
})

const loadData = async () => {
  try {
    const [statsRes, usersRes, jobsRes] = await Promise.all([
      contentApi.stats(),
      usersApi.list(),
      logsApi.getJobs()
    ])
    stats.value = statsRes
    users.value = usersRes
    jobs.value = jobsRes
  } catch (error) {
    console.error(error)
  }
}

const triggerUS = async () => {
  loading.us = true
  try {
    await contentApi.triggerUS()
    ElMessage.success('美股总结任务已执行')
    loadData()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '执行失败')
  } finally {
    loading.us = false
  }
}

const triggerAShare = async () => {
  loading.aShare = true
  try {
    await contentApi.triggerAShare()
    ElMessage.success('A股总结任务已执行')
    loadData()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '执行失败')
  } finally {
    loading.aShare = false
  }
}

const triggerIPO = async () => {
  loading.ipo = true
  try {
    await contentApi.triggerIPO()
    ElMessage.success('IPO分析任务已执行')
    loadData()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '执行失败')
  } finally {
    loading.ipo = false
  }
}

const triggerHot = async () => {
  loading.hot = true
  try {
    await contentApi.triggerHot()
    ElMessage.success('热点个股任务已执行')
    loadData()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '执行失败')
  } finally {
    loading.hot = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #409eff;
}

.status-ok {
  font-size: 16px;
  color: #67c23a;
}
</style>
