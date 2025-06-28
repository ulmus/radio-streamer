# Stream Deck Thumbnail Support

The Stream Deck interface now supports thumbnail images for radio stations instead of text-only buttons.

## How it works

1. **Image Detection**: The system automatically looks for station thumbnail images in the `images/stations/` directory
2. **Fallback**: If no thumbnail is found, the system falls back to text-based buttons
3. **Status Indication**: Colored borders around thumbnails indicate the station status:
   - **Blue border**: Available to play
   - **Green border**: Currently playing
   - **Orange border**: Loading/buffering
   - **Red border**: Error state

## Adding Station Thumbnails

To add thumbnails for your radio stations:

1. Create a thumbnail image (recommended size: 72x72 pixels)
2. Save it in the `images/stations/` directory with the station ID as filename
3. Supported formats: `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`

### Naming Convention

For a station with ID `station_id`, the image should be named:
- `station_id.png` (preferred)
- `station_id.jpg`
- `station_id.jpeg`
- etc.

### Examples

Based on the current `stations.json`:
- P1 station: `images/stations/p1.png`
- P2 station: `images/stations/p2.png`
- P3 station: `images/stations/p3.png`
- P4 Stockholm: `images/stations/p4_stockholm.png`
- BBC World: `images/stations/bbc_world.png`

## Current Thumbnails

The following placeholder thumbnails have been created:
- `p1.png` - Red thumbnail with "P1" text
- `p2.png` - Purple thumbnail with "P2" text  
- `p3.png` - Orange thumbnail with "P3" text
- `p4_stockholm.png` - Blue thumbnail with "P4 STH" text
- `bbc_world.png` - Light blue thumbnail with "BBC World" text

## Customization

You can replace these placeholder images with:
- Official station logos
- Custom artwork
- Photos or graphics that represent each station

Just ensure the images are reasonably sized (72x72 recommended) and use one of the supported formats.

## Testing

Test images showing how the thumbnails appear on Stream Deck buttons are generated in `/tmp/test_button_*.png` when running the test script.
