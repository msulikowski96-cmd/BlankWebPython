from functools import wraps
from flask import request, jsonify
import time
from collections import defaultdict, deque

class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(deque)
        self.limits = {
            'cv_upload': (5, 300),  # 5 uploads per 5 minutes
            'cv_process': (10, 3600),  # 10 processes per hour
            'ai_analysis': (20, 3600),  # 20 AI calls per hour
            'general': (100, 3600)  # 100 general requests per hour
        }

    def is_allowed(self, identifier, limit_type='general'):
        now = time.time()
        max_requests, time_window = self.limits.get(limit_type, (100, 3600))

        # Clean old requests
        user_requests = self.requests[identifier]
        while user_requests and user_requests[0] < now - time_window:
            user_requests.popleft()

        # Check if limit exceeded
        if len(user_requests) >= max_requests:
            return False

        # Add current request
        user_requests.append(now)
        return True

    def get_reset_time(self, identifier, limit_type='general'):
        now = time.time()
        _, time_window = self.limits.get(limit_type, (100, 3600))
        user_requests = self.requests[identifier]

        if user_requests:
            return int(user_requests[0] + time_window - now)
        return 0

rate_limiter = RateLimiter()

def rate_limit(limit_type='general'):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Use IP address or user ID as identifier
            identifier = request.remote_addr
            try:
                from flask_login import current_user
                if current_user.is_authenticated:
                    identifier = f"user_{current_user.id}"
            except ImportError:
                pass

            if not rate_limiter.is_allowed(identifier, limit_type):
                reset_time = rate_limiter.get_reset_time(identifier, limit_type)
                return jsonify({
                    'success': False,
                    'message': f'Rate limit exceeded. Try again in {reset_time} seconds.',
                    'retry_after': reset_time
                }), 429

            return f(*args, **kwargs)
        return decorated_function
    return decorator