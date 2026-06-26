import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'Dashboard', component: () => import('../views/Dashboard.vue') },
  { path: '/data', name: 'DataBrowser', component: () => import('../views/DataBrowser.vue') },
  { path: '/validation', name: 'ValidationQueue', component: () => import('../views/ValidationQueue.vue') },
  { path: '/datasets', name: 'Datasets', component: () => import('../views/Datasets.vue') },
  { path: '/sources', name: 'Sources', component: () => import('../views/Sources.vue') },
  { path: '/crawl', name: 'CrawlControl', component: () => import('../views/CrawlControl.vue') },
  { path: '/process', name: 'ProcessingConsole', component: () => import('../views/ProcessingConsole.vue') },
  { path: '/exports', name: 'ExportSettings', component: () => import('../views/ExportSettings.vue') },
  { path: '/dead-letter', name: 'DeadLetter', component: () => import('../views/DeadLetterQueue.vue') },
  { path: '/proxies', name: 'Proxies', component: () => import('../views/ProxySettings.vue') },
  { path: '/analysis', name: 'Analysis', component: () => import('../views/AnalysisResults.vue') },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
