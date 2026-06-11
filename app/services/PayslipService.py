"""
Payslip Management Service
Handles payslip generation and tracking
"""

from app import db
from app.models import Payslip, User, SalaryRecord
from app.services.SalaryService import SalaryService
from datetime import datetime
from flask import current_app
import os


class PayslipService:
    
    @staticmethod
    def generate_payslip(user_id, month, year):
        """Generate payslip for a user for a specific month/year"""
        
        user = User.query.get(user_id)
        if not user:
            return None, "User not found"
        
        existing = Payslip.query.filter_by(
            user_id=user_id,
            month=month,
            year=year
        ).first()

        # Calculate take-home salary. It is stored in net_salary for compatibility.
        salary_data, error = SalaryService.calculate_net_salary(user_id, month, year)
        if error:
            return None, error
        
        # Get user role
        from app.auth import get_user_primary_role
        role = get_user_primary_role(user_id)
        
        if existing:
            payslip = existing
            payslip.role_id = role.role_id if role else None
            payslip.role_name = role.role_name if role else 'EMPLOYEE'
            payslip.total_salary = salary_data.get('gross_salary')
            payslip.unpaid_leave_days = salary_data.get('unpaid_days')
            payslip.loss_of_pay_amount = salary_data.get('loss_of_pay')
            payslip.total_other_deductions = salary_data.get('total_deductions')
            payslip.net_salary = salary_data.get('net_salary')
            payslip.generated_at = datetime.utcnow()
        else:
            payslip = Payslip(
                user_id=user_id,
                role_id=role.role_id if role else None,
                role_name=role.role_name if role else 'EMPLOYEE',
                month=month,
                year=year,
                total_salary=salary_data.get('gross_salary'),
                unpaid_leave_days=salary_data.get('unpaid_days'),
                loss_of_pay_amount=salary_data.get('loss_of_pay'),
                total_other_deductions=salary_data.get('total_deductions'),
                net_salary=salary_data.get('net_salary'),
                generated_at=datetime.utcnow()
            )
            db.session.add(payslip)

        db.session.commit()
        
        return payslip, None
    
    @staticmethod
    def get_payslip(payslip_id):
        """Get payslip by ID"""
        return Payslip.query.get(payslip_id)
    
    @staticmethod
    def get_user_payslips(user_id, limit=12):
        """Get payslips for a user (latest first)"""
        return Payslip.query.filter_by(user_id=user_id).order_by(
            Payslip.generated_at.desc()
        ).limit(limit).all()
    
    @staticmethod
    def get_payslip_by_month(user_id, month, year):
        """Get payslip for a specific month"""
        return Payslip.query.filter_by(
            user_id=user_id,
            month=month,
            year=year
        ).first()
    
    @staticmethod
    def mark_email_sent(payslip_id):
        """Mark payslip as emailed"""
        payslip = Payslip.query.get(payslip_id)
        if payslip:
            payslip.email_sent = True
            payslip.email_sent_at = datetime.utcnow()
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def update_payslip_file(payslip_id, file_name, file_path):
        """Update payslip file information"""
        payslip = Payslip.query.get(payslip_id)
        if payslip:
            payslip.payslip_file_name = file_name
            payslip.payslip_file_path = file_path
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def get_unsent_payslips(limit=None):
        """Get all payslips that haven't been emailed yet"""
        query = Payslip.query.filter_by(email_sent=False).order_by(Payslip.generated_at.asc())
        if limit:
            query = query.limit(limit)
        return query.all()
    
    @staticmethod
    def get_payroll_summary(month, year):
        """Get payroll summary for a month"""
        payslips = Payslip.query.filter_by(month=month, year=year).all()
        
        total_employees = len(payslips)
        total_payroll = sum(p.net_salary or 0 for p in payslips)
        total_deductions = sum(p.total_other_deductions or 0 for p in payslips)
        total_loss_of_pay = sum(p.loss_of_pay_amount or 0 for p in payslips)
        
        return {
            'month': month,
            'year': year,
            'total_employees': total_employees,
            'total_payroll': round(total_payroll, 2),
            'total_deductions': round(total_deductions, 2),
            'total_loss_of_pay': round(total_loss_of_pay, 2),
            'average_salary': round(total_payroll / total_employees, 2) if total_employees > 0 else 0
        }
    
    @staticmethod
    def generate_pdf_filename(user_id, month, year):
        """Generate PDF filename"""
        user = User.query.get(user_id)
        if not user:
            return None
        
        # Format: PAYSLIP_USERID_YYYY_MM.pdf
        filename = f"PAYSLIP_{user_id}_{year}_{month:02d}.pdf"
        return filename
    
    @staticmethod
    def get_payslip_storage_path(user_id, month, year):
        """Get storage path for payslip PDF"""
        configured_dir = current_app.config.get('PAYSLIP_FOLDER')
        if configured_dir:
            storage_dir = configured_dir
            if not os.path.isabs(storage_dir):
                storage_dir = os.path.join(os.getcwd(), storage_dir)
        else:
            storage_dir = os.path.join(current_app.static_folder, 'payslips')
        
        # Create directory if doesn't exist
        os.makedirs(storage_dir, exist_ok=True)
        
        filename = PayslipService.generate_pdf_filename(user_id, month, year)
        filepath = os.path.join(storage_dir, filename)
        return filepath, storage_dir
