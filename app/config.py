import os


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'mysecretkey123')

    # PostgreSQL connection
    USERNAME = os.getenv('POSTGRES_USER', 'postgres')
    PASSWORD = os.getenv('POSTGRES_PASSWORD', 'postgres')
    HOST = os.getenv('POSTGRES_HOST', 'localhost')
    PORT = int(os.getenv('POSTGRES_PORT', '5432'))
    DB_NAME = os.getenv('POSTGRES_DB', 'payroll')
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        f'postgresql://{USERNAME}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Mail config
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', 'rayalabhargavsai@gmail.com')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', 'uexqlyyfkfhtsepp')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', MAIL_USERNAME or 'noreply@company.com')
    
    # Payroll Settings
    TOTAL_WORKING_DAYS = 22
    PF_DEDUCTION_PERCENT = 0.12
    OVERTIME_MULTIPLIER = 1.5
    
    # File Upload
    UPLOAD_FOLDER = 'app/static/uploads'
    PAYSLIP_FOLDER = 'app/static/payslips'
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size
