from app import db
from datetime import datetime
 
 
class User(db.Model):
    __tablename__ = 'users'
    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(100), nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role          = db.Column(db.String(20))
    department    = db.Column(db.String(100))
    designation   = db.Column(db.String(100))
    basic_salary  = db.Column(db.Float)
    hourly_rate   = db.Column(db.Float, default=150.0)
    def __init__(self, id, name, email, password, role='employee', department=None, designation=None, basic_salary=0.0, hourly_rate=150.0):
        self.id = id
        self.name = name
        self.email = email
        self.password = password
        self.role = role
        self.department = department
        self.designation = designation
        self.basic_salary = basic_salary
        self.hourly_rate = hourly_rate
 
 
class Attendance(db.Model):
    __tablename__ = 'attendance'
    id             = db.Column(db.Integer, primary_key=True)
    user_id        = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    clock_in       = db.Column(db.DateTime, nullable=True)
    clock_out      = db.Column(db.DateTime, nullable=True)
    date           = db.Column(db.Date, default=datetime.utcnow)
    worked_hours   = db.Column(db.Float)
    regular_hours  = db.Column(db.Float)
    overtime_hours = db.Column(db.Float)
    def __init__(self, id, user_id, clock_in, clock_out, date, worked_hours=0.0, regular_hours=0.0, overtime_hours=0.0):
        self.id = id
        self.user_id = user_id
        self.clock_in = clock_in
        self.clock_out = clock_out
        self.date = date or datetime.utcnow().date()
        self.worked_hours = worked_hours
        self.regular_hours = regular_hours
        self.overtime_hours = overtime_hours

 
class LeaveRequest(db.Model):
    __tablename__ = 'leave_requests'
    id             = db.Column(db.Integer, primary_key=True)
    user_id        = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    leave_type     = db.Column(db.String(50), nullable=False)
    from_date      = db.Column(db.Date, nullable=False)
    to_date        = db.Column(db.Date, nullable=False)
    days           = db.Column(db.Integer)
    reason         = db.Column(db.Text, nullable=False)
    status         = db.Column(db.String(20))
    applied_on     = db.Column(db.DateTime, default=datetime.utcnow)
    def __init__(self, id, user_id, leave_type, from_date, days, to_date, reason, status='pending'):
        self.id = id
        self.user_id = user_id
        self.leave_type = leave_type
        self.from_date = from_date
        self.days = days
        self.to_date = to_date
        self.days = days
        self.reason = reason
        self.status = status    
 
 
class Salary(db.Model):
    __tablename__ = 'salary'
    id             = db.Column(db.Integer, primary_key=True)
    user_id        = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    month          = db.Column(db.Integer, nullable=False)
    year           = db.Column(db.Integer, nullable=False)
    basic_salary   = db.Column(db.Float)
    regular_pay    = db.Column(db.Float)
    overtime_pay   = db.Column(db.Float)
    deductions     = db.Column(db.Float)
    working_days   = db.Column(db.Integer)
    leaves_taken   = db.Column(db.Integer)
    total_hours    = db.Column(db.Float)
    overtime_hours = db.Column(db.Float)
    present_days   = db.Column(db.Integer, default=0)
    net_salary     = db.Column(db.Float, default=0.0)
    def __init__(self,id, user_id, month, year, basic_salary=0.0, regular_pay=0.0, overtime_pay=0.0, deductions=0.0, working_days=0, leaves_taken=0, total_hours=0.0, overtime_hours=0.0, present_days=0, net_salary=0.0):
        self.id = id
        self.user_id = user_id
        self.month = month
        self.year = year
        self.basic_salary = basic_salary
        self.regular_pay = regular_pay
        self.overtime_pay = overtime_pay
        self.deductions = deductions
        self.working_days = working_days
        self.leaves_taken = leaves_taken
        self.total_hours = total_hours
        self.overtime_hours = overtime_hours
        self.present_days = present_days
        self.net_salary = net_salary