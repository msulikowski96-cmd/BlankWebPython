
from cryptography.fernet import Fernet
import os
import base64
from werkzeug.security import generate_password_hash
import secrets

class DataEncryption:
    def __init__(self):
        # Generate or load encryption key
        key = os.environ.get('ENCRYPTION_KEY')
        if not key:
            # Generate new key if not exists
            key = Fernet.generate_key()
            print(f"⚠️  Generated new encryption key: {key.decode()}")
            print("⚠️  Add this to your .env file: ENCRYPTION_KEY={key.decode()}")
        else:
            key = key.encode()
        
        self.cipher = Fernet(key)
    
    def encrypt_text(self, text):
        """Encrypt sensitive text data"""
        if not text:
            return text
        return self.cipher.encrypt(text.encode()).decode()
    
    def decrypt_text(self, encrypted_text):
        """Decrypt sensitive text data"""
        if not encrypted_text:
            return encrypted_text
        try:
            return self.cipher.decrypt(encrypted_text.encode()).decode()
        except Exception:
            return encrypted_text  # Return original if decryption fails
    
    def generate_secure_token(self, length=32):
        """Generate secure random token"""
        return secrets.token_urlsafe(length)

encryption = DataEncryption()
