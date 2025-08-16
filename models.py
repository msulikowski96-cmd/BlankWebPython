
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import json

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    login_count = db.Column(db.Integer, default=0)
    active = db.Column(db.Boolean, default=True, nullable=False)
    premium_until = db.Column(db.DateTime)
    stripe_customer_id = db.Column(db.String(100))
    stripe_session_id = db.Column(db.String(200))
    
    # Relationships
    cv_uploads = db.relationship('CVUpload', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, username=None, email=None, first_name=None, last_name=None, **kwargs):
        """Initialize User with keyword arguments"""
        super().__init__(**kwargs)
        if username:
            self.username = username
        if email:
            self.email = email
        if first_name:
            self.first_name = first_name
        if last_name:
            self.last_name = last_name
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    def is_premium_active(self):
        """Check if user has active premium subscription"""
        if not self.premium_until:
            return False
        return datetime.utcnow() < self.premium_until
    
    def activate_premium(self, months=1):
        """Activate premium subscription for specified months"""
        if self.premium_until and self.premium_until > datetime.utcnow():
            # Extend existing premium
            self.premium_until += timedelta(days=30 * months)
        else:
            # Start new premium
            self.premium_until = datetime.utcnow() + timedelta(days=30 * months)
    
    def get_full_name(self):
        """Get user's full name or username as fallback"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def update_login(self):
        """Update login statistics"""
        self.last_login = datetime.utcnow()
        self.login_count = (self.login_count or 0) + 1
    
    def is_developer(self):
        """Check if user is developer"""
        return self.username == 'developer'
    
    @property
    def is_active(self):
        """Override UserMixin is_active property"""
        return self.active
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.get_full_name(),
            'is_premium': self.is_premium_active(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
    
    def __repr__(self):
        return f'<User {self.username}>'

class CVUpload(db.Model):
    __tablename__ = 'cv_uploads'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_text = db.Column(db.Text, nullable=False)
    job_title = db.Column(db.String(200))
    job_description = db.Column(db.Text)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    analysis_results = db.relationship('AnalysisResult', backref='cv_upload', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<CVUpload {self.filename}>'

class AnalysisResult(db.Model):
    __tablename__ = 'analysis_results'
    
    id = db.Column(db.Integer, primary_key=True)
    cv_upload_id = db.Column(db.Integer, db.ForeignKey('cv_uploads.id'), nullable=False)
    analysis_type = db.Column(db.String(50), nullable=False)
    result_data = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_result_json(self):
        """Parse result_data as JSON"""
        try:
            return json.loads(self.result_data)
        except json.JSONDecodeError:
            return {}
    
    def __repr__(self):
        return f'<AnalysisResult {self.analysis_type}>'
