from app import db
from datetime import datetime
import json


# ============= ROLES TABLE =============
class Role(db.Model):
    __tablename__ = 'roles'
    role_id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String(50), unique=True, nullable=False)
    permissions = db.Column(db.JSON, nullable=False, default={})
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user_roles = db.relationship('UserRole', backref='role', lazy=True, cascade='all, delete-orphan')
    payslips = db.relationship('Payslip', backref='role', lazy=True)


# ============= UPDATED USERS TABLE =============
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    department = db.Column(db.String(100))
    designation = db.Column(db.String(100))
    basic_salary = db.Column(db.Float, default=0.0)
    hourly_rate = db.Column(db.Float, default=150.0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user_roles = db.relationship('UserRole', backref='user', lazy=True, cascade='all, delete-orphan')
    manager_mappings = db.relationship('ManagerMapping', foreign_keys='ManagerMapping.user_id', backref='employee', lazy=True)
    managed_employees = db.relationship('ManagerMapping', foreign_keys='ManagerMapping.manager_id', backref='manager', lazy=True)
    sessions = db.relationship('UserSession', backref='user', lazy=True, cascade='all, delete-orphan')
    attendance = db.relationship('Attendance', backref='user', lazy=True, cascade='all, delete-orphan')
    leave_requests = db.relationship('LeaveRequest', foreign_keys='LeaveRequest.user_id', backref='employee', lazy=True, cascade='all, delete-orphan')
    approved_leaves = db.relationship('LeaveRequest', foreign_keys='LeaveRequest.approved_by', backref='approver', lazy=True)
    salary_records = db.relationship('SalaryRecord', backref='user', lazy=True, cascade='all, delete-orphan')
    salary_deductions = db.relationship('SalaryDeduction', backref='user', lazy=True, cascade='all, delete-orphan')
    payslips = db.relationship('Payslip', backref='user', lazy=True, cascade='all, delete-orphan')
    audit_logs = db.relationship('AuditLog', backref='user', lazy=True, cascade='all, delete-orphan')


# ============= USER ROLE MAPPING TABLE =============
class UserRole(db.Model):
    __tablename__ = 'user_roles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.role_id'), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'role_id', name='uq_user_role'),)


# ============= MANAGER MAPPING TABLE =============
class ManagerMapping(db.Model):
    __tablename__ = 'manager_mapping'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    manager_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'manager_id', name='uq_user_manager'),)


# ============= USER SESSION TRACKING TABLE =============
class UserSession(db.Model):
    __tablename__ = 'user_sessions'
    session_id = db.Column(db.String(255), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    login_time = db.Column(db.DateTime, default=datetime.utcnow)
    logout_time = db.Column(db.DateTime, nullable=True)
    last_activity_time = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(50))
    device_info = db.Column(db.String(255))
    browser_info = db.Column(db.String(255))
    operating_system = db.Column(db.String(100))
    session_status = db.Column(db.String(20), default='ACTIVE')  # ACTIVE, LOGGED_OUT, EXPIRED
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============= ATTENDANCE TABLE =============
class Attendance(db.Model):
    __tablename__ = 'attendance'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    clock_in = db.Column(db.DateTime, nullable=True)
    clock_out = db.Column(db.DateTime, nullable=True)
    date = db.Column(db.Date, default=datetime.utcnow)
    worked_hours = db.Column(db.Float, default=0.0)
    regular_hours = db.Column(db.Float, default=0.0)
    overtime_hours = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============= LEAVE REQUEST TABLE =============
class LeaveRequest(db.Model):
    __tablename__ = 'leave_requests'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    leave_type = db.Column(db.String(50), nullable=False)
    from_date = db.Column(db.Date, nullable=False)
    to_date = db.Column(db.Date, nullable=False)
    days = db.Column(db.Integer)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')
    applied_on = db.Column(db.DateTime, default=datetime.utcnow)
    approved_on = db.Column(db.DateTime, nullable=True)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============= SALARY RECORD TABLE =============
class SalaryRecord(db.Model):
    __tablename__ = 'salary_records'
    salary_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    basic_salary = db.Column(db.Float, nullable=False)
    allowances = db.Column(db.Float, default=0.0)
    bonus = db.Column(db.Float, default=0.0)
    other_earnings = db.Column(db.Float, default=0.0)
    gross_salary = db.Column(db.Float)
    effective_from = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============= SALARY DEDUCTIONS TABLE =============
class SalaryDeduction(db.Model):
    __tablename__ = 'salary_deductions'
    deduction_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    deduction_type = db.Column(db.String(50), nullable=False)
    deduction_amount = db.Column(db.Float, nullable=False)
    deduction_reason = db.Column(db.String(255))
    deduction_month = db.Column(db.Integer)
    deduction_year = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============= PAYSLIP TABLE =============
class Payslip(db.Model):
    __tablename__ = 'payslips'
    payslip_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.role_id'), nullable=True)
    role_name = db.Column(db.String(50))
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    total_salary = db.Column(db.Float)
    unpaid_leave_days = db.Column(db.Integer, default=0)
    loss_of_pay_amount = db.Column(db.Float, default=0.0)
    total_other_deductions = db.Column(db.Float, default=0.0)
    net_salary = db.Column(db.Float)
    payslip_file_name = db.Column(db.String(255))
    payslip_file_path = db.Column(db.String(500))
    email_sent = db.Column(db.Boolean, default=False)
    email_sent_at = db.Column(db.DateTime, nullable=True)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'month', 'year', name='uq_user_month_year'),)


# ============= AUDIT LOG TABLE =============
class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    audit_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    entity_type = db.Column(db.String(50), nullable=False)
    entity_id = db.Column(db.Integer)
    old_values = db.Column(db.JSON)
    new_values = db.Column(db.JSON)
    ip_address = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# Legacy Salary table (kept for backward compatibility - can be deprecated later)
class Salary(db.Model):
    __tablename__ = 'salary'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    basic_salary = db.Column(db.Float)
    regular_pay = db.Column(db.Float)
    overtime_pay = db.Column(db.Float)
    deductions = db.Column(db.Float)
    working_days = db.Column(db.Integer)
    leaves_taken = db.Column(db.Integer)
    total_hours = db.Column(db.Float)
    overtime_hours = db.Column(db.Float)
    present_days = db.Column(db.Integer, default=0)
    net_salary = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)