from flask import Blueprint, request, jsonify, render_template
from app import db
from app.models import User, Attendance, LeaveRequest, Salary
from datetime import datetime, date, timedelta
from werkzeug.security import check_password_hash
import csv
from io import StringIO, BytesIO
import json

bp = Blueprint('main', __name__)

def parse_datetime(value):
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None


@bp.route('/users', methods=['POST'])
def create_user():
    data = request.get_json() or []

    if not isinstance(data, list):
        return jsonify({'error': 'Expected a list of users'}), 400

    users = []

    for item in data:
        user = User(
            id=item.get('id'),
            name=item.get('name'),
            email=item.get('email'),
            password=item.get('password'),
            role=item.get('role', 'employee'),
            department=item.get('department'),
            designation=item.get('designation'),
            basic_salary=item.get('basic_salary', 0.0),
            hourly_rate=item.get('hourly_rate', 150.0)
        )
        users.append(user)

    db.session.add_all(users)
    db.session.commit()

    return jsonify({
        'count': len(users),
        'ids': [user.id for user in users]
    }), 201


@bp.route('/attendance', methods=['POST'])
def create_attendance():
    data = request.get_json() or {}
    clock_in = parse_datetime(data.get('clock_in'))
    clock_out = parse_datetime(data.get('clock_out'))

    attendance = Attendance(
        id=data.get('id'),
        user_id=data.get('user_id'),
        clock_in=clock_in,
        clock_out=clock_out,
        date=data.get('date'),
        worked_hours=data.get('worked_hours'),
        regular_hours=data.get('regular_hours'),
        overtime_hours=data.get('overtime_hours')
    )
    db.session.add(attendance)
    db.session.commit()
    return jsonify({'id': attendance.id}), 201


@bp.route('/leave_requests', methods=['POST'])
def create_leave():
    data = request.get_json() or {}
    required = ['user_id', 'leave_type', 'from_date', 'to_date', 'reason']
   
    leave = LeaveRequest(
        id=data.get('id'),
        user_id=data.get('user_id'),
        leave_type=data.get('leave_type'),
        from_date=data.get('from_date'),
        to_date=data.get('to_date'),
        days=data.get('days'),
        reason=data.get('reason'),
        status=data.get('status', 'pending')
    )
    db.session.add(leave)
    db.session.commit()
    return jsonify({'id': leave.id}), 201


@bp.route('/salary', methods=['POST'])
def create_salary():
    data = request.get_json() or {}
    salary = Salary(
        id=data.get('id'),
        user_id=data.get('user_id'),
        month=data.get('month'),
        year=data.get('year'),
        basic_salary=data.get('basic_salary'),
        regular_pay=data.get('regular_pay'),
        overtime_pay=data.get('overtime_pay'),
        deductions=data.get('deductions'),
        working_days=data.get('working_days'),
        leaves_taken=data.get('leaves_taken'),
        total_hours=data.get('total_hours'),
        overtime_hours=data.get('overtime_hours'),
        present_days=data.get('present_days', 0),
        net_salary=data.get('net_salary', 0.0)
    )
    db.session.add(salary)
    db.session.commit()
    return jsonify({'id': salary.id}), 201


# ============= FRONTEND =============

@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400

    user = User.query.filter_by(email=email).first()
    
    if not user or user.password != password:  # In production, use werkzeug.security.check_password_hash
        return jsonify({'error': 'Invalid email or password'}), 401

    return jsonify({
        'user_id': user.id,
        'name': user.name,
        'email': user.email,
        'role': user.role,
        'department': user.department,
        'message': 'Login successful'
    }), 200


@bp.route('/dashboard/<int:user_id>', methods=['GET'])
def dashboard(user_id):
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
def get_attendance(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    month = request.args.get('month', type=int, default=date.today().month)
    year = request.args.get('year', type=int, default=date.today().year)

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
def get_salary(user_id):
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

    if not salary:
        # Create default salary record if not exists
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


# ============= MANAGER API ENDPOINTS =============

@bp.route('/manager/dashboard/<int:manager_id>', methods=['GET'])
def manager_dashboard(manager_id):
    """Get manager dashboard stats - shows ALL users"""
    manager = User.query.get(manager_id)
    if not manager or manager.role != 'manager':
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get ALL users from users table
    all_users = User.query.filter(User.role == 'employee').all()
    
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
        'manager_name': manager.name,
        'department': manager.department
    }), 200


@bp.route('/manager/leave-requests/<int:manager_id>', methods=['GET'])
def get_leave_requests(manager_id):
    """Get all leave requests from ALL employees"""
    manager = User.query.get(manager_id)
    if not manager or manager.role != 'manager':
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get ALL employees
    all_employees = User.query.filter(User.role == 'employee').all()
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
def approve_leave(request_id):
    """Approve a leave request - manager can approve any employee leave"""
    data = request.get_json() or {}
    manager_id = data.get('manager_id')
    
    manager = User.query.get(manager_id)
    if not manager or manager.role != 'manager':
        return jsonify({'error': 'Unauthorized'}), 403
    
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
def reject_leave(request_id):
    """Reject a leave request"""
    data = request.get_json() or {}
    manager_id = data.get('manager_id')
    
    manager = User.query.get(manager_id)
    if not manager or manager.role != 'manager':
        return jsonify({'error': 'Unauthorized'}), 403
    
    leave_request = LeaveRequest.query.get(request_id)
    if not leave_request:
        return jsonify({'error': 'Leave request not found'}), 404
    
    employee = User.query.get(leave_request.user_id)
    if employee.department != manager.department:
        return jsonify({'error': 'Cannot reject leaves from other departments'}), 403
    
    leave_request.status = 'rejected'
    db.session.commit()
    
    return jsonify({
        'message': 'Leave request rejected',
        'leave_request_id': leave_request.id,
        'status': 'rejected'
    }), 200


@bp.route('/manager/team-attendance/<int:manager_id>', methods=['GET'])
def get_team_attendance(manager_id):
    """Get team attendance data"""
    manager = User.query.get(manager_id)
    if not manager or manager.role != 'manager':
        return jsonify({'error': 'Unauthorized'}), 403
    
    month = request.args.get('month', type=int, default=date.today().month)
    year = request.args.get('year', type=int, default=date.today().year)
    
    team_members = User.query.filter_by(
        department=manager.department,
        role='employee'
    ).all()
    
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
def get_team_details(manager_id):
    """Get all team member details"""
    manager = User.query.get(manager_id)
    if not manager or manager.role != 'manager':
        return jsonify({'error': 'Unauthorized'}), 403
    
    team_members = User.query.filter_by(
        department=manager.department,
        role='employee'
    ).all()
    
    month = date.today().month
    year = date.today().year
    
    team_data = []
    for member in team_members:
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
def get_payroll_report(manager_id):
    """Generate payroll report for team"""
    manager = User.query.get(manager_id)
    if not manager or manager.role != 'manager':
        return jsonify({'error': 'Unauthorized'}), 403
    
    month = request.args.get('month', type=int, default=date.today().month)
    year = request.args.get('year', type=int, default=date.today().year)
    
    team_members = User.query.filter_by(
        department=manager.department,
        role='employee'
    ).all()
    
    payroll_data = []
    total_payroll = 0
    
    for member in team_members:
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
        'department': manager.department,
        'payroll': payroll_data,
        'total_payroll': round(total_payroll, 2)
    }), 200
