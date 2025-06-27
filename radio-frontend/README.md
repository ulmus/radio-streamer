# Radio Streamer Frontend

A modern Vue 3 frontend for the Radio Streamer API, built with TypeScript, Vite, and Pinia.

## Features

- 🎵 Stream Swedish Radio stations (P1, P2, P3) out of the box
- 🎛️ Full playback controls (play, pause, stop)
- 🔊 Volume control
- 📻 Add and manage custom radio stations
- 📱 Responsive design
- 🎨 Modern, glassmorphic UI design
- ⚡ Real-time status updates
- 🔄 Auto-refresh when playing

## Prerequisites

- Node.js 18+ 
- Radio Streamer backend running on `http://localhost:8000`

## Quick Start

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Start the development server:**
   ```bash
   npm run dev
   ```

3. **Open your browser:**
   Navigate to `http://localhost:5173`

4. **Make sure the backend is running:**
   The frontend expects the radio backend to be running on `http://localhost:8000`

## Usage

### Playing Radio Stations

1. **Swedish Radio Stations**: P1, P2, and P3 are available by default
2. **Play a station**: Click the "Play" button on any station card
3. **Pause/Resume**: Use the main player controls or click the playing station again
4. **Stop**: Click the "Stop" button to completely stop playback
5. **Volume**: Adjust using the volume slider

### Adding Custom Stations

1. Click the "Add Station" button
2. Fill in the form:
   - **Station ID**: Unique identifier (e.g., "mystation")
   - **Station Name**: Display name for the station
   - **Stream URL**: Direct URL to the audio stream
   - **Description**: Optional description
3. Click "Add Station" to save

### Managing Stations

- **Remove**: Click the trash icon on custom stations (predefined stations cannot be removed)
- **Play/Pause**: Click the play button on any station card

## Configuration

To change the backend URL, edit the `API_BASE_URL` in `src/services/radioApi.ts`:

```typescript
const API_BASE_URL = 'http://your-backend-url:8000'
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run type-check` - Run TypeScript type checking
- `npm run lint` - Run ESLint
- `npm run format` - Format code with Prettier

## Architecture

### State Management
- **Pinia** for reactive state management
- Automatic status polling when playing
- Real-time error handling

### API Communication
- **Axios** for HTTP requests
- Centralized API service with TypeScript types
- Automatic error handling and timeouts

### UI Components
- **RadioPlayer**: Main player interface with controls
- **StationList**: Station management and display
- **Heroicons** for consistent iconography

### Styling
- **CSS3** with modern features (backdrop-filter, grid, flexbox)
- Glassmorphic design with gradients and transparency
- Fully responsive layout
- Custom scrollbars and focus states

## Browser Support

- Chrome/Edge 88+
- Firefox 94+
- Safari 14+

## Troubleshooting

### Backend Connection Issues
- Ensure the backend is running on `http://localhost:8000`
- Check browser console for CORS errors
- Verify the backend is accessible from your network

### Audio Not Playing
- Check browser audio permissions
- Ensure the stream URLs are accessible
- Some streams may require specific headers or authentication

### Development Issues
- Clear browser cache and restart dev server
- Check for TypeScript errors: `npm run type-check`
- Verify all dependencies are installed: `npm install`
