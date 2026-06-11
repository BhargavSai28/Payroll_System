from flask import Blueprint, request, jsonify
from app import db
from app.models import Attendance, User, LeaveRequest, Salary
from datetime import datetime, date
from app.services.EmployeeServices import EmployeeServices
from app.auth import jwt_required

# instantiate service
userServices = EmployeeServices()

employee = Blueprint('employee', __name__)

@employee.route('/checkIn', methods=['POST'])
@jwt_required
def check_in(current_user):
    return userServices.checkIn(current_user.id)

 
@employee.route('/checkOut', methods=['POST'])
@jwt_required
def check_out(current_user):
    return userServices.checkOut(current_user.id)


@employee.route('/applyLeave', methods=['POST'])
@jwt_required
def apply_leave(current_user):
    data = request.get_json()
 
    leave_type = data.get('leave_type')
    from_date  = data.get('from_date')
    to_date    = data.get('to_date')
    reason     = data.get('reason')
 
    return userServices.ApplyLeave(current_user.id, from_date, to_date, reason, leave_type, current_user)


 
@employee.route('/viewAttendance', methods=['GET'])
@jwt_required
def view_attendance(current_user):
    user_id = current_user.id
    records = Attendance.query.filter_by(user_id=user_id).order_by(Attendance.date.desc()).all()
 
    if not records:
        return jsonify({'message': 'No attendance records found', 'user_id': user_id}), 404
    return userServices.viewAttendance(user_id, records,)


 
@employee.route('/monthlySalary', methods=['POST'])
@jwt_required
def monthly_Salary(current_user):
    data = request.get_json()
 
    user_id = current_user.id
    month   = data.get('month')
    year    = data.get('year')
    print(f"Received monthly salary request for user_id={user_id}, month={month}, year={year}")
    print(f"DEBUG: userServices type = {type(userServices)}")
    print(f"DEBUG: userServices.__class__.__module__ = {userServices.__class__.__module__}")
    if not month or not year:
        return jsonify({'error': 'month and year are required'}), 400
 
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return userServices.monthlySalary(user_id, month, year)
