import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue')
  },
  {
    path: '/preview/:id',
    name: 'Preview',
    component: () => import('../views/Preview.vue'),
    meta: { public: true }
  },
  {
    path: '/',
    component: () => import('../views/Layout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('../views/Dashboard.vue'),
        meta: { title: 'Dashboard', icon: 'Odometer' }
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import('../views/Users.vue'),
        meta: { title: 'Users', icon: 'User' }
      },
      {
        path: 'content',
        name: 'Content',
        component: () => import('../views/Content.vue'),
        meta: { title: 'Content', icon: 'Document' }
      },
      {
        path: 'config',
        name: 'Config',
        component: () => import('../views/Config.vue'),
        meta: { title: 'Config', icon: 'Setting' }
      },
      {
        path: 'logs',
        name: 'Logs',
        component: () => import('../views/Logs.vue'),
        meta: { title: 'Logs', icon: 'List' }
      },
      {
        path: 'distribution',
        name: 'Distribution',
        component: () => import('../views/Distribution.vue'),
        meta: { title: 'Distribution', icon: 'Share' }
      },
      {
        path: 'subscriptions',
        name: 'Subscriptions',
        component: () => import('../views/Subscriptions.vue'),
        meta: { title: 'Subscriptions', icon: 'Bell' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  
  // 允许公开访问的页面
  if (to.meta.public) {
    next()
  } else if (to.path === '/login') {
    next()
  } else if (!token) {
    next('/login')
  } else {
    next()
  }
})

export default router
