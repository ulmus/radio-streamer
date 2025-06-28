<script setup lang="ts">
import { ref } from 'vue'
import RadioPlayer from '@/components/RadioPlayer.vue'
import StationList from '@/components/StationList.vue'
import AlbumList from '@/components/AlbumList.vue'

const activeTab = ref<'radio' | 'albums'>('radio')

const setActiveTab = (tab: 'radio' | 'albums') => {
  activeTab.value = tab
}
</script>

<template>
  <main>
    <RadioPlayer />
    
    <!-- Tab Controller -->
    <div class="tab-controller">
      <button 
        :class="{ active: activeTab === 'radio' }" 
        @click="setActiveTab('radio')"
        class="tab-button"
      >
        📻 Radio Stations
      </button>
      <button 
        :class="{ active: activeTab === 'albums' }" 
        @click="setActiveTab('albums')"
        class="tab-button"
      >
        🎵 Albums
      </button>
    </div>
    
    <!-- Tab Content -->
    <div class="tab-content">
      <StationList v-if="activeTab === 'radio'" />
      <AlbumList v-if="activeTab === 'albums'" />
    </div>
  </main>
</template>

<style scoped>
.tab-controller {
  display: flex;
  margin: 20px 0;
  border-bottom: 2px solid rgba(255, 255, 255, 0.2);
}

.tab-button {
  flex: 1;
  padding: 12px 24px;
  background: transparent;
  color: rgba(255, 255, 255, 0.7);
  border: none;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  border-bottom: 2px solid transparent;
}

.tab-button:hover {
  color: white;
  background: rgba(255, 255, 255, 0.1);
}

.tab-button.active {
  color: white;
  border-bottom-color: #4f46e5;
  background: rgba(255, 255, 255, 0.1);
}

.tab-content {
  min-height: 400px;
}
</style>
