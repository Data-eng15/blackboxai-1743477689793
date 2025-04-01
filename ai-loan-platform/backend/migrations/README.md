# Database Migrations

This directory contains database migration scripts for the AI Loan Platform. Migrations are managed using Flask-Migrate and Alembic.

## Setup

1. Initialize migrations:
```bash
./init_migrations.sh
```

This script will:
- Create a virtual environment if it doesn't exist
- Install required packages
- Initialize Flask-Migrate
- Create and apply initial migration
- Create admin user

## Migration Commands

### Create a New Migration

After making changes to your models, create a new migration:
```bash
flask db migrate -m "Description of changes"
```

### Apply Migrations

Apply pending migrations:
```bash
flask db upgrade
```

### Rollback Migration

Rollback the last migration:
```bash
flask db downgrade
```

### View Migration Status

Check current migration version:
```bash
flask db current
```

View migration history:
```bash
flask db history
```

## Database Management

The `manage_db.py` script provides several commands for database management:

### Create Database Tables
```bash
python manage_db.py create_db
```

### Drop Database Tables
```bash
python manage_db.py drop_db
```
⚠️ Not available in production

### Reset Database
```bash
python manage_db.py reset_db
```
⚠️ Not available in production

### Create Admin User
```bash
python manage_db.py create_admin
```

### Backup Database
```bash
python manage_db.py backup_db
```
Creates a timestamped backup in the `backups` directory

### Restore Database
```bash
python manage_db.py restore_db
```
Restores from a selected backup file

### Seed Database
```bash
python manage_db.py seed_db
```
⚠️ Not available in production

## Migration Files

- `versions/`: Contains individual migration files
- `script.py.mako`: Template for new migrations
- `env.py`: Environment configuration for Alembic
- `alembic.ini`: Alembic configuration file

## Best Practices

1. Always review migration files before applying them
2. Test migrations on development/staging before production
3. Back up database before applying migrations
4. Use meaningful descriptions in migration messages
5. Keep migrations small and focused
6. Handle data migrations separately from schema migrations
7. Version control all migration files

## Troubleshooting

### Migration Conflicts

If you get migration conflicts:
1. Rollback to last known good state
2. Delete conflicting migration file
3. Recreate migration

### Failed Migrations

If a migration fails:
1. Check the error message
2. Rollback to previous version
3. Fix the issue
4. Recreate migration

### Database Out of Sync

If database is out of sync with migrations:
1. Check current database state
2. Compare with migration history
3. Either stamp current version or recreate migrations

## Production Deployment

1. Always backup database before migrations
2. Schedule migrations during low-traffic periods
3. Have a rollback plan ready
4. Test migrations on staging environment
5. Monitor system during migration

## Security Notes

- Never commit sensitive data in migrations
- Protect backup files
- Use strong admin passwords
- Restrict migration commands in production
- Log all database operations

## Directory Structure

```
migrations/
├── versions/           # Migration version files
├── env.py             # Environment configuration
├── script.py.mako     # Migration template
├── alembic.ini        # Alembic configuration
├── manage_db.py       # Database management script
├── init_migrations.sh # Initialization script
└── README.md         # This file
```

## Dependencies

- Flask-Migrate
- Flask-Script
- psycopg2-binary (for PostgreSQL)
- alembic

## Contributing

1. Create feature branch
2. Make changes
3. Test migrations
4. Submit pull request

## Support

For migration issues:
1. Check logs in `logs/migration.log`
2. Review error messages
3. Consult Flask-Migrate documentation
4. Contact development team