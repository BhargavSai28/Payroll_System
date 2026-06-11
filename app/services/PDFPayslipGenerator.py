"""
PDF Payslip Generation Service
Generates PDF payslips for employees
"""

from fpdf import FPDF
from app.models import Payslip, User, SalaryRecord, SalaryDeduction
from app.services.SalaryService import SalaryService
from datetime import datetime
import os


class PDFPayslipGenerator:
    
    COMPANY_NAME = "Your Company Name"
    COMPANY_ADDRESS = "123 Business Street, City, State 12345"
    COMPANY_PHONE = "+1-800-123-4567"
    COMPANY_EMAIL = "hr@company.com"
    
    def __init__(self, user_id, month, year):
        self.user_id = user_id
        self.month = month
        self.year = year
        self.user = User.query.get(user_id)
        self.payslip = Payslip.query.filter_by(
            user_id=user_id,
            month=month,
            year=year
        ).first()
        self.salary_record = SalaryService.get_active_salary(user_id)
    
    def generate_pdf(self, filepath):
        """Generate PDF payslip"""
        
        if not self.user:
            raise ValueError("User not found")
        
        if not self.payslip:
            raise ValueError("Payslip not found")
        
        if not self.salary_record:
            raise ValueError("Salary record not found")
        
        # Create PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=11)
        
        # Company Header
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, self.COMPANY_NAME, ln=True, align="C")
        
        pdf.set_font("Helvetica", size=9)
        pdf.cell(0, 6, self.COMPANY_ADDRESS, ln=True, align="C")
        pdf.cell(0, 6, f"Phone: {self.COMPANY_PHONE} | Email: {self.COMPANY_EMAIL}", ln=True, align="C")
        
        pdf.ln(5)
        
        # Payslip Header
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "PAYSLIP", ln=True, align="C")
        
        month_name = datetime(self.year, self.month, 1).strftime("%B")
        pdf.set_font("Helvetica", size=10)
        pdf.cell(0, 6, f"For the month of {month_name} {self.year}", ln=True, align="C")
        
        pdf.ln(3)
        
        # Employee Information Section
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, "EMPLOYEE INFORMATION", ln=True, border=1)
        
        pdf.set_font("Helvetica", size=10)
        
        info_data = [
            ["Employee ID:", str(self.user.id)],
            ["Employee Name:", self.user.name],
            ["Email:", self.user.email],
            ["Designation:", self.user.designation or "N/A"],
            ["Department:", self.user.department or "N/A"],
            ["Role:", self.payslip.role_name or "Employee"],
        ]
        
        for label, value in info_data:
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(60, 6, label)
            pdf.set_font("Helvetica", size=10)
            pdf.cell(0, 6, value, ln=True)
        
        pdf.ln(3)
        
        # Salary Details Section
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, "SALARY STRUCTURE", ln=True, border=1)
        
        pdf.set_font("Helvetica", size=10)
        
        salary_data = [
            ["Basic Salary:", f"Rs. {self.salary_record.basic_salary:,.2f}"],
            ["Allowances:", f"Rs. {self.salary_record.allowances:,.2f}"],
            ["Bonus:", f"Rs. {self.salary_record.bonus:,.2f}"],
            ["Other Earnings:", f"Rs. {self.salary_record.other_earnings:,.2f}"],
        ]
        
        for label, value in salary_data:
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(60, 6, label)
            pdf.set_font("Helvetica", size=10)
            pdf.cell(0, 6, value, ln=True)
        
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(60, 6, "Gross Salary:")
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, f"Rs. {self.payslip.total_salary:,.2f}", ln=True)
        
        pdf.ln(3)
        
        # Leave Information Section
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, "LEAVE INFORMATION", ln=True, border=1)
        
        pdf.set_font("Helvetica", size=10)
        
        leave_data = [
            ["Unpaid Leave Days:", str(self.payslip.unpaid_leave_days)],
            ["Loss of Pay:", f"Rs. {self.payslip.loss_of_pay_amount:,.2f}"],
        ]
        
        for label, value in leave_data:
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(60, 6, label)
            pdf.set_font("Helvetica", size=10)
            pdf.cell(0, 6, value, ln=True)
        
        pdf.ln(3)
        
        # Deductions Section
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, "DEDUCTIONS", ln=True, border=1)
        
        deductions = SalaryDeduction.query.filter_by(
            user_id=self.user_id,
            deduction_month=self.month,
            deduction_year=self.year
        ).all()
        
        pdf.set_font("Helvetica", size=10)
        
        if deductions:
            for deduction in deductions:
                pdf.set_font("Helvetica", "B", 10)
                pdf.cell(60, 6, f"{deduction.deduction_type}:")
                pdf.set_font("Helvetica", size=10)
                pdf.cell(0, 6, f"Rs. {deduction.deduction_amount:,.2f}", ln=True)
        
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(60, 6, "Total Deductions:")
        pdf.set_font("Helvetica", size=10)
        pdf.cell(0, 6, f"Rs. {self.payslip.total_other_deductions:,.2f}", ln=True)
        
        pdf.ln(3)
        
        # Summary Section
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, "SALARY SUMMARY", ln=True, border=1)
        
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(60, 7, "Gross Salary:")
        pdf.set_font("Helvetica", size=10)
        pdf.cell(0, 7, f"Rs. {self.payslip.total_salary:,.2f}", ln=True)
        
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(60, 7, "Total Deductions:")
        pdf.set_font("Helvetica", size=10)
        total_deductions = self.payslip.loss_of_pay_amount + self.payslip.total_other_deductions
        pdf.cell(0, 7, f"Rs. {total_deductions:,.2f}", ln=True)
        
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(60, 8, "TAKE HOME SALARY:")
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, f"Rs. {self.payslip.net_salary:,.2f}", ln=True)
        
        pdf.ln(5)
        
        # Footer
        pdf.set_font("Helvetica", "I", 9)
        pdf.cell(0, 6, "This is a system generated payslip. No signature required.", ln=True, align="C")
        pdf.cell(0, 6, f"Generated on: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}", ln=True, align="C")
        
        # Save PDF
        pdf.output(filepath)
        return filepath
    
    @staticmethod
    def generate_all_monthly_payslips(month, year):
        """Generate payslips for all employees for a month"""
        from app.models import Payslip
        
        payslips = Payslip.query.filter_by(month=month, year=year).all()
        
        generated = 0
        failed = 0
        
        for payslip in payslips:
            try:
                filepath, _ = PayslipService.get_payslip_storage_path(
                    payslip.user_id, 
                    month, 
                    year
                )
                generator = PDFPayslipGenerator(payslip.user_id, month, year)
                generator.generate_pdf(filepath)
                
                # Update payslip with file information
                PayslipService.update_payslip_file(
                    payslip.payslip_id,
                    os.path.basename(filepath),
                    filepath
                )
                generated += 1
            except Exception as e:
                print(f"Error generating payslip for user {payslip.user_id}: {e}")
                failed += 1
        
        return generated, failed


# Import PayslipService here to avoid circular imports
from app.services.PayslipService import PayslipService
