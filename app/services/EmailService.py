"""
Email Notification Service
Handles sending payslip emails and other notifications
"""

from flask_mail import Mail, Message
from flask import current_app
from app.models import Payslip
from app import db
from datetime import datetime
import os


mail = Mail()


class EmailService:
    
    @staticmethod
    def init_mail(app):
        """Initialize mail with Flask app"""
        mail.init_app(app)
    
    @staticmethod
    def send_payslip_email(payslip_id, recipient_email, recipient_name):
        """Send payslip email to employee"""
        
        payslip = Payslip.query.get(payslip_id)
        if not payslip:
            return False, "Payslip not found"
        
        if not payslip.payslip_file_path or not os.path.exists(payslip.payslip_file_path):
            return False, "Payslip PDF file not found"

        if not recipient_email:
            return False, "Recipient email is missing"
        
        try:
            # Create email message
            subject = f"Payslip for {payslip.year}-{payslip.month:02d} - {recipient_name}"
            
            body = f"""
Dear {recipient_name},

Please find attached your payslip for {payslip.year}-{payslip.month:02d}.

Salary Summary:
- Gross Salary: Rs. {payslip.total_salary:,.2f}
- Total Deductions: Rs. {payslip.total_other_deductions + payslip.loss_of_pay_amount:,.2f}
- Take Home Salary: Rs. {payslip.net_salary:,.2f}

If you have any questions regarding your payslip, please contact the HR department.

Best regards,
HR Department
"""
            
            msg = Message(
                subject=subject,
                recipients=[recipient_email],
                body=body
            )
            
            # Attach PDF
            with open(payslip.payslip_file_path, 'rb') as attachment:
                msg.attach(
                    payslip.payslip_file_name or 'payslip.pdf',
                    'application/pdf',
                    attachment.read()
                )
            
            # Send email
            mail.send(msg)
            
            # Mark as sent
            payslip.email_sent = True
            payslip.email_sent_at = datetime.utcnow()
            db.session.commit()
            
            return True, "Email sent successfully"
        
        except Exception as e:
            return False, f"Error sending email: {str(e)}"
    
    @staticmethod
    def send_bulk_payslip_emails(month, year):
        """Send payslips to all employees for a month"""
        from app.models import User, Payslip
        
        payslips = Payslip.query.filter_by(
            month=month,
            year=year,
            email_sent=False
        ).all()
        
        sent = 0
        failed = 0
        failed_users = []
        
        for payslip in payslips:
            user = User.query.get(payslip.user_id)
            if not user:
                failed += 1
                failed_users.append(payslip.user_id)
                continue
            
            success, error = EmailService.send_payslip_email(
                payslip.payslip_id,
                user.email,
                user.name
            )
            
            if success:
                sent += 1
            else:
                failed += 1
                failed_users.append(f"{user.name} ({user.email}): {error}")
        
        return {
            'sent': sent,
            'failed': failed,
            'failed_users': failed_users
        }
