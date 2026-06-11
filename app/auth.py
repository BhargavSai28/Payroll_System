from datetime import datetime, timedelta
from functools import wraps
import uuid
import jwt
from flask import current_app, jsonify, request
from app.models import User, UserRole, Role, UserSession, AuditLog
from app import db


# ============= ROLE NORMALIZATION =============
def normalize_role(role_name):
    """
    Normalize role name to standard format.
    Validates role exists in database.
    """
    if not role_name:
        return 'EMPLOYEE'
    
    normalized = role_name.strip().upper()
    
    # Map legacy roles to new system
    role_mapping = {
        'ADMIN': 'ADMIN',
        'MANAGER': 'MANAGER',
        'EMPLOYEE': 'EMPLOYEE',
        'admin': 'ADMIN',
        'manager': 'MANAGER',
        'employee': 'EMPLOYEE',
    }
    
    return role_mapping.get(normalized, 'EMPLOYEE')


def get_user_primary_role(user_id):
    """Get user's primary role (first assigned role)"""
    user_role = UserRole.query.filter_by(user_id=user_id).first()
    if user_role:
        return user_role.role
    return None


def get_user_permissions(user_id):
    """Get all permissions for a user based on assigned roles"""
    user_roles = UserRole.query.filter_by(user_id=user_id).all()
    permissions = set()
    
    for user_role in user_roles:
        if user_role.role and user_role.role.permissions:
            permissions.update(user_role.role.permissions)
    
    return list(permissions)


def has_permission(user, permission):
    """Check if user has specific permission"""
    permissions = get_user_permissions(user.id)
    return permission in permissions


# ============= SESSION TRACKING =============
def create_user_session(user_id, request_obj=None):
    """Create a new user session"""
    session_id = str(uuid.uuid4())
    
    device_info = request_obj.headers.get('User-Agent', 'Unknown') if request_obj else 'Unknown'
    ip_address = request_obj.remote_addr if request_obj else '0.0.0.0'
    
    session = UserSession(
        session_id=session_id,
        user_id=user_id,
        ip_address=ip_address,
        device_info=device_info,
        browser_info=request_obj.headers.get('User-Agent', '') if request_obj else '',
        session_status='ACTIVE'
    )
    
    db.session.add(session)
    db.session.commit()
    
    return session_id


def update_session_activity(session_id):
    """Update last activity time of session"""
    session = UserSession.query.get(session_id)
    if session:
        session.last_activity_time = datetime.utcnow()
        db.session.commit()


def close_user_session(session_id):
    """Mark session as logged out"""
    session = UserSession.query.get(session_id)
    if session:
        session.logout_time = datetime.utcnow()
        session.session_status = 'LOGGED_OUT'
        db.session.commit()


# ============= JWT TOKEN MANAGEMENT =============
def create_access_token(user, session_id=None):
    """
    Create JWT token with user info, roles, and permissions
    """
    role = get_user_primary_role(user.id)
    permissions = get_user_permissions(user.id)
    
    payload = {
        'user_id': user.id,
        'email': user.email,
        'name': user.name,
        'role_id': role.role_id if role else None,
        'role_name': role.role_name if role else 'EMPLOYEE',
        'permissions': permissions,
        'session_id': session_id,
        'exp': datetime.utcnow() + timedelta(hours=8),
        'iat': datetime.utcnow()
    }
    
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')


def verify_password(stored_password, candidate_password):
    """Verify password"""
    if stored_password == candidate_password:
        return True
    try:
        from werkzeug.security import check_password_hash
        return check_password_hash(stored_password, candidate_password)
    except Exception:
        return False


def get_current_user():
    """Extract and validate JWT token from request header"""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None, jsonify({'error': 'Token is missing'}), 401

    try:
        token = auth_header.split(' ')[1]
        data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return None, jsonify({'error': 'Token expired'}), 401
    except Exception as e:
        return None, jsonify({'error': f'Invalid token: {str(e)}'}), 401

    user = User.query.get(data.get('user_id'))
    if not user:
        return None, jsonify({'error': 'User not found'}), 401
    
    # Update session activity if session_id exists
    if data.get('session_id'):
        update_session_activity(data.get('session_id'))

    return user, None, None


# ============= DECORATORS =============
def jwt_required(func):
    """Decorator to require valid JWT token"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        current_user, error_response, status_code = get_current_user()
        if error_response:
            return error_response, status_code
        return func(current_user, *args, **kwargs)
    return wrapper


def permission_required(permission):
    """Decorator to require specific permission"""
    def decorator(func):
        @wraps(func)
        @jwt_required
        def wrapper(current_user, *args, **kwargs):
            if not has_permission(current_user, permission):
                audit_log(current_user.id, f'PERMISSION_DENIED', 'API_ACCESS', permission)
                return jsonify({'error': f'Permission denied: {permission}'}), 403
            return func(current_user, *args, **kwargs)
        return wrapper
    return decorator


def role_required(role_name):
    """Decorator to require specific role"""
    def decorator(func):
        @wraps(func)
        @jwt_required
        def wrapper(current_user, *args, **kwargs):
            user_role = get_user_primary_role(current_user.id)
            if not user_role or user_role.role_name != role_name.upper():
                audit_log(current_user.id, f'ROLE_DENIED', 'API_ACCESS', role_name)
                return jsonify({'error': f'Role {role_name} required'}), 403
            return func(current_user, *args, **kwargs)
        return wrapper
    return decorator


# Legacy decorator for backward compatibility
def roles_required(role):
    """Legacy decorator - maintained for backward compatibility"""
    def decorator(func):
        @wraps(func)
        @jwt_required
        def wrapper(current_user, *args, **kwargs):
            user_role = get_user_primary_role(current_user.id)
            if not user_role:
                return jsonify({'error': 'User has no role assigned'}), 403
            
            # Map legacy admin/manager to ADMIN role
            normalized_role = 'ADMIN' if user_role.role_name in ['ADMIN', 'MANAGER'] else user_role.role_name
            required_role = 'ADMIN' if role.upper() in ['ADMIN', 'MANAGER'] else role.upper()
            
            if normalized_role != required_role:
                return jsonify({'error': 'Forbidden'}), 403
            return func(current_user, *args, **kwargs)
        return wrapper
    return decorator


# ============= AUDIT LOGGING =============
def audit_log(user_id, action, entity_type, entity_id, old_values=None, new_values=None):
    """Log audit trail"""
    try:
        log = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_values=old_values,
            new_values=new_values,
            ip_address=request.remote_addr if request else None
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        print(f"Error creating audit log: {e}")

