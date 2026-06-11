"""
Manager Mapping Service
Handles manager-employee relationships and team management
"""

from app import db
from app.models import ManagerMapping, User, LeaveRequest
from datetime import datetime


class ManagerMappingService:
    
    @staticmethod
    def assign_manager(employee_id, manager_id):
        """Assign a manager to an employee"""
        employee = User.query.get(employee_id)
        if not employee:
            return None, "Employee not found"
        
        manager = User.query.get(manager_id)
        if not manager:
            return None, "Manager not found"
        
        # Check if already assigned
        existing = ManagerMapping.query.filter_by(
            user_id=employee_id, 
            manager_id=manager_id
        ).first()
        
        if existing:
            return None, "Manager already assigned to this employee"
        
        mapping = ManagerMapping(
            user_id=employee_id,
            manager_id=manager_id,
            assigned_at=datetime.utcnow()
        )
        db.session.add(mapping)
        db.session.commit()
        return mapping, None
    
    @staticmethod
    def update_manager(employee_id, new_manager_id):
        """Update manager for an employee"""
        mapping = ManagerMapping.query.filter_by(user_id=employee_id).first()
        if not mapping:
            return ManagerMappingService.assign_manager(employee_id, new_manager_id)
        
        manager = User.query.get(new_manager_id)
        if not manager:
            return None, "Manager not found"
        
        mapping.manager_id = new_manager_id
        mapping.assigned_at = datetime.utcnow()
        db.session.commit()
        return mapping, None
    
    @staticmethod
    def remove_manager(employee_id):
        """Remove manager assignment from employee"""
        mapping = ManagerMapping.query.filter_by(user_id=employee_id).first()
        if not mapping:
            return False, "No manager assigned to this employee"
        
        db.session.delete(mapping)
        db.session.commit()
        return True, None
    
    @staticmethod
    def get_manager_for_employee(employee_id):
        """Get the manager assigned to an employee"""
        mapping = ManagerMapping.query.filter_by(user_id=employee_id).first()
        if mapping:
            return mapping.manager
        return None
    
    @staticmethod
    def get_team_members(manager_id):
        """Get all employees managed by a manager"""
        mappings = ManagerMapping.query.filter_by(manager_id=manager_id).all()
        return [mapping.employee for mapping in mappings]
    
    @staticmethod
    def get_team_members_ids(manager_id):
        """Get IDs of all employees managed by a manager"""
        mappings = ManagerMapping.query.filter_by(manager_id=manager_id).all()
        return [mapping.user_id for mapping in mappings]
    
    @staticmethod
    def get_pending_leave_requests_for_manager(manager_id):
        """Get all pending leave requests from manager's team"""
        team_members = ManagerMappingService.get_team_members_ids(manager_id)
        leave_requests = LeaveRequest.query.filter(
            LeaveRequest.user_id.in_(team_members),
            LeaveRequest.status == 'pending'
        ).all()
        return leave_requests
    
    @staticmethod
    def get_manager_mapping_by_ids(employee_id, manager_id):
        """Get specific manager mapping"""
        return ManagerMapping.query.filter_by(
            user_id=employee_id,
            manager_id=manager_id
        ).first()
