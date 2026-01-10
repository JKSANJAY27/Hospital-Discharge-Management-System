# Camera Implementation for Desktop & Mobile

## Overview
Implemented proper webcam capture functionality that works on both desktop and mobile devices using the MediaDevices API.

## Technical Implementation

### State Management
```typescript
const [showCamera, setShowCamera] = useState(false);
const [stream, setStream] = useState<MediaStream | null>(null);
const videoRef = useRef<HTMLVideoElement>(null);
const canvasRef = useRef<HTMLCanvasElement>(null);
```

### Camera Workflow

1. **Start Camera** (`handleCameraClick`)
   - Opens camera modal
   - Requests camera access via `navigator.mediaDevices.getUserMedia()`
   - Displays live video stream in modal
   - Falls back to file picker if camera access fails

2. **Capture Photo** (`capturePhoto`)
   - Draws current video frame to canvas
   - Converts canvas to JPEG blob (95% quality)
   - Creates File object from blob
   - Shows preview and closes camera

3. **Close Camera** (`closeCamera`)
   - Stops all media tracks
   - Closes camera modal
   - Cleans up resources

### UI Components

**Camera Modal** (Z-index 50 overlay):
- Full-screen dark backdrop
- White card with video preview
- "Capture Photo" button with camera icon
- "Cancel" button to close
- Close (X) button in header

**Hidden Canvas**:
- Used for frame capture
- Not displayed to user
- Auto-sized to video dimensions

## User Flow

1. User clicks "Take Photo" button (Camera icon)
2. Browser requests camera permission
3. Modal opens with live camera preview
4. User clicks "Capture Photo" when ready
5. Photo captured and modal closes
6. Image preview shown with upload option
7. User can submit to extract prescription data

## Platform Compatibility

### Desktop
- Uses `getUserMedia()` with video constraints
- Default camera (usually front camera)
- Works in Chrome, Edge, Firefox, Safari (with permissions)

### Mobile
- Attempts rear camera via `facingMode: 'environment'`
- Falls back to front camera if unavailable
- Full native camera support in modern browsers

## Error Handling

- Camera permission denied → Falls back to file picker
- No camera available → Falls back to file picker
- Console logs errors for debugging

## Integration with Image Processing

Captured photos are processed through:
1. Set `uploadMode = 'image'`
2. Create File object: `camera-capture.jpg`
3. Generate preview via canvas.toDataURL()
4. Submit to `/extract/prescription` endpoint
5. Use Google Gemini Vision for extraction

## Next Steps

- Test on various devices (desktop, mobile, tablet)
- Add camera switch button (front/rear toggle)
- Add flash/torch control for mobile
- Add zoom controls
- Improve error messages for permissions
- Add loading state while camera initializes
