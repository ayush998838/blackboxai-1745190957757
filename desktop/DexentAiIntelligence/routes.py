import os
import json
import logging
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from app import app, db
from models import User, VoiceProfile, AudioSample, UserSetting, ProcessingJob
from audio_pipeline.noise_suppression import process_noise_suppression
from audio_pipeline.accent_conversion import process_accent_conversion
from config import AUDIO_SAMPLES_DIR, VOICE_PROFILES_DIR, PROCESSED_AUDIO_DIR

# Set up logging
logger = logging.getLogger(__name__)

# Set up login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        
        flash('Invalid username or password', 'danger')
    
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Check if username or email already exists
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Username or email already exists', 'danger')
            return redirect(url_for('index'))
        
        # Create new user
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('index'))
    
    return render_template('index.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    voice_profiles = VoiceProfile.query.filter_by(user_id=current_user.id).all()
    processing_jobs = ProcessingJob.query.filter_by(user_id=current_user.id).order_by(ProcessingJob.created_at.desc()).limit(5).all()
    
    return render_template('profile.html', 
                          user=current_user, 
                          voice_profiles=voice_profiles,
                          processing_jobs=processing_jobs)

@app.route('/settings')
@login_required
def settings():
    user_settings = UserSetting.query.filter_by(user_id=current_user.id).all()
    settings_dict = {setting.setting_key: setting.setting_value for setting in user_settings}
    
    return render_template('settings.html', settings=settings_dict)

@app.route('/update_settings', methods=['POST'])
@login_required
def update_settings():
    for key, value in request.form.items():
        # Skip csrf token
        if key == 'csrf_token':
            continue
            
        # Update or create setting
        setting = UserSetting.query.filter_by(user_id=current_user.id, setting_key=key).first()
        if setting:
            setting.setting_value = value
        else:
            new_setting = UserSetting(user_id=current_user.id, setting_key=key, setting_value=value)
            db.session.add(new_setting)
    
    db.session.commit()
    flash('Settings updated successfully', 'success')
    return redirect(url_for('settings'))

@app.route('/upload_voice_sample', methods=['POST'])
@login_required
def upload_voice_sample():
    if 'audio_file' not in request.files:
        flash('No file part', 'danger')
        return redirect(request.referrer)
    
    file = request.files['audio_file']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(request.referrer)
    
    if file:
        # Create user directory if it doesn't exist
        user_dir = os.path.join(AUDIO_SAMPLES_DIR, str(current_user.id))
        os.makedirs(user_dir, exist_ok=True)
        
        # Save the file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        saved_filename = f"{timestamp}_{filename}"
        file_path = os.path.join(user_dir, saved_filename)
        file.save(file_path)
        
        # Create audio sample record
        sample_type = request.form.get('sample_type', 'training')
        new_sample = AudioSample(
            user_id=current_user.id,
            file_path=file_path,
            sample_type=sample_type,
            duration=float(request.form.get('duration', 0))
        )
        
        db.session.add(new_sample)
        db.session.commit()
        
        flash('Voice sample uploaded successfully', 'success')
    
    return redirect(request.referrer)

@app.route('/create_voice_profile', methods=['POST'])
@login_required
def create_voice_profile():
    name = request.form.get('profile_name')
    description = request.form.get('description', '')
    
    # Check if profile with this name already exists
    existing_profile = VoiceProfile.query.filter_by(user_id=current_user.id, name=name).first()
    if existing_profile:
        flash('A profile with this name already exists', 'danger')
        return redirect(request.referrer)
    
    # Create user directory if it doesn't exist
    user_dir = os.path.join(VOICE_PROFILES_DIR, str(current_user.id))
    os.makedirs(user_dir, exist_ok=True)
    
    # Create embedding path
    embedding_path = os.path.join(user_dir, f"{secure_filename(name)}.pt")
    
    # Create voice profile
    new_profile = VoiceProfile(
        name=name,
        user_id=current_user.id,
        description=description,
        embedding_path=embedding_path
    )
    
    db.session.add(new_profile)
    db.session.commit()
    
    # Trigger background job to generate embedding
    # This would typically be handled by a task queue like Celery
    flash('Voice profile created. Embedding generation will start shortly.', 'success')
    return redirect(request.referrer)

@app.route('/api/process_audio', methods=['POST'])
@login_required
def process_audio():
    try:
        data = request.json
        processing_type = data.get('processing_type')
        input_file = data.get('input_file')
        
        # Create a processing job
        job = ProcessingJob(
            user_id=current_user.id,
            job_type=processing_type,
            status='processing',
            input_file=input_file,
            parameters=json.dumps(data)
        )
        
        db.session.add(job)
        db.session.commit()
        
        # Process based on type
        if processing_type == 'noise_suppression':
            output_file = process_noise_suppression(input_file, job.id)
        elif processing_type == 'accent_conversion':
            target_accent = data.get('target_accent')
            voice_profile_id = data.get('voice_profile_id')
            voice_profile = VoiceProfile.query.get(voice_profile_id)
            
            output_file = process_accent_conversion(
                input_file, 
                target_accent,
                voice_profile.embedding_path if voice_profile else None,
                job.id
            )
        else:
            raise ValueError(f"Unknown processing type: {processing_type}")
        
        # Update job
        job.status = 'completed'
        job.completed_at = datetime.utcnow()
        job.output_file = output_file
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'job_id': job.id,
            'output_file': output_file
        })
    
    except Exception as e:
        logger.error(f"Error processing audio: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/download_processed/<int:job_id>')
@login_required
def download_processed(job_id):
    job = ProcessingJob.query.get_or_404(job_id)
    
    # Security check
    if job.user_id != current_user.id:
        flash('You do not have permission to access this file', 'danger')
        return redirect(url_for('dashboard'))
    
    # Check if job is completed
    if job.status != 'completed' or not job.output_file:
        flash('The requested file is not available', 'danger')
        return redirect(url_for('dashboard'))
    
    return send_file(job.output_file, as_attachment=True)

@app.route('/api/audio_status', methods=['GET'])
@login_required
def audio_status():
    # This endpoint would be called by the frontend to get the status of the audio processing
    # It would typically connect to the virtual microphone system to get real-time status
    
    # For now, we'll return a dummy status
    return jsonify({
        'status': 'active',
        'noise_suppression': True,
        'accent_conversion': False,
        'current_profile': 'Default',
        'audio_level': 0.7
    })

@app.route('/api/toggle_processing', methods=['POST'])
@login_required
def toggle_processing():
    data = request.json
    process_type = data.get('type')
    enabled = data.get('enabled', False)
    
    # This would typically communicate with the virtual microphone system
    # to enable/disable specific processing
    
    return jsonify({
        'status': 'success',
        'type': process_type,
        'enabled': enabled
    })
