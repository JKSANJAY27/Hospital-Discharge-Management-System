"""
Firebase authentication utilities
"""
import os
import firebase_admin
from firebase_admin import credentials, auth
from typing import Optional

# Initialize Firebase Admin SDK (only once)
_firebase_initialized = False

def initialize_firebase():
    """Initialize Firebase Admin SDK with service account"""
    global _firebase_initialized
    
    if _firebase_initialized:
        return
    
    try:
        # Option 1: Use service account JSON file
        cred_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
        print(f"🔍 Looking for Firebase credentials at: {cred_path}")
        
        if cred_path and os.path.exists(cred_path):
            print(f"✓ Found service account file at: {cred_path}")
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            _firebase_initialized = True
            print("✓ Firebase Admin SDK initialized with service account")
            return
        else:
            if cred_path:
                print(f"❌ Service account file not found at: {cred_path}")
            else:
                print("❌ FIREBASE_SERVICE_ACCOUNT_PATH not set in .env")
        
        # Option 2: Use environment variables to construct credentials
        project_id = os.getenv("FIREBASE_PROJECT_ID")
        private_key = os.getenv("FIREBASE_PRIVATE_KEY")
        client_email = os.getenv("FIREBASE_CLIENT_EMAIL")
        
        if project_id and private_key and client_email:
            print("🔍 Attempting to initialize with environment variables...")
            # Replace literal \n with actual newlines in private key
            private_key = private_key.replace('\\n', '\n')
            
            cred_dict = {
                "type": "service_account",
                "project_id": project_id,
                "private_key": private_key,
                "client_email": client_email,
                "token_uri": "https://oauth2.googleapis.com/token",
            }
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            _firebase_initialized = True
            print("✓ Firebase Admin SDK initialized with environment variables")
            return
        else:
            print("❌ Firebase environment variables not set (FIREBASE_PROJECT_ID, FIREBASE_PRIVATE_KEY, FIREBASE_CLIENT_EMAIL)")
        
        # Option 3: Use default credentials (if deployed on GCP)
        try:
            firebase_admin.initialize_app()
            _firebase_initialized = True
            print("✓ Firebase Admin SDK initialized with default credentials")
            return
        except Exception as e2:
            print(f"❌ Default credentials also failed: {e2}")
        
        print("⚠️ Firebase Admin SDK not initialized - no credentials found")
        print("   Option 1: Set FIREBASE_SERVICE_ACCOUNT_PATH in .env")
        print("   Option 2: Set FIREBASE_PROJECT_ID, FIREBASE_PRIVATE_KEY, FIREBASE_CLIENT_EMAIL in .env")
        print("   Option 3: Deploy to GCP with default credentials")
    
    except Exception as e:
        print(f"⚠️ Firebase initialization error: {e}")
        import traceback
        traceback.print_exc()


def verify_firebase_token(id_token: str, clock_skew_seconds: int = 10) -> Optional[dict]:
    """
    Verify Firebase ID token and return decoded token with user info
    
    Args:
        id_token: Firebase ID token from client
        clock_skew_seconds: Allowed clock skew in seconds (default 10)
        
    Returns:
        Decoded token dict with user info or None if invalid
    """
    if not _firebase_initialized:
        print("⚠️ Attempting to verify token but Firebase not initialized")
        initialize_firebase()
    
    if not _firebase_initialized:
        print("❌ Cannot verify token - Firebase Admin SDK not initialized")
        return None
    
    try:
        # Verify the ID token with clock skew tolerance
        print(f"🔐 Verifying Firebase token...")
        decoded_token = auth.verify_id_token(id_token, clock_skew_seconds=clock_skew_seconds)
        print(f"✓ Token verified for user: {decoded_token.get('email')}")
        return decoded_token
    except Exception as e:
        # It's common for this to fail if the token is a Custom JWT (not Firebase)
        # We process this silently or with a debug log to allow fallback methods to work
        # print(f"ℹ️ Firebase token verification failed (likely Custom JWT): {e}") 
        return None
