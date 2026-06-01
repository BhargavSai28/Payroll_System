class Config:
    SECRET_KEY = 'mysecretkey123'

    # PostgreSQL connection
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:postgres@localhost:5432/payroll'
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    USERNAME = 'postgres'
    PASSWORD = 'postgres'
    HOST = 'localhost'
    PORT = 5432
    DB_NAME = 'payroll'

    # Mail config
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'your_email@gmail.com'
    MAIL_PASSWORD = 'your_password'
