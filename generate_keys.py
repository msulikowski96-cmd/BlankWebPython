
#!/usr/bin/env python3
"""
Generator kluczy bezpieczeństwa dla Azure deployment
"""

import secrets
import string

def generate_secret_key(length=50):
    """Generate a secure secret key"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_encryption_key():
    """Generate encryption key"""
    import base64
    key = secrets.token_bytes(32)
    return base64.b64encode(key).decode()

if __name__ == "__main__":
    print("🔑 Generowanie kluczy dla Azure deployment\n")
    
    secret_key = generate_secret_key()
    encryption_key = generate_encryption_key()
    
    print("📋 Skopiuj te wartości do Azure App Settings:")
    print("="*60)
    print(f"SECRET_KEY = {secret_key}")
    print(f"ENCRYPTION_KEY = {encryption_key}")
    print("="*60)
    
    print("\n📝 Application Settings do dodania w Azure Portal:")
    print("1. OPENROUTER_API_KEY = sk-or-v1-your-key-here")
    print("2. STRIPE_SECRET_KEY = sk_test_your-stripe-secret")  
    print("3. VITE_STRIPE_PUBLIC_KEY = pk_test_your-stripe-public")
    print(f"4. SECRET_KEY = {secret_key}")
    print(f"5. ENCRYPTION_KEY = {encryption_key}")
    print("6. FLASK_ENV = production")
    print("7. PORT = 8000")
    print("8. SCM_DO_BUILD_DURING_DEPLOYMENT = true")
    
    print("\n🚀 Gotowe do deploy na Azure!")
