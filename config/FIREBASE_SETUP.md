# Firebase Service Account Setup

## How to get your Firebase Service Account JSON:

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project: **pran-prototcol**
3. Click the gear icon (⚙️) next to "Project Overview" → **Project settings**
4. Go to the **Service accounts** tab
5. Click **Generate new private key**
6. Save the downloaded JSON file as `firebase-service-account.json` in the `config/` directory

## Temporary Alternative:

If you can't get the service account file right now, you can use the Firebase Web API Key for authentication instead. The backend will fall back to custom JWT validation.

## File Location:
Place the file at: `config/firebase-service-account.json`

**IMPORTANT**: Add this file to `.gitignore` to prevent committing sensitive credentials.
