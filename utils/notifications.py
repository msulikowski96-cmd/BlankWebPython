
from flask import session
from datetime import datetime
import json

class NotificationSystem:
    def __init__(self):
        self.notification_types = {
            'success': '✅',
            'warning': '⚠️',
            'error': '❌',
            'info': 'ℹ️',
            'premium': '💎'
        }
    
    def add_notification(self, message, type='info', persistent=False):
        """Add notification to user session"""
        if 'notifications' not in session:
            session['notifications'] = []
        
        notification = {
            'id': len(session['notifications']),
            'message': message,
            'type': type,
            'icon': self.notification_types.get(type, 'ℹ️'),
            'timestamp': datetime.now().isoformat(),
            'persistent': persistent
        }
        
        session['notifications'].append(notification)
        session.modified = True
    
    def get_notifications(self, clear_non_persistent=True):
        """Get all notifications and optionally clear non-persistent ones"""
        notifications = session.get('notifications', [])
        
        if clear_non_persistent:
            # Keep only persistent notifications
            persistent_notifications = [n for n in notifications if n.get('persistent', False)]
            session['notifications'] = persistent_notifications
            session.modified = True
        
        return notifications
    
    def clear_notification(self, notification_id):
        """Clear specific notification"""
        notifications = session.get('notifications', [])
        session['notifications'] = [n for n in notifications if n.get('id') != notification_id]
        session.modified = True

notification_system = NotificationSystem()
