from app import db
from flask import jsonify
from app.models import Attendance, User, LeaveRequest, Salary
from datetime import datetime, date
import calendar

# Paid leave limits based on leave type
PAID_LEAVE_CONFIG = {
    'casual leave': 3,
    'sick leave': 3,
    'bereavement leave': 7
}

class EmployeeServices:
    def __init__(self):
        pass

    def checkIn(self, user_id,):
        clock_in_dt = datetime.now()
        today       = clock_in_dt.date()

        existing = Attendance.query.filter_by(user_id=user_id, date=today).first()
        if existing:
            return jsonify({'error': 'User already checked in today'}), 409

        attendance = Attendance(
            id             = None,
            user_id        = user_id,
            clock_in       = clock_in_dt,
            clock_out      = None,
            date           = today,
            worked_hours   = 0.0,
            regular_hours  = 0.0,
            overtime_hours = 0.0
        )
        db.session.add(attendance)
        db.session.commit()
        user = User.query.get(user_id)
        return jsonify({
            'message'      : 'Check-in recorded successfully',
            'attendance_id': attendance.id,
            'user_id'      : user_id,
            'name'         : user.name,
            'clock_in'     : clock_in_dt.strftime('%Y-%m-%dT%H:%M:%S'),
            'date'         : today.isoformat()
        }), 201

    def checkOut(self, user_id):
        clock_out_dt = datetime.now()
        today        = clock_out_dt.date()

        attendance = Attendance.query.filter_by(user_id=user_id, date=today).first()
        if not attendance:
            return jsonify({'error': 'No check-in found for today. Please check in first'}), 404
        if attendance.clock_out:
            return jsonify({'error': 'User already checked out today'}), 409

        attendance.clock_out = clock_out_dt

        diff           = clock_out_dt - attendance.clock_in
        total_hours    = round(diff.total_seconds() / 3600, 2)
        regular_hours  = round(min(total_hours, 8.0), 2)
        overtime_hours = round(max(0, total_hours - 8.0), 2)

        attendance.worked_hours   = total_hours
        attendance.regular_hours  = regular_hours
        attendance.overtime_hours = overtime_hours

        db.session.commit()
        user = User.query.get(user_id)

        return jsonify({
            'message'       : 'Check-out recorded successfully',
            'attendance_id' : attendance.id,
            'user_id'       : user_id,
            'name'          : user.name,
            'clock_in'      : attendance.clock_in.strftime('%Y-%m-%dT%H:%M:%S'),
            'clock_out'     : clock_out_dt.strftime('%Y-%m-%dT%H:%M:%S'),
            'worked_hours'  : total_hours,
            'regular_hours' : regular_hours,
            'overtime_hours': overtime_hours
        }), 200

    def ApplyLeave(self, user_id, from_date, to_date, reason, leave_type,user):
        try:
            from_date_obj = date.fromisoformat(from_date)
            to_date_obj   = date.fromisoformat(to_date)
        except Exception:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

        days = (to_date_obj - from_date_obj).days + 1

        if from_date_obj > to_date_obj:
            return jsonify({'error': 'from_date cannot be after to_date'}), 400

        total_days = (to_date_obj - from_date_obj).days + 1

        already_used = db.session.query(db.func.sum(LeaveRequest.days)).filter_by(
            user_id=user_id,
            status='approved'
        ).scalar() or 0

        # Use leave type specific paid leave limit
        paid_limit = PAID_LEAVE_CONFIG.get(leave_type.lower() if leave_type else 'casual', 3)
        remaining_paid = max(0, paid_limit - already_used)
        paid_days      = min(total_days, remaining_paid)
        unpaid_days    = total_days - paid_days

        applied_on = datetime.now()
        leave = LeaveRequest(
            id         = None,
            user_id    = user_id,
            leave_type = leave_type,
            from_date  = from_date_obj,
            to_date    = to_date_obj,
            days       = days,
            reason     = reason,
            status     = 'pending'
        )
        db.session.add(leave)
        db.session.commit()

        return jsonify({
            'message'   : 'Leave request submitted successfully',
            'leave_id'  : leave.id,
            'user_id'   : user_id,
            'name'      : user.name,
            'leave_type': leave_type,
            'from_date' : from_date_obj.isoformat(),
            'to_date'   : to_date_obj.isoformat(),
            'days'      : days,
            'reason'    : reason,
            'status'    : 'pending',
            'applied_on': applied_on.strftime('%Y-%m-%dT%H:%M:%S')
        }), 201

    def viewAttendance(self, user_id, records):
        present_days   = len(records)
        total_hours    = round(sum(r.worked_hours   or 0 for r in records), 2)
        overtime_hours = round(sum(r.overtime_hours or 0 for r in records), 2)
        regular_hours  = round(sum(r.regular_hours  or 0 for r in records), 2)

        leaves       = LeaveRequest.query.filter_by(user_id=user_id, status='approved').all()
        leaves_taken = sum(l.days or 0 for l in leaves)
        working_days = present_days + leaves_taken

        attendance_list = []
        for r in records:
            attendance_list.append({
                'attendance_id' : r.id,
                'date'          : r.date.isoformat(),
                'clock_in'      : r.clock_in.strftime('%Y-%m-%dT%H:%M:%S')  if r.clock_in  else None,
                'clock_out'     : r.clock_out.strftime('%Y-%m-%dT%H:%M:%S') if r.clock_out else None,
                'worked_hours'  : r.worked_hours,
                'regular_hours' : r.regular_hours,
                'overtime_hours': r.overtime_hours
            })

        return jsonify({
            'user_id'   : user_id,
            'summary'   : {
                'present_days'  : present_days,
                'working_days'  : working_days,
                'leaves_taken'  : leaves_taken,
                'total_hours'   : total_hours,
                'regular_hours' : regular_hours,
                'overtime_hours': overtime_hours
            },
            'attendance': attendance_list
        }), 200

    def monthlySalary(self, user_id, month, year):
        user          = User.query.get(user_id)
        annual_salary = getattr(user, 'basic_salary', 0.0) if user else 0.0

        # Get days in the current month
        days_in_month = calendar.monthrange(year, month)[1]

        # Fetch attendance records for the month
        attendance_records = Attendance.query.filter(
            Attendance.user_id == user_id,
            db.extract('month', Attendance.date) == month,
            db.extract('year',  Attendance.date) == year
        ).all()

        leaves = LeaveRequest.query.filter(
            LeaveRequest.user_id == user_id,
            LeaveRequest.status  == 'approved',
            db.extract('month', LeaveRequest.from_date) == month,
            db.extract('year',  LeaveRequest.from_date) == year
        ).all()

        # Calculate attendance metrics
        present_days     = len(attendance_records)
        total_hours      = round(sum(r.worked_hours   or 0 for r in attendance_records), 2)
        overtime_hours   = round(sum(r.overtime_hours or 0 for r in attendance_records), 2)

        # Categorize leaves by type and calculate totals
        leaves_by_type = {}
        total_leave_days = 0
        for leave in leaves:
            leave_type = leave.leave_type.lower() if leave.leave_type else 'casual'
            if leave_type not in leaves_by_type:
                leaves_by_type[leave_type] = 0
            leaves_by_type[leave_type] += leave.days or 0
            total_leave_days += leave.days or 0

        # Calculate paid and unpaid leaves based on leave type
        paid_days = 0
        unpaid_days = 0

        for leave_type, days_taken in leaves_by_type.items():
            paid_limit = PAID_LEAVE_CONFIG.get(leave_type, 0)
            paid_for_type = min(days_taken, paid_limit)
            unpaid_for_type = days_taken - paid_for_type
            paid_days += paid_for_type
            unpaid_days += unpaid_for_type

        # Calculate working days and salary components
        working_days = present_days + total_leave_days

        # Calculate salary from the monthly basic amount:
        # deductions come out of basic first, then LOP comes out of regular pay.
        monthly_salary = round(annual_salary / 12, 2)
        pf_deduction = round(monthly_salary * 0.12, 2)
        salary_after_deductions = round(max(0, monthly_salary - pf_deduction), 2)
        daily_salary = round(salary_after_deductions / days_in_month, 2) if days_in_month > 0 else 0
        hourly_salary = round(daily_salary / 8, 2) if daily_salary > 0 else 0

        loss_of_pay = round(daily_salary * unpaid_days, 2)
        regular_pay = round(max(0, salary_after_deductions - loss_of_pay), 2)
        overtime_pay = round(overtime_hours * hourly_salary * 1.5, 2) if hourly_salary > 0 else 0
        total_deductions = pf_deduction
        take_home_salary = round(regular_pay + overtime_pay, 2)
        
        existing = Salary.query.filter_by(user_id=user_id, month=month, year=year).first()
        if existing:
            sal = existing
        else:
            sal = Salary(
                id             = None,
                user_id        = user_id,
                month          = month,
                year           = year,
                basic_salary   = 0.0,
                regular_pay    = 0.0,
                overtime_pay   = 0.0,
                deductions     = 0.0,
                working_days   = 0,
                leaves_taken   = 0,
                total_hours    = 0.0,
                overtime_hours = 0.0,
                present_days   = 0,
                net_salary     = 0.0
            )
            db.session.add(sal)

        # Update salary record
        sal.basic_salary   = monthly_salary
        sal.regular_pay    = regular_pay
        sal.overtime_pay   = overtime_pay
        sal.deductions     = total_deductions
        sal.working_days   = working_days
        sal.present_days   = present_days
        sal.leaves_taken   = total_leave_days
        sal.total_hours    = total_hours
        sal.overtime_hours = overtime_hours
        sal.net_salary     = take_home_salary

        db.session.commit()

        return jsonify({
            'message'       : 'Monthly salary calculated and saved successfully',
            'salary_id'     : sal.id,
            'user_id'       : user_id,
            'month'         : month,
            'year'          : year,
            'salary_breakup': {
                'annual_salary' : annual_salary,
                'monthly_salary': monthly_salary,
                'salary_after_deductions': salary_after_deductions,
                'daily_salary'  : daily_salary,
                'hourly_salary' : hourly_salary,
                'days_in_month' : days_in_month
            },
            'attendance'    : {
                'present_days'  : present_days,
                'working_days'  : working_days,
                'total_hours'   : total_hours,
                'overtime_hours': overtime_hours
            },
            'leave_details' : {
                'total_leave_days': total_leave_days,
                'paid_days'       : paid_days,
                'unpaid_days'     : unpaid_days,
                'leaves_by_type'  : leaves_by_type,
                'paid_leave_config': PAID_LEAVE_CONFIG
            },
            'earnings'      : {
                'regular_pay'    : regular_pay,
                'overtime_pay'   : overtime_pay,
                'pf_deduction'   : pf_deduction,
                'loss_of_pay'    : loss_of_pay,
                'total_deductions': total_deductions,
                'take_home_salary': take_home_salary,
                'net_salary'     : take_home_salary
            }
        }), 200
