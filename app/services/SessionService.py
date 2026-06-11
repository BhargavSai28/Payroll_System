"""
User Session Management Service
Handles user login sessions and tracking
"""

from app import db
from app.models import UserSession
from datetime import datetime, timedelta


class SessionService:
    
    @staticmethod
    def get_active_sessions(user_id):
        """Get all active sessions for a user"""
        return UserSession.query.filter_by(
            user_id=user_id,
            session_status='ACTIVE'
        ).all()
    
    @staticmethod
    def get_session_history(user_id, limit=50):
        """Get login history for a user"""
        return UserSession.query.filter_by(user_id=user_id).order_by(
            UserSession.login_time.desc()
        ).limit(limit).all()
    
    @staticmethod
    def get_session_by_id(session_id):
        """Get session details"""
        return UserSession.query.get(session_id)

    @staticmethod
    def force_logout_session(session_id):
        """Mark an active session as logged out"""
        session = UserSession.query.get(session_id)
        if not session:
            return False, "Session not found"

        if session.session_status != 'ACTIVE':
            return False, f"Session is already {session.session_status.lower()}"

        session.logout_time = datetime.utcnow()
        session.session_status = 'LOGGED_OUT'
        db.session.commit()
        return True, None
    
    
    @staticmethod
    def mark_expired_sessions():
        """Mark sessions as expired if inactive for > 8 hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=8)
        expired_sessions = UserSession.query.filter(
            UserSession.last_activity_time < cutoff_time,
            UserSession.session_status == 'ACTIVE'
        ).all()
        
        count = 0
        for session in expired_sessions:
            session.session_status = 'EXPIRED'
            count += 1
        
        db.session.commit()
        return count
    
    @staticmethod
    def get_session_stats(user_id):
        """Get session statistics for a user"""
        all_sessions = UserSession.query.filter_by(user_id=user_id).all()
        active = len([s for s in all_sessions if s.session_status == 'ACTIVE'])
        logged_out = len([s for s in all_sessions if s.session_status == 'LOGGED_OUT'])
        expired = len([s for s in all_sessions if s.session_status == 'EXPIRED'])
        
        return {
            'total_sessions': len(all_sessions),
            'active_sessions': active,
            'logged_out_sessions': logged_out,
            'expired_sessions': expired
        }
    
    @staticmethod
    def get_concurrent_active_sessions(user_id):
        """Get count of currently active sessions"""
        return UserSession.query.filter_by(
            user_id=user_id,
            session_status='ACTIVE'
        ).count()
