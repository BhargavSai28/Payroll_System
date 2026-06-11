"""
Payroll Management APIs
Handles all payroll-related operations
"""

from flask import Blueprint, request, jsonify, current_app, send_file
from app import db
from app.models import (Role, User, UserRole, ManagerMapping, UserSession, 
                       SalaryRecord, SalaryDeduction, Payslip, AuditLog, LeaveRequest)
from app.auth import (jwt_required, permission_required, role_required, 
                     get_user_primary_role, get_user_permissions, audit_log,
                     create_user_session, close_user_session)
from app.services.RoleService import RoleService
from app.services.ManagerMappingService import ManagerMappingService
from app.services.SessionService import SessionService
from app.services.SalaryService import SalaryService
from app.services.PayslipService import PayslipService
from app.services.PDFPayslipGenerator import PDFPayslipGenerator
from app.services.EmailService import EmailService
from datetime import datetime
import os


payroll_bp = Blueprint('payroll', __name__)


# ============= ROLE MANAGEMENT APIs =============

@payroll_bp.route('/roles', methods=['GET'])
@permission_required('role_management')
def get_all_roles(current_user):
    """Get all roles"""
    roles = RoleService.get_all_roles()
    
    result = []
    for role in roles:
        result.append({
            'role_id': role.role_id,
            'role_name': role.role_name,
            'permissions': role.permissions,
            'description': role.description,
            'created_at': role.created_at.isoformat(),
            'updated_at': role.updated_at.isoformat()
        })
    
    return jsonify(result), 200


@payroll_bp.route('/roles', methods=['POST'])
@role_required('ADMIN')
def create_role(current_user):
    """Create a new role"""
    data = request.get_json()
    
    role_name = data.get('role_name')
    permissions = data.get('permissions', [])
    description = data.get('description')
    
    if not role_name:
        return jsonify({'error': 'role_name is required'}), 400
    
    role, error = RoleService.create_role(role_name, permissions, description)
    if error:
        return jsonify({'error': error}), 409
    
    audit_log(current_user.id, 'CREATE', 'ROLE', role.role_id, None, {
        'role_name': role.role_name,
        'permissions': role.permissions
    })
    
    return jsonify({
        'role_id': role.role_id,
        'role_name': role.role_name,
        'permissions': role.permissions,
        'message': 'Role created successfully'
    }), 201


@payroll_bp.route('/roles/<int:role_id>', methods=['PUT'])
@role_required('ADMIN')
def update_role(current_user, role_id):
    """Update a role"""
    data = request.get_json()
    
    role, error = RoleService.update_role(
        role_id,
        role_name=data.get('role_name'),
        permissions=data.get('permissions'),
        description=data.get('description')
    )
    
    if error:
        return jsonify({'error': error}), 400
    
    audit_log(current_user.id, 'UPDATE', 'ROLE', role_id, None, {
        'role_name': role.role_name,
        'permissions': role.permissions
    })
    
    return jsonify({
        'role_id': role.role_id,
        'role_name': role.role_name,
        'message': 'Role updated successfully'
    }), 200


@payroll_bp.route('/roles/<int:role_id>', methods=['DELETE'])
@role_required('ADMIN')
def delete_role(current_user, role_id):
    """Delete a role"""
    success, error = RoleService.delete_role(role_id)
    
    if not success:
        return jsonify({'error': error}), 400
    
    audit_log(current_user.id, 'DELETE', 'ROLE', role_id, None, None)
    
    return jsonify({'message': 'Role deleted successfully'}), 200


@payroll_bp.route('/users/<int:user_id>/roles', methods=['POST'])
@role_required('ADMIN')
def assign_role(current_user, user_id):
    """Assign a role to user"""
    data = request.get_json()
    role_id = data.get('role_id')
    
    if not role_id:
        return jsonify({'error': 'role_id is required'}), 400
    
    user_role, error = RoleService.assign_role_to_user(user_id, role_id)
    if error:
        return jsonify({'error': error}), 400
    
    audit_log(current_user.id, 'ASSIGN_ROLE', 'USER', user_id, None, {'role_id': role_id})
    
    return jsonify({
        'user_id': user_id,
        'role_id': role_id,
        'message': 'Role assigned successfully'
    }), 201


@payroll_bp.route('/users/<int:user_id>/roles/<int:role_id>', methods=['DELETE'])
@role_required('ADMIN')
def revoke_role(current_user, user_id, role_id):
    """Revoke a role from user"""
    success, error = RoleService.revoke_role_from_user(user_id, role_id)
    
    if not success:
        return jsonify({'error': error}), 400
    
    audit_log(current_user.id, 'REVOKE_ROLE', 'USER', user_id, {'role_id': role_id}, None)
    
    return jsonify({'message': 'Role revoked successfully'}), 200


# ============= MANAGER MAPPING APIs =============

@payroll_bp.route('/manager-mapping', methods=['POST'])
@role_required('ADMIN')
def assign_manager(current_user):
    """Assign a manager to an employee"""
    data = request.get_json()
    
    employee_id = data.get('employee_id')
    manager_id = data.get('manager_id')
    
    if not employee_id or not manager_id:
        return jsonify({'error': 'employee_id and manager_id are required'}), 400
    
    mapping, error = ManagerMappingService.assign_manager(employee_id, manager_id)
    if error:
        return jsonify({'error': error}), 400
    
    audit_log(current_user.id, 'ASSIGN_MANAGER', 'EMPLOYEE', employee_id, 
              None, {'manager_id': manager_id})
    
    return jsonify({
        'id': mapping.id,
        'employee_id': mapping.user_id,
        'manager_id': mapping.manager_id,
        'assigned_at': mapping.assigned_at.isoformat(),
        'message': 'Manager assigned successfully'
    }), 201


@payroll_bp.route('/manager-mapping/<int:employee_id>', methods=['PUT'])
@role_required('ADMIN')
def update_manager(current_user, employee_id):
    """Update manager for an employee"""
    data = request.get_json()
    new_manager_id = data.get('manager_id')
    
    if not new_manager_id:
        return jsonify({'error': 'manager_id is required'}), 400
    
    mapping, error = ManagerMappingService.update_manager(employee_id, new_manager_id)
    if error:
        return jsonify({'error': error}), 400
    
    audit_log(current_user.id, 'UPDATE_MANAGER', 'EMPLOYEE', employee_id,
              None, {'manager_id': new_manager_id})
    
    return jsonify({
        'employee_id': mapping.user_id,
        'manager_id': mapping.manager_id,
        'message': 'Manager updated successfully'
    }), 200


@payroll_bp.route('/team-members/<int:manager_id>', methods=['GET'])
@jwt_required
def get_team_members(current_user, manager_id):
    """Get all team members for a manager"""
    
    # Check if user is authorized (admin or the manager themselves)
    user_role = get_user_primary_role(current_user.id)
    if user_role.role_name != 'ADMIN' and current_user.id != manager_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    team_members = ManagerMappingService.get_team_members(manager_id)
    
    result = []
    for member in team_members:
        result.append({
            'user_id': member.id,
            'name': member.name,
            'email': member.email,
            'designation': member.designation,
            'department': member.department
        })
    
    return jsonify(result), 200


# ============= SESSION TRACKING APIs =============

@payroll_bp.route('/sessions/active', methods=['GET'])
@jwt_required
def get_active_sessions(current_user):
    """Get active sessions for current user"""
    sessions = SessionService.get_active_sessions(current_user.id)
    
    result = []
    for session in sessions:
        result.append({
            'session_id': session.session_id,
            'login_time': session.login_time.isoformat(),
            'last_activity_time': session.last_activity_time.isoformat(),
            'ip_address': session.ip_address,
            'device_info': session.device_info,
            'status': session.session_status
        })
    
    return jsonify(result), 200


@payroll_bp.route('/sessions/history', methods=['GET'])
@jwt_required
def get_session_history(current_user):
    """Get session history for current user"""
    limit = request.args.get('limit', 50, type=int)
    sessions = SessionService.get_session_history(current_user.id, limit)
    
    result = []
    for session in sessions:
        result.append({
            'session_id': session.session_id,
            'login_time': session.login_time.isoformat(),
            'logout_time': session.logout_time.isoformat() if session.logout_time else None,
            'duration_minutes': round((session.logout_time - session.login_time).total_seconds() / 60) if session.logout_time else None,
            'ip_address': session.ip_address,
            'status': session.session_status
        })
    
    return jsonify(result), 200


@payroll_bp.route('/sessions/<session_id>/logout', methods=['POST'])
@jwt_required
def force_logout_session(current_user, session_id):
    """Force logout a session"""
    session = SessionService.get_session_by_id(session_id)
    
    if not session or session.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    success, error = SessionService.force_logout_session(session_id)
    if not success:
        return jsonify({'error': error}), 400
    
    return jsonify({'message': 'Session logged out successfully'}), 200


# ============= SALARY MANAGEMENT APIs =============

@payroll_bp.route('/salary', methods=['POST'])
@role_required('ADMIN')
def create_salary(current_user):
    """Create salary record"""
    data = request.get_json()
    
    user_id = data.get('user_id')
    basic_salary = data.get('basic_salary')
    
    if not user_id or not basic_salary:
        return jsonify({'error': 'user_id and basic_salary are required'}), 400
    
    salary, error = SalaryService.create_salary_record(
        user_id,
        basic_salary,
        data.get('allowances', 0),
        data.get('bonus', 0),
        data.get('other_earnings', 0)
    )
    
    if error:
        return jsonify({'error': error}), 400
    
    audit_log(current_user.id, 'CREATE', 'SALARY_RECORD', salary.salary_id, None, {
        'user_id': user_id,
        'basic_salary': basic_salary
    })
    
    return jsonify({
        'salary_id': salary.salary_id,
        'user_id': user_id,
        'basic_salary': salary.basic_salary,
        'gross_salary': salary.gross_salary,
        'message': 'Salary record created'
    }), 201


@payroll_bp.route('/salary/<int:salary_id>', methods=['PUT'])
@role_required('ADMIN')
def update_salary(current_user, salary_id):
    """Update salary record"""
    data = request.get_json()
    
    salary, error = SalaryService.update_salary_record(
        salary_id,
        basic_salary=data.get('basic_salary'),
        allowances=data.get('allowances'),
        bonus=data.get('bonus'),
        other_earnings=data.get('other_earnings')
    )
    
    if error:
        return jsonify({'error': error}), 400
    
    audit_log(current_user.id, 'UPDATE', 'SALARY_RECORD', salary_id, None, data)
    
    return jsonify({
        'salary_id': salary.salary_id,
        'gross_salary': salary.gross_salary,
        'message': 'Salary record updated'
    }), 200


@payroll_bp.route('/deductions', methods=['POST'])
@role_required('ADMIN')
def add_deduction(current_user):
    """Add salary deduction"""
    data = request.get_json()
    
    user_id = data.get('user_id')
    deduction_type = data.get('deduction_type')
    amount = data.get('amount')
    
    if not all([user_id, deduction_type, amount]):
        return jsonify({'error': 'user_id, deduction_type, and amount are required'}), 400
    
    deduction, error = SalaryService.add_salary_deduction(
        user_id,
        deduction_type,
        amount,
        data.get('reason'),
        data.get('month'),
        data.get('year')
    )
    
    if error:
        return jsonify({'error': error}), 400
    
    audit_log(current_user.id, 'CREATE', 'SALARY_DEDUCTION', deduction.deduction_id, None, {
        'user_id': user_id,
        'deduction_type': deduction_type,
        'amount': amount
    })
    
    return jsonify({
        'deduction_id': deduction.deduction_id,
        'message': 'Deduction added successfully'
    }), 201


# ============= PAYSLIP APIs =============

@payroll_bp.route('/payslips/<int:user_id>/month/<int:month>/<int:year>', methods=['GET'])
@jwt_required
def get_payslip(current_user, user_id, month, year):
    """Get payslip for a specific month"""
    
    # Authorization check
    user_role = get_user_primary_role(current_user.id)
    if user_role.role_name != 'ADMIN' and current_user.id != user_id:
        # Check if current user is manager
        manager = ManagerMappingService.get_manager_for_employee(user_id)
        if not manager or manager.id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
    
    payslip = PayslipService.get_payslip_by_month(user_id, month, year)
    if not payslip:
        return jsonify({'error': 'Payslip not found'}), 404
    
    return jsonify({
        'payslip_id': payslip.payslip_id,
        'user_id': payslip.user_id,
        'month': payslip.month,
        'year': payslip.year,
        'role_name': payslip.role_name,
        'total_salary': payslip.total_salary,
        'unpaid_leave_days': payslip.unpaid_leave_days,
        'loss_of_pay_amount': payslip.loss_of_pay_amount,
        'total_deductions': payslip.total_other_deductions,
        'net_salary': payslip.net_salary,
        'email_sent': payslip.email_sent,
        'generated_at': payslip.generated_at.isoformat()
    }), 200


@payroll_bp.route('/payslips/<int:user_id>/download/<int:month>/<int:year>', methods=['GET'])
@jwt_required
def download_payslip(current_user, user_id, month, year):
    """Download payslip PDF"""
    
    # Authorization check
    user_role = get_user_primary_role(current_user.id)
    if user_role.role_name != 'ADMIN' and current_user.id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    payslip = PayslipService.get_payslip_by_month(user_id, month, year)
    if not payslip or not payslip.payslip_file_path:
        return jsonify({'error': 'Payslip PDF not found'}), 404
    
    filepath = payslip.payslip_file_path
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    
    return send_file(filepath, as_attachment=True, download_name=payslip.payslip_file_name)


@payroll_bp.route('/payslips/<int:user_id>/history', methods=['GET'])
@jwt_required
def get_payslip_history(current_user, user_id):
    """Get payslip history for employee"""
    
    # Authorization check
    user_role = get_user_primary_role(current_user.id)
    if user_role.role_name != 'ADMIN' and current_user.id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    payslips = PayslipService.get_user_payslips(user_id)
    
    result = []
    for payslip in payslips:
        result.append({
            'payslip_id': payslip.payslip_id,
            'month': payslip.month,
            'year': payslip.year,
            'total_salary': payslip.total_salary,
            'net_salary': payslip.net_salary,
            'email_sent': payslip.email_sent,
            'generated_at': payslip.generated_at.isoformat()
        })
    
    return jsonify(result), 200


@payroll_bp.route('/payslips/generate/<int:month>/<int:year>', methods=['POST'])
@role_required('ADMIN')
def generate_payslips_manual(current_user, month, year):
    """Manually generate payslips for a month"""
    
    data = request.get_json(silent=True) or {}
    user_ids = data.get('user_ids', [])
    
    if not user_ids:
        users = User.query.all()
        user_ids = [u.id for u in users]
    
    generated = 0
    failed = 0
    
    for user_id in user_ids:
        try:
            payslip, error = PayslipService.generate_payslip(user_id, month, year)
            if error:
                failed += 1
            else:
                generated += 1
        except Exception as e:
            failed += 1
    
    audit_log(current_user.id, 'GENERATE_PAYSLIPS', 'PAYROLL', 0, None, {
        'month': month,
        'year': year,
        'count': generated
    })
    
    return jsonify({
        'message': 'Payslip generation completed',
        'generated': generated,
        'failed': failed
    }), 200


@payroll_bp.route('/payroll/summary/<int:month>/<int:year>', methods=['GET'])
@permission_required('payroll_management')
def get_payroll_summary(current_user, month, year):
    """Get payroll summary for a month"""
    summary = PayslipService.get_payroll_summary(month, year)
    return jsonify(summary), 200


# ============= AUDIT LOG APIs =============

@payroll_bp.route('/audit-logs', methods=['GET'])
@role_required('ADMIN')
def get_audit_logs(current_user):
    """Get audit logs"""
    limit = request.args.get('limit', 100, type=int)
    action_filter = request.args.get('action')
    entity_type_filter = request.args.get('entity_type')
    
    query = AuditLog.query
    
    if action_filter:
        query = query.filter_by(action=action_filter)
    if entity_type_filter:
        query = query.filter_by(entity_type=entity_type_filter)
    
    logs = query.order_by(AuditLog.created_at.desc()).limit(limit).all()
    
    result = []
    for log in logs:
        user = User.query.get(log.user_id)
        result.append({
            'audit_id': log.audit_id,
            'user_name': user.name if user else 'System',
            'action': log.action,
            'entity_type': log.entity_type,
            'entity_id': log.entity_id,
            'old_values': log.old_values,
            'new_values': log.new_values,
            'ip_address': log.ip_address,
            'created_at': log.created_at.isoformat()
        })
    
    return jsonify(result), 200
