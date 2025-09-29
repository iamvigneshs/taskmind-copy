# Database Safety Guidelines

## 🚨 CRITICAL: Database Protection Rules

This project uses a **production RDS PostgreSQL database**. To prevent data loss:

### 1. **NEVER Run Destructive Commands Without Permission**
- No `DROP TABLE`, `DROP DATABASE`, `TRUNCATE`
- No `DELETE FROM` without `WHERE` clause
- No `ALTER TABLE` that removes columns
- No database migrations that destroy data

### 2. **Always Use Transactions**
```python
from app.database import session_scope

with session_scope() as session:
    try:
        # Your database operations here
        session.commit()
    except Exception:
        session.rollback()
        raise
```

### 3. **Read-Only First**
When exploring the database, always start with SELECT queries:
```sql
-- Check what's in a table first
SELECT * FROM task LIMIT 10;

-- Count records before any operation
SELECT COUNT(*) FROM task;
```

### 4. **Required Environment Setup**
The `.env` file MUST contain:
```
DATABASE_URL=postgresql://username:password@host:port/database
```

**NEVER use SQLite** for this project.

### 5. **Testing Safety**
- Tests should use transactions that rollback
- Consider using a separate test database
- Never run tests against production data without explicit permission

### 6. **Before Running Scripts**
- `scripts/safe_init_database.py` - Will warn if tables exist
- `scripts/generate_synthetic_data.py` - Will warn if data exists
- Always check what a script does before running it

### 7. **Backup Before Changes**
Before any structural changes:
1. Confirm a recent backup exists
2. Document what will be changed
3. Have a rollback plan

## Emergency Contacts
If you accidentally damage the database:
1. Stop all operations immediately
2. Do NOT attempt to fix without guidance
3. Contact the database administrator
4. Document exactly what happened

## Safe Commands Reference
```bash
# Check database status (read-only)
psql $DATABASE_URL -c "SELECT table_name FROM information_schema.tables WHERE table_schema='public';"

# Count records (read-only)  
psql $DATABASE_URL -c "SELECT COUNT(*) FROM task;"

# Safe data viewing
psql $DATABASE_URL -c "SELECT * FROM task ORDER BY created_at DESC LIMIT 5;"
```

Remember: **When in doubt, ASK FIRST!**