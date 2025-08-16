
# CV Optimizer Pro - Replit Deployment Guide

## Quick Deploy na Replit

### 1. Przygotowanie Bazy Danych
```bash
# W Replit Console uruchom:
python check_config.py
```

### 2. Konfiguracja Environment Variables w Replit
Dodaj w Secrets (🔒):
- `SECRET_KEY`: losowy klucz bezpieczeństwa
- `OPENROUTER_API_KEY`: klucz API do OpenRouter
- `FLASK_ENV`: production

### 3. Uruchomienie Aplikacji
Aplikacja uruchomi się automatycznie przez:
```bash
python app.py
```

### 4. PWA Deployment
Aplikacja jest gotowa jako Progressive Web App:
- Manifest: `/manifest.json`
- Service Worker: `/service-worker.js`
- Ikony PWA w `/static/icons/`

### 5. Mobile Optimization
✅ Responsive design
✅ Touch-friendly interface  
✅ Fast loading on mobile
✅ Offline capabilities

### 6. Production Features
- ✅ Gzip compression
- ✅ Static file caching
- ✅ Database connection pooling
- ✅ Error handling
- ✅ Security headers
- ✅ Mobile-first design

### 7. Monitoring
Sprawdź logi w Replit Console:
```bash
# Sprawdź status aplikacji
curl https://your-repl-name.your-username.repl.co/
```

## Automatic Scaling
Aplikacja skaluje się automatycznie na Replit w zależności od ruchu.

## Troubleshooting
1. Jeśli baza się nie łączy - uruchom `python check_config.py`
2. Jeśli brak API key - sprawdź Secrets w Replit
3. Jeśli błędy CSS - sprawdź czy pliki statyczne są dostępne

To wszystko! 🚀
