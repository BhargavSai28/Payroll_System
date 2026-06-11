from flask import Blueprint, request, jsonify, render_template, current_app
from app import db
from app.models import User, Attendance, LeaveRequest, Salary, Role, UserRole
from app.auth import (create_access_token, jwt_required, normalize_role, roles_required,
                     get_user_primary_role, get_user_permissions, verify_password,
                     create_user_session, close_user_session, audit_log)
from datetime import datetime, date, timedelta
from werkzeug.security import check_password_hash
import jwt


bp = Blueprint('main', __name__)

def parse_datetime(value):
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None


def employee_query():
    return (
        User.query
        .join(UserRole, UserRole.user_id == User.id)
        .join(Role, Role.role_id == UserRole.role_id)
        .filter(Role.role_name == 'EMPLOYEE')
        .distinct()
    )


# ============= LOGIN & AUTHENTICATION =============

@bp.route('/login', methods=['POST'])
def login():
    """Enhanced login with session tracking"""
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400

    user = User.query.filter_by(email=email).first()
    
    password_ok = user and verify_password(user.password, password)
    if not password_ok:
        audit_log(None, 'LOGIN_FAILED', 'USER_AUTH', None, None, {'email': email})
        return jsonify({'error': 'Invalid email or password'}), 401

    # Create session
    session_id = create_user_session(user.id, request)
    
    # Get user role and permissions
    role = get_user_primary_role(user.id)
    permissions = get_user_permissions(user.id)
    
    # Create token with session
    token = create_access_token(user, session_id)
    
    audit_log(user.id, 'LOGIN', 'USER_AUTH', user.id, None, {'session_id': session_id})
    
    role_name = role.role_name if role else 'EMPLOYEE'

    return jsonify({
        'user_id': user.id,
        'name': user.name,
        'email': user.email,
        'role': role_name.lower(),
        'role_name': role_name,
        'permissions': permissions,
        'department': user.department,
        'session_id': session_id,
        'access_token': token,
        'token_type': 'Bearer',
        'message': 'Login successful'
    }), 200


@bp.route('/logout', methods=['POST'])
@jwt_required
def logout(current_user):
    """Logout and close session"""
    auth_header = request.headers.get('Authorization')
    if auth_header:
        try:
            token = auth_header.split(' ')[1]
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            session_id = data.get('session_id')
            if session_id:
                close_user_session(session_id)
        except:
            pass
    
    audit_log(current_user.id, 'LOGOUT', 'USER_AUTH', current_user.id, None, None)
    
    return jsonify({'message': 'Logout successful'}), 200


@bp.route('/me', methods=['GET'])
@jwt_required
def me(current_user):
    role = get_user_primary_role(current_user.id)
    permissions = get_user_permissions(current_user.id)
    
    return jsonify({
        'user_id': current_user.id,
        'name': current_user.name,
        'email': current_user.email,
        'role_name': role.role_name if role else 'EMPLOYEE',
        'permissions': permissions,
        'department': current_user.department,
        'designation': current_user.designation
    }), 200


@bp.route('/dashboard', methods=['GET'])
@jwt_required
def my_dashboard(current_user):
    user_role = get_user_primary_role(current_user.id)
    user_role_name = normalize_role(user_role.role_name if user_role else 'EMPLOYEE')
    if user_role_name == 'ADMIN':
        return _admin_dashboard(current_user)
    return _employee_dashboard(current_user.id)


@bp.route('/dashboard/<int:user_id>', methods=['GET'])
@jwt_required
def dashboard(current_user, user_id):
    user_role = get_user_primary_role(current_user.id)
    user_role_name = normalize_role(user_role.role_name if user_role else 'EMPLOYEE')
    if user_role_name != 'ADMIN' and current_user.id != user_id:
        return jsonify({'error': 'Forbidden'}), 403
    return _employee_dashboard(user_id)


def _employee_dashboard(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    today = date.today()
    
    # Today's attendance
    today_attendance = Attendance.query.filter_by(
        user_id=user_id, 
        date=today
    ).first()

    current_month_start = date(today.year, today.month, 1)
    if today.month == 12:
        current_month_end = date(today.year + 1, 1, 1) - timedelta(days=1)
    else:
        current_month_end = date(today.year, today.month + 1, 1) - timedelta(days=1)

    month_attendance = Attendance.query.filter(
        Attendance.user_id == user_id,
        Attendance.date >= current_month_start,
        Attendance.date <= current_month_end
    ).all()

    present_days = len([a for a in month_attendance if a.clock_in and a.clock_out])
    
    # Current salary
    salary_record = Salary.query.filter_by(
        user_id=user_id,
        month=today.month,
        year=today.year
    ).first()

    seven_days_ago = today - timedelta(days=7)
    recent = Attendance.query.filter(
        Attendance.user_id == user_id,
        Attendance.date >= seven_days_ago,
        Attendance.date <= today
    ).order_by(Attendance.date.desc()).all()

    recent_data = []
    for record in recent:
        recent_data.append({
            'date': record.date.isoformat(),
            'clock_in': record.clock_in.isoformat() if record.clock_in else None,
            'clock_out': record.clock_out.isoformat() if record.clock_out else None,
            'worked_hours': record.worked_hours or 0,
            'status': 'present' if record.clock_out else ('checked_in' if record.clock_in else 'absent')
        })

    return jsonify({
        'today_hours': (today_attendance.worked_hours or 0) if today_attendance else 0,
        'today_checkin': today_attendance.clock_in.isoformat() if today_attendance and today_attendance.clock_in else None,
        'today_checkout': today_attendance.clock_out.isoformat() if today_attendance and today_attendance.clock_out else None,
        'present_days': present_days,
        'leaves_taken': 0,
        'current_salary': (salary_record.net_salary if salary_record else 0),
        'recent_attendance': recent_data
    }), 200


@bp.route('/attendance/<int:user_id>', methods=['GET'])
@jwt_required
def get_attendance(current_user, user_id):
    user_role = get_user_primary_role(current_user.id)
    user_role_name = normalize_role(user_role.role_name if user_role else 'EMPLOYEE')
    if user_role_name != 'ADMIN' and current_user.id != user_id:
        return jsonify({'error': 'Forbidden'}), 403
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    month_arg = request.args.get('month', type=int)
    year_arg = request.args.get('year', type=int)

    if month_arg is None and year_arg is None:
        salaries = Salary.query.filter_by(user_id=user_id).order_by(
            Salary.year.desc(),
            Salary.month.desc()
        ).all()
        return jsonify([{
            'user_id': user_id,
            'month': salary.month,
            'year': salary.year,
            'basic_salary': salary.basic_salary or 0,
            'regular_pay': salary.regular_pay or 0,
            'overtime_pay': salary.overtime_pay or 0,
            'deductions': salary.deductions or 0,
            'net_salary': salary.net_salary or 0,
            'working_days': salary.working_days or 22,
            'present_days': salary.present_days or 0,
            'leaves_taken': salary.leaves_taken or 0,
            'total_hours': salary.total_hours or 0,
            'overtime_hours': salary.overtime_hours or 0
        } for salary in salaries]), 200

    month = month_arg or date.today().month
    year = year_arg or date.today().year

    # Get all attendance for the month
    attendance_records = Attendance.query.filter(
        Attendance.user_id == user_id,
        db.func.EXTRACT('month', Attendance.date) == month,
        db.func.EXTRACT('year', Attendance.date) == year
    ).all()

    # Prepare records
    records = []
    for record in attendance_records:
        status = 'absent'
        if record.clock_in and record.clock_out:
            status = 'present'
        elif record.clock_in:
            status = 'checked_in'

        records.append({
            'date': record.date.isoformat(),
            'clock_in': record.clock_in.isoformat() if record.clock_in else None,
            'clock_out': record.clock_out.isoformat() if record.clock_out else None,
            'worked_hours': record.worked_hours or 0,
            'regular_hours': record.regular_hours or 0,
            'overtime_hours': record.overtime_hours or 0,
            'status': status
        })

    # Calculate stats
    present_days = len([r for r in records if r['status'] == 'present'])
    absent_days = len([r for r in records if r['status'] == 'absent'])
    total_hours = sum([r['worked_hours'] for r in records])

    return jsonify({
        'records': records,
        'present_days': present_days,
        'absent_days': absent_days,
        'leave_days': 0,
        'total_hours': total_hours,
        'working_days': 22,  # Default working days
        'month': month,
        'year': year
    }), 200



@bp.route('/salary/<int:user_id>', methods=['GET'])
@jwt_required
def get_salary(current_user, user_id):
    user_role = get_user_primary_role(current_user.id)
    user_role_name = normalize_role(user_role.role_name if user_role else 'EMPLOYEE')
    if user_role_name != 'ADMIN' and current_user.id != user_id:
        return jsonify({'error': 'Forbidden'}), 403
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    month = request.args.get('month', type=int, default=date.today().month)
    year = request.args.get('year', type=int, default=date.today().year)

    salary = Salary.query.filter_by(
        user_id=user_id,
        month=month,
        year=year
    ).first()

    has_attendance = Attendance.query.filter(
        Attendance.user_id == user_id,
        db.func.EXTRACT('month', Attendance.date) == month,
        db.func.EXTRACT('year', Attendance.date) == year
    ).first()
    has_approved_leave = LeaveRequest.query.filter(
        LeaveRequest.user_id == user_id,
        LeaveRequest.status == 'approved',
        db.func.EXTRACT('month', LeaveRequest.from_date) == month,
        db.func.EXTRACT('year', LeaveRequest.from_date) == year
    ).first()

    if has_attendance or has_approved_leave:
        from app.services.EmployeeServices import EmployeeServices
        EmployeeServices().monthlySalary(user_id, month, year)
        salary = Salary.query.filter_by(
            user_id=user_id,
            month=month,
            year=year
        ).first()

    if not salary:
        # Create default salary response if not enough payroll data exists yet.
        return jsonify({
            'user_id': user_id,
            'month': month,
            'year': year,
            'basic_salary': user.basic_salary or 0,
            'regular_pay': 0,
            'overtime_pay': 0,
            'deductions': 0,
            'net_salary': 0,
            'working_days': 22,
            'present_days': 0,
            'leaves_taken': 0,
            'total_hours': 0,
            'overtime_hours': 0
        }), 200

    return jsonify({
        'user_id': user_id,
        'month': salary.month,
        'year': salary.year,
        'basic_salary': salary.basic_salary or 0,
        'regular_pay': salary.regular_pay or 0,
        'overtime_pay': salary.overtime_pay or 0,
        'deductions': salary.deductions or 0,
        'net_salary': salary.net_salary or 0,
        'working_days': salary.working_days or 22,
        'present_days': salary.present_days or 0,
        'leaves_taken': salary.leaves_taken or 0,
        'total_hours': salary.total_hours or 0,
        'overtime_hours': salary.overtime_hours or 0
    }), 200


@bp.route('/attendance/today/<int:user_id>', methods=['GET'])
@jwt_required
def get_today_attendance(current_user, user_id):
    """Get today's attendance status"""
    if current_user.id != user_id:
        return jsonify({'error': 'Forbidden'}), 403
    
    today = date.today()
    record = Attendance.query.filter_by(
        user_id=user_id,
        date=today
    ).first()
    
    if not record:
        return jsonify({'record': None}), 200
    
    return jsonify({
        'record': {
            'date': record.date.isoformat(),
            'clock_in': record.clock_in.isoformat() if record.clock_in else None,
            'clock_out': record.clock_out.isoformat() if record.clock_out else None,
            'status': 'checked_out' if record.clock_out else 'checked_in'
        }
    }), 200


@bp.route('/checkin', methods=['POST'])
@jwt_required
def api_checkin(current_user):
    """Check-in endpoint"""
    user_id = current_user.id
    today = date.today()
    
    # Check if already checked in today
    existing = Attendance.query.filter_by(user_id=user_id, date=today).first()
    
    if existing:
        if existing.clock_in:
            return jsonify({'error': 'Already checked in today'}), 400
        # Update existing record
        existing.clock_in = datetime.now()
        db.session.commit()
        return jsonify({'message': 'Check-in successful', 'clock_in': existing.clock_in.isoformat()}), 200
    
    # Create new attendance record
    attendance = Attendance(
        user_id=user_id,
        date=today,
        clock_in=datetime.now()
    )
    db.session.add(attendance)
    db.session.commit()
    
    return jsonify({'message': 'Check-in successful', 'clock_in': attendance.clock_in.isoformat()}), 200


@bp.route('/checkout', methods=['POST'])
@jwt_required
def api_checkout(current_user):
    """Check-out endpoint"""
    user_id = current_user.id
    today = date.today()
    
    attendance = Attendance.query.filter_by(user_id=user_id, date=today).first()
    
    if not attendance:
        return jsonify({'error': 'No check-in found for today'}), 404
    
    if attendance.clock_out:
        return jsonify({'error': 'Already checked out today'}), 400
    
    attendance.clock_out = datetime.now()
    
    # Calculate worked hours
    if attendance.clock_in:
        worked_hours = (attendance.clock_out - attendance.clock_in).total_seconds() / 3600
        attendance.worked_hours = round(worked_hours, 2)
        
        # Simple logic: hours up to 8 are regular, rest is overtime
        if worked_hours <= 8:
            attendance.regular_hours = round(worked_hours, 2)
            attendance.overtime_hours = 0
        else:
            attendance.regular_hours = 8
            attendance.overtime_hours = round(worked_hours - 8, 2)
    
    db.session.commit()
    
    return jsonify({
        'message': 'Check-out successful',
        'clock_out': attendance.clock_out.isoformat(),
        'worked_hours': attendance.worked_hours
    }), 200


# ============= MANAGER API ENDPOINTS =============

@bp.route('/manager/dashboard/<int:manager_id>', methods=['GET'])
@roles_required('admin')
def manager_dashboard(current_user, manager_id):
    return _admin_dashboard(current_user)


def _admin_dashboard(admin_user):
    """Get admin dashboard stats - shows all employees"""
    all_users = employee_query().all()
    
    team_count = len(all_users)
    
    # Get pending leave requests from all employees
    pending_leaves = LeaveRequest.query.filter(
        LeaveRequest.user_id.in_([m.id for m in all_users]),
        LeaveRequest.status == 'pending'
    ).all()
    
    # Get today's attendance from all employees
    today = date.today()
    today_present = Attendance.query.filter(
        Attendance.user_id.in_([m.id for m in all_users]),
        Attendance.date == today,
        Attendance.clock_in.isnot(None),
        Attendance.clock_out.isnot(None)
    ).count()
    
    return jsonify({
        'team_count': team_count,
        'pending_leaves': len(pending_leaves),
        'today_present': today_present,
        'manager_name': admin_user.name,
        'admin_name': admin_user.name,
        'department': admin_user.department
    }), 200


@bp.route('/manager/leave-requests/<int:manager_id>', methods=['GET'])
@roles_required('admin')
def get_leave_requests(current_user, manager_id):
    """Get all leave requests from all employees"""
    
    # Get ALL employees
    all_employees = employee_query().all()
    team_ids = [m.id for m in all_employees]
    
    status_filter = request.args.get('status', 'pending')
    
    leaves = LeaveRequest.query.filter(
        LeaveRequest.user_id.in_(team_ids),
        LeaveRequest.status == status_filter
    ).order_by(LeaveRequest.applied_on.desc()).all()
    
    result = []
    for leave in leaves:
        employee = User.query.get(leave.user_id)
        result.append({
            'id': leave.id,
            'user_id': leave.user_id,
            'employee_name': employee.name,
            'employee_email': employee.email,
            'leave_type': leave.leave_type,
            'from_date': leave.from_date.isoformat(),
            'to_date': leave.to_date.isoformat(),
            'days': leave.days,
            'reason': leave.reason,
            'status': leave.status,
            'applied_on': leave.applied_on.isoformat()
        })
    
    return jsonify(result), 200


@bp.route('/manager/leave-request/<int:request_id>/approve', methods=['POST'])
@roles_required('admin')
def approve_leave(current_user, request_id):
    """Approve a leave request"""
    leave_request = LeaveRequest.query.get(request_id)
    if not leave_request:
        return jsonify({'error': 'Leave request not found'}), 404
    
    leave_request.status = 'approved'
    db.session.commit()
    
    return jsonify({
        'message': 'Leave request approved',
        'leave_request_id': leave_request.id,
        'status': 'approved'
    }), 200


@bp.route('/manager/leave-request/<int:request_id>/reject', methods=['POST'])
@roles_required('admin')
def reject_leave(current_user, request_id):
    """Reject a leave request"""
    leave_request = LeaveRequest.query.get(request_id)
    if not leave_request:
        return jsonify({'error': 'Leave request not found'}), 404

    leave_request.status = 'rejected'
    db.session.commit()
    
    return jsonify({
        'message': 'Leave request rejected',
        'leave_request_id': leave_request.id,
        'status': 'rejected'
    }), 200


@bp.route('/manager/team-attendance/<int:manager_id>', methods=['GET'])
@roles_required('admin')
def get_team_attendance(current_user, manager_id):
    """Get team attendance data"""
    month = request.args.get('month', type=int, default=date.today().month)
    year = request.args.get('year', type=int, default=date.today().year)
    
    team_members = employee_query().all()
    
    team_data = []
    for member in team_members:
        attendance_records = Attendance.query.filter(
            Attendance.user_id == member.id,
            db.func.EXTRACT('month', Attendance.date) == month,
            db.func.EXTRACT('year', Attendance.date) == year
        ).all()
        
        present_days = len([a for a in attendance_records if a.clock_in and a.clock_out])
        absent_days = len([a for a in attendance_records if not a.clock_in])
        total_hours = sum([a.worked_hours or 0 for a in attendance_records])
        
        team_data.append({
            'user_id': member.id,
            'name': member.name,
            'designation': member.designation,
            'present_days': present_days,
            'absent_days': absent_days,
            'total_hours': round(total_hours, 2)
        })
    
    return jsonify({
        'month': month,
        'year': year,
        'team_attendance': team_data
    }), 200


@bp.route('/manager/team-details/<int:manager_id>', methods=['GET'])
@roles_required('admin')
def get_team_details(current_user, manager_id):
    """Get all team member details"""
    team_members = employee_query().all()
    
    month = date.today().month
    year = date.today().year
    
    team_data = []
    from app.services.EmployeeServices import EmployeeServices
    salary_service = EmployeeServices()

    for member in team_members:
        has_attendance = Attendance.query.filter(
            Attendance.user_id == member.id,
            db.func.EXTRACT('month', Attendance.date) == month,
            db.func.EXTRACT('year', Attendance.date) == year
        ).first()
        has_approved_leave = LeaveRequest.query.filter(
            LeaveRequest.user_id == member.id,
            LeaveRequest.status == 'approved',
            db.func.EXTRACT('month', LeaveRequest.from_date) == month,
            db.func.EXTRACT('year', LeaveRequest.from_date) == year
        ).first()

        if has_attendance or has_approved_leave:
            salary_service.monthlySalary(member.id, month, year)

        # Get salary info
        salary = Salary.query.filter_by(
            user_id=member.id,
            month=month,
            year=year
        ).first()
        
        # Get attendance
        attendance_records = Attendance.query.filter(
            Attendance.user_id == member.id,
            db.func.EXTRACT('month', Attendance.date) == month,
            db.func.EXTRACT('year', Attendance.date) == year
        ).all()
        
        present_days = len([a for a in attendance_records if a.clock_in and a.clock_out])
        total_hours = sum([a.worked_hours or 0 for a in attendance_records])
        
        team_data.append({
            'user_id': member.id,
            'name': member.name,
            'email': member.email,
            'designation': member.designation,
            'basic_salary': member.basic_salary or 0,
            'hourly_rate': member.hourly_rate or 0,
            'present_days': present_days,
            'total_hours': round(total_hours, 2),
            'net_salary': salary.net_salary if salary else 0
        })
    
    return jsonify(team_data), 200


@bp.route('/manager/payroll-report/<int:manager_id>', methods=['GET'])
@roles_required('admin')
def get_payroll_report(current_user, manager_id):
    """Generate payroll report for team"""
    month = request.args.get('month', type=int, default=date.today().month)
    year = request.args.get('year', type=int, default=date.today().year)
    
    team_members = employee_query().all()
    
    payroll_data = []
    total_payroll = 0
    from app.services.EmployeeServices import EmployeeServices
    salary_service = EmployeeServices()
    
    for member in team_members:
        has_attendance = Attendance.query.filter(
            Attendance.user_id == member.id,
            db.func.EXTRACT('month', Attendance.date) == month,
            db.func.EXTRACT('year', Attendance.date) == year
        ).first()
        has_approved_leave = LeaveRequest.query.filter(
            LeaveRequest.user_id == member.id,
            LeaveRequest.status == 'approved',
            db.func.EXTRACT('month', LeaveRequest.from_date) == month,
            db.func.EXTRACT('year', LeaveRequest.from_date) == year
        ).first()

        if has_attendance or has_approved_leave:
            salary_service.monthlySalary(member.id, month, year)

        salary = Salary.query.filter_by(
            user_id=member.id,
            month=month,
            year=year
        ).first()
        
        if salary:
            payroll_data.append({
                'user_id': member.id,
                'name': member.name,
                'designation': member.designation,
                'basic_salary': salary.basic_salary or 0,
                'regular_pay': salary.regular_pay or 0,
                'overtime_pay': salary.overtime_pay or 0,
                'deductions': salary.deductions or 0,
                'net_salary': salary.net_salary or 0,
                'present_days': salary.present_days or 0,
                'leaves_taken': salary.leaves_taken or 0
            })
            total_payroll += salary.net_salary or 0
    
    return jsonify({
        'month': month,
        'year': year,
        'department': current_user.department,
        'payroll': payroll_data,
        'total_payroll': round(total_payroll, 2)
    }), 200
