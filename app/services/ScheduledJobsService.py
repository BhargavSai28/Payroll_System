

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import date
from app.models import User
import logging


logger = logging.getLogger(__name__)


class PayrollScheduler:
    
    scheduler = None
    
    @staticmethod
    def init_scheduler(app):
        """Initialize APScheduler"""
        PayrollScheduler.scheduler = BackgroundScheduler()
        
        # Schedule monthly payslip generation and email delivery on the last day.
        PayrollScheduler.scheduler.add_job(
            func=PayrollScheduler.generate_monthly_payslips,
            trigger="cron",
            day="last",
            hour=2,
            minute=0,
            id='monthly_payslip_generation',
            name='Generate and Email Monthly Payslips',
            args=[app]
        )
        
        # Schedule session cleanup
        PayrollScheduler.scheduler.add_job(
            func=PayrollScheduler.cleanup_expired_sessions,
            trigger="cron",
            hour=3,
            minute=0,
            id='session_cleanup',
            name='Clean up Expired Sessions',
            args=[app]
        )
        
        try:
            PayrollScheduler.scheduler.start()
            logger.info("Payroll scheduler started successfully")
        except Exception as e:
            logger.error(f"Error starting scheduler: {e}")
    
    @staticmethod
    def generate_monthly_payslips(app):
        """Generate and email payslips for every user in the users table."""
        
        with app.app_context():
            try:
                today = date.today()
                month = today.month
                year = today.year
                all_users = User.query.all()
                
                generated = 0
                failed = 0
                
                from app.services.PayslipService import PayslipService

                for user in all_users:
                    try:
                        payslip, error = PayslipService.generate_payslip(
                            user.id,
                            month,
                            year
                        )
                        
                        if error:
                            logger.error(f"Error generating payslip for user {user.id}: {error}")
                            failed += 1
                        else:
                            generated += 1
                            logger.info(f"Payslip generated/refreshed for user {user.id}")
                    
                    except Exception as e:
                        logger.error(f"Exception generating payslip for user {user.id}: {e}")
                        failed += 1
                
                # Log results
                logger.info(f"Monthly payslip generation completed: {generated} generated, {failed} failed")
                
                # Generate PDFs
                try:
                    from app.services.PDFPayslipGenerator import PDFPayslipGenerator
                    pdf_generated, pdf_failed = PDFPayslipGenerator.generate_all_monthly_payslips(
                        month,
                        year
                    )
                    logger.info(f"PDF generation: {pdf_generated} generated, {pdf_failed} failed")
                except Exception as e:
                    logger.error(f"Error generating PDFs: {e}")
                
                # Send emails
                try:
                    from app.services.EmailService import EmailService
                    results = EmailService.send_bulk_payslip_emails(month, year)
                    logger.info(f"Email delivery: {results['sent']} sent, {results['failed']} failed")
                except Exception as e:
                    logger.error(f"Error sending emails: {e}")
            
            except Exception as e:
                logger.error(f"Error in monthly payslip generation job: {e}")
    
    @staticmethod
    def cleanup_expired_sessions(app):
        """Clean up expired sessions"""
        
        with app.app_context():
            try:
                from app.services.SessionService import SessionService
                count = SessionService.mark_expired_sessions()
                logger.info(f"Session cleanup: {count} sessions marked as expired")
            except Exception as e:
                logger.error(f"Error in session cleanup job: {e}")
    
    @staticmethod
    def stop_scheduler():
        """Stop the scheduler"""
        if PayrollScheduler.scheduler:
            PayrollScheduler.scheduler.shutdown()
            logger.info("Payroll scheduler stopped")
