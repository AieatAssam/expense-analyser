# Database Migrations Guide

This document provides guidance on using Alembic for database migrations in the Expense Analyser project.

## Initial Migration Status

The initial database migration has been created and applied, establishing the following tables:
- `user`: For user authentication and management
- `category`: For expense categorization with hierarchical structure
- `receipt`: For storing receipt metadata and user relationships
- `lineitem`: For individual items within receipts

The migration script is located at `migrations/versions/a96b03e13043_initial.py`.

## Migration Setup

The project uses Alembic for database schema migrations. The configuration is already set up with:

- `alembic.ini`: Main configuration file
- `migrations/env.py`: Environment configuration that loads models and settings
- `migrations/versions/`: Directory that will store individual migration scripts

## Connection to PostgreSQL Container

The Alembic configuration is designed to connect to the PostgreSQL database defined in your `docker-compose.yml` file. It will:

1. First check for a `DATABASE_URL` environment variable
2. Fall back to the URL in `alembic.ini` if the environment variable is not set

This ensures that migrations can run both inside Docker containers and in local development environments.

## Using Migrations

### Creating a New Migration

To create a new migration after model changes:

```bash
# Local development
alembic revision --autogenerate -m "description of changes"

# Inside Docker container
docker-compose exec api alembic revision --autogenerate -m "description of changes"
```

### Applying Migrations

To apply all pending migrations:

```bash
# Local development
alembic upgrade head

# Inside Docker container
docker-compose exec api alembic upgrade head
```

### Checking Migration Status

To check the current migration status:

```bash
# Local development
alembic current

# Inside Docker container
docker-compose exec api alembic current
```

### Rolling Back Migrations

To roll back to a previous migration:

```bash
# Roll back one step
alembic downgrade -1

# Roll back to a specific revision
alembic downgrade <revision_id>

# Roll back all migrations
alembic downgrade base
```

## Best Practices

1. Always review autogenerated migration scripts before applying them
2. Run tests after migration to verify database functionality
3. Include migrations in version control
4. Consider using transaction boundaries for safe migrations
5. Test migrations in a development environment before applying to production

## Troubleshooting

If you encounter migration issues:

1. Check database connection settings
2. Verify all models are properly imported in `env.py`
3. Ensure the database user has sufficient privileges
4. Check for syntax errors in your models
5. Review migration scripts for correctness

For more information, refer to the [official Alembic documentation](https://alembic.sqlalchemy.org/en/latest/).
