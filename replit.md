# CV Optimizer Pro - Architecture Overview

## Overview

CV Optimizer Pro is an AI-powered resume optimization platform built with Flask and designed as a Progressive Web Application (PWA). The system leverages artificial intelligence to analyze, optimize, and enhance CVs based on specific job requirements. The application supports multiple deployment strategies and includes comprehensive user management, payment processing, and advanced CV analysis features.

## System Architecture

### Backend Architecture
- **Framework**: Flask (Python 3.11+) with SQLAlchemy ORM
- **Database**: PostgreSQL with automatic URL compatibility handling
- **Authentication**: Flask-Login with bcrypt password hashing
- **API Integration**: OpenRouter AI API for CV analysis and optimization
- **Payment Processing**: Stripe integration for subscription and one-time payments
- **File Processing**: PDF text extraction using PyPDF2 and PDFMiner
- **Web Server**: Gunicorn WSGI server for production deployment

### Frontend Architecture
- **Template Engine**: Jinja2 with modern glassmorphism UI design
- **CSS Framework**: Custom modern CSS with Bootstrap integration
- **JavaScript**: Vanilla JavaScript with enhanced user interactions
- **PWA Features**: Service Worker for offline functionality, Web App Manifest
- **Responsive Design**: Mobile-first approach with cross-platform compatibility

### Database Schema
- **Users**: User accounts with premium subscription management
- **CVUpload**: CV document storage and metadata
- **AnalysisResult**: AI analysis results and optimization history
- **Relationship Management**: Foreign key relationships with cascading deletes

## Key Components

### User Management System
- User registration and authentication with role-based access
- Premium subscription management with Stripe integration
- Developer account with special privileges (username: 'developer')
- Profile management and password change functionality
- Session management with remember-me functionality

### CV Processing Pipeline
- PDF upload and text extraction using multiple fallback methods
- AI-powered analysis using OpenRouter API with configurable models
- Language-specific processing (Polish/English) with appropriate prompts
- Real-time optimization feedback and scoring system
- ATS compatibility checking and keyword analysis

### Payment Integration
- Stripe payment gateway for secure transactions
- One-time payment model (9.99 PLN per CV optimization)
- Premium subscription option (29.99 PLN/month)
- Payment verification and status tracking
- Webhook handling for payment confirmations

### AI Analysis Engine
- OpenRouter API integration with advanced prompt engineering
- Multi-language support with context-aware responses
- CV optimization for specific job positions
- Cover letter generation and interview preparation
- Grammar and style checking with professional recommendations

## Data Flow

### CV Upload and Processing
1. User uploads PDF file through drag-and-drop interface
2. System extracts text using PDF processing utilities
3. Text is stored in database with user association
4. CV content is displayed for user review and editing
5. User can modify CV text before AI processing

### AI Analysis Workflow
1. User selects optimization options and provides job details
2. Payment verification ensures user has valid access
3. System constructs language-specific prompts for AI
4. OpenRouter API processes CV with job-specific context
5. Results are formatted and stored in database
6. User receives comprehensive analysis and recommendations

### Payment Processing
1. User initiates payment through Stripe checkout
2. Secure payment form handles card processing
3. Webhook confirms successful payment
4. User account is updated with payment status
5. AI features are unlocked for the session

## External Dependencies

### API Services
- **OpenRouter AI**: Primary AI service for CV analysis and optimization
- **Stripe**: Payment processing and subscription management
- **PostgreSQL**: Database hosting (Render.com or similar platforms)

### Third-Party Libraries
- **Flask Ecosystem**: Core web framework with extensions
- **PDFMiner/PyPDF2**: PDF text extraction capabilities
- **ReportLab**: PDF generation for optimized CVs
- **BeautifulSoup**: HTML parsing for job posting extraction
- **Requests**: HTTP client for external API calls

### Development Tools
- **Gunicorn**: Production WSGI server
- **psycopg2-binary**: PostgreSQL database adapter
- **Werkzeug**: WSGI utilities and development server

## Deployment Strategy

### Platform Support
- **Render.com**: Primary deployment platform with automated Blueprint setup
- **Docker**: Containerized deployment with multi-stage builds
- **Replit**: Development environment with integrated database
- **Heroku**: Alternative cloud platform deployment

### Environment Configuration
- Environment-specific configuration files (.env.example)
- Automatic PostgreSQL URL format conversion
- Secure API key management
- Production-ready settings with debug controls

### PWA Deployment
- Progressive Web App manifest for app store deployment
- Service Worker for offline functionality
- PWABuilder.com integration for store packages
- Cross-platform app generation capabilities

### Monitoring and Logging
- Comprehensive logging with configurable levels
- Error tracking and debugging capabilities
- Performance monitoring for AI API calls
- User activity tracking and analytics

## Recent Changes
- June 24, 2025: Fixed database connection issues by creating new Replit PostgreSQL database
- June 24, 2025: Updated database configuration to use built-in Replit database instead of external Neon service
- June 24, 2025: Initialized database tables and created developer account
- June 24, 2025: Configured OpenRouter API key for AI functionality with qwen/qwen-2.5-72b-instruct:free model

## Changelog
- June 24, 2025. Initial setup

## User Preferences

Preferred communication style: Simple, everyday language.