
from flask import request, g
import logging
from datetime import datetime
import json

class SecurityMiddleware:
    def __init__(self, app=None):
        self.app = app
        self.suspicious_patterns = [
            'script', 'javascript:', 'eval(', 'function(',
            'SELECT', 'INSERT', 'DELETE', 'UPDATE', 'DROP',
            '../', '..\\', '/etc/passwd', 'cmd.exe'
        ]
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        app.before_request(self.before_request)
        app.after_request(self.after_request)
    
    def before_request(self):
        """Security checks before processing request"""
        # Log suspicious activity
        self._check_suspicious_patterns()
        
        # Store request start time
        g.start_time = datetime.utcnow()
        
        # Check for common attack patterns
        self._check_security_headers()
    
    def after_request(self, response):
        """Security processing after request"""
        # Add security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Log response time
        if hasattr(g, 'start_time'):
            duration = (datetime.utcnow() - g.start_time).total_seconds()
            if duration > 10:  # Log slow requests
                logging.warning(f"Slow request: {request.endpoint} took {duration:.2f}s")
        
        return response
    
    def _check_suspicious_patterns(self):
        """Check for suspicious patterns in request data"""
        request_data = {}
        
        # Check URL parameters
        if request.args:
            request_data.update(request.args)
        
        # Check form data
        if request.form:
            request_data.update(request.form)
        
        # Check JSON data
        if request.is_json:
            try:
                json_data = request.get_json()
                if json_data:
                    request_data.update(json_data)
            except:
                pass
        
        # Check for suspicious patterns
        for key, value in request_data.items():
            if isinstance(value, str):
                for pattern in self.suspicious_patterns:
                    if pattern.lower() in value.lower():
                        logging.warning(f"Suspicious pattern '{pattern}' detected in {key}: {value[:100]}")
    
    def _check_security_headers(self):
        """Check for security headers"""
        user_agent = request.headers.get('User-Agent', '')
        
        # Log unusual user agents
        if not user_agent or len(user_agent) < 10:
            logging.warning(f"Suspicious User-Agent: {user_agent}")
        
        # Check for automated tools
        automated_tools = ['curl', 'wget', 'python-requests', 'bot', 'crawler']
        if any(tool in user_agent.lower() for tool in automated_tools):
            logging.info(f"Automated tool detected: {user_agent}")

security_middleware = SecurityMiddleware()
