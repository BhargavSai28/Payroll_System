# Enterprise Payroll Management System

A comprehensive Flask-based payroll management system with role-based access control, manager mappings, session tracking, salary management, automated payslip generation, and email notifications.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Architecture](#architecture)
- [Key Components](#key-components)
- [Documentation](#documentation)
- [API Endpoints](#api-endpoints)
- [Database Schema](#database-schema)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Support](#support)

---

## 🎯 Overview

This payroll system modernizes enterprise employee management with:
- **Role-Based Access Control (RBAC)**: 3 predefined roles (ADMIN, MANAGER, EMPLOYEE) with granular permissions
- **Manager-Employee Mapping**: Track reporting relationships and team structures
- **Session Tracking**: Monitor user logins, sessions, and activity
- **Salary Management**: Track salaries, allowances, deductions, and calculations
- **Automated Payslips**: Monthly payslip generation with PDF output
- **Email Integration**: Automated payslip delivery via email
- **Comprehensive Auditing**: Track all system changes with detailed logs
- **PostgreSQL Backend**: Enterprise-grade relational database
- **RESTful APIs**: 60+ endpoints for complete functionality

---

## ✨ Features

### 🔐 Authentication & Authorization
- JWT-based authentication with 8-hour expiration
- Session tracking with login/logout history
- Device and browser information capture
- IP address logging
- Session activity timestamps
- Force logout capability

### 👥 Role Management
- **ADMIN** (9 permissions): Full system access
- **MANAGER** (6 permissions): Team management and leave approvals
- **EMPLOYEE** (5 permissions): Personal dashboard and payslip access
- Dynamic permission assignment
- Custom role creation capability

### 👔 Manager Mapping
- Assign managers to employees
- Track reporting relationships
- Get team member lists
- Retrieve pending leave requests by team

### 📊 Salary Management
- Create and maintain salary records
- Track salary components:
  - Basic salary
  - Allowances
  - Bonus
  - Other earnings
- Add salary deductions
- Automatic gross salary calculation
- Daily salary derivation

### 📄 Payslip Generation
- Monthly automated payslip generation (28th @ 2 AM)
- Professional PDF generation
- Leave calculations and loss of pay
- Deduction summaries
- Net salary calculations
- Email delivery tracking

### 📧 Email Service
- Automated payslip email delivery
- PDF attachment support
- Leave notification emails
- User onboarding emails
- Bulk email sending with retry logic

### 📅 Scheduled Jobs
- Monthly payslip generation
- Automatic session cleanup (8+ hour inactive)
- Extensible scheduler architecture

### 📋 Audit Logging
- Track all system changes
- Store old and new values
- User and IP address logging
- Action classification
- Timestamped records

### 🔍 Comprehensive APIs
- 60+ RESTful endpoints
- Standard HTTP status codes
- JSON request/response format
- Error handling and validation
- Authorization checks on every endpoint

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- pip (Python package manager)

### Installation

1. **Clone Repository**
```bash
cd d:\payroll
```

2. **Create Virtual Environment**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # Linux/Mac
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

4. **Initialize Database**
```bash
python migrations.py
```
Expected output:
```
✓ Database tables created
✓ Default roles seeded: ADMIN, MANAGER, EMPLOYEE
```

5. **Run Application**
```bash
python run.py
```
Expected output:
```
✓ Flask app created successfully
✓ Configuration loaded
✓ All tables verified/created in PostgreSQL
✓ Default roles created: ADMIN, MANAGER, EMPLOYEE
✓ Scheduled jobs initialized
✓ Running on http://localhost:8080/
```

### First Login

1. Create admin user in database:
```bash
python -c "
from app import create_app, db
from app.models import User, UserRole, Role

app = create_app()
with app.app_context():
    # Create admin user
    from werkzeug.security import generate_password_hash
    admin = User(
        name='Admin User',
        email='admin@example.com',
        password=generate_password_hash('password123'),
        role='ADMIN'
    )
    db.session.add(admin)
    db.session.commit()
    
    # Assign ADMIN role
    admin_role = Role.query.filter_by(role_name='ADMIN').first()
    user_role = UserRole(user_id=admin.id, role_id=admin_role.id)
    db.session.add(user_role)
    db.session.commit()
    print(f'✓ Admin user created: {admin.email}')
"
```

2. Login via API:
```bash
curl -X POST http://localhost:8080/api/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "password123"}'
```

---

## 📁 Project Structure

```
payroll/
├── app/
│   ├── __init__.py
│   ├── models.py                 # Database models (12 tables)
│   ├── auth.py                   # Authentication & authorization
│   ├── config.py                 # Configuration
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── api.py                # Auth endpoints (login, logout, me)
│   │   ├── payroll_api.py        # Payroll endpoints (60+ operations)
│   │   ├── employee.py           # Employee routes
│   │   └── web.py                # Web routes
│   ├── services/
│   │   ├── __init__.py
│   │   ├── RoleService.py        # Role management
│   │   ├── ManagerMappingService.py  # Manager assignment
│   │   ├── SessionService.py     # Session tracking
│   │   ├── SalaryService.py      # Salary calculations
│   │   ├── PayslipService.py     # Payslip generation
│   │   ├── PDFPayslipGenerator.py # PDF creation
│   │   ├── EmailService.py       # Email sending
│   │   ├── ScheduledJobsService.py # Scheduled jobs
│   │   └── EmployeeServices.py   # Employee operations
│   ├── static/
│   │   ├── uploads/
│   │   ├── payslips/             # Generated PDF payslips
│   │   └── ...
│   └── templates/
│       └── ...
├── run.py                        # Application entry point
├── migrations.py                 # Database initialization
├── requirements.txt              # Python dependencies
├── IMPLEMENTATION_GUIDE.md       # Complete implementation guide
├── DATABASE_SCHEMA.md            # Database architecture
├── API_REFERENCE.md              # API documentation
├── DEPLOYMENT_GUIDE.md           # Deployment & troubleshooting
└── README.md                     # This file
```

---

## 🏗️ Architecture

### Layered Architecture

```
┌─────────────────────────────────────────────┐
│         API Layer (routes/)                 │
│  - payroll_api.py (60 endpoints)            │
│  - api.py (auth endpoints)                  │
│  - employee.py, web.py                      │
└────────────────────┬────────────────────────┘
                     │
┌────────────────────▼────────────────────────┐
│     Business Logic Layer (services/)        │
│  - RoleService                              │
│  - SalaryService                            │
│  - PayslipService                           │
│  - SessionService                           │
│  - PDFPayslipGenerator                      │
│  - EmailService                             │
└────────────────────┬────────────────────────┘
                     │
┌────────────────────▼────────────────────────┐
│  Auth & Security Layer (auth.py)            │
│  - JWT token generation/validation          │
│  - Permission checking                      │
│  - Session management                       │
│  - Audit logging                            │
└────────────────────┬────────────────────────┘
                     │
┌────────────────────▼────────────────────────┐
│   Data Access Layer (models.py + SQLAlchemy)│
│  - 12 database tables with relationships    │
│  - Automatic timestamps                     │
│  - Cascade relationships                    │
└────────────────────┬────────────────────────┘
                     │
┌────────────────────▼────────────────────────┐
│     PostgreSQL Database                     │
│  - 12 normalized tables                     │
│  - Performance indexes                      │
│  - Referential integrity                    │
└─────────────────────────────────────────────┘
```

---

## 🔌 API Endpoints Summary

**Authentication (3 endpoints)**
- POST /api/login - User login with session
- POST /api/logout - User logout
- GET /api/me - Current user info

**Role Management (6 endpoints)**
- GET /api/payroll/roles
- POST /api/payroll/roles
- PUT /api/payroll/roles/<id>
- DELETE /api/payroll/roles/<id>
- POST /api/payroll/users/<id>/roles
- DELETE /api/payroll/users/<id>/roles/<id>

**Manager Mapping (3 endpoints)**
- POST /api/payroll/manager-mapping
- PUT /api/payroll/manager-mapping/<id>
- GET /api/payroll/team-members/<id>

**Session Management (3 endpoints)**
- GET /api/payroll/sessions/active
- GET /api/payroll/sessions/history
- POST /api/payroll/sessions/<id>/logout

**Salary Management (4 endpoints)**
- POST /api/payroll/salary
- PUT /api/payroll/salary/<id>
- POST /api/payroll/deductions
- GET /api/payroll/deductions

**Payslip Management (5 endpoints)**
- GET /api/payroll/payslips/<user_id>/month/<m>/<y>
- GET /api/payroll/payslips/<user_id>/download/<m>/<y>
- GET /api/payroll/payslips/<user_id>/history
- POST /api/payroll/payslips/generate/<m>/<y>
- GET /api/payroll/payroll/summary/<m>/<y>

**Plus:** Audit logs, comprehensive error handling, and more

---

## 📚 Comprehensive Documentation

### Available Guides

1. **IMPLEMENTATION_GUIDE.md** - 900+ lines
   - Complete feature overview
   - All 12 database models
   - 8 service modules
   - Backward compatibility
   - Usage examples

2. **DATABASE_SCHEMA.md** - 500+ lines
   - ER diagram description
   - Table specifications
   - Relationships and constraints
   - Query examples
   - Scaling strategies

3. **API_REFERENCE.md** - 600+ lines
   - All 60+ endpoints detailed
   - Request/response formats
   - Authentication methods
   - Status codes
   - Error responses

4. **DEPLOYMENT_GUIDE.md** - 700+ lines
   - Step-by-step setup
   - 20+ troubleshooting scenarios
   - Performance optimization
   - Production deployment
   - Backup/recovery

---

## 🔒 Security Features

✅ **JWT Authentication** - 8-hour expiration  
✅ **Role-Based Access Control** - Granular permissions  
✅ **Session Tracking** - Activity monitoring  
✅ **Audit Logging** - All changes tracked  
✅ **SQL Injection Prevention** - SQLAlchemy ORM  
✅ **Password Hashing** - Werkzeug security  
✅ **IP Logging** - Request tracking  
✅ **Device Tracking** - Browser/OS information  

---

## ⚙️ Configuration

See `app/config.py` for:
- Database connection
- Email SMTP settings
- Payroll parameters
- JWT settings
- File upload paths

---

## 🔧 Troubleshooting

### Common Issues (Quick Solutions)

**Database Connection Failed**
```bash
# Ensure PostgreSQL is running
psql -U postgres -c "SELECT 1"
```

**Permission Denied**
```bash
# Check user role has required permission
curl http://localhost:8080/api/me -H "Authorization: Bearer <token>"
```

**Email Not Sending**
- Verify SMTP credentials in config.py
- Use Gmail app-specific password
- Check firewall allows port 587

**Scheduled Jobs Not Running**
- Ensure use_reloader=False in run.py (already set)
- Keep app running in foreground

See **DEPLOYMENT_GUIDE.md** for 20+ additional scenarios and detailed solutions.

---

## 📊 Database

**12 Tables:**
- users, roles, user_roles, manager_mapping
- user_sessions, attendance, leave_requests
- salary_records, salary_deductions, payslips
- audit_logs, salary (legacy)

**Performance Indexes:** ✓ Included  
**Referential Integrity:** ✓ Enforced  
**Normalization:** ✓ 3NF compliant  

---

## ✅ Verification Checklist

- [ ] pip install -r requirements.txt
- [ ] python migrations.py
- [ ] python run.py (starts successfully)
- [ ] Create test admin user
- [ ] POST /api/login (returns session_id)
- [ ] GET /api/me (returns permissions)
- [ ] All role/salary/payslip APIs working
- [ ] Audit logs tracking changes
- [ ] Email service configured (optional)
- [ ] Scheduled jobs initialized

---

## 📞 Support Resources

1. **DEPLOYMENT_GUIDE.md** - For setup and troubleshooting
2. **API_REFERENCE.md** - For endpoint details
3. **DATABASE_SCHEMA.md** - For data model questions
4. **IMPLEMENTATION_GUIDE.md** - For feature details

---

## 🎯 Next Steps

1. Run migrations: `python migrations.py`
2. Create admin user and test login
3. Verify role-based access works
4. Test payslip generation
5. Configure email service
6. Update frontend templates

---

**Version:** 1.0  
**Status:** Production Ready  
**Last Updated:** June 2024

---

## 📝 Legacy Features (Maintained for Backward Compatibility)

- **Employee Features** - Dashboard, attendance, leave management
- **Manager Features** - Dashboard, leave approval, team management
- **Legacy Salary Table** - Kept for compatibility

All new features are built alongside existing implementation with full backward compatibility.

## Tech Stack

- **Frontend:** HTML5, CSS3, JavaScript (Vanilla)
- **Backend:** Flask (Python)
- **Database:** PostgreSQL with SQLAlchemy ORM
- **Server:** Werkzeug Development Server

## Directory Structure

```
payroll/
├── app/
│   ├── routes/
│   │   ├── api.py          - API endpoints for all operations
│   │   └── web.py          - Web routes and page rendering
│   ├── templates/          - HTML templates
│   │   ├── login.html
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── attendance.html
│   │   ├── salary.html
│   │   ├── leave.html
│   │   ├── manager_dashboard.html
│   │   ├── manager_leave_requests.html
│   │   ├── manager_attendance.html
│   │   ├── manager_payroll.html
│   │   └── manager_team.html
│   ├── models.py           - Database models
│   ├── config.py           - Application configuration
│   └── __init__.py         - Flask app initialization
├── run.py                  - Application entry point
├── requirements.txt        - Python dependencies
└── README.md              - This file
```

## Installation & Setup

### Prerequisites
- Python 3.8+
- PostgreSQL database
- pip package manager

### Steps

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Database**
   - Edit `app/config.py` with your PostgreSQL credentials
   - Create the database and tables

3. **Run Application**
   ```bash
   python run.py
   ```
   - App will start at `http://localhost:8080`

## Usage

### Employee Login
1. Navigate to http://localhost:8080/login
2. Enter email and password
3. Access employee dashboard with features:
   - Check-in/Check-out
   - View attendance
   - Apply leave
   - Download salary slip

### Manager Login
1. Login with manager credentials
2. Redirected to manager dashboard
3. Access features:
   - View pending leave requests
   - Approve/reject leaves
   - Monitor team attendance
   - Generate payroll reports

## API Endpoints

### Authentication
- `POST /api/login` - User login with role detection

### Employee Endpoints
- `POST /api/check-in/<user_id>` - Check in
- `POST /api/check-out/<user_id>` - Check out
- `GET /api/attendance/<user_id>` - Get attendance records
- `POST /user/applyLeave` - Apply for leave
- `GET /api/leave-requests/<user_id>` - Get leave status
- `GET /api/salary/<user_id>` - Get salary information

### Manager Endpoints
- `GET /api/manager/dashboard/<manager_id>` - Dashboard statistics
- `GET /api/manager/leave-requests/<manager_id>` - Team leave requests
- `POST /api/manager/leave-request/<request_id>/approve` - Approve leave
- `POST /api/manager/leave-request/<request_id>/reject` - Reject leave
- `GET /api/manager/team-attendance/<manager_id>` - Team attendance
- `GET /api/manager/team-details/<manager_id>` - Employee details
- `GET /api/manager/payroll-report/<manager_id>` - Payroll report

## Database Schema

### Key Tables
- **users** - User accounts with role and department
- **attendance** - Check-in/check-out records
- **leave_requests** - Leave applications with status
- **salary** - Salary information

## Security Features

- Role-based access control (RBAC)
- Department-based team isolation
- SQL injection prevention via SQLAlchemy ORM
- Session management with localStorage
- Server-side validation
- Error handling

## Key Workflows

### Leave Approval
1. Employee applies for leave → Status: "pending"
2. Manager sees request in dashboard
3. Manager clicks approve/reject
4. Status updates to "approved" or "rejected"
5. Employee sees updated status immediately

### Payroll Report
1. Manager selects month/year
2. System aggregates payroll data
3. Display summary and detailed table
4. Download as CSV file

### Attendance Tracking
1. Employee checks in → Records start time
2. Employee checks out → Records end time
3. System calculates hours worked
4. Manager views team attendance monthly

## Testing Credentials

Example login credentials (check database):
- **Employee:** Standard user credentials
- **Manager:** User with manager role

## Deployment Notes

- Change database credentials in `app/config.py`
- Disable debug mode in production
- Use environment variables for sensitive data
- Configure proper CORS policies
- Set up proper logging

## Responsive Design

- Desktop (1920x1080) - Full layout
- Tablet (768x1024) - 2-column layout
- Mobile (375x667) - Single column layout

## Troubleshooting

**Port Already in Use**
```bash
# Change port in run.py or use different port
python run.py --port 8081
```

**Database Connection Error**
- Verify PostgreSQL is running
- Check credentials in `app/config.py`
- Ensure database exists

**Login Not Working**
- Verify user exists in database
- Check email and password
- Review browser console for errors

## Future Enhancements

- Email notifications for approvals
- Audit logs and activity tracking
- Password hashing (bcrypt)
- JWT token authentication
- Advanced analytics and reporting
- Multi-language support
- Mobile app (React Native/Flutter)
- API rate limiting

## Support

For issues or questions, review the code comments and API documentation in the source files.

## License

This project is for internal use only.

---

**Version:** 2.0  
**Last Updated:** June 1, 2026  
**Status:** Production Ready ✅
