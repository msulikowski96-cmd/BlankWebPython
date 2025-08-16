
# 🚀 CV Optimizer Pro - Azure Deployment Guide

## 📋 Wymagania przed wdrożeniem

### 1. Konta i subskrypcje
- ✅ Konto Microsoft Azure z aktywną subskrypcją
- ✅ Konto OpenRouter (dla AI) - https://openrouter.ai/
- ✅ Konto Stripe (dla płatności) - https://stripe.com/
- ✅ Repozytorium GitHub z kodem

### 2. Klucze API do uzyskania
```bash
# OpenRouter API Key
# 1. Zarejestruj się na https://openrouter.ai/
# 2. Idź do Settings > Keys
# 3. Stwórz nowy klucz: sk-or-v1-...

# Stripe Keys  
# 1. Zarejestruj się na https://stripe.com/
# 2. Idź do Developers > API keys
# 3. Skopiuj: pk_test_... i sk_test_...
```

## 🚀 Kroki wdrożenia na Azure

### Krok 1: Stworzenie App Service
```bash
# W Azure Portal:
1. Utwórz "App Service"
2. Wybierz Python 3.11
3. Wybierz region (Europe West)
4. Plan Basic B1 (wystarczy na start)
```

### Krok 2: Konfiguracja Environment Variables
W Azure Portal → App Service → Configuration → Application Settings:

```env
OPENROUTER_API_KEY = sk-or-v1-your-key-here
STRIPE_SECRET_KEY = sk_test_your-stripe-secret
VITE_STRIPE_PUBLIC_KEY = pk_test_your-stripe-public
SECRET_KEY = wygenerowany-losowy-klucz
FLASK_ENV = production
PORT = 8000
SCM_DO_BUILD_DURING_DEPLOYMENT = true
```

### Krok 3: Deploy z GitHub
```bash
# Azure Portal → App Service → Deployment Center:
1. Wybierz "GitHub"
2. Autoryzuj Azure w GitHub
3. Wybierz repozytorium
4. Wybierz branch: main
5. Kliknij "Save"
```

### Krok 4: Konfiguracja bazy danych (opcjonalne)
```bash
# Dla PostgreSQL na Azure:
1. Utwórz "Azure Database for PostgreSQL"
2. Skopiuj connection string
3. Dodaj do App Settings: DATABASE_URL
```

## 📁 Struktura plików do upload na GitHub

```
cv-optimizer-azure/
├── app.py                    # Główna aplikacja
├── startup.py               # Azure startup script  
├── requirements-azure.txt   # Zależności dla Azure
├── web.config              # IIS configuration
├── .env.azure              # Template zmiennych
├── models.py               # Modele bazy danych
├── forms.py                # Formularze
├── static/                 # Pliki statyczne
├── templates/              # Szablony HTML
├── utils/                  # Narzędzia AI/PDF
└── .github/workflows/      # GitHub Actions
    └── azure-deploy.yml    # Auto-deploy workflow
```

## ⚡ Auto-deployment z GitHub Actions

Po każdym push na main branch:
1. GitHub Actions automatycznie zbuduje aplikację
2. Wykona deploy na Azure App Service  
3. Aplikacja będzie dostępna pod: `https://your-app-name.azurewebsites.net`

## 🔧 Troubleshooting

### Problem: App nie startuje
```bash
# Sprawdź logi w Azure Portal:
App Service → Monitoring → Log stream
```

### Problem: Brak połączenia z bazą
```bash
# Sprawdź connection string:
DATABASE_URL w Application Settings
```

### Problem: Błędy AI
```bash
# Sprawdź klucz OpenRouter:
OPENROUTER_API_KEY w Application Settings
```

## 🎯 Po wdrożeniu

### URLs aplikacji:
- **Production:** `https://your-app-name.azurewebsites.net`
- **Custom domain:** Można skonfigurować w Azure

### Konto developer (darmowy dostęp):
- **Username:** `developer`
- **Password:** `DevAdmin2024!`

### Funkcje gotowe:
- ✅ Upload i analiza CV
- ✅ AI optymalizacja (9.99 PLN)
- ✅ Premium features (29.99 PLN/miesiąc)
- ✅ Stripe payments
- ✅ User management
- ✅ PWA ready

## 💰 Koszty Azure

### Minimalna konfiguracja:
- **App Service B1:** ~15 USD/miesiąc
- **PostgreSQL Basic:** ~20 USD/miesiąc (opcjonalne)
- **Storage:** ~1 USD/miesiąc

### Oszczędności:
- Używaj SQLite zamiast PostgreSQL na start
- Plan B1 wystarcza na 1000+ użytkowników/dzień

## 🔐 Bezpieczeństwo

### Automatycznie skonfigurowane:
- ✅ HTTPS (SSL cert)
- ✅ Environment variables encryption
- ✅ Session security
- ✅ CSRF protection
- ✅ SQL injection protection

---

**🎉 Aplikacja gotowa do produkcji na Azure!**
