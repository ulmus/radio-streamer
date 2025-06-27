<script setup lang="ts">
import { onMounted } from 'vue'
import { RouterView } from 'vue-router'
import { useRadioStore } from '@/stores/radio'

const radioStore = useRadioStore()

onMounted(() => {
  radioStore.initialize()
})
</script>

<template>
  <div class="app">
    <header class="header">
      <div class="container">
        <h1 class="title">
          <span class="icon">📻</span>
          Radio Streamer
        </h1>
      </div>
    </header>
    
    <main class="main">
      <div class="container">
        <RouterView />
      </div>
    </main>
    
    <footer class="footer">
      <div class="container">
        <p>&copy; 2025 Radio Streamer</p>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #333;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

.header {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  padding: 20px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}

.title {
  color: white;
  margin: 0;
  font-size: 2rem;
  font-weight: 700;
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.icon {
  font-size: 2.5rem;
}

.main {
  flex: 1;
  padding: 40px 0;
}

.footer {
  background: rgba(0, 0, 0, 0.1);
  padding: 20px 0;
  text-align: center;
  color: rgba(255, 255, 255, 0.8);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.footer p {
  margin: 0;
  font-size: 0.9rem;
}
</style>
