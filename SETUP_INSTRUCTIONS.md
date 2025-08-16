
# 🚀 CV Optimizer Pro - Instrukcje Uruchomienia na Replit

## ⚡ Szybkie uruchomienie

1. **Sprawdź konfigurację:**
   ```bash
   python check_config.py
   ```

2. **Ustaw zmienne środowiskowe** w Replit Secrets:
   - `OPENROUTER_API_KEY` - Twój klucz API OpenRouter
   - `STRIPE_SECRET_KEY` - Klucz tajny Stripe (sk_test_...)
   - `VITE_STRIPE_PUBLIC_KEY` - Klucz publiczny Stripe (pk_test_...)

3. **Uruchom aplikację:**
   ```bash
   python app.py
   ```
   lub kliknij przycisk **Run**

## 🔑 Konto Developer (darmowy dostęp)

Po uruchomieniu aplikacji automatycznie zostanie utworzone konto:
- **Username:** `developer`
- **Password:** `DevAdmin2024!`
- **Email:** `dev@cvoptimizer.pro`

To konto ma **pełny dostęp bez płatności**.

## 🌐 Dostęp do aplikacji

Aplikacja uruchomi się na porcie 5000:
- Local: `http://localhost:5000`
- Replit: automatyczny URL w oknie przeglądarki

## 🔧 Rozwiązywanie problemów

### Port już używany
```bash
# Zatrzymaj wszystkie procesy Python
pkill -f python
# Uruchom ponownie
python app.py
```

### Błędy bazy danych
Aplikacja używa SQLite jako fallback - nie wymaga konfiguracji PostgreSQL.

### Brakujące pakiety
```bash
pip install -r requirements.txt
```

## 📋 Status aplikacji

- ✅ **Backend:** Flask + SQLAlchemy
- ✅ **Frontend:** Modern UI z glassmorphism
- ✅ **Płatności:** Stripe integration
- ✅ **AI:** OpenRouter API
- ✅ **Baza danych:** SQLite fallback
- ✅ **PWA:** Manifest + Service Worker

## 🎯 Następne kroki

1. Ustaw zmienne środowiskowe w Replit Secrets
2. Uruchom `python check_config.py`
3. Kliknij **Run** lub `python app.py`
4. Zaloguj się jako `developer` / `DevAdmin2024!`
5. Testuj funkcje aplikacji

**Aplikacja gotowa do użytku!** 🚀
