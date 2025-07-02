# StreamDeck Carousel Interface

The StreamDeck interface now uses a **carousel system** that allows browsing through all available media objects using just 6 buttons.

## Button Layout

```
┌─────────┬─────────┬─────────┐
│ Button 0│ Button 1│ Button 2│  ← Carousel (3 visible media objects)
│ Media 1 │ Media 2 │ Media 3 │
├─────────┼─────────┼─────────┤
│ Button 3│ Button 4│ Button 5│
│Now Play │   ◄     │    ►    │  ← Controls
│  ing    │ Previous│  Next   │
└─────────┴─────────┴─────────┘
```

## Button Functions

### Carousel Buttons (0, 1, 2)

- **Display**: Currently visible media objects (3 at a time)
- **Action**: Press to play/stop the displayed media
- **Behavior**:
  - If media is not playing → Start playing
  - If media is currently playing → Stop playback

### Now Playing Button (3)

- **Display**: Shows currently playing media or "NOW PLAYING" text
- **Action**: Control current playback
- **Behavior**:
  - If playing → Stop playback
  - If stopped/error → Restart current media

### Navigation Buttons (4, 5)

- **Button 4 (◄)**: Navigate to previous media objects
- **Button 5 (►)**: Navigate to next media objects
- **Visual**: Arrow symbols with color indication
  - **Blue**: Navigation available
  - **Gray**: No more items in that direction

## How It Works

### Carousel Navigation

- The carousel shows **3 media objects at a time**
- Use **Previous (◄)** and **Next (►)** buttons to scroll through all available media
- Carousel wraps around - when you reach the end, navigation stops

### Media Selection

- Press any carousel button (0, 1, or 2) to play that media object
- The display will show radio stations, Spotify albums, and local albums
- Media objects appear in the order defined in `media_objects.json`

### Example Navigation Flow

**Starting position (offset 0):**

```
Button 0: Sveriges Radio P1
Button 1: Sveriges Radio P2
Button 2: Sveriges Radio P3
```

**After pressing Next (►) once (offset 1):**

```
Button 0: Sveriges Radio P2
Button 1: Sveriges Radio P3
Button 2: Abbey Road - The Beatles
```

**After pressing Next (►) again (offset 2):**

```
Button 0: Sveriges Radio P3
Button 1: Abbey Road - The Beatles
Button 2: Sveriges Radio P4 Stockholm
```

## Visual Indicators

### Button Colors

- **Green**: Currently playing media
- **Orange**: Media loading
- **Blue**: Available media
- **Red**: Error state
- **Gray**: Inactive/unavailable

### Arrow Button States

- **Blue arrows**: Navigation available
- **Gray arrows**: End of list reached

## Benefits

✅ **Access All Media**: Browse through unlimited media objects with just 6 buttons  
✅ **Intuitive Navigation**: Simple left/right navigation like a TV remote  
✅ **Clear Status**: Always see what's playing and what's available  
✅ **Efficient**: Makes optimal use of limited StreamDeck buttons  
✅ **Visual Feedback**: Color-coded states and clear arrow indicators

## Configuration

The carousel respects the order defined in `media_objects.json`. To reorder items:

1. Edit `media_objects.json`
2. Rearrange items in the array
3. Restart the application

The first item in the array becomes the first item in the carousel, and so on.

## Technical Details

- **Carousel Size**: 3 visible items (configurable in code)
- **Total Capacity**: Unlimited (scrolls through all available media)
- **Update Rate**: Real-time updates when media state changes
- **Memory Efficient**: Only loads 3 button images at a time
- **Responsive**: Immediate feedback on button presses

This carousel system transforms the StreamDeck from a static 6-button interface into a dynamic browser capable of accessing any number of media objects!
