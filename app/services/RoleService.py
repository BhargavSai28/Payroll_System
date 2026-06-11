

from app import db
from app.models import Role, User, UserRole
from flask import jsonify


class RoleService:
    
    @staticmethod
    def create_role(role_name, permissions, description=None):
        """Create a new role"""
        normalized_role_name = role_name.upper()
        if Role.query.filter_by(role_name=normalized_role_name).first():
            return None, f"Role {normalized_role_name} already exists"
        
        role = Role(
            role_name=normalized_role_name,
            permissions=permissions,
            description=description
        )
        db.session.add(role)
        db.session.commit()
        return role, None
    
    @staticmethod
    def update_role(role_id, role_name=None, permissions=None, description=None):
        """Update an existing role"""
        role = Role.query.get(role_id)
        if not role:
            return None, "Role not found"
        
        if role_name:
            role.role_name = role_name.upper()
        if permissions is not None:
            role.permissions = permissions
        if description:
            role.description = description
        
        db.session.commit()
        return role, None
    
    @staticmethod
    def delete_role(role_id):
        """Delete a role"""
        role = Role.query.get(role_id)
        if not role:
            return False, "Role not found"
        
        # Check if role is assigned to users
        user_roles = UserRole.query.filter_by(role_id=role_id).count()
        if user_roles > 0:
            return False, f"Cannot delete role. {user_roles} users assigned to this role"
        
        db.session.delete(role)
        db.session.commit()
        return True, None
    
    @staticmethod
    def assign_role_to_user(user_id, role_id):
        """Assign a role to user"""
        user = User.query.get(user_id)
        if not user:
            return None, "User not found"
        
        role = Role.query.get(role_id)
        if not role:
            return None, "Role not found"
        
        # Check if already assigned
        existing = UserRole.query.filter_by(user_id=user_id, role_id=role_id).first()
        if existing:
            return None, "Role already assigned to user"
        
        user_role = UserRole(user_id=user_id, role_id=role_id)
        db.session.add(user_role)
        db.session.commit()
        return user_role, None

    @staticmethod
    def revoke_role_from_user(user_id, role_id):
        """Remove a role assignment from a user"""
        user_role = UserRole.query.filter_by(user_id=user_id, role_id=role_id).first()
        if not user_role:
            return False, "Role assignment not found"

        db.session.delete(user_role)
        db.session.commit()
        return True, None
    
    @staticmethod
    def get_user_roles(user_id):
        """Get all roles assigned to a user"""
        user_roles = UserRole.query.filter_by(user_id=user_id).all()
        return [ur.role for ur in user_roles]
    
    @staticmethod
    def get_all_roles():
        """Get all roles in the system"""
        return Role.query.all()
    
    @staticmethod
    def get_role_by_name(role_name):
        """Get role by name"""
        return Role.query.filter_by(role_name=role_name.upper()).first()
