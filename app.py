import os
import logging
from tempfile import mkdtemp
from dotenv import load_dotenv
from collections import defaultdict

# Load environment variables from .env file - with override
load_dotenv(override=True)

# Verify critical environment variables are loaded
def verify_env_vars():
    """Verify that all critical environment variables are loaded"""
    critical_vars = [
        'OPENROUTER_API_KEY',
        'STRIPE_SECRET_KEY', 
        'SECRET_KEY',
        'DATABASE_URL'
    ]
    
    missing_vars = []
    for var in critical_vars:
        value = os.environ.get(var)
        if not value or value.startswith('TWÓJ_') or len(value.strip()) < 10:
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ BŁĄD: Brakujące lub niepoprawne zmienne środowiskowe: {missing_vars}")
        print("🔧 Sprawdź plik .env i ustaw prawdziwe wartości!")
        return False
    
    print("✅ Wszystkie krytyczne zmienne środowiskowe są ustawione")
    return True

# Verify environment on startup
env_check_passed = verify_env_vars()

from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, session, flash, redirect, url_for
from werkzeug.utils import secure_filename
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
import uuid
import stripe
import json
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import io
import base64
from datetime import datetime
from models import db, User, CVUpload, AnalysisResult
from forms import LoginForm, RegistrationForm, UserProfileForm, ChangePasswordForm
from utils.pdf_extraction import extract_text_from_pdf
from utils.openrouter_api import (
    optimize_cv, generate_recruiter_feedback, generate_cover_letter,
    analyze_job_url, ats_optimization_check, generate_interview_questions,
    analyze_cv_strengths, analyze_cv_score, analyze_keywords_match,
    check_grammar_and_style, optimize_for_position, generate_interview_tips)
from utils.rate_limiter import rate_limit
from utils.encryption import encryption
from utils.security_middleware import security_middleware
from utils.notifications import notification_system
from utils.analytics import analytics
from utils.cv_validator import cv_validator

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Load all configuration from environment variables
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY", "dev-super-secret-key-fallback"),
    SESSION_SECRET=os.environ.get("SESSION_SECRET", os.environ.get("SECRET_KEY", "dev-super-secret-key-fallback")),
    FLASK_ENV=os.environ.get("FLASK_ENV", "production"),
    DEBUG=os.environ.get("DEBUG", "False").lower() == "true",
    PORT=int(os.environ.get("PORT", 5000)),
    MAX_CONTENT_LENGTH=int(os.environ.get("MAX_CONTENT_LENGTH", 16 * 1024 * 1024)),
)

app.secret_key = app.config["SECRET_KEY"]

# Enhanced session security with size optimization
app.config.update(
    SESSION_COOKIE_SECURE=os.environ.get("FLASK_ENV", "production") == "production",  # True in production with HTTPS
    SESSION_COOKIE_HTTPONLY=True,  # No JavaScript access
    SESSION_COOKIE_SAMESITE='Lax',  # CSRF protection
    PERMANENT_SESSION_LIFETIME=timedelta(hours=24),  # Session timeout
    SESSION_COOKIE_NAME='cv_optimizer_session',
    SECRET_KEY=os.environ.get("SESSION_SECRET",
                              "dev-super-secret-key-for-sessions-12345"))

# Database configuration
database_url = os.environ.get('DATABASE_URL')
if not database_url:
    # Fallback to SQLite for development - use absolute path for Replit
    import tempfile
    db_dir = os.path.join(os.getcwd(), 'database')
    os.makedirs(db_dir, exist_ok=True)
    database_url = f'sqlite:///{os.path.join(db_dir, "cv_optimizer.db")}'
    logger.warning(f"Using SQLite database: {database_url}")

# Fix for PostgreSQL URL compatibility
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'pool_timeout': 20,
    'pool_size': 10,
    'max_overflow': 20
}

# Initialize extensions
db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Zaloguj się, aby uzyskać dostęp do tej strony.'
login_manager.login_message_category = 'info'

# Initialize security middleware
security_middleware.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    try:
        if not user_id:
            return None

        user = db.session.get(User, int(user_id))
        if user and user.is_active:
            return user
        return None
    except (ValueError, TypeError):
        return None
    except Exception as e:
        logger.error(f"Error loading user {user_id}: {str(e)}")
        return None


# Session management functions removed - using standard Flask-Login

# Stripe configuration - ładowanie z .env
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

# Verify Stripe configuration
if not stripe.api_key or len(stripe.api_key) < 20:
    logger.warning("⚠️ STRIPE_SECRET_KEY nie jest poprawnie ustawiony w .env")
else:
    logger.info("✅ Stripe API key załadowany poprawnie")

# Configuration for file uploads - z zmiennych środowiskowych
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', mkdtemp())
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
logger.info(f"📁 Upload folder: {UPLOAD_FOLDER}")


def allowed_file(filename):
    return '.' in filename and filename.rsplit(
        '.', 1)[1].lower() in ALLOWED_EXTENSIONS


def add_watermark_to_cv(cv_text):
    """
    Dodaj znak wodny do CV dla niepłacących użytkowników
    """
    watermark = "\n\n" + "=" * 60 + "\n"
    watermark += "🔒 WERSJA DEMO - CV OPTIMIZER PRO\n"
    watermark += "Aby otrzymać pełną wersję CV bez znaku wodnego,\n"
    watermark += "dokonaj płatności 9,99 PLN\n"
    watermark += "=" * 60 + "\n"

    # Dodaj znak wodny na początku i na końcu
    watermarked_cv = watermark + cv_text + watermark

    return watermarked_cv


def optimize_session_data():
    """
    Optymalizuj dane w sesji, aby zmieścić się w limicie 4000 bajtów
    """
    # Lista kluczy do skrócenia/usunięcia
    keys_to_optimize = [
        'cv_text', 'original_cv_text', 'last_optimized_cv', 'cv_data',
        'pending_ai_cv_data', 'ai_generated_cv'
    ]

    for key in keys_to_optimize:
        if key in session:
            value = session[key]

            # Jeśli to tekst, skróć do maksymalnie 1000 znaków
            if isinstance(value, str) and len(value) > 1000:
                session[key] = value[:1000] + "...[skrócono]"

            # Jeśli to słownik, zachowaj tylko kluczowe informacje
            elif isinstance(value, dict):
                if key == 'cv_data':
                    # Zachowaj tylko podstawowe informacje z CV
                    optimized = {
                        'firstName': value.get('firstName', ''),
                        'lastName': value.get('lastName', ''),
                        'email': value.get('email', ''),
                        'jobTitle': value.get('jobTitle', '')
                    }
                    session[key] = optimized

    # Usuń stare, nieużywane klucze
    old_keys = [
        'large_cv_analysis', 'full_job_description', 'detailed_analysis'
    ]
    for old_key in old_keys:
        session.pop(old_key, None)


def clean_session_before_new_data():
    """
    Wyczyść sesję przed dodaniem nowych danych - zachowaj Flask-Login
    """
    # Zachowaj kluczowe informacje Flask-Login i aplikacji
    keys_to_keep = [
        '_user_id', '_fresh', 'csrf_token', 'payment_verified', 'cv_upload_id',
        'cv_builder_paid', 'user_just_logged_in', 'logged_in_username',
        'user_id'
    ]

    # Usuń tylko duże dane, nie podstawowe informacje o użytkowniku
    keys_to_remove = [
        'cv_text', 'original_cv_text', 'last_optimized_cv', 'cv_data',
        'pending_ai_cv_data', 'ai_generated_cv', 'large_cv_analysis',
        'full_job_description', 'detailed_analysis'
    ]

    # Iterate through the session keys and remove those not in keys_to_keep AND are in keys_to_remove
    for key in list(session.keys()):  # Iterate over a copy of the keys
        if key not in keys_to_keep and key in keys_to_remove:
            session.pop(key)


def parse_ai_json_response(ai_result):
    """
    Parse JSON response from AI, handling various formats
    For optimize_cv function, return clean CV text directly
    """
    import json
    try:
        logger.debug(f"AI result before parsing: {ai_result[:200]}...")

        # Check if it's already clean CV text (not JSON)
        if not ('{' in ai_result and '}' in ai_result):
            logger.debug(
                "AI result appears to be clean CV text, returning as-is")
            return ai_result

        # Clean AI result - remove markdown formatting if present
        clean_result = ai_result
        if '```json' in clean_result:
            json_start = clean_result.find('```json') + 7
            json_end = clean_result.find('```', json_start)
            if json_end != -1:
                clean_result = clean_result[json_start:json_end].strip()
        elif '{' in clean_result and '}' in clean_result:
            json_start = clean_result.find('{')
            json_end = clean_result.rfind('}') + 1
            clean_result = clean_result[json_start:json_end]

        parsed_result = json.loads(clean_result)
        optimized_cv = parsed_result.get('optimized_cv', ai_result)
        logger.debug(
            f"Successfully parsed AI response, extracted optimized_cv")
        return optimized_cv

    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(
            f"Failed to parse AI response as JSON, returning original: {e}")
        return ai_result


@app.before_request
def monitor_session_size():
    """
    Monitoruj rozmiar sesji przed każdym requestem
    """
    try:
        import pickle
        session_size = len(pickle.dumps(dict(session)))

        # Jeśli sesja zbliża się do limitu, optymalizuj
        if session_size > 9500:  # 9.5KB - ostrzeżenie
            logger.warning(
                f"Sesja zbliża się do limitu: {session_size} bajtów")
            optimize_session_data()

        # Jeśli nadal za duża, wyczyść
        if session_size > 10000:  # 10KB - wymuszenie czyszczenia
            logger.error(
                f"Sesja przekracza limit: {session_size} bajtów - wymuszam czyszczenie"
            )
            clean_session_before_new_data()

    except Exception as e:
        logger.error(f"Błąd podczas monitorowania sesji: {e}")


@app.route('/')
def index():
    """Main index route"""
    try:
        # Initialize user stats
        user_stats = {
            'total_uploads': 0,
            'total_analyses': 0,
            'user_level': 'Początkujący',
            'improvement_score': 0
        }

        # Calculate user statistics if authenticated
        if current_user.is_authenticated:
            try:
                user_cvs = CVUpload.query.filter_by(
                    user_id=current_user.id).all()
                total_analyses = sum(
                    len(cv.analysis_results) for cv in user_cvs)

                user_stats = {
                    'total_uploads': len(user_cvs),
                    'total_analyses': total_analyses,
                    'user_level': get_user_level(len(user_cvs)),
                    'improvement_score': min(95, 20 + total_analyses * 8)
                }
            except Exception as e:
                logger.error(f"Error calculating user stats: {str(e)}")

        # Prepare template context
        template_context = {'user_stats': user_stats}

        # Add debug info only for developer
        if current_user.is_authenticated and hasattr(
                current_user,
                'username') and current_user.username == 'developer':
            template_context['debug_info'] = {
                'is_authenticated': current_user.is_authenticated,
                'username': current_user.username,
                'session_user': session.get('logged_in_username')
            }

        return render_template('clean-index.html', **template_context)

    except Exception as e:
        logger.error(f"Error in index route: {str(e)}")
        # Return simple error page without breaking
        return render_template('clean-index.html',
                               user_stats={
                                   'total_uploads': 0,
                                   'total_analyses': 0,
                                   'user_level': 'Początkujący',
                                   'improvement_score': 0
                               })


def get_user_level(cv_count):
    """Determine user level based on CV uploads"""
    if cv_count >= 5:
        return 'Diamond 💎'
    elif cv_count >= 3:
        return 'Gold 🥇'
    elif cv_count >= 1:
        return 'Silver 🥈'
    else:
        return 'Bronze 🥉'


@app.route('/test')
def test():
    """Simple test route"""
    return "<h1>✅ Aplikacja działa!</h1><p><a href='/'>Strona główna</a> | <a href='/login'>Logowanie</a></p>"


@app.route('/ads.txt')
def ads_txt():
    """Serve ads.txt file for Google AdSense verification"""
    from flask import send_from_directory
    return send_from_directory('static', 'ads.txt', mimetype='text/plain')


@app.route('/manifest.json')
def manifest():
    """Serve PWA manifest file"""
    from flask import send_from_directory
    return send_from_directory('.', 'manifest.json')


@app.route('/service-worker.js')
def service_worker():
    """Serve service worker file"""
    from flask import send_from_directory
    return send_from_directory('.',
                               'service-worker.js',
                               mimetype='application/javascript')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login route"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()

    if form.validate_on_submit():
        username_or_email = form.username_or_email.data.strip() if form.username_or_email.data else ''
        password = form.password.data

        print(f"🔍 Login attempt: {username_or_email}")

        # Find user by username or email
        user = User.query.filter(
            (db.func.lower(User.username) == username_or_email.lower()) |
            (db.func.lower(User.email) == username_or_email.lower())).first()

        print(f"🔍 User found: {bool(user)}")
        if user:
            print(f"🔍 User active: {user.is_active}")
            print(f"🔍 Password check: {user.check_password(password)}")

        if user and user.is_active and user.check_password(password):
            # Update login statistics
            user.update_login()
            db.session.commit()

            # Login user
            login_user(user, remember=form.remember_me.data)

            # Clear old session data and set new
            session.permanent = True
            session['logged_in_username'] = user.username

            print(f"✅ User {user.username} logged in successfully")
            flash(f'Witaj ponownie, {user.username}!', 'success')

            # Redirect to next page or index
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('index'))
        else:
            print(f"❌ Login failed for: {username_or_email}")
            flash('Nieprawidłowa nazwa użytkownika/email lub hasło.', 'error')

    return render_template('auth/login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration route"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegistrationForm()

    if form.validate_on_submit():
        try:
            # Create new user
            user = User(
                username=form.username.data,
                email=form.email.data.lower() if form.email.data else '',
                first_name=form.first_name.data,
                last_name=form.last_name.data
            )
            user.set_password(form.password.data)

            db.session.add(user)
            db.session.commit()

            flash('Konto zostało utworzone! Możesz się teraz zalogować.',
                  'success')
            return redirect(url_for('login'))

        except Exception as e:
            db.session.rollback()
            logger.error(f"Registration error: {str(e)}")
            flash('Wystąpił błąd podczas rejestracji. Spróbuj ponownie.',
                  'error')

    return render_template('auth/register.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Zostałeś wylogowany.', 'info')
    return redirect(url_for('index'))


@app.route('/profile')
@login_required
def profile():
    # Pobierz wszystkie CV użytkownika
    user_cvs = CVUpload.query.filter_by(user_id=current_user.id).order_by(
        CVUpload.uploaded_at.desc()).all()
    recent_cvs = user_cvs[:5]  # Ostatnie 5 CV

    # Oblicz rzeczywiste statystyki
    total_analyses = sum(len(cv.analysis_results) for cv in user_cvs)

    # Grupuj analizy według typu
    analysis_types = {}
    for cv in user_cvs:
        for analysis in cv.analysis_results:
            analysis_type = analysis.analysis_type
            if analysis_type in analysis_types:
                analysis_types[analysis_type] += 1
            else:
                analysis_types[analysis_type] = 1

    # Oblicz dni od rejestracji
    days_since_registration = (datetime.utcnow() -
                               current_user.created_at).days

    # Statystyki wydajności
    user_stats = {
        'total_uploads':
        len(user_cvs),
        'total_analyses':
        total_analyses,
        'user_level':
        get_user_level(len(user_cvs)),
        'days_registered':
        days_since_registration,
        'avg_analyses_per_cv':
        round(total_analyses / len(user_cvs), 1) if user_cvs else 0,
        'most_used_function':
        max(analysis_types.items(), key=lambda x: x[1])[0]
        if analysis_types else 'Brak',
        'analysis_types':
        analysis_types,
        'is_premium':
        current_user.is_premium_active(),
        'premium_until':
        current_user.premium_until
    }

    return render_template('auth/profile.html',
                           user=current_user,
                           recent_cvs=recent_cvs,
                           user_stats=user_stats,
                           all_cvs=user_cvs)


@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = UserProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Profil został zaktualizowany.', 'success')
        return redirect(url_for('profile'))

    return render_template('auth/edit_profile.html', form=form)


@app.route('/profile/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Hasło zostało zmienione.', 'success')
            return redirect(url_for('profile'))
        else:
            flash('Obecne hasło jest nieprawidłowe.', 'error')

    return render_template('auth/change_password.html', form=form)


@app.route('/checkout')
def checkout():
    stripe_public_key = os.environ.get('VITE_STRIPE_PUBLIC_KEY')
    return render_template('checkout.html',
                           stripe_public_key=stripe_public_key)


@app.route('/payment-options')
@login_required
def payment_options():
    """Payment options page - choose between one-time CV or Premium subscription"""
    stripe_public_key = os.environ.get('VITE_STRIPE_PUBLIC_KEY')
    return render_template('payment_options.html',
                           stripe_public_key=stripe_public_key)


@app.route('/cv-generator')
@login_required
def cv_generator():
    """CV Generator page"""
    # Sprawdź dostęp do kreatora CV
    cv_builder_access = False
    if current_user.username == 'developer':
        cv_builder_access = True
    elif session.get('cv_builder_paid', False):
        cv_builder_access = True
    elif current_user.is_premium_active():
        cv_builder_access = True  # Premium ma dostęp do wszystkiego

    return render_template('cv_generator.html',
                           cv_builder_access=cv_builder_access)


@app.route('/ai-cv-generator')
@login_required
def ai_cv_generator():
    """AI CV Generator page - Premium feature"""
    return render_template('ai_cv_generator.html')


@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')


@app.route('/debug-session')
def debug_session():
    """Debug endpoint to check session state"""
    if current_user.username != 'developer':
        return "Access denied", 403

    debug_info = {
        'current_user_authenticated': current_user.is_authenticated,
        'current_user_id': getattr(current_user, 'id', None),
        'current_user_username': getattr(current_user, 'username', None),
        'session_data': dict(session),
        'session_permanent': session.permanent,
        'app_secret_key_length': len(app.secret_key),
        'flask_login_user_id': session.get('_user_id'),
        'flask_login_fresh': session.get('_fresh')
    }

    return f"<pre>{json.dumps(debug_info, indent=2, default=str)}</pre>"


@app.route('/privacy')
def privacy():
    """Privacy policy page"""
    from datetime import datetime
    return render_template('privacy.html', moment=datetime.now())


@app.route('/premium-dashboard')
@login_required
def premium_dashboard():
    """Premium Dashboard - proste statystyki użytkowania"""
    if not current_user.is_premium_active():
        flash(
            'Dashboard Premium jest dostępny tylko dla użytkowników Premium.',
            'warning')
        return redirect(url_for('premium_subscription'))

    # Proste statystyki dla Premium
    user_cvs = CVUpload.query.filter_by(user_id=current_user.id).all()
    total_analyses = sum(len(cv.analysis_results) for cv in user_cvs)

    # Uproszczone statystyki
    stats = {
        'total_cvs':
        len(user_cvs),
        'total_optimizations':
        total_analyses,
        'user_level':
        get_user_level(len(user_cvs)),
        'improvement_score':
        min(95, 20 + total_analyses * 8),
        'cv_score':
        min(95, 60 + total_analyses * 5),
        'score_improvement':
        min(25, total_analyses * 2),
        'profile_views':
        120 + total_analyses * 8,
        'views_change':
        min(30, total_analyses * 3),
        'applications_sent':
        total_analyses * 2,
        'response_rate':
        min(25, 10 + total_analyses),
        'match_percentage':
        min(85, 45 + total_analyses * 4),
        'is_premium':
        hasattr(current_user, 'is_premium') and current_user.is_premium
    }

    return render_template('premium_dashboard.html', user_stats=stats)


@app.route('/premium-subscription')
@login_required
def premium_subscription():
    """Premium subscription page"""
    stripe_public_key = os.environ.get('VITE_STRIPE_PUBLIC_KEY')
    return render_template('premium_subscription.html',
                           stripe_public_key=stripe_public_key)


@app.route('/api/create-cv-builder-payment', methods=['POST'])
@login_required
def create_cv_builder_payment():
    """Create payment intent for CV Builder access"""
    try:
        intent = stripe.PaymentIntent.create(
            amount=1499,  # 14,99 PLN
            currency='pln',
            metadata={
                'service': 'cv_builder',
                'user_id': current_user.id
            })
        return jsonify({'client_secret': intent.client_secret})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/create-premium-subscription', methods=['POST'])
@login_required
def create_premium_subscription():
    """Create Stripe checkout session for premium subscription"""
    try:
        stripe_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'pln',
                    'product_data': {
                        'name':
                        'CV Optimizer Pro Premium',
                        'description':
                        'Miesięczna subskrypcja Premium z pełnym dostępem do dashboardu i analiz AI',
                    },
                    'unit_amount': 2900,  # 29.00 PLN w groszach
                    'recurring': {
                        'interval': 'month',
                    },
                },
                'quantity': 1,
            }],
            mode='subscription',
            success_url=url_for('premium_success', _external=True),
            cancel_url=url_for('payment_options', _external=True),
            customer_email=current_user.email,
            metadata={
                'user_id': current_user.id,
                'subscription_type': 'premium'
            })

        return jsonify({'url': stripe_session.url})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/premium-success')
@login_required
def premium_success():
    """Premium subscription success page - automatically activate premium for 1 month"""
    session_id = request.args.get('session_id')

    try:
        # Activate premium subscription for exactly 1 month
        current_user.activate_premium(months=1)
        current_user.stripe_session_id = session_id
        db.session.commit()

        flash(
            '🎉 Subskrypcja Premium została aktywowana na dokładnie 1 miesiąc!',
            'success')

    except Exception as e:
        flash(f'Wystąpił błąd podczas aktywacji premium: {str(e)}', 'error')

    return render_template('premium_success.html', session_id=session_id)


@app.route('/payment-success')
def payment_success():
    return render_template('payment_success.html')


@app.route('/compare-cv-versions')
def compare_cv_versions():
    original_cv = session.get('original_cv_text', 'Brak oryginalnego CV')
    optimized_cv = session.get('last_optimized_cv',
                               'Brak zoptymalizowanego CV')

    return jsonify({
        'success':
        True,
        'original':
        original_cv,
        'optimized':
        optimized_cv,
        'has_both_versions':
        bool(
            session.get('original_cv_text')
            and session.get('last_optimized_cv'))
    })


@app.route('/upload-cv', methods=['POST'])
@login_required
@rate_limit('cv_upload')
def upload_cv():
    if 'cv_file' not in request.files:
        return jsonify({'success': False, 'message': 'Nie wybrano pliku'}), 400

    file = request.files['cv_file']
    cv_text = request.form.get('cv_text', '')

    if file.filename == '':
        if not cv_text.strip():
            return jsonify({
                'success':
                False,
                'message':
                'Nie wybrano pliku ani nie wprowadzono tekstu CV'
            }), 400

    try:
        original_filename = file.filename if file and file.filename else 'wklejone_cv.txt'

        if file and file.filename and file.filename != '' and allowed_file(
                file.filename):
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            file_path = os.path.join(UPLOAD_FOLDER, unique_filename)

            # Save the file
            file.save(file_path)

            try:
                # Extract text from PDF
                cv_text = extract_text_from_pdf(file_path)
                # Remove the file after extraction
                os.remove(file_path)
            except Exception as e:
                logger.error(f"Error processing PDF: {str(e)}")
                if os.path.exists(file_path):
                    os.remove(file_path)
                return jsonify({
                    'success':
                    False,
                    'message':
                    f"Błąd podczas przetwarzania PDF: {str(e)}"
                }), 500

        elif file and file.filename != '':
            return jsonify({
                'success':
                False,
                'message':
                'Nieprawidłowy format pliku. Obsługiwane formaty: PDF'
            }), 400

        if not cv_text.strip():
            return jsonify({
                'success':
                False,
                'message':
                'CV jest puste lub nie udało się wyodrębnić tekstu'
            }), 400

        # Validate CV quality
        validation_results = cv_validator.validate_cv(cv_text)

        if not validation_results['is_valid']:
            return jsonify({
                'success': False,
                'message': 'CV nie spełnia wymagań jakości',
                'validation_errors': validation_results['errors']
            }), 400

        # Add validation warnings to notifications
        if validation_results['warnings']:
            notification_system.add_notification(
                f"Uwagi dotyczące CV: {'; '.join(validation_results['warnings'])}",
                'warning')

        if validation_results['suggestions']:
            notification_system.add_notification(
                f"Sugestie: {'; '.join(validation_results['suggestions'])}",
                'info')

        # Zapisz CV w bazie danych
        cv_upload = CVUpload(user_id=current_user.id,
                             filename=original_filename,
                             original_text=cv_text,
                             job_title=request.form.get('job_title', ''),
                             job_description=request.form.get(
                                 'job_description', ''))
        db.session.add(cv_upload)
        db.session.commit()

        # Wyczyść sesję przed dodaniem nowych danych
        clean_session_before_new_data()

        # Store CV data in session for processing (skrócone wersje)
        session['cv_text'] = cv_text[:2000] + "...[skrócono]" if len(
            cv_text) > 2000 else cv_text
        session['original_cv_text'] = cv_text[:1500] + "...[skrócono]" if len(
            cv_text) > 1500 else cv_text
        session[
            'original_filename'] = original_filename[:
                                                     100]  # Limit filename length
        session['job_title'] = request.form.get('job_title',
                                                '')[:200]  # Limit job title
        session['job_description'] = request.form.get(
            'job_description', '')[:500]  # Limit job description
        session['cv_upload_id'] = cv_upload.id

        return jsonify({
            'success': True,
            'cv_text': cv_text,
            'message': 'CV zostało pomyślnie przesłane i zapisane.'
        })

    except Exception as e:
        logger.error(f"Error in upload_cv: {str(e)}")
        return jsonify({
            'success':
            False,
            'message':
            f'Wystąpił błąd podczas przesyłania pliku: {str(e)}'
        }), 500


@app.route('/create-payment-intent', methods=['POST'])
def create_payment_intent():
    try:
        # Cena za generowanie CV: 9.99 PLN (999 groszy)
        amount = 999  # w groszach

        # Tworzenie Payment Intent
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency='pln',
            metadata={'service': 'cv_optimization'})

        return jsonify({
            'success': True,
            'client_secret': intent.client_secret,
            'amount': amount
        })

    except Exception as e:
        logger.error(f"Error creating payment intent: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Błąd podczas tworzenia płatności: {str(e)}"
        }), 500


@app.route('/verify-payment', methods=['POST'])
def verify_payment():
    try:
        data = request.get_json()
        payment_intent_id = data.get('payment_intent_id')

        if not payment_intent_id:
            return jsonify({
                'success': False,
                'message': 'Brak ID płatności'
            }), 400

        # Sprawdzenie statusu płatności
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)

        if intent.status == 'succeeded':
            # Płatność zakończona sukcesem - zapisz w sesji
            session['payment_verified'] = True
            session['payment_intent_id'] = payment_intent_id

            return jsonify({
                'success':
                True,
                'message':
                'Płatność zakończona sukcesem! Możesz teraz wygenerować CV.'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Płatność nie została zakończona'
            }), 400

    except Exception as e:
        logger.error(f"Error verifying payment: {str(e)}")
        return jsonify({
            'success':
            False,
            'message':
            f"Błąd podczas weryfikacji płatności: {str(e)}"
        }), 500


@app.route('/create-cv-payment', methods=['POST'])
@login_required
def create_cv_payment():
    """Create payment intent for CV generator"""
    try:
        cv_data = request.get_json()

        # Store CV data in session for later use (optymalizowane)
        optimized_cv_data = {
            'firstName': cv_data.get('firstName', '')[:50],
            'lastName': cv_data.get('lastName', '')[:50],
            'email': cv_data.get('email', '')[:100],
            'phone': cv_data.get('phone', '')[:20],
            'jobTitle': cv_data.get('jobTitle', '')[:100]
        }
        session['cv_data'] = optimized_cv_data

        # Create payment intent for CV generation (9.99 PLN)
        intent = stripe.PaymentIntent.create(
            amount=999,  # 9.99 PLN in grosze
            currency='pln',
            metadata={
                'service': 'cv_generator',
                'user_id': current_user.id
            })

        return jsonify({
            'success':
            True,
            'client_secret':
            intent.client_secret,
            'checkout_url':
            f'/checkout?client_secret={intent.client_secret}&service=cv_generator'
        })

    except Exception as e:
        logger.error(f"Error creating CV payment: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Błąd podczas tworzenia płatności: {str(e)}"
        }), 500


@app.route('/generate-cv-pdf', methods=['POST'])
@login_required
def generate_cv_pdf():
    """Generate PDF from CV data after payment verification"""
    try:
        data = request.get_json()
        payment_intent_id = data.get('payment_intent_id')

        if not payment_intent_id:
            return jsonify({
                'success': False,
                'message': 'Brak ID płatności'
            }), 400

        # Verify payment
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)

        if intent.status != 'succeeded':
            return jsonify({
                'success': False,
                'message': 'Płatność nie została zakończona'
            }), 400

        # Get CV data from session
        cv_data = session.get('cv_data')
        if not cv_data:
            return jsonify({
                'success': False,
                'message': 'Brak danych CV do wygenerowania'
            }), 400

        # Generate PDF
        pdf_buffer = generate_cv_pdf_file(cv_data)

        # Encode as base64 for frontend
        pdf_base64 = base64.b64encode(pdf_buffer.getvalue()).decode()

        return jsonify({
            'success':
            True,
            'pdf_data':
            pdf_base64,
            'filename':
            f"CV_{cv_data.get('firstName', 'CV')}_{cv_data.get('lastName', '')}.pdf"
        })

    except Exception as e:
        logger.error(f"Error generating CV PDF: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Błąd podczas generowania PDF: {str(e)}"
        }), 500


@app.route('/api/generate-ai-cv', methods=['POST'])
@login_required
def generate_ai_cv():
    """Generate complete CV using AI with professional templates"""
    try:
        data = request.get_json()

        # Basic user input - minimal required
        basic_info = {
            'firstName': data.get('firstName', ''),
            'lastName': data.get('lastName', ''),
            'email': data.get('email', ''),
            'phone': data.get('phone', ''),
            'city': data.get('city', ''),
            'targetPosition': data.get('targetPosition', ''),
            'experience_level': data.get('experience_level',
                                         'junior'),  # junior/mid/senior
            'industry': data.get('industry', ''),
            'template_style': data.get('template_style', 'modern_blue'),
            'brief_background': data.get('brief_background',
                                         '')  # 2-3 zdania o doświadczeniu
        }

        # Sprawdź dostęp do funkcji
        is_developer = current_user.username == 'developer'
        is_premium_active = current_user.is_premium_active()

        # Funkcja tylko dla Premium lub developer
        if not is_developer and not is_premium_active:
            return jsonify({
                'success': False,
                'message':
                'Automatyczne generowanie CV jest dostępne tylko dla użytkowników Premium.',
                'premium_required': True
            }), 403

        # Generate AI content based on basic info
        from utils.openrouter_api import generate_complete_cv_content

        ai_cv_content = generate_complete_cv_content(
            target_position=basic_info['targetPosition'],
            experience_level=basic_info['experience_level'],
            industry=basic_info['industry'],
            brief_background=basic_info['brief_background'],
            language='pl')

        # Parse AI response
        import json
        try:
            cv_content = json.loads(ai_cv_content)
        except json.JSONDecodeError:
            # Fallback parsing
            cv_content = parse_ai_json_response(ai_cv_content)

        # Combine basic info with AI-generated content
        complete_cv_data = {
            'firstName':
            basic_info['firstName'],
            'lastName':
            basic_info['lastName'],
            'email':
            basic_info['email'],
            'phone':
            basic_info['phone'],
            'city':
            basic_info['city'],
            'jobTitle':
            cv_content.get('professional_title', basic_info['targetPosition']),
            'summary':
            cv_content.get('professional_summary', ''),
            'experiences':
            cv_content.get('experience_suggestions', []),
            'education':
            cv_content.get('education_suggestions', []),
            'skills':
            cv_content.get('skills_list', ''),
            'template_style':
            basic_info['template_style']
        }

        # Generate PDF with selected template
        from utils.cv_templates import generate_cv_with_template

        pdf_buffer = generate_cv_with_template(complete_cv_data,
                                               basic_info['template_style'])

        # Encode as base64
        pdf_base64 = base64.b64encode(pdf_buffer.getvalue()).decode()

        # Store in session for potential edits
        session['ai_generated_cv'] = complete_cv_data

        return jsonify({
            'success':
            True,
            'cv_data':
            complete_cv_data,
            'pdf_data':
            pdf_base64,
            'filename':
            f"AI_CV_{basic_info['firstName']}_{basic_info['lastName']}.pdf",
            'message':
            'CV zostało wygenerowane przez AI z profesjonalnym szablonem!'
        })

    except Exception as e:
        logger.error(f"Error generating AI CV: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Błąd podczas generowania CV: {str(e)}'
        }), 500


@app.route('/api/create-ai-cv-payment', methods=['POST'])
@login_required
def create_ai_cv_payment():
    """Create payment for AI CV generation (Premium feature alternative)"""
    try:
        # Store request data for after payment
        cv_request_data = request.get_json()
        session['pending_ai_cv_data'] = cv_request_data

        # Create payment intent for AI CV generation (29.99 PLN - same as Premium monthly)
        intent = stripe.PaymentIntent.create(
            amount=2999,  # 29.99 PLN
            currency='pln',
            metadata={
                'service': 'ai_cv_generation',
                'user_id': current_user.id
            })

        return jsonify({
            'success':
            True,
            'client_secret':
            intent.client_secret,
            'checkout_url':
            f'/checkout?client_secret={intent.client_secret}&service=ai_cv_generation'
        })

    except Exception as e:
        logger.error(f"Error creating AI CV payment: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Błąd podczas tworzenia płatności: {str(e)}"
        }), 500


def generate_cv_pdf_file(cv_data):
    """Generate PDF file from CV data"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#6366f1'),
        spaceAfter=30,
        alignment=1  # Center
    )

    subtitle_style = ParagraphStyle('CustomSubtitle',
                                    parent=styles['Heading2'],
                                    fontSize=16,
                                    textColor=colors.HexColor('#4f46e5'),
                                    spaceAfter=20)

    normal_style = ParagraphStyle('CustomNormal',
                                  parent=styles['Normal'],
                                  fontSize=11,
                                  spaceAfter=12)

    # Header
    name = f"{cv_data.get('firstName', '')} {cv_data.get('lastName', '')}".strip(
    )
    story.append(Paragraph(name, title_style))

    job_title = cv_data.get('jobTitle', '')
    if job_title:
        story.append(Paragraph(job_title, styles['Heading3']))

    # Contact info
    contact_info = []
    if cv_data.get('email'):
        contact_info.append(cv_data['email'])
    if cv_data.get('phone'):
        contact_info.append(cv_data['phone'])
    if cv_data.get('city'):
        contact_info.append(cv_data['city'])
    if cv_data.get('linkedin'):
        contact_info.append(cv_data['linkedin'])

    if contact_info:
        story.append(Paragraph(' | '.join(contact_info), normal_style))

    story.append(Spacer(1, 20))

    # Summary
    if cv_data.get('summary'):
        story.append(Paragraph("O mnie", subtitle_style))
        story.append(Paragraph(cv_data['summary'], normal_style))
        story.append(Spacer(1, 15))

    # Experience
    experiences = cv_data.get('experiences', [])
    if experiences and any(
            exp.get('title') or exp.get('company') for exp in experiences):
        story.append(Paragraph("Doświadczenie zawodowe", subtitle_style))
        for exp in experiences:
            if exp.get('title') or exp.get('company'):
                # Title and company
                exp_header = f"<b>{exp.get('title', 'Stanowisko')}</b> - {exp.get('company', 'Firma')}"
                story.append(Paragraph(exp_header, normal_style))

                # Dates
                start_date = exp.get('startDate', '')
                end_date = exp.get('endDate', 'obecnie')
                if start_date:
                    date_range = f"{start_date} - {end_date}"
                    story.append(Paragraph(date_range, normal_style))

                # Description
                if exp.get('description'):
                    story.append(Paragraph(exp['description'], normal_style))

                story.append(Spacer(1, 10))

    # Education
    education = cv_data.get('education', [])
    if education and any(
            edu.get('degree') or edu.get('school') for edu in education):
        story.append(Paragraph("Wykształcenie", subtitle_style))
        for edu in education:
            if edu.get('degree') or edu.get('school'):
                # Degree and school
                edu_header = f"<b>{edu.get('degree', 'Kierunek')}</b> - {edu.get('school', 'Uczelnia')}"
                story.append(Paragraph(edu_header, normal_style))

                # Years
                start_year = edu.get('startYear', '')
                end_year = edu.get('endYear', '')
                if start_year or end_year:
                    year_range = f"{start_year} - {end_year}"
                    story.append(Paragraph(year_range, normal_style))

                story.append(Spacer(1, 10))

    # Skills
    skills = cv_data.get('skills', '')
    if skills:
        story.append(Paragraph("Umiejętności", subtitle_style))
        skills_list = [
            skill.strip() for skill in skills.split(',') if skill.strip()
        ]
        skills_text = ' • '.join(skills_list)
        story.append(Paragraph(skills_text, normal_style))

    doc.build(story)
    buffer.seek(0)
    return buffer


@app.route('/process-cv', methods=['POST'])
@login_required
@rate_limit('cv_process')
def process_cv():
    # PRODUCTION MODE - Payment required except for developer account
    # Sprawdzenie czy to konto developer (darmowy dostęp)
    if current_user.username == 'developer':
        # Developer account - free access
        pass
    elif not session.get('payment_verified'):
        return jsonify({
            'success': False,
            'message':
            'Aby wygenerować CV, musisz najpierw dokonać płatności 9,99 PLN.',
            'payment_required': True
        }), 402  # Payment Required

    data = request.json
    cv_text = data.get('cv_text') or session.get('cv_text')
    job_url = data.get('job_url', '')
    selected_option = data.get('selected_option', '')
    roles = data.get('roles', [])
    language = data.get('language', 'pl')  # Default to Polish

    if not cv_text:
        return jsonify({
            'success': False,
            'message': 'No CV text found. Please upload a CV first.'
        }), 400

    # Process Job URL if provided
    extracted_job_description = ''
    if job_url:
        try:
            extracted_job_description = analyze_job_url(job_url)
        except Exception as e:
            logger.error(
                f"Error extracting job description from URL: {str(e)}")
            return jsonify({
                'success':
                False,
                'message':
                f"Error extracting job description from URL: {str(e)}"
            }), 500

    try:
        job_description = data.get('job_description',
                                   extracted_job_description)
        result = None

        options_handlers = {
            'optimize': optimize_cv,
            'feedback': generate_recruiter_feedback,
            'cover_letter': generate_cover_letter,
            'ats_check': ats_optimization_check,
            'interview_questions': generate_interview_questions,
            'cv_score': analyze_cv_score,
            'keyword_analysis': analyze_keywords_match,
            'grammar_check': check_grammar_and_style,
            'position_optimization': optimize_for_position,
            'interview_tips': generate_interview_tips,
            'advanced_position_optimization': 'advanced_position_optimization'
        }

        if selected_option not in options_handlers:
            return jsonify({
                'success': False,
                'message': 'Invalid option selected.'
            }), 400

        # Sprawdź status płatności i dostępu
        payment_verified = session.get('payment_verified',
                                       False)  # 9,99 PLN - jednorazowe CV
        is_developer = current_user.username == 'developer'
        is_premium_active = current_user.is_premium_active(
        )  # 29,99 PLN - Premium

        # Definicja funkcji według poziomów dostępu - zgodnie ze screenem
        basic_paid_functions = [
            'optimize', 'ats_optimization_check', 'grammar_check'
        ]  # Za 9,99 PLN - 3 funkcje podstawowe
        premium_functions = [
            'recruiter_feedback', 'cover_letter', 'cv_score', 'interview_tips',
            'keyword_analysis', 'position_optimization', 'interview_questions',
            'advanced_position_optimization'
        ]  # Premium 29,99 PLN/miesiąc - wszystkie funkcje ze screena + nowa zaawansowana
        cv_builder_functions = ['cv_builder'
                                ]  # STWÓRZ CV SAMEMU - oddzielna płatna usługa
        free_functions = []  # Tylko podgląd ze znakiem wodnym dla bezpłatnych

        logger.info(
            f"Processing CV with language: {language}, option: {selected_option}"
        )

        # Sprawdź dostęp do funkcji według poziomów płatności
        if selected_option in premium_functions:
            # Funkcje tylko dla Premium (29,99 PLN/miesiąc)
            if not is_developer and not is_premium_active:
                return jsonify({
                    'success': False,
                    'message':
                    'Ta funkcja jest dostępna tylko dla użytkowników Premium. Wykup subskrypcję za 29,99 PLN/miesiąc.',
                    'premium_required': True
                }), 403

        elif selected_option in basic_paid_functions:
            # Funkcje za 9,99 PLN lub Premium
            if not is_developer and not payment_verified and not is_premium_active:
                return jsonify({
                    'success': False,
                    'message':
                    'Ta funkcja wymaga płatności. Zapłać 9,99 PLN za jednorazowe CV lub 29,99 PLN za Premium.',
                    'payment_required': True
                }), 403

        elif selected_option in cv_builder_functions:
            # STWÓRZ CV SAMEMU - oddzielna płatna usługa
            cv_builder_paid = session.get('cv_builder_paid', False)
            if not is_developer and not cv_builder_paid:
                return jsonify({
                    'success': False,
                    'message':
                    'Funkcja STWÓRZ CV SAMEMU wymaga oddzielnej płatności.',
                    'cv_builder_payment_required': True
                }), 403

        # Obsługa funkcji według poziomów dostępu
        if selected_option == 'optimize':
            # Funkcja za 9,99 PLN lub Premium z ulepszoną optymalizacją
            if not is_developer and not payment_verified and not is_premium_active:
                ai_result = optimize_cv(cv_text,
                                        job_description,
                                        language,
                                        is_premium=False,
                                        payment_verified=False)
                result = parse_ai_json_response(ai_result)
                result = add_watermark_to_cv(result)
            else:
                # Użyj nowej zaawansowanej funkcji dla płacących
                from utils.openrouter_api import enhanced_cv_optimization_with_reasoning

                logger.info(
                    "Używam zaawansowanej optymalizacji CV z AI reasoning")
                ai_result = enhanced_cv_optimization_with_reasoning(
                    cv_text,
                    job_description,
                    language,
                    is_premium=is_premium_active,
                    payment_verified=True)
                result = parse_ai_json_response(ai_result)

        elif selected_option == 'ats_optimization_check':
            # Funkcja za 9,99 PLN lub Premium
            result = options_handlers[selected_option](cv_text,
                                                       job_description,
                                                       language)

        elif selected_option == 'position_optimization':
            # Funkcja tylko Premium
            job_title = data.get('job_title', 'Specjalista')
            ai_result = optimize_for_position(cv_text, job_title,
                                              job_description, language)
            result = parse_ai_json_response(ai_result)

        elif selected_option == 'advanced_position_optimization':
            # NOWA ZAAWANSOWANA FUNKCJA - tylko Premium
            from utils.openrouter_api import optimize_cv_for_specific_position

            job_title = data.get('job_title', 'Specjalista')
            company_name = data.get('company_name', '')

            ai_result = optimize_cv_for_specific_position(
                cv_text,
                job_title,
                job_description,
                company_name,
                language,
                is_premium=is_premium_active,
                payment_verified=payment_verified)
            result = parse_ai_json_response(ai_result)

        elif selected_option == 'interview_questions':
            # Funkcja dla Premium
            job_title = data.get('job_title', 'Specjalista')
            ai_result = generate_interview_questions(cv_text,
                                                     job_description,
                                                     language,
                                                     job_title=job_title)
            result = parse_ai_json_response(ai_result)

        elif selected_option in [
                'cover_letter', 'interview_tips', 'recruiter_feedback'
        ]:
            # Funkcje tylko Premium
            if selected_option == 'cover_letter':
                result = options_handlers[selected_option](cv_text,
                                                           job_description,
                                                           language)
            else:
                result = options_handlers[selected_option](cv_text,
                                                           job_description,
                                                           language)

        else:
            # Pozostałe funkcje
            result = options_handlers[selected_option](cv_text,
                                                       job_description,
                                                       language)

        # Store optimized CV for comparison (only for optimization options) - skrócona wersja
        if selected_option in [
                'optimize', 'position_optimization',
                'advanced_position_optimization'
        ]:
            if isinstance(result, str) and len(result) > 1500:
                session[
                    'last_optimized_cv'] = result[:1500] + "...[skrócono dla optymalizacji sesji]"
            else:
                session['last_optimized_cv'] = result

        # Optymalizuj sesję po dodaniu nowych danych
        optimize_session_data()

        # Zapisz wynik analizy w bazie danych
        cv_upload_id = session.get('cv_upload_id')
        if cv_upload_id:
            try:
                analysis_result = AnalysisResult(
                    cv_upload_id=cv_upload_id,
                    analysis_type=selected_option,
                    result_data=json.dumps(
                        {
                            'result':
                            result,
                            'job_description':
                            extracted_job_description
                            if extracted_job_description else job_description,
                            'job_url':
                            job_url,
                            'timestamp':
                            datetime.utcnow().isoformat()
                        },
                        ensure_ascii=False))
                db.session.add(analysis_result)
                db.session.commit()
            except Exception as e:
                logger.error(f"Error saving analysis result: {str(e)}")
                # Nie blokujemy odpowiedzi, tylko logujemy błąd

        return jsonify({
            'success':
            True,
            'result':
            result,
            'job_description':
            extracted_job_description if extracted_job_description else None
        })

    except Exception as e:
        logger.error(f"Error processing CV: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Error processing request: {str(e)}"
        }), 500


@app.route('/apply-recruiter-feedback', methods=['POST'])
@login_required
@rate_limit('cv_process')
def apply_recruiter_feedback():
    """
    Apply recruiter feedback to CV - PAID FEATURE (9.99 PLN or Premium)
    """
    try:
        data = request.get_json()
        cv_text = data.get('cv_text') or session.get('cv_text')
        recruiter_feedback = data.get('recruiter_feedback', '')
        job_description = data.get('job_description', '')
        language = data.get('language', 'pl')

        if not cv_text:
            return jsonify({
                'success': False,
                'message': 'Brak tekstu CV. Prześlij najpierw CV.'
            }), 400

        if not recruiter_feedback:
            return jsonify({
                'success': False,
                'message': 'Brak opinii rekrutera do zastosowania.'
            }), 400

        # Sprawdź dostęp do funkcji
        is_developer = current_user.username == 'developer'
        is_premium_active = current_user.is_premium_active()
        payment_verified = session.get('payment_verified', False)

        # Ta funkcja wymaga płatności (9.99 PLN) lub Premium
        if not is_developer and not payment_verified and not is_premium_active:
            return jsonify({
                'success': False,
                'message':
                'Zastosowanie poprawek rekrutera wymaga płatności 9,99 PLN lub subskrypcji Premium.',
                'payment_required': True
            }), 403

        # Zastosuj poprawki rekrutera do CV
        from utils.openrouter_api import apply_recruiter_feedback_to_cv

        ai_result = apply_recruiter_feedback_to_cv(
            cv_text,
            recruiter_feedback,
            job_description,
            language,
            is_premium=is_premium_active,
            payment_verified=payment_verified or is_developer)

        # Parse JSON response
        result = parse_ai_json_response(ai_result)

        # Store improved CV for comparison
        if isinstance(result, dict) and 'improved_cv' in result:
            session['last_optimized_cv'] = result['improved_cv']
            session['last_feedback_applied'] = True

        # Zapisz wynik w bazie danych
        cv_upload_id = session.get('cv_upload_id')
        if cv_upload_id:
            try:
                analysis_result = AnalysisResult(
                    cv_upload_id=cv_upload_id,
                    analysis_type='apply_recruiter_feedback',
                    result_data=json.dumps(
                        {
                            'result': result,
                            'original_feedback': recruiter_feedback,
                            'job_description': job_description,
                            'timestamp': datetime.utcnow().isoformat()
                        },
                        ensure_ascii=False))
                db.session.add(analysis_result)
                db.session.commit()
            except Exception as e:
                logger.error(
                    f"Error saving feedback application result: {str(e)}")

        return jsonify({
            'success':
            True,
            'result':
            result,
            'message':
            'Poprawki rekrutera zostały pomyślnie zastosowane do CV!'
        })

    except Exception as e:
        logger.error(f"Error applying recruiter feedback: {str(e)}")
        return jsonify({
            'success':
            False,
            'message':
            f'Błąd podczas zastosowania poprawek: {str(e)}'
        }), 500


@app.route('/analyze-job-posting', methods=['POST'])
def analyze_job_posting():
    """
    Analizuje opis stanowiska i zwraca szczegółowe informacje
    """
    try:
        data = request.get_json()
        job_description = data.get('job_description', '')
        job_url = data.get('job_url', '')
        language = data.get('language', 'pl')

        if not job_description and not job_url:
            return jsonify({
                'success':
                False,
                'message':
                'Podaj opis stanowiska lub URL oferty pracy'
            }), 400

        # Jeśli podano URL, najpierw wyciągnij opis
        if job_url and not job_description:
            try:
                job_description = analyze_job_url(job_url)
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'Błąd podczas analizy URL: {str(e)}'
                }), 500

        # Analizuj opis stanowiska
        from utils.openrouter_api import analyze_polish_job_posting
        analysis_result = analyze_polish_job_posting(job_description, language)

        # Spróbuj sparsować JSON z odpowiedzi AI
        try:
            import json
            parsed_analysis = json.loads(analysis_result)
        except json.JSONDecodeError:
            # Jeśli nie da się sparsować jako JSON, wyciągnij JSON z tekstu
            import re
            json_match = re.search(r'\{.*\}', analysis_result, re.DOTALL)
            if json_match:
                parsed_analysis = json.loads(json_match.group())
            else:
                parsed_analysis = {'analysis': analysis_result}

        return jsonify({
            'success': True,
            'analysis': parsed_analysis,
            'raw_description': job_description
        })

    except Exception as e:
        logger.error(f"Error analyzing job posting: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Błąd podczas analizy stanowiska: {str(e)}'
        }), 500


def check_configuration():
    """Sprawdź kompletną konfigurację aplikacji"""
    print("\n" + "="*60)
    print("🔧 SPRAWDZANIE KONFIGURACJI CV OPTIMIZER PRO")
    print("="*60)
    
    # Sprawdź zmienne środowiskowe
    config_status = {
        'OPENROUTER_API_KEY': bool(os.environ.get('OPENROUTER_API_KEY', '').strip() and 
                                  not os.environ.get('OPENROUTER_API_KEY', '').startswith('TWÓJ_')),
        'STRIPE_SECRET_KEY': bool(os.environ.get('STRIPE_SECRET_KEY', '').strip()),
        'SECRET_KEY': bool(os.environ.get('SECRET_KEY', '').strip()),
        'DATABASE_URL': bool(os.environ.get('DATABASE_URL', '').strip()),
    }
    
    for key, status in config_status.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {key}: {'OK' if status else 'BRAK/NIEPOPRAWNY'}")
    
    if not all(config_status.values()):
        print("\n❌ KONFIGURACJA NIEKOMPLETNA!")
        print("🔧 Sprawdź plik .env i ustaw wszystkie wymagane zmienne")
        return False
    
    print("\n✅ KONFIGURACJA KOMPLETNA!")
    print("="*60 + "\n")
    return True

def initialize_app():
    """Initialize application database and users"""
    with app.app_context():
        # Create all database tables
        db.create_all()
        print("✅ Database tables created successfully!")

        # Create new developer account
        dev_user = User.query.filter_by(username='developer').first()
        if not dev_user:
            dev_user = User(username='developer',
                            email='dev@cvoptimizer.pro',
                            first_name='System',
                            last_name='Developer',
                            is_active=True)
            dev_user.set_password('NewDev2024!')
            db.session.add(dev_user)
            db.session.commit()
            print("✅ NEW Developer account created successfully!")
        else:
            print("✅ Developer account already exists")

# Initialize app when imported (for production)
if os.environ.get('FLASK_ENV') == 'production':
    initialize_app()

if __name__ == '__main__':
    # Sprawdź konfigurację przed startem
    if not check_configuration():
        print("⚠️ Aplikacja może nie działać poprawnie bez kompletnej konfiguracji")
        print("🔧 Zaktualizuj plik .env z prawidłowymi wartościami")
    
    # Initialize for development
    if os.environ.get('FLASK_ENV') != 'production':
        initialize_app()

    # Replit używa PORT, lokalnie fallback na 5000
    port = int(os.environ.get('PORT', 5000))

    # Log startup info
    print(f"🚀 Starting CV Optimizer Pro on 0.0.0.0:{port}")
    
    # Ensure proper binding
    debug_mode = os.environ.get("DEBUG", "False").lower() == "true"
    app.run(host='0.0.0.0', port=port, debug=debug_mode, threaded=True)
