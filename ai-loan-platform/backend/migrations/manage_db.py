from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from backend import create_app, db
import os

app = create_app()
migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)

@manager.command
def create_db():
    """Create database tables"""
    db.create_all()
    print('Database tables created successfully!')

@manager.command
def drop_db():
    """Drop all database tables"""
    if app.config['FLASK_ENV'] == 'production':
        print('This command cannot be run in production!')
        return
    db.drop_all()
    print('Database tables dropped successfully!')

@manager.command
def reset_db():
    """Reset database tables"""
    if app.config['FLASK_ENV'] == 'production':
        print('This command cannot be run in production!')
        return
    db.drop_all()
    db.create_all()
    print('Database reset successfully!')

@manager.command
def create_admin():
    """Create admin user"""
    from backend.models import User
    
    email = input('Enter admin email: ')
    password = input('Enter admin password: ')
    
    admin = User(
        email=email,
        name='Admin',
        is_admin=True
    )
    admin.set_password(password)
    
    db.session.add(admin)
    db.session.commit()
    print('Admin user created successfully!')

@manager.command
def backup_db():
    """Backup database"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = os.path.join(app.root_path, 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    
    if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgresql'):
        # PostgreSQL backup
        backup_file = os.path.join(backup_dir, f'backup_{timestamp}.sql')
        os.system(f'pg_dump {app.config["SQLALCHEMY_DATABASE_URI"]} > {backup_file}')
    else:
        # SQLite backup
        import shutil
        db_file = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        backup_file = os.path.join(backup_dir, f'backup_{timestamp}.db')
        shutil.copy2(db_file, backup_file)
    
    print(f'Database backed up to {backup_file}')

@manager.command
def restore_db():
    """Restore database from backup"""
    backup_dir = os.path.join(app.root_path, 'backups')
    backups = os.listdir(backup_dir)
    
    if not backups:
        print('No backups found!')
        return
    
    print('Available backups:')
    for i, backup in enumerate(backups):
        print(f'{i+1}. {backup}')
    
    choice = input('Enter backup number to restore: ')
    try:
        backup_file = os.path.join(backup_dir, backups[int(choice)-1])
    except (ValueError, IndexError):
        print('Invalid choice!')
        return
    
    if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgresql'):
        # PostgreSQL restore
        os.system(f'psql {app.config["SQLALCHEMY_DATABASE_URI"]} < {backup_file}')
    else:
        # SQLite restore
        import shutil
        db_file = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        shutil.copy2(backup_file, db_file)
    
    print('Database restored successfully!')

@manager.command
def seed_db():
    """Seed database with sample data"""
    if app.config['FLASK_ENV'] == 'production':
        print('This command cannot be run in production!')
        return
    
    from backend.models import User, LoanApplication
    from datetime import datetime, date
    
    # Create test users
    users = [
        {
            'email': 'user1@example.com',
            'name': 'Test User 1',
            'phone': '+919876543210'
        },
        {
            'email': 'user2@example.com',
            'name': 'Test User 2',
            'phone': '+919876543211'
        }
    ]
    
    for user_data in users:
        user = User(**user_data)
        user.set_password('Test@123')
        db.session.add(user)
    
    db.session.commit()
    
    # Create test loan applications
    applications = [
        {
            'user_id': 1,
            'full_name': 'Test User 1',
            'date_of_birth': date(1990, 1, 1),
            'pan_number': 'ABCDE1234F',
            'aadhaar_number': '123456789012',
            'employment_type': 'full_time',
            'monthly_income': 50000,
            'loan_amount': 500000,
            'loan_purpose': 'personal',
            'loan_tenure': 24,
            'status': 'submitted'
        },
        {
            'user_id': 2,
            'full_name': 'Test User 2',
            'date_of_birth': date(1992, 2, 2),
            'pan_number': 'PQRST5678G',
            'aadhaar_number': '987654321098',
            'employment_type': 'business_owner',
            'monthly_income': 80000,
            'loan_amount': 800000,
            'loan_purpose': 'business',
            'loan_tenure': 36,
            'status': 'approved'
        }
    ]
    
    for app_data in applications:
        application = LoanApplication(**app_data)
        db.session.add(application)
    
    db.session.commit()
    print('Database seeded successfully!')

if __name__ == '__main__':
    manager.run()