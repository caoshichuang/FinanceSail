<template>
  <div class="config-page">
    <el-tabs v-model="activeTab">
      <el-tab-pane label="API配置" name="api">
        <el-card>
          <el-form :model="envConfig" label-width="150px">
            <el-form-item label="DeepSeek API Key">
              <el-input v-model="envConfig.DEEPSEEK_API_KEY" show-password />
            </el-form-item>
            <el-form-item label="Tushare Token">
              <el-input v-model="envConfig.TUSHARE_TOKEN" show-password />
            </el-form-item>
            <el-form-item label="发件邮箱">
              <el-input v-model="envConfig.QQ_EMAIL" />
            </el-form-item>
            <el-form-item label="邮箱授权码">
              <el-input v-model="envConfig.QQ_EMAIL_AUTH_CODE" show-password />
            </el-form-item>
            <el-form-item label="收件邮箱">
              <el-input v-model="envConfig.RECEIVER_EMAIL" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveEnvConfig" :loading="saving">保存配置</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="节假日配置" name="holidays">
        <el-card>
          <el-form :model="holidayForm" inline style="margin-bottom: 16px">
            <el-form-item label="年份">
              <el-select v-model="holidayForm.year" @change="loadHolidays">
                <el-option v-for="y in years" :key="y" :label="y" :value="y" />
              </el-select>
            </el-form-item>
          </el-form>
          
          <el-input
            v-model="holidayForm.datesText"
            type="textarea"
            :rows="10"
            placeholder="每行一个日期，格式：YYYY-MM-DD"
          />
          
          <div style="margin-top: 16px">
            <el-button type="primary" @click="saveHolidays" :loading="savingHolidays">保存节假日</el-button>
          </div>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="定时任务" name="scheduler">
        <el-card>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="美股总结">{{ schedulerConfig.us_stock_time }}</el-descriptions-item>
            <el-descriptions-item label="A股港股总结">{{ schedulerConfig.a_share_time }}</el-descriptions-item>
            <el-descriptions-item label="热点个股">{{ schedulerConfig.hot_stock_time }}</el-descriptions-item>
            <el-descriptions-item label="IPO分析">{{ schedulerConfig.ipo_time }}</el-descriptions-item>
          </el-descriptions>
          <p style="margin-top: 16px; color: #999">修改定时任务需要编辑服务器配置文件</p>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { configApi } from '../utils/api'

const activeTab = ref('api')
const saving = ref(false)
const savingHolidays = ref(false)

const envConfig = reactive({
  DEEPSEEK_API_KEY: '',
  TUSHARE_TOKEN: '',
  QQ_EMAIL: '',
  QQ_EMAIL_AUTH_CODE: '',
  RECEIVER_EMAIL: ''
})

const holidayForm = reactive({
  year: new Date().getFullYear(),
  datesText: ''
})

const schedulerConfig = reactive({
  us_stock_time: '',
  a_share_time: '',
  hot_stock_time: '',
  ipo_time: ''
})

const years = [2025, 2026, 2027, 2028]

const loadEnvConfig = async () => {
  try {
    const data = await configApi.getEnv()
    Object.assign(envConfig, data)
  } catch (error) {
    ElMessage.error('加载配置失败')
  }
}

const loadHolidays = async () => {
  try {
    const data = await configApi.getHolidays()
    const dates = data[holidayForm.year] || []
    holidayForm.datesText = dates.join('\n')
  } catch (error) {
    ElMessage.error('加载节假日失败')
  }
}

const loadSchedulerConfig = async () => {
  try {
    const data = await configApi.getScheduler()
    Object.assign(schedulerConfig, data)
  } catch (error) {
    ElMessage.error('加载定时任务配置失败')
  }
}

const saveEnvConfig = async () => {
  saving.value = true
  try {
    await configApi.updateEnv(envConfig)
    ElMessage.success('配置已保存，请重启服务生效')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

const saveHolidays = async () => {
  savingHolidays.value = true
  try {
    const dates = holidayForm.datesText.split('\n').filter(d => d.trim())
    await configApi.updateHolidays({ year: holidayForm.year, dates })
    ElMessage.success('节假日配置已保存')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '保存失败')
  } finally {
    savingHolidays.value = false
  }
}

onMounted(() => {
  loadEnvConfig()
  loadHolidays()
  loadSchedulerConfig()
})
</script>

<style scoped>
.config-page {
  max-width: 800px;
}
</style>
