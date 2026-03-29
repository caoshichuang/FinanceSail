import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => response.data,
  error => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// 认证API
export const authApi = {
  login: (username, password) => {
    const formData = new URLSearchParams()
    formData.append('username', username)
    formData.append('password', password)
    return api.post('/auth/login', formData)
  },
  getMe: () => api.get('/auth/me'),
  verify: () => api.post('/auth/verify')
}

// 用户API
export const usersApi = {
  list: (params) => api.get('/users/', { params }),
  create: (data) => api.post('/users/', data),
  delete: (email) => api.delete(`/users/${email}`),
  renew: (email, days) => api.post(`/users/${email}/renew?days=${days}`),
  getSubscriptions: (email) => api.get(`/users/${email}/subscriptions`),
  addSubscription: (email, data) => api.post(`/users/${email}/subscriptions`, data),
  deleteSubscription: (email, stock) => api.delete(`/users/${email}/subscriptions/${stock}`),
  cleanup: () => api.post('/users/cleanup')
}

// 内容API
export const contentApi = {
  list: (params) => api.get('/content/', { params }),
  get: (id) => api.get(`/content/${id}`),
  delete: (id) => api.delete(`/content/${id}`),
  triggerUS: () => api.post('/content/trigger/us'),
  triggerAShare: () => api.post('/content/trigger/a-share'),
  triggerIPO: () => api.post('/content/trigger/ipo'),
  triggerHot: () => api.post('/content/trigger/hot'),
  stats: () => api.get('/content/stats/summary')
}

// 配置API
export const configApi = {
  getEnv: () => api.get('/config/env'),
  updateEnv: (data) => api.put('/config/env', data),
  getHolidays: () => api.get('/config/holidays'),
  updateHolidays: (data) => api.put('/config/holidays', data),
  getStarStocks: () => api.get('/config/star-stocks'),
  getScheduler: () => api.get('/config/scheduler')
}

// 日志API
export const logsApi = {
  getAppLog: (lines) => api.get('/logs/app', { params: { lines } }),
  getErrorLog: (lines) => api.get('/logs/error', { params: { lines } }),
  getSystemStatus: () => api.get('/logs/system'),
  getJobs: () => api.get('/logs/jobs')
}

export default api
