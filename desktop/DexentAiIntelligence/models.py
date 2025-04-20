from app import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    oauth_provider = db.Column(db.String(32))

class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    voice_sample_path = db.Column(db.String(255))
    settings = db.relationship('UserSettings', backref='profile', lazy=True, uselist=False)

class UserSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('user_profile.id'), nullable=False)
    audio_processing_enabled = db.Column(db.Boolean, default=True)
    noise_suppression_enabled = db.Column(db.Boolean, default=True)
    noise_suppression_level = db.Column(db.Integer, default=70)
    accent_conversion_enabled = db.Column(db.Boolean, default=True)
    target_accent = db.Column(db.String(32), default='american')
    identity_preservation_enabled = db.Column(db.Boolean, default=True)
    input_device = db.Column(db.String(64), default='default')
    output_device = db.Column(db.String(64), default='default')