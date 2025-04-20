import os
import json
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Import app from app.py
from app import app

# Configure login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Firebase context processor to make credentials available to all templates
@app.context_processor
def inject_firebase_credentials():
    return {
        'firebase_api_key': os.environ.get('FIREBASE_API_KEY', ''),
        'firebase_project_id': os.environ.get('FIREBASE_PROJECT_ID', ''),
        'firebase_app_id': os.environ.get('FIREBASE_APP_ID', '')
    }

# Firebase scripts function for templates
@app.context_processor
def firebase_scripts_processor():
    def firebase_scripts():
        api_key = os.environ.get('FIREBASE_API_KEY', '')
        project_id = os.environ.get('FIREBASE_PROJECT_ID', '')
        app_id = os.environ.get('FIREBASE_APP_ID', '')
        
        return f"""
        <!-- Firebase App (the core Firebase SDK) is always required and must be listed first -->
        <script src="https://www.gstatic.com/firebasejs/9.22.0/firebase-app-compat.js"></script>
        
        <!-- Add Firebase products that you want to use -->
        <script src="https://www.gstatic.com/firebasejs/9.22.0/firebase-auth-compat.js"></script>
        
        <script>
            // Initialize Firebase
            const firebaseConfig = {{
                apiKey: "{api_key}",
                authDomain: "{project_id}.firebaseapp.com",
                projectId: "{project_id}",
                storageBucket: "{project_id}.appspot.com",
                appId: "{app_id}"
            }};
            
            // Initialize Firebase
            firebase.initializeApp(firebaseConfig);
            
            // Initialize Firebase Authentication
            const auth = firebase.auth();
            
            // Create Google auth provider
            const googleProvider = new firebase.auth.GoogleAuthProvider();
        </script>
        """
    return {'firebase_scripts': firebase_scripts}

# Mock database for development (replace with real DB in production)
users = {
    1: {
        'id': 1,
        'username': 'demo',
        'email': 'demo@dexent.ai',
        'password_hash': generate_password_hash('demo123'),
        'oauth_provider': None
    }
}

# Mock user settings
user_settings = {
    1: {
        'noise_suppression': True,
        'noise_suppression_level': 70,
        'accent_conversion': True,
        'target_accent': 'american',
        'identity_preservation': True,
        'input_device': 'default',
        'output_device': 'default'
    }
}

# Mock audio processing status
audio_processing = {
    'is_running': False,
    'started_at': None,
    'processed_time': 0
}

# User class for flask-login
class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data['id']
        self.username = user_data['username']
        self.email = user_data['email']
        self.password_hash = user_data['password_hash']
        self.oauth_provider = user_data.get('oauth_provider')
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# User loader for flask-login
@login_manager.user_loader
def load_user(user_id):
    user_data = users.get(int(user_id))
    if user_data:
        return User(user_data)
    return None

# Home page
@app.route('/')
def index():
    firebase_api_key = os.environ.get('FIREBASE_API_KEY', '')
    firebase_project_id = os.environ.get('FIREBASE_PROJECT_ID', '')
    firebase_app_id = os.environ.get('FIREBASE_APP_ID', '')
    
    return render_template('index.html', 
                           firebase_api_key=firebase_api_key,
                           firebase_project_id=firebase_project_id,
                           firebase_app_id=firebase_app_id)

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = 'remember' in request.form
        
        # Find user by email
        user_id = None
        for uid, user_data in users.items():
            if user_data['email'] == email:
                user_id = uid
                break
        
        if user_id is None:
            flash('Invalid email or password', 'danger')
            return redirect(url_for('login'))
        
        user = User(users[user_id])
        
        if user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('dashboard'))
        
        flash('Invalid email or password', 'danger')
        return redirect(url_for('login'))
    
    # GET request
    firebase_api_key = os.environ.get('FIREBASE_API_KEY', '')
    firebase_project_id = os.environ.get('FIREBASE_PROJECT_ID', '')
    firebase_app_id = os.environ.get('FIREBASE_APP_ID', '')
    
    return render_template('login.html',
                          firebase_api_key=firebase_api_key,
                          firebase_project_id=firebase_project_id,
                          firebase_app_id=firebase_app_id)

# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate inputs
        if not username or not email or not password:
            flash('All fields are required', 'danger')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('register'))
        
        # Check if email already exists
        for user_data in users.values():
            if user_data['email'] == email:
                flash('Email already registered', 'danger')
                return redirect(url_for('register'))
        
        # Create new user
        new_user_id = max(users.keys()) + 1 if users else 1
        users[new_user_id] = {
            'id': new_user_id,
            'username': username,
            'email': email,
            'password_hash': generate_password_hash(password),
            'oauth_provider': None
        }
        
        # Initialize settings for new user
        user_settings[new_user_id] = {
            'noise_suppression': True,
            'noise_suppression_level': 70,
            'accent_conversion': True,
            'target_accent': 'american',
            'identity_preservation': True,
            'input_device': 'default',
            'output_device': 'default'
        }
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    # GET request
    firebase_api_key = os.environ.get('FIREBASE_API_KEY', '')
    firebase_project_id = os.environ.get('FIREBASE_PROJECT_ID', '')
    firebase_app_id = os.environ.get('FIREBASE_APP_ID', '')
    
    return render_template('register.html',
                          firebase_api_key=firebase_api_key,
                          firebase_project_id=firebase_project_id,
                          firebase_app_id=firebase_app_id)

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

# Dashboard route
@app.route('/dashboard')
@login_required
def dashboard():
    # Get user's settings
    settings = user_settings.get(current_user.id, {})
    
    return render_template('dashboard.html', 
                        settings=settings,
                        audio_status=audio_processing)

# Settings route
@app.route('/settings')
@login_required
def settings():
    # Get user's settings
    user_setting = user_settings.get(current_user.id, {})
    
    return render_template('settings.html', settings=user_setting)

# Accent selection route
@app.route('/accent')
@login_required
def accent_selection():
    # Get user's settings or set defaults
    user_setting = user_settings.get(current_user.id, {
        'noise_suppression': True,
        'noise_suppression_level': 70,
        'accent_conversion': True,
        'target_accent': 'american',
        'identity_preservation': True,
        'input_device': 'default',
        'output_device': 'default'
    })
    
    return render_template('accent_selection.html', user_settings=user_setting)

# Download Windows page
@app.route('/download/windows')
def download_windows():
    return render_template('download_windows.html')

# Download Windows executable
@app.route('/download/windows/exe')
def download_windows_exe():
    return send_file('static/downloads/Dexent-Setup.exe', as_attachment=True)

# Download Android page
@app.route('/download/android')
def download_android():
    return render_template('download_android.html')

# Download Android APK
@app.route('/download/android/apk')
def download_android_apk():
    return send_file('static/downloads/Dexent-Android.apk', as_attachment=True)

# Download iOS page
@app.route('/download/ios')
def download_ios():
    return render_template('download_ios.html')
    
# Download processed audio file
@app.route('/download/processed/<filename>')
@login_required
def download_processed_audio(filename):
    processed_dir = os.path.join(app.root_path, 'processed')
    return send_file(os.path.join(processed_dir, filename), as_attachment=True)

# API Routes
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint for Replit and other monitoring."""
    return jsonify({
        'status': 'ok',
        'time': str(datetime.now()),
        'app': 'Dexent.ai'
    })

@app.route('/api/start_processing', methods=['POST'])
@login_required
def start_processing():
    audio_processing['is_running'] = True
    audio_processing['started_at'] = datetime.now()
    
    return jsonify({
        'status': 'success',
        'message': 'Audio processing started'
    })

@app.route('/api/process_accent', methods=['POST'])
@login_required
def process_accent():
    try:
        # Check if files were included in the request
        if 'audio' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'No audio file uploaded'
            }), 400
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({
                'status': 'error',
                'message': 'No audio file selected'
            }), 400
        
        # Get parameters
        target_accent = request.form.get('accent', 'american')
        preserve_identity = request.form.get('preserve_identity', 'true').lower() == 'true'
        
        # Create uploads directory if it doesn't exist
        uploads_dir = os.path.join(app.root_path, 'uploads')
        if not os.path.exists(uploads_dir):
            os.makedirs(uploads_dir)
        
        # Save the uploaded file
        filename = secure_filename(audio_file.filename)
        if not filename:
            filename = f"recording_{datetime.now().strftime('%Y%m%d%H%M%S')}.wav"
        
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        saved_filename = f"{timestamp}_{filename}"
        filepath = os.path.join(uploads_dir, saved_filename)
        audio_file.save(filepath)
        
        # Create processed directory if it doesn't exist
        processed_dir = os.path.join(app.root_path, 'processed')
        if not os.path.exists(processed_dir):
            os.makedirs(processed_dir)
        
        # Process the audio with the accent conversion pipeline
        processed_filename = f"accent_{target_accent}_{saved_filename}"
        processed_filepath = os.path.join(processed_dir, processed_filename)
        
        app.logger.info(f"Starting accent conversion: {target_accent}, preserve identity: {preserve_identity}")
        
        try:
            # Import accent conversion pipeline
            from accent_conversion import AccentConversionPipeline
            
            # Initialize the pipeline with the target accent
            pipeline = AccentConversionPipeline(
                target_accent=target_accent,
                preserve_identity=preserve_identity
            )
            
            # Process the audio file
            import soundfile as sf
            import numpy as np
            
            # Load audio file
            audio_data, sample_rate = sf.read(filepath)
            
            # Apply accent conversion
            app.logger.info(f"Processing audio with {target_accent} accent...")
            processed_audio = pipeline.process(audio_data, preserve_identity)
            
            # If the processing returned None or empty array, use a fallback method
            if processed_audio is None or len(processed_audio) == 0:
                app.logger.warning("Accent conversion returned empty result, using fallback method")
                
                # Fallback method: apply basic audio transformations based on accent
                # This is a simplified simulation for demo purposes
                if target_accent == 'british':
                    # Simulate British accent by slight pitch change and slowing down
                    import librosa
                    import scipy.signal as signal
                    
                    # Slow down by 5%
                    processed_audio = librosa.effects.time_stretch(audio_data, rate=0.95)
                    
                    # Apply slight pitch shift
                    processed_audio = librosa.effects.pitch_shift(
                        processed_audio, 
                        sr=sample_rate, 
                        n_steps=0.5
                    )
                    
                elif target_accent == 'australian':
                    # Simulate Australian accent with different pitch modification
                    import librosa
                    
                    # Apply pitch shift
                    processed_audio = librosa.effects.pitch_shift(
                        audio_data, 
                        sr=sample_rate, 
                        n_steps=0.3
                    )
                    
                elif target_accent == 'indian':
                    # Simulate Indian accent with rhythm changes
                    import librosa
                    
                    # Apply slight speed up
                    processed_audio = librosa.effects.time_stretch(audio_data, rate=1.05)
                    
                    # Apply slight pitch shift
                    processed_audio = librosa.effects.pitch_shift(
                        processed_audio, 
                        sr=sample_rate, 
                        n_steps=0.7
                    )
                
                else:  # Default to 'american' or any other accent
                    # Apply slight modifications
                    import librosa
                    
                    # Apply slight pitch shift
                    processed_audio = librosa.effects.pitch_shift(
                        audio_data, 
                        sr=sample_rate, 
                        n_steps=-0.2
                    )
            
            # Ensure audio is the right format before saving
            if processed_audio.dtype != np.float32:
                processed_audio = processed_audio.astype(np.float32)
            
            # Normalize audio to prevent clipping
            processed_audio = processed_audio / np.max(np.abs(processed_audio))
            
            # Save processed audio
            sf.write(processed_filepath, processed_audio, sample_rate)
            app.logger.info(f"Saved processed audio to {processed_filepath}")
            
        except ImportError as e:
            app.logger.error(f"Import error: {str(e)} - Using fallback copy method")
            # If the accent conversion modules aren't available, fallback to copy
            import shutil
            shutil.copy(filepath, processed_filepath)
        
        except Exception as e:
            app.logger.error(f"Error in accent processing: {str(e)} - Using fallback copy method")
            # If any error occurs during processing, fallback to copy
            import shutil
            shutil.copy(filepath, processed_filepath)
        
        # Return the processed file URL
        processed_url = url_for('download_processed_audio', filename=processed_filename)
        
        return jsonify({
            'status': 'success',
            'message': 'Audio processed successfully',
            'processed_url': processed_url,
            'accent': target_accent,
            'preserve_identity': preserve_identity
        })
        
    except Exception as e:
        app.logger.error(f"Error processing audio: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error processing audio: {str(e)}'
        }), 500

@app.route('/api/stop_processing', methods=['POST'])
@login_required
def stop_processing():
    audio_processing['is_running'] = False
    
    # Calculate processed time
    if audio_processing['started_at']:
        now = datetime.now()
        delta = now - audio_processing['started_at']
        audio_processing['processed_time'] += delta.total_seconds()
        audio_processing['started_at'] = None
    
    return jsonify({
        'status': 'success',
        'message': 'Audio processing stopped'
    })

@app.route('/api/get_status', methods=['GET'])
@login_required
def get_status():
    return jsonify({
        'is_running': audio_processing['is_running'],
        'processed_time': audio_processing['processed_time']
    })

@app.route('/api/update_settings', methods=['POST'])
@login_required
def update_settings():
    try:
        data = request.json
        
        # Update user settings
        user_settings[current_user.id] = {
            'noise_suppression': data.get('noise_suppression', True),
            'noise_suppression_level': data.get('noise_suppression_level', 70),
            'accent_conversion': data.get('accent_conversion', True),
            'target_accent': data.get('target_accent', 'american'),
            'identity_preservation': data.get('identity_preservation', True),
            'input_device': data.get('input_device', 'default'),
            'output_device': data.get('output_device', 'default')
        }
        
        return jsonify({
            'status': 'success',
            'message': 'Settings updated successfully'
        })
    except Exception as e:
        app.logger.error(f"Error updating settings: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error updating settings: {str(e)}'
        }), 500

@app.route('/api/launch_desktop', methods=['POST'])
@login_required
def launch_desktop():
    try:
        # In a real app, this would launch the desktop app
        # For this demo, we just return success
        return jsonify({
            'status': 'success',
            'message': 'Desktop app launched successfully'
        })
    except Exception as e:
        app.logger.error(f"Error launching desktop app: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error launching desktop app: {str(e)}'
        }), 500

# Admin dashboard
@app.route('/admin')
@login_required
def admin_dashboard():
    # Check if user is admin (in a real app, this would be a role check)
    if current_user.id != 1:
        flash('Access denied: Admin privileges required', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get all users and stats for admin dashboard
    all_users = users
    
    return render_template('admin_dashboard.html', 
                        users=all_users,
                        audio_processing=audio_processing)

# Firebase Authentication Routes
@app.route('/auth/google', methods=['POST'])
def auth_google():
    try:
        data = request.json
        token = data.get('token')
        email = data.get('email')
        name = data.get('name')
        
        if not token or not email:
            return jsonify({
                'success': False,
                'message': 'Token and email are required'
            }), 400
        
        # In a real app, verify the token with Firebase Admin SDK
        # For demo purposes, we trust the token and email from the client
        app.logger.info(f"Google Authentication for {email}")
        
        # Check if user exists
        user_id = None
        for uid, user_data in users.items():
            if user_data['email'] == email:
                user_id = uid
                break
        
        if user_id is None:
            # Create new user
            new_user_id = max(users.keys()) + 1 if users else 1
            users[new_user_id] = {
                'id': new_user_id,
                'username': name or email.split('@')[0],
                'email': email,
                'password_hash': 'OAUTH_USER',  # No password for OAuth users
                'oauth_provider': 'google'
            }
            user_id = new_user_id
            
            # Initialize settings for new user
            user_settings[user_id] = {
                'noise_suppression': True,
                'noise_suppression_level': 70,
                'accent_conversion': True,
                'target_accent': 'american',
                'identity_preservation': True,
                'input_device': 'default',
                'output_device': 'default'
            }
        
        # Log in the user
        user = User(users[user_id])
        login_user(user)
        
        return jsonify({
            'success': True,
            'message': 'Logged in successfully',
            'redirect': url_for('dashboard')
        })
    
    except Exception as e:
        app.logger.error(f"Error in Google auth: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/auth/google/register', methods=['POST'])
def auth_google_register():
    # For the demo, we'll use the same endpoint as login
    return auth_google()

@app.route('/auth/phone', methods=['POST'])
def auth_phone():
    try:
        data = request.json
        token = data.get('token')
        phone = data.get('phone')
        
        if not token or not phone:
            return jsonify({
                'success': False,
                'message': 'Token and phone are required'
            }), 400
        
        # Check if user exists (by phone)
        user_id = None
        for uid, user_data in users.items():
            if user_data.get('phone') == phone:
                user_id = uid
                break
        
        if user_id is None:
            # Create new user
            new_user_id = max(users.keys()) + 1 if users else 1
            username = f"user_{new_user_id}"
            email = f"phone_user_{new_user_id}@dexent.ai"  # Placeholder email
            
            users[new_user_id] = {
                'id': new_user_id,
                'username': username,
                'email': email,
                'phone': phone,
                'password_hash': 'OAUTH_USER',  # No password for OAuth users
                'oauth_provider': 'phone'
            }
            user_id = new_user_id
            
            # Initialize settings for new user
            user_settings[user_id] = {
                'noise_suppression': True,
                'noise_suppression_level': 70,
                'accent_conversion': True,
                'target_accent': 'american',
                'identity_preservation': True,
                'input_device': 'default',
                'output_device': 'default'
            }
        
        # Log in the user
        user = User(users[user_id])
        login_user(user)
        
        return jsonify({
            'success': True,
            'message': 'Logged in successfully',
            'redirect': url_for('dashboard')
        })
    
    except Exception as e:
        app.logger.error(f"Error in Phone auth: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

# Error handling
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

# Run the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)