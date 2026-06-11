
from app import db
from app.models import SalaryRecord, SalaryDeduction, User, LeaveRequest, Attendance
from datetime import datetime
import calendar


class SalaryService:
    
    # Paid leave limits by leave type
    PAID_LEAVE_CONFIG = {
        'casual leave': 3,
        'sick leave': 3,
        'bereavement leave': 7,
        'earned leave': 20
    }
    
    # Constants
    TOTAL_WORKING_DAYS = 22
    WORKING_HOURS_PER_DAY = 8
    PF_DEDUCTION_PERCENT = 0.12
    OVERTIME_MULTIPLIER = 1.5
    
    @staticmethod
    def create_salary_record(user_id, basic_salary, allowances=0.0, bonus=0.0, other_earnings=0.0):
        """Create a new salary record for an employee"""
        user = User.query.get(user_id)
        if not user:
            return None, "User not found"
        
        # Calculate gross salary
        gross_salary = basic_salary + allowances + bonus + other_earnings
        
        salary = SalaryRecord(
            user_id=user_id,
            basic_salary=basic_salary,
            allowances=allowances,
            bonus=bonus,
            other_earnings=other_earnings,
            gross_salary=gross_salary,
            effective_from=datetime.utcnow()
        )
        db.session.add(salary)
        db.session.commit()
        return salary, None
    
    @staticmethod
    def update_salary_record(salary_id, basic_salary=None, allowances=None, bonus=None, other_earnings=None):
        """Update an existing salary record"""
        salary = SalaryRecord.query.get(salary_id)
        if not salary:
            return None, "Salary record not found"
        
        if basic_salary is not None:
            salary.basic_salary = basic_salary
        if allowances is not None:
            salary.allowances = allowances
        if bonus is not None:
            salary.bonus = bonus
        if other_earnings is not None:
            salary.other_earnings = other_earnings
        
        # Recalculate gross salary
        salary.gross_salary = (salary.basic_salary + salary.allowances + 
                              salary.bonus + salary.other_earnings)
        salary.updated_at = datetime.utcnow()
        
        db.session.commit()
        return salary, None
    
    @staticmethod
    def get_active_salary(user_id):
        """Get current active salary for a user"""
        salary = SalaryRecord.query.filter_by(user_id=user_id).order_by(
            SalaryRecord.effective_from.desc()
        ).first()
        return salary
    
    
    @staticmethod
    def calculate_daily_salary(gross_salary, working_days=TOTAL_WORKING_DAYS):
        """Calculate daily salary"""
        return round(gross_salary / working_days, 2) if working_days > 0 else 0
    
    @staticmethod
    def calculate_loss_of_pay(daily_salary, unpaid_leave_days):
        """Calculate loss of pay for unpaid leaves"""
        return round(daily_salary * unpaid_leave_days, 2)
    
    @staticmethod
    def get_monthly_deductions(user_id, month, year):
        """Get all deductions for a specific month"""
        deductions = SalaryDeduction.query.filter_by(
            user_id=user_id,
            deduction_month=month,
            deduction_year=year
        ).all()
        return deductions
    
    @staticmethod
    def calculate_total_deductions(user_id, month, year):
        """Calculate total deductions for a month"""
        deductions = SalaryService.get_monthly_deductions(user_id, month, year)
        total = sum(d.deduction_amount for d in deductions)
        return round(total, 2)
    
    @staticmethod
    def add_salary_deduction(user_id, deduction_type, amount, reason=None, month=None, year=None):
        """Add a salary deduction"""
        user = User.query.get(user_id)
        if not user:
            return None, "User not found"
        
        if not month:
            month = datetime.utcnow().month
        if not year:
            year = datetime.utcnow().year
        
        deduction = SalaryDeduction(
            user_id=user_id,
            deduction_type=deduction_type,
            deduction_amount=amount,
            deduction_reason=reason,
            deduction_month=month,
            deduction_year=year
        )
        db.session.add(deduction)
        db.session.commit()
        return deduction, None
    
    @staticmethod
    def calculate_net_salary(user_id, month, year):
        """
        Calculate take-home salary for a user for a specific month.
        The value is returned as net_salary for database/API compatibility.
        
        Formula:
        Take Home Salary = Basic/Gross Salary - Deductions - Loss of Pay
        """
        
        user = User.query.get(user_id)
        if not user:
            return None, "User not found"
        
        # Get active salary
        salary_record = SalaryService.get_active_salary(user_id)
        if not salary_record:
            return None, "No salary record found for user"
        
        gross_salary = salary_record.gross_salary
        
        # Calculate unpaid leaves
        approved_leaves = LeaveRequest.query.filter(
            LeaveRequest.user_id == user_id,
            LeaveRequest.status == 'approved',
            db.extract('month', LeaveRequest.from_date) == month,
            db.extract('year', LeaveRequest.from_date) == year
        ).all()
        
        total_leave_days = sum(l.days or 0 for l in approved_leaves)
        
        # Categorize leaves by type
        leaves_by_type = {}
        for leave in approved_leaves:
            leave_type = (leave.leave_type or 'casual leave').lower()
            if leave_type not in leaves_by_type:
                leaves_by_type[leave_type] = 0
            leaves_by_type[leave_type] += leave.days or 0
        
        # Calculate paid and unpaid leaves
        paid_days = 0
        unpaid_days = 0
        
        for leave_type, days_taken in leaves_by_type.items():
            paid_limit = SalaryService.PAID_LEAVE_CONFIG.get(leave_type, 0)
            paid_for_type = min(days_taken, paid_limit)
            unpaid_for_type = days_taken - paid_for_type
            paid_days += paid_for_type
            unpaid_days += unpaid_for_type
        
        # Get total deductions
        total_deductions = SalaryService.calculate_total_deductions(user_id, month, year)

        salary_after_deductions = round(max(0, gross_salary - total_deductions), 2)

        # Calculate loss of pay from the amount remaining after deductions.
        daily_salary = SalaryService.calculate_daily_salary(salary_after_deductions)
        loss_of_pay = SalaryService.calculate_loss_of_pay(daily_salary, unpaid_days)

        # Stored as net_salary for DB compatibility, displayed as take-home salary.
        take_home_salary = round(max(0, salary_after_deductions - loss_of_pay), 2)
        
        return {
            'gross_salary': gross_salary,
            'salary_after_deductions': salary_after_deductions,
            'daily_salary': daily_salary,
            'total_leave_days': total_leave_days,
            'paid_days': paid_days,
            'unpaid_days': unpaid_days,
            'loss_of_pay': loss_of_pay,
            'total_deductions': total_deductions,
            'take_home_salary': take_home_salary,
            'net_salary': take_home_salary
        }, None
