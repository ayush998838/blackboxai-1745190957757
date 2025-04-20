"""
Mobile app module for Dexent.ai.
Implements mobile application features and API endpoints for Android and iOS clients.
"""

import os
import json
import logging
import datetime
import uuid
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from config import SETTINGS
from models import db, User, UserProfile
from audio_processor import AudioProcessor
from firebase_integration import FirebaseManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create blueprint
mobile_bp = Blueprint('mobile', __name__)

# Initialize managers
firebase_manager = FirebaseManager()
audio_processor = AudioProcessor()

# Constants
API_VERSION = "1.0.0"
PLATFORM_VERSIONS = {
    "android": "1.0.0",
    "ios": "1.0.0"
}

@mobile_bp.route('/api/info', methods=['GET'])
def api_info():
    """Get API information."""
    return jsonify({
        "name": "Dexent.ai Mobile API",
        "version": API_VERSION,
        "platforms": PLATFORM_VERSIONS,
        "status": "active"
    })

@mobile_bp.route('/api/auth/register', methods=['POST'])
def mobile_register():
    """Register a new user from mobile app."""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['username', 'email', 'password', 'device_id', 'platform']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Check if username or email already exists
        existing_user = User.query.filter(
            (User.username == data['username']) | (User.email == data['email'])
        ).first()
        
        if existing_user:
            if existing_user.username == data['username']:
                return jsonify({"error": "Username already exists"}), 409
            else:
                return jsonify({"error": "Email already exists"}), 409
        
        # Create new user
        new_user = User(
            username=data['username'],
            email=data['email'],
            password_hash=generate_password_hash(data['password']),
            created_at=datetime.datetime.now()
        )
        
        # Add user to database
        db.session.add(new_user)
        db.session.commit()
        
        # Create user profile
        new_profile = UserProfile(
            user_id=new_user.id,
            full_name=data.get('full_name', ''),
            bio=data.get('bio', ''),
            profile_picture=data.get('profile_picture', ''),
            mobile_device_id=data['device_id'],
            mobile_platform=data['platform'],
            mobile_push_token=data.get('push_token', ''),
            settings=json.dumps({
                "accent": data.get('accent', 'american'),
                "noise_suppression": True,
                "identity_preservation": True,
                "notifications": True
            })
        )
        
        db.session.add(new_profile)
        db.session.commit()
        
        # Create Firebase account
        firebase_result = firebase_manager.create_user(
            email=data['email'],
            password=data['password'],
            display_name=data['username']
        )
        
        # Generate authentication token
        auth_token = firebase_manager.create_custom_token(new_user.id)
        
        return jsonify({
            "success": True,
            "user_id": new_user.id,
            "username": new_user.username,
            "email": new_user.email,
            "token": auth_token,
            "firebase_uid": firebase_result.get("uid", "")
        })
    
    except Exception as e:
        logger.error(f"Error in mobile registration: {str(e)}")
        return jsonify({"error": str(e)}), 500

@mobile_bp.route('/api/auth/login', methods=['POST'])
def mobile_login():
    """Login a user from mobile app."""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['email', 'password', 'device_id']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Find user by email
        user = User.query.filter_by(email=data['email']).first()
        
        if not user or not check_password_hash(user.password_hash, data['password']):
            return jsonify({"error": "Invalid email or password"}), 401
        
        # Update device ID if needed
        profile = UserProfile.query.filter_by(user_id=user.id).first()
        if profile:
            profile.mobile_device_id = data['device_id']
            profile.mobile_platform = data.get('platform', profile.mobile_platform)
            profile.mobile_push_token = data.get('push_token', profile.mobile_push_token)
            db.session.commit()
        
        # Generate authentication token
        auth_token = firebase_manager.create_custom_token(user.id)
        
        return jsonify({
            "success": True,
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "token": auth_token
        })
    
    except Exception as e:
        logger.error(f"Error in mobile login: {str(e)}")
        return jsonify({"error": str(e)}), 500

@mobile_bp.route('/api/auth/refresh', methods=['POST'])
def refresh_token():
    """Refresh authentication token."""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['user_id', 'token']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Verify current token
        verification = firebase_manager.verify_id_token(data['token'])
        
        if not verification or str(verification.get('uid')) != str(data['user_id']):
            return jsonify({"error": "Invalid token"}), 401
        
        # Generate new token
        new_token = firebase_manager.create_custom_token(data['user_id'])
        
        return jsonify({
            "success": True,
            "token": new_token,
            "expires_at": datetime.datetime.now() + datetime.timedelta(hours=1)
        })
    
    except Exception as e:
        logger.error(f"Error refreshing token: {str(e)}")
        return jsonify({"error": str(e)}), 500

@mobile_bp.route('/api/user/profile', methods=['GET'])
def get_user_profile():
    """Get user profile for mobile app."""
    try:
        # Get user ID from token
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        verification = firebase_manager.verify_id_token(token)
        
        if not verification:
            return jsonify({"error": "Invalid token"}), 401
        
        user_id = verification.get('uid')
        
        # Get user and profile
        user = User.query.filter_by(id=user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        profile = UserProfile.query.filter_by(user_id=user.id).first()
        
        # Build response
        response = {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
        
        if profile:
            response.update({
                "full_name": profile.full_name,
                "bio": profile.bio,
                "profile_picture": profile.profile_picture,
                "settings": json.loads(profile.settings) if profile.settings else {}
            })
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}")
        return jsonify({"error": str(e)}), 500

@mobile_bp.route('/api/user/profile', methods=['PUT'])
def update_user_profile():
    """Update user profile for mobile app."""
    try:
        # Get user ID from token
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        verification = firebase_manager.verify_id_token(token)
        
        if not verification:
            return jsonify({"error": "Invalid token"}), 401
        
        user_id = verification.get('uid')
        
        # Get data
        data = request.json
        
        # Get user and profile
        user = User.query.filter_by(id=user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        profile = UserProfile.query.filter_by(user_id=user.id).first()
        if not profile:
            return jsonify({"error": "Profile not found"}), 404
        
        # Update profile fields
        if 'full_name' in data:
            profile.full_name = data['full_name']
        
        if 'bio' in data:
            profile.bio = data['bio']
        
        if 'profile_picture' in data:
            profile.profile_picture = data['profile_picture']
        
        if 'settings' in data:
            # Merge with existing settings
            current_settings = json.loads(profile.settings) if profile.settings else {}
            current_settings.update(data['settings'])
            profile.settings = json.dumps(current_settings)
        
        # Save changes
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Profile updated successfully"
        })
    
    except Exception as e:
        logger.error(f"Error updating user profile: {str(e)}")
        return jsonify({"error": str(e)}), 500

@mobile_bp.route('/api/audio/process', methods=['POST'])
def process_audio():
    """Process audio from mobile app."""
    try:
        # Get user ID from token
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        verification = firebase_manager.verify_id_token(token)
        
        if not verification:
            return jsonify({"error": "Invalid token"}), 401
        
        user_id = verification.get('uid')
        
        # Check if audio file is provided
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file provided"}), 400
        
        audio_file = request.files['audio']
        
        # Check processing options
        processing_options = {
            "target_accent": request.form.get('target_accent', 'american'),
            "noise_suppression": request.form.get('noise_suppression', 'true').lower() == 'true',
            "identity_preservation": request.form.get('identity_preservation', 'true').lower() == 'true'
        }
        
        # Save audio file
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"mobile_upload_{user_id}_{timestamp}.wav"
        upload_path = os.path.join('uploads', filename)
        
        os.makedirs('uploads', exist_ok=True)
        audio_file.save(upload_path)
        
        # Process audio
        job_id = f"job_{timestamp}_{str(uuid.uuid4())[:8]}"
        result = audio_processor.process_audio(
            upload_path,
            job_id=job_id,
            target_accent=processing_options["target_accent"],
            noise_suppression=processing_options["noise_suppression"],
            identity_preservation=processing_options["identity_preservation"],
            user_id=user_id
        )
        
        if "error" in result:
            return jsonify({"error": result["error"]}), 500
        
        # Return job information
        return jsonify({
            "success": True,
            "job_id": job_id,
            "status": "processing",
            "estimated_time": result.get("estimated_time", 30)
        })
    
    except Exception as e:
        logger.error(f"Error processing audio: {str(e)}")
        return jsonify({"error": str(e)}), 500

@mobile_bp.route('/api/audio/status/<job_id>', methods=['GET'])
def check_audio_status(job_id):
    """Check status of an audio processing job."""
    try:
        # Get user ID from token
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        verification = firebase_manager.verify_id_token(token)
        
        if not verification:
            return jsonify({"error": "Invalid token"}), 401
        
        user_id = verification.get('uid')
        
        # Check job status
        status = audio_processor.get_job_status(job_id)
        
        return jsonify(status)
    
    except Exception as e:
        logger.error(f"Error checking job status: {str(e)}")
        return jsonify({"error": str(e)}), 500

@mobile_bp.route('/api/audio/result/<job_id>', methods=['GET'])
def get_audio_result(job_id):
    """Get result of an audio processing job."""
    try:
        # Get user ID from token
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        verification = firebase_manager.verify_id_token(token)
        
        if not verification:
            return jsonify({"error": "Invalid token"}), 401
        
        user_id = verification.get('uid')
        
        # Get job result
        result = audio_processor.get_job_result(job_id)
        
        if "error" in result:
            return jsonify({"error": result["error"]}), 500
        
        # Return result
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error getting job result: {str(e)}")
        return jsonify({"error": str(e)}), 500

@mobile_bp.route('/api/audio/jobs', methods=['GET'])
def get_user_jobs():
    """Get user's audio processing jobs."""
    try:
        # Get user ID from token
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        verification = firebase_manager.verify_id_token(token)
        
        if not verification:
            return jsonify({"error": "Invalid token"}), 401
        
        user_id = verification.get('uid')
        
        # Get limit parameter
        limit = request.args.get('limit', 10, type=int)
        
        # Get user jobs
        jobs = audio_processor.get_user_jobs(user_id, limit)
        
        return jsonify({
            "success": True,
            "jobs": jobs
        })
    
    except Exception as e:
        logger.error(f"Error getting user jobs: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Add routes for other features

# Learning Path
@mobile_bp.route('/api/learning/paths', methods=['GET'])
def get_learning_paths():
    """Get available learning paths."""
    try:
        # Get user ID from token
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        verification = firebase_manager.verify_id_token(token)
        
        if not verification:
            return jsonify({"error": "Invalid token"}), 401
        
        user_id = verification.get('uid')
        
        # Import the manager here to avoid circular imports
        from learning_path import get_learning_path_manager
        
        # Get learning paths
        manager = get_learning_path_manager()
        paths = manager.get_all_learning_paths()
        
        # Get user progress
        progress = manager.get_user_progress(user_id)
        
        return jsonify({
            "success": True,
            "learning_paths": paths,
            "user_progress": progress
        })
    
    except Exception as e:
        logger.error(f"Error getting learning paths: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Voice Samples
@mobile_bp.route('/api/samples/search', methods=['GET'])
def search_voice_samples():
    """Search voice samples."""
    try:
        # Get user ID from token
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        verification = firebase_manager.verify_id_token(token)
        
        if not verification:
            return jsonify({"error": "Invalid token"}), 401
        
        user_id = verification.get('uid')
        
        # Get search parameters
        query = request.args.get('query', '')
        accent = request.args.get('accent', '')
        category = request.args.get('category', '')
        limit = request.args.get('limit', 20, type=int)
        
        # Import the manager here to avoid circular imports
        from voice_sample_library import get_voice_sample_library
        
        # Search samples
        manager = get_voice_sample_library()
        
        categories = {}
        if accent:
            categories['accent'] = accent
        
        if category:
            category_parts = category.split(':')
            if len(category_parts) == 2:
                categories[category_parts[0]] = category_parts[1]
        
        samples = manager.search_samples(query, categories, limit=limit)
        
        return jsonify({
            "success": True,
            "samples": samples,
            "count": len(samples)
        })
    
    except Exception as e:
        logger.error(f"Error searching voice samples: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Social Sharing
@mobile_bp.route('/api/social/share', methods=['POST'])
def share_audio():
    """Share an audio clip."""
    try:
        # Get user ID from token
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        verification = firebase_manager.verify_id_token(token)
        
        if not verification:
            return jsonify({"error": "Invalid token"}), 401
        
        user_id = verification.get('uid')
        
        # Get data
        data = request.json
        
        # Validate required fields
        required_fields = ['audio_file', 'title', 'description']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Import the manager here to avoid circular imports
        from social_sharing import get_social_sharing_manager
        
        # Create shareable clip
        manager = get_social_sharing_manager()
        
        clip = manager.create_shareable_clip(
            user_id=user_id,
            audio_file=data['audio_file'],
            title=data['title'],
            description=data['description'],
            accent=data.get('accent', ''),
            metadata=data.get('metadata', {}),
            is_public=data.get('is_public', True)
        )
        
        if "error" in clip:
            return jsonify({"error": clip["error"]}), 500
        
        # Get share links
        share_links = manager.get_social_share_links(clip["share_id"])
        
        # Return result
        return jsonify({
            "success": True,
            "share_id": clip["share_id"],
            "title": clip["title"],
            "description": clip["description"],
            "file_url": clip["file_url"],
            "share_links": share_links
        })
    
    except Exception as e:
        logger.error(f"Error sharing audio: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Add route for registering mobile app with Firebase
@mobile_bp.route('/api/app/register', methods=['POST'])
def register_app():
    """Register a mobile app installation."""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['device_id', 'platform', 'app_version']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Get user ID from token if available
        user_id = None
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if token:
            verification = firebase_manager.verify_id_token(token)
            if verification:
                user_id = verification.get('uid')
        
        # Register app
        app_data = {
            "device_id": data['device_id'],
            "platform": data['platform'],
            "app_version": data['app_version'],
            "user_id": user_id,
            "push_token": data.get('push_token', ''),
            "device_info": data.get('device_info', {}),
            "registered_at": datetime.datetime.now().isoformat()
        }
        
        # Save to Firebase
        result = firebase_manager.save_app_registration(app_data)
        
        return jsonify({
            "success": True,
            "message": "App registered successfully",
            "registration_id": result.get("id", "")
        })
    
    except Exception as e:
        logger.error(f"Error registering app: {str(e)}")
        return jsonify({"error": str(e)}), 500

def register_mobile_routes(app):
    """Register mobile routes with the Flask app."""
    app.register_blueprint(mobile_bp)
    logger.info("Mobile routes registered")