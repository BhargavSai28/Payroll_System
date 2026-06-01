#!/usr/bin/env python3
import requests
import json

# API Base URL
BASE_URL = 'http://localhost:8080/api'

# Create test users
def create_test_users():
    users = [
        # Manager
        {
            'id': 1,
            'name': 'Alice Manager',
            'email': 'alice@example.com',
            'password': 'password123',
            'role': 'manager',
            'department': 'IT',
            'designation': 'Manager',
            'basic_salary': 50000,
            'hourly_rate': 300
        },
        # Employees in IT department
        {
            'id': 2,
            'name': 'John Doe',
            'email': 'john@example.com',
            'password': 'password123',
            'role': 'employee',
            'department': 'IT',
            'designation': 'Developer',
            'basic_salary': 30000,
            'hourly_rate': 200
        },
        {
            'id': 3,
            'name': 'Jane Smith',
            'email': 'jane@example.com',
            'password': 'password123',
            'role': 'employee',
            'department': 'IT',
            'designation': 'Senior Developer',
            'basic_salary': 40000,
            'hourly_rate': 250
        },
        # Employee in HR department
        {
            'id': 4,
            'name': 'Bob Johnson',
            'email': 'bob@example.com',
            'password': 'password123',
            'role': 'employee',
            'department': 'HR',
            'designation': 'HR Officer',
            'basic_salary': 25000,
            'hourly_rate': 150
        },
        # Manager in HR
        {
            'id': 5,
            'name': 'Carol Williams',
            'email': 'carol@example.com',
            'password': 'password123',
            'role': 'manager',
            'department': 'HR',
            'designation': 'HR Manager',
            'basic_salary': 45000,
            'hourly_rate': 280
        }
    ]
    
    try:
        response = requests.post(f'{BASE_URL}/users', json=users)
        if response.ok:
            print('✓ Test users created successfully')
            print(f'  Users: {response.json()["ids"]}')
        else:
            print(f'✗ Failed to create users: {response.text}')
    except Exception as e:
        print(f'✗ Error creating users: {e}')

# Test manager login
def test_manager_login():
    print('\n📝 Testing Manager Login...')
    try:
        response = requests.post(f'{BASE_URL}/login', json={
            'email': 'alice@example.com',
            'password': 'password123'
        })
        if response.ok:
            data = response.json()
            print(f'✓ Manager login successful')
            print(f'  Role: {data["role"]}')
            print(f'  Department: {data["department"]}')
            return data['user_id']
        else:
            print(f'✗ Login failed: {response.text}')
    except Exception as e:
        print(f'✗ Error: {e}')
    return None

# Test manager dashboard
def test_manager_dashboard(manager_id):
    print('\n📊 Testing Manager Dashboard...')
    try:
        response = requests.get(f'{BASE_URL}/manager/dashboard/{manager_id}')
        if response.ok:
            data = response.json()
            print('✓ Manager dashboard loaded')
            print(f'  Team Count: {data["team_count"]}')
            print(f'  Pending Leaves: {data["pending_leaves"]}')
            print(f'  Present Today: {data["today_present"]}')
        else:
            print(f'✗ Failed: {response.text}')
    except Exception as e:
        print(f'✗ Error: {e}')

# Test manager leave requests
def test_manager_leave_requests(manager_id):
    print('\n📋 Testing Manager Leave Requests...')
    try:
        response = requests.get(f'{BASE_URL}/manager/leave-requests/{manager_id}?status=pending')
        if response.ok:
            data = response.json()
            print(f'✓ Leave requests loaded: {len(data)} requests')
        else:
            print(f'✗ Failed: {response.text}')
    except Exception as e:
        print(f'✗ Error: {e}')

# Test manager team attendance
def test_manager_team_attendance(manager_id):
    print('\n👥 Testing Manager Team Attendance...')
    try:
        response = requests.get(f'{BASE_URL}/manager/team-attendance/{manager_id}?month=6&year=2026')
        if response.ok:
            data = response.json()
            print(f'✓ Team attendance loaded')
            print(f'  Month: {data["month"]}/{data["year"]}')
            print(f'  Team Members: {len(data["team_attendance"])}')
        else:
            print(f'✗ Failed: {response.text}')
    except Exception as e:
        print(f'✗ Error: {e}')

# Test manager team details
def test_manager_team_details(manager_id):
    print('\n📄 Testing Manager Team Details...')
    try:
        response = requests.get(f'{BASE_URL}/manager/team-details/{manager_id}')
        if response.ok:
            data = response.json()
            print(f'✓ Team details loaded: {len(data)} employees')
            if len(data) > 0:
                emp = data[0]
                print(f'  Employee: {emp["name"]} - {emp["designation"]}')
        else:
            print(f'✗ Failed: {response.text}')
    except Exception as e:
        print(f'✗ Error: {e}')

# Test payroll report
def test_payroll_report(manager_id):
    print('\n💰 Testing Payroll Report...')
    try:
        response = requests.get(f'{BASE_URL}/manager/payroll-report/{manager_id}?month=6&year=2026')
        if response.ok:
            data = response.json()
            print(f'✓ Payroll report generated')
            print(f'  Department: {data["department"]}')
            print(f'  Total Payroll: ₹{data["total_payroll"]}')
            print(f'  Employees: {len(data["payroll"])}')
        else:
            print(f'✗ Failed: {response.text}')
    except Exception as e:
        print(f'✗ Error: {e}')

# Main
if __name__ == '__main__':
    print('🚀 Starting Manager Feature Tests\n')
    
    # Create test users
    create_test_users()
    
    # Test manager login and endpoints
    manager_id = test_manager_login()
    
    if manager_id:
        test_manager_dashboard(manager_id)
        test_manager_leave_requests(manager_id)
        test_manager_team_attendance(manager_id)
        test_manager_team_details(manager_id)
        test_payroll_report(manager_id)
    
    print('\n✅ All tests completed!')
