import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'Dashboard', component: () => import('../views/Dashboard.vue') },
  { path: '/containers', name: 'Containers', component: () => import('../views/ContainersList.vue') },
  { path: '/containers/new', name: 'NewContainer', component: () => import('../views/ContainerEditor.vue') },
  { path: '/containers/:id/edit', name: 'EditContainer', component: () => import('../views/ContainerEditor.vue') },
  { path: '/crawl', name: 'CrawlControl', component: () => import('../views/CrawlControl.vue') },
  { path: '/dead-letter', name: 'DeadLetter', component: () => import('../views/DeadLetterQueue.vue') },
  { path: '/proxies', name: 'Proxies', component: () => import('../views/ProxySettings.vue') },
  { path: '/data', name: 'DataBrowser', component: () => import('../views/DataBrowser.vue') },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
