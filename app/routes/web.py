from flask import Blueprint, render_template, redirect, request
from app.models import User

web = Blueprint('web', __name__)

@web.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        return redirect('/dashboard')
    return render_template('login.html')

@web.route('/dashboard', methods=['GET'])
def dashboard():
    return render_template('dashboard.html')

@web.route('/attendance', methods=['GET'])
def attendance():
    return render_template('attendance.html')

@web.route('/salary', methods=['GET'])
def salary():
    return render_template('salary.html')

@web.route('/leave', methods=['GET'])
def leave():
    return render_template('leave.html')

# Manager Routes
@web.route('/manager-dashboard', methods=['GET'])
def manager_dashboard():
    return render_template('manager_dashboard.html')

@web.route('/manager-leave-requests', methods=['GET'])
def manager_leave_requests():
    return render_template('manager_leave_requests.html')

@web.route('/manager-attendance', methods=['GET'])
def manager_attendance():
    return render_template('manager_attendance.html')

@web.route('/manager-payroll', methods=['GET'])
def manager_payroll():
    return render_template('manager_payroll.html')

@web.route('/manager-team', methods=['GET'])
def manager_team():
    return render_template('manager_team.html')

@web.route('/', methods=['GET'])
def index():
    return redirect('/login')
