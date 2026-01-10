# Integrated Document Upload in Chat

## Overview
All document upload functionality (prescriptions, discharge summaries, lab reports) is now integrated directly into the chatbot interface. No more separate tabs!

## What Changed

### 1. Fixed Import Error
**File:** `src/document_processor/image_extractor.py`
- **Issue:** Missing `src.utils.logging_utils` module causing 500 errors
- **Fix:** Replaced with standard Python `logging` module
```python
import logging
logger = logging.getLogger(__name__)
```

### 2. Enhanced Document Uploader
**File:** `frontend/src/components/DocumentUploader.tsx`

**New Features:**
- ✅ **Three Upload Options:**
  - 📄 **Upload PDF** - Traditional file upload for PDFs
  - 📸 **Take Photo** - Open webcam and capture prescription/document photo
  - 🖼️ **Upload Image** - Upload existing image file (JPG, PNG)

- ✅ **Camera Integration:**
  - Opens webcam in modal
  - Live video preview
  - Capture button to take snapshot
  - Works on both desktop and mobile

- ✅ **Image Extraction:**
  - Automatically extracts structured data from images
  - Uses `/api/extract/prescription` endpoint
  - Displays extracted information (patient, doctor, medications, etc.)
  - Shows success confirmation

- ✅ **Chat Integration:**
  - New prop: `onExtractComplete` callback
  - Passes extracted data back to parent chat component
  - Data appears as message in chat conversation

### 3. Updated Chat Component
**File:** `frontend/src/components/chat.tsx`

**New Features:**
- ✅ **Document Modal Integration:**
  - Click 📄 button next to chat input
  - Opens document upload modal
  - Supports PDF upload, camera capture, and image upload

- ✅ **Extracted Data Display:**
  - New `formatExtractedData()` function
  - Displays extracted medical information in chat
  - Formatted with icons and structured layout
  - Includes patient, doctor, date, diagnosis, medications, instructions

- ✅ **Message Flow:**
  1. User uploads document via modal
  2. System extracts medical data
  3. Two messages added to chat:
     - User: "📄 Uploaded medical document"
     - Assistant: Formatted extracted data with all details
  4. User can now ask questions about the document

## User Experience

### Before
- ❌ Separate tabs for discharge, prescription, health reports
- ❌ Confusing navigation
- ❌ Data not integrated with chat context

### After
- ✅ Everything in one place - the chatbot
- ✅ Click 📄 button → Upload → Data appears in chat
- ✅ Ask questions immediately about uploaded documents
- ✅ Seamless conversation flow
- ✅ Three flexible upload options (PDF/Camera/Image)

## Usage Flow

### For Users:
1. **Open Chat** - Main chat interface
2. **Click 📄 Button** - Next to chat input (between text field and voice recorder)
3. **Choose Upload Method:**
   - **PDF:** For detailed discharge summaries
   - **Camera:** Point at prescription and capture
   - **Image:** Upload existing photo from device
4. **Wait for Extraction** - AI processes document
5. **Review Extracted Data** - Appears as chat message
6. **Ask Questions** - "What's this medication for?", "When should I take this?", etc.

### Example Conversation:
```
User: 📄 Uploaded medical document

Bot: ✅ Medical Document Processed

     Patient: John Doe
     Doctor: Dr. Sarah Smith
     Date: January 9, 2026
     
     Medications:
     • Amoxicillin - 500mg (3 times daily)
     • Ibuprofen - 200mg (as needed for pain)
     
     💬 You can now ask me questions about this prescription or document!

User: When should I take the Amoxicillin?

Bot: Based on your prescription, you should take Amoxicillin 500mg three times daily. 
     This means approximately every 8 hours. It's best to take it:
     - Morning (8 AM)
     - Afternoon (4 PM)  
     - Night (12 AM)
     
     Important: Take with food to avoid stomach upset and complete the full course...
```

## Technical Details

### API Endpoints Used
- `POST /api/extract/prescription` - Extract data from prescription images
- `POST /api/extract/discharge` - Extract data from discharge summaries
- `POST /api/extract/lab-report` - Extract data from lab reports
- `POST /api/documents` - Upload PDF documents
- `GET /api/documents` - List uploaded documents

### Technologies
- **Frontend:** React 19, Next.js 16, TypeScript
- **Camera:** MediaDevices API (`getUserMedia`)
- **Image Processing:** Canvas API, FileReader API
- **Backend:** Google Gemini Vision API
- **Authentication:** Firebase JWT tokens

### File Structure
```
frontend/src/components/
├── chat.tsx (Main chat interface with modal)
└── DocumentUploader.tsx (Upload component with camera)

src/document_processor/
└── image_extractor.py (Gemini Vision integration)
```

## Benefits

### For Users:
- 📱 **Mobile-Friendly** - Camera works on phones
- 💬 **Conversational** - Ask questions about documents
- 🎯 **Focused** - One interface for everything
- ⚡ **Fast** - Upload and get answers immediately

### For Developers:
- 🔧 **Maintainable** - Single source of truth
- 🧩 **Modular** - Reusable DocumentUploader component
- 📊 **Contextual** - Documents integrated with chat history
- 🎨 **Consistent** - Unified UI/UX

## Testing Checklist

- [ ] Upload PDF document
- [ ] Take photo with desktop webcam
- [ ] Take photo with mobile camera (rear camera)
- [ ] Upload existing image file
- [ ] Verify extracted data displays correctly
- [ ] Ask follow-up questions about uploaded document
- [ ] Check camera permissions handling
- [ ] Test with handwritten prescriptions
- [ ] Test with printed discharge summaries
- [ ] Verify error messages display properly

## Troubleshooting

### Camera Not Opening
- **Issue:** Browser blocking camera access
- **Solution:** Check browser permissions (chrome://settings/content/camera)

### Extraction Fails
- **Issue:** Poor image quality or unclear text
- **Solution:** Ensure good lighting, clear focus, text readable

### Modal Won't Close
- **Issue:** State not updating
- **Solution:** Click X button or Cancel, refresh if needed

## Future Enhancements
- [ ] Add document type auto-detection
- [ ] Support multiple image upload at once
- [ ] Add OCR quality indicator before extraction
- [ ] Enable edit extracted data before saving
- [ ] Add document search across chat history
- [ ] Support voice commands for document upload
