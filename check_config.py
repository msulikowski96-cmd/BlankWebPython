
#!/usr/bin/env python3
"""
CV Optimizer Pro - Configuration Checker
Sprawdza czy wszystkie wymagane komponenty są dostępne
"""

import os
import sys

def check_env_vars():
    """Check environment variables"""
    print("🔍 Sprawdzanie zmiennych środowiskowych...")
    
    required_vars = {
        'OPENROUTER_API_KEY': 'Klucz API OpenRouter',
        'STRIPE_SECRET_KEY': 'Klucz tajny Stripe', 
        'VITE_STRIPE_PUBLIC_KEY': 'Klucz publiczny Stripe'
    }
    
    optional_vars = {
        'DATABASE_URL': 'URL bazy danych (opcjonalne - SQLite jako fallback)',
        'SESSION_SECRET': 'Klucz sesji (generowany automatycznie)'
    }
    
    all_good = True
    
    for var, desc in required_vars.items():
        if os.environ.get(var):
            print(f"✅ {var}: OK")
        else:
            print(f"❌ {var}: BRAK - {desc}")
            all_good = False
    
    for var, desc in optional_vars.items():
        if os.environ.get(var):
            print(f"✅ {var}: OK")
        else:
            print(f"⚠️  {var}: BRAK - {desc}")
    
    return all_good

def check_imports():
    """Check if all required packages can be imported"""
    print("\n🔍 Sprawdzanie pakietów Python...")
    
    packages = [
        'flask', 'flask_sqlalchemy', 'flask_login', 'flask_bcrypt',
        'stripe', 'openai', 'requests', 'reportlab', 'beautifulsoup4'
    ]
    
    all_good = True
    
    for package in packages:
        try:
            __import__(package)
            print(f"✅ {package}: OK")
        except ImportError:
            print(f"❌ {package}: BRAK")
            all_good = False
    
    return all_good

def main():
    print("🚀 CV Optimizer Pro - Sprawdzanie konfiguracji\n")
    
    env_ok = check_env_vars()
    imports_ok = check_imports()
    
    print("\n" + "="*50)
    
    if env_ok and imports_ok:
        print("✅ Konfiguracja kompletna! Aplikacja gotowa do uruchomienia.")
        print("🚀 Uruchom aplikację: python app.py")
    else:
        print("❌ Problemy z konfiguracją:")
        if not env_ok:
            print("   • Brakujące zmienne środowiskowe")
        if not imports_ok:
            print("   • Brakujące pakiety Python")
        print("\n📝 Sprawdź plik .env.example dla przykładowych wartości")

if __name__ == '__main__':
    main()
