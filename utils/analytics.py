
from datetime import datetime, timedelta
from collections import defaultdict
import json

from collections import defaultdict
from datetime import datetime, timedelta

class AnalyticsTracker:
    def __init__(self):
        self.events = defaultdict(list)
    
    def track_event(self, user_id, event_type, metadata=None):
        """Track user event"""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'metadata': metadata or {}
        }
        self.events[user_id].append(event)
    
    def get_user_stats(self, user_id, days=30):
        """Get comprehensive user statistics"""
        user_events = self.events.get(user_id, [])
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        recent_events = [
            e for e in user_events 
            if datetime.fromisoformat(e['timestamp']) > cutoff_date
        ]
        
        stats = {
            'total_events': len(recent_events),
            'cv_optimizations': len([e for e in recent_events if e['event_type'] == 'cv_optimization']),
            'ai_analyses': len([e for e in recent_events if e['event_type'] == 'ai_analysis']),
            'cover_letters': len([e for e in recent_events if e['event_type'] == 'cover_letter']),
            'most_active_day': self._get_most_active_day(recent_events),
            'improvement_trend': self._calculate_improvement_trend(recent_events)
        }
        
        return stats
    
    def _get_most_active_day(self, events):
        """Find most active day of the week"""
        day_counts = defaultdict(int)
        for event in events:
            day = datetime.fromisoformat(event['timestamp']).strftime('%A')
            day_counts[day] += 1
        
        return max(day_counts.items(), key=lambda x: x[1])[0] if day_counts else None
    
    def _calculate_improvement_trend(self, events):
        """Calculate improvement trend based on CV scores"""
        cv_scores = []
        for event in events:
            if event['event_type'] == 'cv_optimization' and 'score' in event.get('metadata', {}):
                cv_scores.append(event['metadata']['score'])
        
        if len(cv_scores) < 2:
            return 0
        
        # Simple trend calculation
        return cv_scores[-1] - cv_scores[0]

analytics = AnalyticsTracker()
