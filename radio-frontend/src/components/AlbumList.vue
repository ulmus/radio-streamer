<template>
  <div class="albums-container">
    <div class="albums-header">
      <h2 class="albums-title">🎵 Music Albums</h2>
      <p class="albums-subtitle">Select an album to start playing</p>
    </div>
    
    <div v-if="loading" class="loading">
      Loading albums...
    </div>
    
    <div v-else-if="albums && Object.keys(albums).length > 0" class="album-grid">
      <div 
        v-for="(album, albumName) in albums" 
        :key="albumName" 
        class="album-card"
        @click="playAlbum(albumName, 1)"
      >
        <div class="album-art">
          <img 
            v-if="album.album_art_path" 
            :src="getAlbumArtUrl(album.album_art_path)" 
            :alt="album.name"
            class="album-image"
          />
          <div v-else class="album-placeholder">
            🎵
          </div>
        </div>
        
        <div class="album-info">
          <h3 class="album-name">{{ album.name }}</h3>
          <p class="album-stats">{{ album.track_count }} tracks</p>
          
          <div class="album-actions">
            <button class="play-btn" @click.stop="playAlbum(albumName, 1)">
              ▶️ Play Album
            </button>
          </div>
        </div>
        
        <div class="track-list" v-if="expandedAlbum === albumName">
          <div class="track-header">
            <strong>Tracks:</strong>
          </div>
          <div 
            v-for="track in album.tracks" 
            :key="track.track_number" 
            class="track-item"
            @click.stop="playTrack(albumName, track.track_number)"
          >
            <span class="track-number">{{ track.track_number }}.</span>
            <span class="track-title">{{ track.title }}</span>
            <button class="track-play-btn">▶️</button>
          </div>
        </div>
        
        <button 
          class="expand-btn"
          @click.stop="toggleExpanded(albumName)"
        >
          {{ expandedAlbum === albumName ? '▲' : '▼' }} 
          {{ expandedAlbum === albumName ? 'Hide' : 'Show' }} Tracks
        </button>
      </div>
    </div>
    
    <div v-else class="no-albums">
      <div class="no-albums-icon">🎵</div>
      <h3>No Albums Found</h3>
      <p>Make sure you have albums in your music folder with the correct format:</p>
      <ul class="format-info">
        <li>Each album should be in its own folder</li>
        <li>MP3 files should be named: "NN.Song Title.mp3"</li>
        <li>Optional: Include "album_art.png" for album artwork</li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { albumApi } from '@/services/radioApi'
import type { Album } from '@/types/radio'

const albums = ref<Record<string, Album>>({})
const loading = ref(true)
const expandedAlbum = ref<string | null>(null)

const loadAlbums = async () => {
  try {
    loading.value = true
    albums.value = await albumApi.getAlbums()
  } catch (error) {
    console.error('Failed to load albums', error)
  } finally {
    loading.value = false
  }
}

const playAlbum = async (albumName: string, trackNumber: number) => {
  try {
    await albumApi.playAlbum(albumName, trackNumber)
  } catch (error) {
    console.error('Failed to play album', error)
  }
}

const playTrack = async (albumName: string, trackNumber: number) => {
  try {
    await albumApi.playTrack(albumName, trackNumber)
  } catch (error) {
    console.error('Failed to play track', error)
  }
}

const toggleExpanded = (albumName: string) => {
  expandedAlbum.value = expandedAlbum.value === albumName ? null : albumName
}

const getAlbumArtUrl = (artPath: string) => {
  // For now, return a placeholder or handle file serving
  return `/api/files/${encodeURIComponent(artPath)}`
}

onMounted(() => loadAlbums())
</script>

<style scoped>
.albums-container {
  padding: 20px 0;
}

.albums-header {
  text-align: center;
  margin-bottom: 30px;
}

.albums-title {
  color: white;
  font-size: 2rem;
  font-weight: 700;
  margin: 0 0 10px 0;
}

.albums-subtitle {
  color: rgba(255, 255, 255, 0.8);
  font-size: 1rem;
  margin: 0;
}

.loading {
  text-align: center;
  color: rgba(255, 255, 255, 0.8);
  font-size: 1.1rem;
  padding: 40px;
}

.album-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.album-card {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
}

.album-card:hover {
  transform: translateY(-5px);
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.3);
}

.album-art {
  width: 100%;
  height: 200px;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 15px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.1);
}

.album-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.album-placeholder {
  font-size: 4rem;
  color: rgba(255, 255, 255, 0.5);
}

.album-info {
  text-align: center;
}

.album-name {
  color: white;
  font-size: 1.2rem;
  font-weight: 600;
  margin: 0 0 5px 0;
}

.album-stats {
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.9rem;
  margin: 0 0 15px 0;
}

.album-actions {
  margin-bottom: 15px;
}

.play-btn {
  background: linear-gradient(135deg, #4f46e5, #7c3aed);
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  width: 100%;
}

.play-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.4);
}

.expand-btn {
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.2);
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.3s ease;
  width: 100%;
}

.expand-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

.track-list {
  margin: 15px 0;
  padding: 15px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
}

.track-header {
  color: white;
  margin-bottom: 10px;
  font-size: 0.9rem;
}

.track-item {
  display: flex;
  align-items: center;
  padding: 8px 0;
  cursor: pointer;
  transition: all 0.2s ease;
  border-radius: 4px;
}

.track-item:hover {
  background: rgba(255, 255, 255, 0.1);
  padding-left: 8px;
}

.track-number {
  color: rgba(255, 255, 255, 0.6);
  width: 30px;
  font-size: 0.85rem;
}

.track-title {
  color: rgba(255, 255, 255, 0.9);
  flex: 1;
  font-size: 0.85rem;
}

.track-play-btn {
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.7);
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.track-play-btn:hover {
  color: white;
  background: rgba(255, 255, 255, 0.1);
}

.no-albums {
  text-align: center;
  padding: 60px 20px;
  color: rgba(255, 255, 255, 0.8);
}

.no-albums-icon {
  font-size: 4rem;
  margin-bottom: 20px;
}

.no-albums h3 {
  color: white;
  font-size: 1.5rem;
  margin: 0 0 15px 0;
}

.no-albums p {
  font-size: 1rem;
  margin: 0 0 20px 0;
}

.format-info {
  text-align: left;
  display: inline-block;
  margin: 0;
  padding-left: 20px;
}

.format-info li {
  margin: 8px 0;
  font-size: 0.9rem;
}
</style>

