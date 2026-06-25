<template>
  <div class="app-layout">
    <aside class="sidebar">
      <div class="sidebar-header">
        <h2>SelfLearningLM</h2>
      </div>
      <nav class="sidebar-nav">
        <router-link to="/" class="nav-item" exact-active-class="active">
          <i class="pi pi-home"></i> Dashboard
        </router-link>
        <router-link to="/containers" class="nav-item" active-class="active">
          <i class="pi pi-box"></i> Containers
        </router-link>
        <router-link to="/crawl" class="nav-item" active-class="active">
          <i class="pi pi-send"></i> Crawl Control
        </router-link>
        <router-link to="/data" class="nav-item" active-class="active">
          <i class="pi pi-database"></i> Data Browser
        </router-link>
        <router-link to="/dead-letter" class="nav-item" active-class="active">
          <i class="pi pi-exclamation-triangle"></i> Dead Letter
        </router-link>
        <router-link to="/proxies" class="nav-item" active-class="active">
          <i class="pi pi-shield"></i> Proxy Settings
        </router-link>
      </nav>
    </aside>
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; color: #333; }
.app-layout { display: flex; min-height: 100vh; }
.sidebar { width: 240px; background: #1e293b; color: #fff; display: flex; flex-direction: column; padding: 1rem; }
.sidebar-header { padding-bottom: 1.5rem; border-bottom: 1px solid #334155; margin-bottom: 1rem; }
.sidebar-header h2 { font-size: 1.25rem; font-weight: 600; }
.sidebar-nav { display: flex; flex-direction: column; gap: 0.25rem; }
.nav-item { display: flex; align-items: center; gap: 0.75rem; padding: 0.65rem 0.75rem; color: #94a3b8; text-decoration: none; border-radius: 6px; font-size: 0.9rem; transition: all 0.15s; }
.nav-item:hover { background: #334155; color: #e2e8f0; }
.nav-item.active { background: #3b82f6; color: #fff; }
.main-content { flex: 1; padding: 2rem; overflow-y: auto; }
</style>
