"""
Firebase integration for Dexent.ai.
Handles user authentication, data storage, and messaging.
"""

import os
import json
import logging
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, auth, firestore, storage

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class FirebaseManager:
    """Manages Firebase integration for Dexent.ai."""
    
    def __init__(self):
        self.app = None
        self.db = None
        self.bucket = None
        self.initialized = False
        
        # Initialize Firebase if credentials are available
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase with credentials."""
        try:
            # Check if required environment variables exist
            project_id = os.environ.get("FIREBASE_PROJECT_ID")
            api_key = os.environ.get("FIREBASE_API_KEY")
            app_id = os.environ.get("FIREBASE_APP_ID")
            
            if not all([project_id, api_key, app_id]):
                logger.warning("Firebase credentials not fully configured. Some features may be limited.")
                return False
            
            # Create service account credentials
            cred_dict = {
                "type": "service_account",
                "project_id": project_id,
                "private_key_id": "firebase_private_key_id",
                "private_key": os.environ.get("FIREBASE_PRIVATE_KEY", "").replace("\\n", "\n"),
                "client_email": os.environ.get("FIREBASE_CLIENT_EMAIL", f"firebase-adminsdk@{project_id}.iam.gserviceaccount.com"),
                "client_id": "firebase_client_id",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk%40{project_id}.iam.gserviceaccount.com"
            }
            
            # Check if service account file exists, otherwise create it
            cred_path = "firebase-credentials.json"
            if not os.path.exists(cred_path):
                if os.environ.get("FIREBASE_PRIVATE_KEY"):
                    # Write credentials to file
                    with open(cred_path, "w") as f:
                        json.dump(cred_dict, f)
                else:
                    logger.warning("Firebase private key not found. Using application default credentials.")
            
            # Initialize Firebase app
            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                self.app = firebase_admin.initialize_app(cred, {
                    'storageBucket': f"{project_id}.appspot.com"
                })
            else:
                # Try to initialize with application default credentials
                self.app = firebase_admin.initialize_app(None, {
                    'projectId': project_id,
                    'storageBucket': f"{project_id}.appspot.com"
                })
            
            # Initialize Firestore and Storage
            self.db = firestore.client()
            self.bucket = storage.bucket()
            
            self.initialized = True
            logger.info("Firebase initialized successfully.")
            return True
        
        except Exception as e:
            logger.error(f"Error initializing Firebase: {str(e)}")
            return False
    
    def is_initialized(self):
        """Check if Firebase is initialized."""
        return self.initialized
    
    def verify_id_token(self, id_token):
        """Verify Firebase ID token and get user data."""
        if not self.initialized:
            logger.warning("Firebase not initialized. Cannot verify token.")
            return None
        
        try:
            decoded_token = auth.verify_id_token(id_token)
            return decoded_token
        except Exception as e:
            logger.error(f"Error verifying ID token: {str(e)}")
            return None
    
    def get_user(self, uid):
        """Get user data by UID."""
        if not self.initialized:
            logger.warning("Firebase not initialized. Cannot get user.")
            return None
        
        try:
            user = auth.get_user(uid)
            return user
        except Exception as e:
            logger.error(f"Error getting user: {str(e)}")
            return None
    
    def create_user(self, email, password, display_name=None):
        """Create a new Firebase user."""
        if not self.initialized:
            logger.warning("Firebase not initialized. Cannot create user.")
            return None
        
        try:
            user_data = {
                'email': email,
                'password': password,
                'email_verified': False
            }
            
            if display_name:
                user_data['display_name'] = display_name
            
            user = auth.create_user(**user_data)
            return user
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            return None
    
    def update_user(self, uid, **kwargs):
        """Update a Firebase user."""
        if not self.initialized:
            logger.warning("Firebase not initialized. Cannot update user.")
            return False
        
        try:
            auth.update_user(uid, **kwargs)
            return True
        except Exception as e:
            logger.error(f"Error updating user: {str(e)}")
            return False
    
    def delete_user(self, uid):
        """Delete a Firebase user."""
        if not self.initialized:
            logger.warning("Firebase not initialized. Cannot delete user.")
            return False
        
        try:
            auth.delete_user(uid)
            return True
        except Exception as e:
            logger.error(f"Error deleting user: {str(e)}")
            return False
    
    def get_document(self, collection, document_id):
        """Get a document from Firestore."""
        if not self.initialized:
            logger.warning("Firebase not initialized. Cannot get document.")
            return None
        
        try:
            doc_ref = self.db.collection(collection).document(document_id)
            doc = doc_ref.get()
            
            if doc.exists:
                return doc.to_dict()
            else:
                return None
        except Exception as e:
            logger.error(f"Error getting document: {str(e)}")
            return None
    
    def set_document(self, collection, document_id, data, merge=True):
        """Set a document in Firestore."""
        if not self.initialized:
            logger.warning("Firebase not initialized. Cannot set document.")
            return False
        
        try:
            doc_ref = self.db.collection(collection).document(document_id)
            doc_ref.set(data, merge=merge)
            return True
        except Exception as e:
            logger.error(f"Error setting document: {str(e)}")
            return False
    
    def update_document(self, collection, document_id, data):
        """Update a document in Firestore."""
        if not self.initialized:
            logger.warning("Firebase not initialized. Cannot update document.")
            return False
        
        try:
            doc_ref = self.db.collection(collection).document(document_id)
            doc_ref.update(data)
            return True
        except Exception as e:
            logger.error(f"Error updating document: {str(e)}")
            return False
    
    def delete_document(self, collection, document_id):
        """Delete a document from Firestore."""
        if not self.initialized:
            logger.warning("Firebase not initialized. Cannot delete document.")
            return False
        
        try:
            doc_ref = self.db.collection(collection).document(document_id)
            doc_ref.delete()
            return True
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            return False
    
    def upload_file(self, file_path, destination_path):
        """Upload a file to Firebase Storage."""
        if not self.initialized:
            logger.warning("Firebase not initialized. Cannot upload file.")
            return None
        
        try:
            blob = self.bucket.blob(destination_path)
            blob.upload_from_filename(file_path)
            
            # Make public and get URL
            blob.make_public()
            return blob.public_url
        except Exception as e:
            logger.error(f"Error uploading file: {str(e)}")
            return None
    
    def download_file(self, source_path, destination_path):
        """Download a file from Firebase Storage."""
        if not self.initialized:
            logger.warning("Firebase not initialized. Cannot download file.")
            return False
        
        try:
            blob = self.bucket.blob(source_path)
            blob.download_to_filename(destination_path)
            return True
        except Exception as e:
            logger.error(f"Error downloading file: {str(e)}")
            return False
    
    def delete_file(self, file_path):
        """Delete a file from Firebase Storage."""
        if not self.initialized:
            logger.warning("Firebase not initialized. Cannot delete file.")
            return False
        
        try:
            blob = self.bucket.blob(file_path)
            blob.delete()
            return True
        except Exception as e:
            logger.error(f"Error deleting file: {str(e)}")
            return False
    
    def get_file_url(self, file_path):
        """Get the public URL for a file in Firebase Storage."""
        if not self.initialized:
            logger.warning("Firebase not initialized. Cannot get file URL.")
            return None
        
        try:
            blob = self.bucket.blob(file_path)
            blob.make_public()
            return blob.public_url
        except Exception as e:
            logger.error(f"Error getting file URL: {str(e)}")
            return None


# Create a singleton instance
firebase_manager = FirebaseManager()

# Function to get the Firebase manager instance
def get_firebase_manager():
    """Get the Firebase manager instance."""
    return firebase_manager