# Payroll Management System

A comprehensive Flask-based payroll management system with dual-role support for employees and managers.

## Features

### Employee Features
- **User Authentication** - Secure login with email and password validation
- **Dashboard** - Personal dashboard with quick access to all features
- **Attendance Management** - Check-in/check-out functionality with attendance tracking
- **Leave Management** - Apply for leaves with automatic day calculation and status tracking
- **Salary Slip** - View monthly salary information with PDF/CSV download capability

### Manager Features
- **Manager Dashboard** - Team overview with statistics and pending leave requests
- **Leave Approval** - Review and approve/reject employee leave requests
- **Team Attendance** - Monitor team attendance with monthly filtering
- **Payroll Reports** - Generate payroll reports with CSV export functionality
- **Team Details** - View all employee information and work statistics

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
