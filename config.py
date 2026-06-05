import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super-secret-futsal-key-12345'
    
    # MySQL Database Connection
    # Format: mysql+pymysql://<username>:<password>@<host>/<database_name>
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://root:1234@localhost/futsal_db'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Futsal settings
    ADMIN_REGISTRATION_KEY = 'FUTSAL_ADMIN_2026'  # Key required to register as admin
    
    # Peak hours: 16:00 to 22:00 (4 PM to 10 PM) are peak hours
    PEAK_START_HOUR = 16
    PEAK_END_HOUR = 22
    PEAK_MULTIPLIER = 1.25  # 25% extra charge for peak hours
    WEEKEND_MULTIPLIER = 1.15  # 15% extra charge for weekends (Saturday, Sunday)
