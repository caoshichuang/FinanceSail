<template>
  <div class="config-container">
    <el-card class="header-card">
      <template #header>
        <div class="card-header">
          <span>⚙️ System Configuration</span>
          <div class="header-actions">
            <el-button type="primary" @click="saveAll" :loading="saving">
              <el-icon><Check /></el-icon>
              Save All
            </el-button>
            <el-button @click="resetAll">
              <el-icon><RefreshLeft /></el-icon>
              Reset
            </el-button>
            <el-button type="success" @click="backupConfig">
              <el-icon><Download /></el-icon>
              Backup
            </el-button>
            <el-button type="warning" @click="showRestoreDialog">
              <el-icon><Upload /></el-icon>
              Restore
            </el-button>
          </div>
        </div>
      </template>
      <p class="description">
        Manage all system configurations. Changes will take effect after saving.
        Some configurations require a service restart.
      </p>
    </el-card>

    <el-row :gutter="20">
      <!-- 左侧分类导航 -->
      <el-col :span="6">
        <el-card class="category-card">
          <el-menu
            :default-active="activeCategory"
            @select="handleCategoryChange"
          >
            <el-menu-item 
              v-for="cat in categories" 
              :key="cat.id" 
              :index="cat.id"
            >
              <el-icon><component :is="cat.icon" /></el-icon>
              <span>{{ cat.name }}</span>
            </el-menu-item>
          </el-menu>
        </el-card>
      </el-col>

      <!-- 右侧配置表单 -->
      <el-col :span="18">
        <el-card class="config-card">
          <template #header>
            <div class="config-header">
              <h3>{{ currentCategory?.name || 'Configuration' }}</h3>
              <p>{{ currentCategory?.description }}</p>
            </div>
          </template>

          <!-- AI 配置 -->
          <div v-if="activeCategory === 'ai'" class="config-form">
            <el-form :model="aiConfig" label-width="180px">
              <el-form-item label="DeepSeek API Key">
                <el-input 
                  v-model="aiConfig.DEEPSEEK_API_KEY" 
                  type="password" 
                  show-password
                  placeholder="sk-xxxxxxxx"
                />
                <div class="form-tip">Your DeepSeek API key</div>
              </el-form-item>
              <el-form-item label="DeepSeek Base URL">
                <el-input 
                  v-model="aiConfig.DEEPSEEK_BASE_URL" 
                  placeholder="https://api.deepseek.com"
                />
                <div class="form-tip">DeepSeek API base URL</div>
              </el-form-item>
              <el-form-item label="DeepSeek Model">
                <el-select v-model="aiConfig.DEEPSEEK_MODEL">
                  <el-option label="deepseek-chat" value="deepseek-chat" />
                  <el-option label="deepseek-coder" value="deepseek-coder" />
                </el-select>
                <div class="form-tip">Model to use for content generation</div>
              </el-form-item>
            </el-form>
          </div>

          <!-- 数据源配置 -->
          <div v-if="activeCategory === 'datasource'" class="config-form">
            <el-form :model="datasourceConfig" label-width="180px">
              <el-form-item label="Tushare Token">
                <el-input 
                  v-model="datasourceConfig.TUSHARE_TOKEN" 
                  type="password" 
                  show-password
                  placeholder="Your Tushare token"
                />
                <div class="form-tip">Tushare API token for data access</div>
              </el-form-item>
            </el-form>
          </div>

          <!-- 邮件配置 -->
          <div v-if="activeCategory === 'email'" class="config-form">
            <el-form :model="emailConfig" label-width="180px">
              <el-form-item label="Sender Email">
                <el-input 
                  v-model="emailConfig.QQ_EMAIL" 
                  placeholder="your_email@qq.com"
                />
                <div class="form-tip">QQ email address for sending</div>
              </el-form-item>
              <el-form-item label="Auth Code">
                <el-input 
                  v-model="emailConfig.QQ_EMAIL_AUTH_CODE" 
                  type="password" 
                  show-password
                  placeholder="16-char auth code"
                />
                <div class="form-tip">QQ email authorization code</div>
              </el-form-item>
              <el-form-item label="Receiver Email">
                <el-input 
                  v-model="emailConfig.RECEIVER_EMAIL" 
                  placeholder="receiver@example.com"
                />
                <div class="form-tip">Email address to receive notifications</div>
              </el-form-item>
              <el-form-item label="SMTP Server">
                <el-input 
                  v-model="emailConfig.SMTP_SERVER" 
                  placeholder="smtp.qq.com"
                />
                <div class="form-tip">SMTP server address</div>
              </el-form-item>
              <el-form-item label="SMTP Port">
                <el-input-number 
                  v-model="emailConfig.SMTP_PORT" 
                  :min="1" 
                  :max="65535"
                />
                <div class="form-tip">SMTP port (usually 465 for SSL)</div>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="testEmail">
                  Test Email Configuration
                </el-button>
              </el-form-item>
            </el-form>
          </div>

          <!-- 应用配置 -->
          <div v-if="activeCategory === 'app'" class="config-form">
            <el-form :model="appConfig" label-width="180px">
              <el-form-item label="Base URL">
                <el-input 
                  v-model="appConfig.BASE_URL" 
                  placeholder="http://your-server:8080"
                />
                <div class="form-tip">Application access URL</div>
              </el-form-item>
              <el-form-item label="Log Level">
                <el-select v-model="appConfig.LOG_LEVEL">
                  <el-option label="DEBUG" value="DEBUG" />
                  <el-option label="INFO" value="INFO" />
                  <el-option label="WARNING" value="WARNING" />
                  <el-option label="ERROR" value="ERROR" />
                </el-select>
                <div class="form-tip">Logging level</div>
              </el-form-item>
              <el-form-item label="Log Rotation">
                <el-input 
                  v-model="appConfig.LOG_ROTATION" 
                  placeholder="10 MB"
                />
                <div class="form-tip">Log file rotation size (e.g., 10 MB, 1 GB)</div>
              </el-form-item>
              <el-form-item label="Log Retention">
                <el-input 
                  v-model="appConfig.LOG_RETENTION" 
                  placeholder="30 days"
                />
                <div class="form-tip">Log file retention period (e.g., 30 days, 1 week)</div>
              </el-form-item>
            </el-form>
          </div>

          <!-- 明星股配置 -->
          <div v-if="activeCategory === 'star_stocks'" class="config-form">
            <el-tabs>
              <el-tab-pane label="A股">
                <div v-for="(stock, index) in starStocksConfig['A股']" :key="index" class="stock-item">
                  <el-input v-model="stock.code" placeholder="Code" style="width: 120px" />
                  <el-input v-model="stock.name" placeholder="Name" style="width: 150px; margin-left: 10px" />
                  <el-button type="danger" size="small" @click="removeStock('A股', index)" style="margin-left: 10px">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </div>
                <el-button type="primary" @click="addStock('A股')" style="margin-top: 10px">
                  <el-icon><Plus /></el-icon>
                  Add A-Share Stock
                </el-button>
              </el-tab-pane>
              <el-tab-pane label="港股">
                <div v-for="(stock, index) in starStocksConfig['港股']" :key="index" class="stock-item">
                  <el-input v-model="stock.code" placeholder="Code" style="width: 120px" />
                  <el-input v-model="stock.name" placeholder="Name" style="width: 150px; margin-left: 10px" />
                  <el-button type="danger" size="small" @click="removeStock('港股', index)" style="margin-left: 10px">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </div>
                <el-button type="primary" @click="addStock('港股')" style="margin-top: 10px">
                  <el-icon><Plus /></el-icon>
                  Add HK Stock
                </el-button>
              </el-tab-pane>
              <el-tab-pane label="美股">
                <div v-for="(stock, index) in starStocksConfig['美股']" :key="index" class="stock-item">
                  <el-input v-model="stock.code" placeholder="Code" style="width: 120px" />
                  <el-input v-model="stock.name" placeholder="Name" style="width: 150px; margin-left: 10px" />
                  <el-button type="danger" size="small" @click="removeStock('美股', index)" style="margin-left: 10px">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </div>
                <el-button type="primary" @click="addStock('美股')" style="margin-top: 10px">
                  <el-icon><Plus /></el-icon>
                  Add US Stock
                </el-button>
              </el-tab-pane>
            </el-tabs>
          </div>

          <!-- 业务阈值配置 -->
          <div v-if="activeCategory === 'thresholds'" class="config-form">
            <el-form :model="thresholdsConfig" label-width="180px">
              <el-form-item label="Hot Stock Threshold">
                <el-input-number 
                  v-model="thresholdsConfig.hot_stock_threshold" 
                  :min="0" 
                  :max="100" 
                  :precision="1"
                  :step="0.1"
                />
                <span style="margin-left: 10px">%</span>
                <div class="form-tip">Price change threshold for hot stock alerts</div>
              </el-form-item>
              <el-form-item label="Limit Up/Down Threshold">
                <el-input-number 
                  v-model="thresholdsConfig.limit_up_down_threshold" 
                  :min="0" 
                  :max="100" 
                  :precision="1"
                  :step="0.1"
                />
                <span style="margin-left: 10px">%</span>
                <div class="form-tip">Threshold for limit up/down detection</div>
              </el-form-item>
            </el-form>
          </div>

          <!-- 定时任务配置 -->
          <div v-if="activeCategory === 'scheduler'" class="config-form">
            <el-form :model="schedulerConfig" label-width="180px">
              <el-form-item label="US Stock Summary">
                <el-time-picker 
                  v-model="schedulerConfig.us_stock_time" 
                  format="HH:mm"
                  value-format="HH:mm"
                  placeholder="09:00"
                />
                <div class="form-tip">Daily US stock market summary time</div>
              </el-form-item>
              <el-form-item label="A-Share Summary">
                <el-time-picker 
                  v-model="schedulerConfig.a_share_time" 
                  format="HH:mm"
                  value-format="HH:mm"
                  placeholder="17:00"
                />
                <div class="form-tip">Daily A-share and HK stock summary time</div>
              </el-form-item>
              <el-form-item label="Hot Stocks">
                <el-time-picker 
                  v-model="schedulerConfig.hot_stock_time" 
                  format="HH:mm"
                  value-format="HH:mm"
                  placeholder="17:30"
                />
                <div class="form-tip">Daily hot stock analysis time</div>
              </el-form-item>
              <el-form-item label="IPO Analysis">
                <el-time-picker 
                  v-model="schedulerConfig.ipo_time" 
                  format="HH:mm"
                  value-format="HH:mm"
                  placeholder="20:00"
                />
                <div class="form-tip">Daily IPO analysis time</div>
              </el-form-item>
            </el-form>
          </div>

          <!-- 项目信息配置 -->
          <div v-if="activeCategory === 'project'" class="config-form">
            <el-form :model="projectConfig" label-width="180px">
              <el-form-item label="Project Name">
                <el-input 
                  v-model="projectConfig.project_name" 
                  placeholder="FinanceSail"
                />
                <div class="form-tip">Project display name</div>
              </el-form-item>
              <el-form-item label="Project Name (EN)">
                <el-input 
                  v-model="projectConfig.project_name_en" 
                  placeholder="FinanceSail"
                />
                <div class="form-tip">Project English name</div>
              </el-form-item>
              <el-form-item label="Version">
                <el-input 
                  v-model="projectConfig.project_version" 
                  placeholder="1.0.0"
                />
                <div class="form-tip">Project version number</div>
              </el-form-item>
              <el-form-item label="Description">
                <el-input 
                  v-model="projectConfig.project_description" 
                  type="textarea" 
                  :rows="3"
                  placeholder="Automated Financial Content Distribution System"
                />
                <div class="form-tip">Project description</div>
              </el-form-item>
              <el-form-item label="Logo">
                <el-input 
                  v-model="projectConfig.project_logo" 
                  placeholder="⛵"
                />
                <div class="form-tip">Project logo (emoji or text)</div>
              </el-form-item>
              <el-form-item label="Slogan">
                <el-input 
                  v-model="projectConfig.project_slogan" 
                  placeholder="Empowering Financial Content Distribution"
                />
                <div class="form-tip">Project slogan</div>
              </el-form-item>
            </el-form>
          </div>

          <!-- 节假日配置 -->
          <div v-if="activeCategory === 'holidays'" class="config-form">
            <el-tabs>
              <el-tab-pane 
                v-for="year in Object.keys(holidaysConfig)" 
                :key="year" 
                :label="year"
              >
                <div class="holiday-list">
                  <el-tag 
                    v-for="(date, index) in holidaysConfig[year]" 
                    :key="index"
                    closable
                    @close="removeHoliday(year, index)"
                    style="margin: 5px"
                  >
                    {{ date }}
                  </el-tag>
                </div>
                <div style="margin-top: 10px">
                  <el-date-picker 
                    v-model="newHoliday[year]" 
                    type="date" 
                    placeholder="Add holiday"
                    value-format="YYYY-MM-DD"
                  />
                  <el-button 
                    type="primary" 
                    @click="addHoliday(year)" 
                    style="margin-left: 10px"
                  >
                    Add
                  </el-button>
                </div>
              </el-tab-pane>
            </el-tabs>
            <el-button type="primary" @click="addYear" style="margin-top: 10px">
              <el-icon><Plus /></el-icon>
              Add Year
            </el-button>
          </div>

          <!-- 分发平台配置 -->
          <div v-if="activeCategory === 'distribution'" class="config-form">
            <el-form :model="distributionConfig" label-width="180px">
              <el-form-item label="WeChat App ID">
                <el-input 
                  v-model="distributionConfig.wechat_app_id" 
                  placeholder="Your WeChat App ID"
                />
                <div class="form-tip">WeChat Official Account App ID</div>
              </el-form-item>
              <el-form-item label="WeChat App Secret">
                <el-input 
                  v-model="distributionConfig.wechat_app_secret" 
                  type="password" 
                  show-password
                  placeholder="Your WeChat App Secret"
                />
                <div class="form-tip">WeChat Official Account App Secret</div>
              </el-form-item>
              <el-form-item label="Toutiao Access Token">
                <el-input 
                  v-model="distributionConfig.toutiao_access_token" 
                  type="password" 
                  show-password
                  placeholder="Your Toutiao Access Token"
                />
                <div class="form-tip">Toutiao (ByteDance) API access token</div>
              </el-form-item>
              <el-form-item label="WxPusher App Token">
                <el-input 
                  v-model="distributionConfig.wxpusher_app_token" 
                  type="password" 
                  show-password
                  placeholder="Your WxPusher App Token"
                />
                <div class="form-tip">WxPusher application token for WeChat notifications</div>
              </el-form-item>
            </el-form>
          </div>

          <!-- 保存按钮 -->
          <div class="form-actions">
            <el-button type="primary" @click="saveCategory" :loading="saving">
              Save Configuration
            </el-button>
            <el-button @click="resetCategory">
              Reset
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 恢复配置对话框 -->
    <el-dialog v-model="restoreDialogVisible" title="Restore Configuration" width="500px">
      <el-upload
        class="upload-demo"
        drag
        :auto-upload="false"
        :on-change="handleRestoreFile"
        accept=".json"
      >
        <el-icon class="el-icon--upload"><Upload /></el-icon>
        <div class="el-upload__text">
          Drop backup file here or <em>click to upload</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            Only JSON backup files are supported
          </div>
        </template>
      </el-upload>
      <template #footer>
        <el-button @click="restoreDialogVisible = false">Cancel</el-button>
        <el-button type="primary" @click="restoreConfig" :disabled="!restoreFile">
          Restore
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Check, RefreshLeft, Download, Upload, Delete, Plus 
} from '@element-plus/icons-vue'
import api from '../utils/api'

// 分类列表
const categories = ref([])
const activeCategory = ref('ai')
const saving = ref(false)
const restoreDialogVisible = ref(false)
const restoreFile = ref(null)

// 配置数据
const aiConfig = ref({
  DEEPSEEK_API_KEY: '',
  DEEPSEEK_BASE_URL: 'https://api.deepseek.com',
  DEEPSEEK_MODEL: 'deepseek-chat'
})

const datasourceConfig = ref({
  TUSHARE_TOKEN: ''
})

const emailConfig = ref({
  QQ_EMAIL: '',
  QQ_EMAIL_AUTH_CODE: '',
  RECEIVER_EMAIL: '',
  SMTP_SERVER: 'smtp.qq.com',
  SMTP_PORT: 465
})

const appConfig = ref({
  BASE_URL: 'http://139.224.40.205:8080',
  LOG_LEVEL: 'INFO',
  LOG_ROTATION: '10 MB',
  LOG_RETENTION: '30 days'
})

const starStocksConfig = ref({
  'A股': [],
  '港股': [],
  '美股': []
})

const thresholdsConfig = ref({
  hot_stock_threshold: 3.0,
  limit_up_down_threshold: 9.9
})

const schedulerConfig = ref({
  us_stock_time: '09:00',
  a_share_time: '17:00',
  hot_stock_time: '17:30',
  ipo_time: '20:00'
})

const projectConfig = ref({
  project_name: 'FinanceSail',
  project_name_en: 'FinanceSail',
  project_version: '1.0.0',
  project_description: 'Automated Financial Content Distribution System',
  project_logo: '⛵',
  project_slogan: 'Empowering Financial Content Distribution'
})

const holidaysConfig = ref({})
const newHoliday = ref({})

const distributionConfig = ref({
  wechat_app_id: '',
  wechat_app_secret: '',
  toutiao_access_token: '',
  wxpusher_app_token: ''
})

// 计算属性
const currentCategory = computed(() => {
  return categories.value.find(c => c.id === activeCategory.value)
})

// 方法
const fetchCategories = async () => {
  try {
    const response = await api.get('/config/categories')
    categories.value = response.data.categories
  } catch (error) {
    console.error('Failed to fetch categories:', error)
    ElMessage.error('Failed to load configuration categories')
  }
}

const fetchCategoryConfig = async (category) => {
  try {
    const response = await api.get(`/config/category/${category}`)
    const data = response.data
    
    switch (category) {
      case 'ai':
        aiConfig.value = data
        break
      case 'datasource':
        datasourceConfig.value = data
        break
      case 'email':
        emailConfig.value = data
        break
      case 'app':
        appConfig.value = data
        break
      case 'star_stocks':
        starStocksConfig.value = data
        break
      case 'thresholds':
        thresholdsConfig.value = data
        break
      case 'scheduler':
        schedulerConfig.value = data
        break
      case 'project':
        projectConfig.value = data
        break
      case 'holidays':
        holidaysConfig.value = data
        // 初始化 newHoliday
        Object.keys(data).forEach(year => {
          newHoliday.value[year] = ''
        })
        break
      case 'distribution':
        distributionConfig.value = data
        break
    }
  } catch (error) {
    console.error(`Failed to fetch ${category} config:`, error)
    ElMessage.error(`Failed to load ${category} configuration`)
  }
}

const handleCategoryChange = (categoryId) => {
  activeCategory.value = categoryId
  fetchCategoryConfig(categoryId)
}

const saveCategory = async () => {
  saving.value = true
  try {
    let configData
    switch (activeCategory.value) {
      case 'ai':
        configData = aiConfig.value
        break
      case 'datasource':
        configData = datasourceConfig.value
        break
      case 'email':
        configData = emailConfig.value
        break
      case 'app':
        configData = appConfig.value
        break
      case 'star_stocks':
        configData = starStocksConfig.value
        break
      case 'thresholds':
        configData = thresholdsConfig.value
        break
      case 'scheduler':
        configData = schedulerConfig.value
        break
      case 'project':
        configData = projectConfig.value
        break
      case 'holidays':
        configData = holidaysConfig.value
        break
      case 'distribution':
        configData = distributionConfig.value
        break
    }
    
    await api.put(`/config/category/${activeCategory.value}`, configData)
    ElMessage.success('Configuration saved successfully')
  } catch (error) {
    console.error('Failed to save config:', error)
    ElMessage.error('Failed to save configuration')
  } finally {
    saving.value = false
  }
}

const resetCategory = () => {
  fetchCategoryConfig(activeCategory.value)
  ElMessage.info('Configuration reset')
}

const saveAll = async () => {
  saving.value = true
  try {
    const allConfig = {
      ai: aiConfig.value,
      datasource: datasourceConfig.value,
      email: emailConfig.value,
      app: appConfig.value,
      star_stocks: starStocksConfig.value,
      thresholds: thresholdsConfig.value,
      scheduler: schedulerConfig.value,
      project: projectConfig.value,
      holidays: holidaysConfig.value,
      distribution: distributionConfig.value
    }
    
    await api.put('/config/batch', { configs: allConfig })
    ElMessage.success('All configurations saved successfully')
  } catch (error) {
    console.error('Failed to save all config:', error)
    ElMessage.error('Failed to save all configurations')
  } finally {
    saving.value = false
  }
}

const resetAll = () => {
  ElMessageBox.confirm(
    'Are you sure you want to reset all configurations to default?',
    'Confirm Reset',
    { type: 'warning' }
  ).then(() => {
    fetchCategoryConfig(activeCategory.value)
    ElMessage.info('All configurations reset')
  }).catch(() => {})
}

const backupConfig = async () => {
  try {
    const response = await api.get('/config/backup')
    const { backup_data, backup_file } = response.data
    
    // 下载备份文件
    const blob = new Blob([JSON.stringify(backup_data, null, 2)], { type: 'application/json' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `config_backup_${new Date().toISOString().slice(0, 10)}.json`
    a.click()
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('Configuration backup downloaded')
  } catch (error) {
    console.error('Failed to backup config:', error)
    ElMessage.error('Failed to backup configuration')
  }
}

const showRestoreDialog = () => {
  restoreDialogVisible.value = true
}

const handleRestoreFile = (file) => {
  restoreFile.value = file.raw
}

const restoreConfig = async () => {
  if (!restoreFile.value) return
  
  try {
    const reader = new FileReader()
    reader.onload = async (e) => {
      try {
        const backupData = JSON.parse(e.target.result)
        await api.post('/config/restore', backupData)
        ElMessage.success('Configuration restored successfully')
        restoreDialogVisible.value = false
        
        // 重新加载所有配置
        Object.keys(backupData).forEach(category => {
          if (category !== 'holidays') {
            fetchCategoryConfig(category)
          }
        })
      } catch (error) {
        console.error('Failed to restore config:', error)
        ElMessage.error('Failed to restore configuration')
      }
    }
    reader.readAsText(restoreFile.value)
  } catch (error) {
    console.error('Failed to read backup file:', error)
    ElMessage.error('Failed to read backup file')
  }
}

const testEmail = async () => {
  try {
    const response = await api.post('/config/test/email')
    if (response.data.success) {
      ElMessage.success('Test email sent successfully')
    } else {
      ElMessage.error(response.data.message)
    }
  } catch (error) {
    console.error('Failed to test email:', error)
    ElMessage.error('Failed to test email configuration')
  }
}

// 明星股操作
const addStock = (market) => {
  starStocksConfig.value[market].push({ code: '', name: '' })
}

const removeStock = (market, index) => {
  starStocksConfig.value[market].splice(index, 1)
}

// 节假日操作
const addHoliday = (year) => {
  if (newHoliday.value[year]) {
    holidaysConfig.value[year].push(newHoliday.value[year])
    newHoliday.value[year] = ''
  }
}

const removeHoliday = (year, index) => {
  holidaysConfig.value[year].splice(index, 1)
}

const addYear = () => {
  const year = new Date().getFullYear() + 1
  if (!holidaysConfig.value[year]) {
    holidaysConfig.value[year] = []
    newHoliday.value[year] = ''
  }
}

// 初始化
onMounted(() => {
  fetchCategories()
  fetchCategoryConfig('ai')
})
</script>

<style scoped>
.config-container {
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

.header-actions {
  display: flex;
  gap: 10px;
}

.description {
  color: #909399;
  margin: 0;
}

.category-card {
  height: calc(100vh - 300px);
}

.category-card .el-menu {
  border-right: none;
}

.config-card {
  min-height: calc(100vh - 300px);
}

.config-header {
  margin-bottom: 20px;
}

.config-header h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
}

.config-header p {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.config-form {
  max-width: 600px;
}

.form-tip {
  color: #909399;
  font-size: 12px;
  margin-top: 4px;
}

.form-actions {
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #eee;
}

.stock-item {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.holiday-list {
  max-height: 300px;
  overflow-y: auto;
}
</style>
