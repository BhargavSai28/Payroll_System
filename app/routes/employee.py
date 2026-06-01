from flask import Blueprint, request, jsonify
from app import db
from app.models import Attendance, User, LeaveRequest, Salary
from datetime import datetime, date
from app.services.EmployeeServices import EmployeeServices

# instantiate service
userServices = EmployeeServices()

employee = Blueprint('employee', __name__)

@employee.route('/checkIn', methods=['POST'])
def check_in():
    data = request.get_json() or {}

    user_id = data.get('user_id') 
    
    user = User.query.filter_by(id=user_id).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return userServices.checkIn(user_id)

 
@employee.route('/checkOut', methods=['POST'])
def check_out():
    data = request.get_json()
 
    user_id = data.get('user_id')
 
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
 
    user = User.query.filter_by(id=user_id).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return userServices.checkOut(user_id)


@employee.route('/applyLeave', methods=['POST'])
def apply_leave():
    data = request.get_json()
 
    user_id    = data.get('user_id')
    leave_type = data.get('leave_type')
    from_date  = data.get('from_date')
    to_date    = data.get('to_date')
    reason     = data.get('reason')
 
    user1 = User.query.filter_by(id=user_id).first()
    if not user1:
        return jsonify({'error': 'User not found'}), 404
    return userServices.ApplyLeave(user_id, from_date, to_date, reason, leave_type, user1)


 
@employee.route('/viewAttendance', methods=['GET'])
def view_attendance():
    user_id = request.args.get('user_id')
 
    if not user_id:
        return jsonify({'error': 'user_id is required as query param'}), 400
    records = Attendance.query.filter_by(user_id=user_id).order_by(Attendance.date.desc()).all()
 
    if not records:
        return jsonify({'message': 'No attendance records found', 'user_id': user_id}), 404
    return userServices.viewAttendance(user_id, records,)


 
@employee.route('/monthlySalary', methods=['POST'])
def monthly_Salary():
    data = request.get_json()
 
    user_id = data.get('user_id')
    month   = data.get('month')
    year    = data.get('year')
    print(f"Received monthly salary request for user_id={user_id}, month={month}, year={year}")
    print(f"DEBUG: userServices type = {type(userServices)}")
    print(f"DEBUG: userServices.__class__.__module__ = {userServices.__class__.__module__}")
    if not user_id or not month or not year:
        return jsonify({'error': 'user_id, month and year are required'}), 400
 
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return userServices.monthlySalary(user_id, month, year)
