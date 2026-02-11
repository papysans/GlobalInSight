import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'stock-hot',
      component: () => import('../views/StockHotView.vue'),
    },
    {
      path: '/analysis',
      name: 'analysis',
      component: () => import('../views/StockAnalysisView.vue'),
    },
    {
      path: '/daily-report',
      name: 'daily-report',
      component: () => import('../views/DailyReportView.vue'),
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('../views/SettingsView.vue'),
    },
  ],
})

export default router
