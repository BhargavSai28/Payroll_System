import os
from flask import Flask
from app.config import Config as config
from app import db
from app.models import (User, Attendance, Salary, LeaveRequest, Role, UserRole, 
                       ManagerMapping, UserSession, SalaryRecord, SalaryDeduction, 
                       Payslip, AuditLog)
from app.routes.api import bp as api_bp
from app.routes.employee import employee
from app.routes.web import web
from app.services.EmailService import mail
from app.services.ScheduledJobsService import PayrollScheduler


def create_app():
    app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
    print("✓ Flask app created successfully")

    # Configure Flask app
    app.config.from_object(config)
    print(f"✓ Configuration loaded")
    
    # Configure SQLAlchemy
    app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
    print(f"✓ Configuring app with PostgreSQL URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

    # Initialize extensions
    db.init_app(app)
    mail.init_app(app)
    
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            print("✓ All tables verified/created in PostgreSQL")
            
            # Initialize default roles if they don't exist
            if Role.query.first() is None:
                print("📋 Initializing default roles...")
                _seed_default_roles()
            
        except Exception as e:
            print(f"✗ ERROR creating tables: {e}")
            import traceback
            traceback.print_exc()
    
    return app


def _seed_default_roles():
    """Seed default roles"""
    
    admin_permissions = [
        "dashboard",
        "user_management",
        "leave_management",
        "role_management",
        "session_tracking",
        "salary_management",
        "payroll_management",
        "reports",
        "audit_logs"
    ]
    
    manager_permissions = [
        "dashboard",
        "team_management",
        "leave_approval",
        "team_reports",
        "team_payroll",
        "team_salary_view"
    ]
    
    employee_permissions = [
        "dashboard",
        "profile",
        "leave_request",
        "view_payslip",
        "view_attendance"
    ]
    
    admin_role = Role(
        role_name='ADMIN',
        permissions=admin_permissions,
        description='Administrator role with full system access'
    )
    
    manager_role = Role(
        role_name='MANAGER',
        permissions=manager_permissions,
        description='Manager role for team management and leave approvals'
    )
    
    employee_role = Role(
        role_name='EMPLOYEE',
        permissions=employee_permissions,
        description='Employee role with basic access'
    )
    
    db.session.add_all([admin_role, manager_role, employee_role])
    db.session.commit()
    print("✓ Default roles created: ADMIN, MANAGER, EMPLOYEE")


if __name__ == '__main__':
    app = create_app()
    
    # Import and register all blueprints
    from app.routes.api import bp as api_bp
    from app.routes.payroll_api import payroll_bp
    from app.routes.employee import employee
    from app.routes.web import web
    
    # Register blueprints
    app.register_blueprint(web)
    app.register_blueprint(employee, url_prefix='/user')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(payroll_bp, url_prefix='/api/payroll')
    
    # Initialize scheduled jobs
    try:
        PayrollScheduler.init_scheduler(app)
        print("✓ Scheduled jobs initialized")
    except Exception as e:
        print(f" Error initializing scheduler: {e}")
    
    # Run the app
    app.run(
        debug=os.getenv('FLASK_DEBUG', 'true').lower() == 'true',
        host=os.getenv('FLASK_RUN_HOST', '0.0.0.0'),
        port=int(os.getenv('FLASK_RUN_PORT', '8080')),
        use_reloader=False
    )
