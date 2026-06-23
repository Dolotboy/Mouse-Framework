<p align="center">
  <img src="framework/nest/assets/images/mouse_logo_circle.png" alt="Mouse Logo" width="256" height="256">
</p>

# Mouse

A Python MVC Web Framework inspired by Laravel

## Tested Environnment

- Docker
    - Windows 10
    - Linux Mint 22
    - Zorin OS 18
    - Ubuntu 24.04 LTS
- On host
    - Windows 10
    - Linux Mint 22
    - Zorin OS 18
    - Ubuntu 24.04 LTS

## Installation

```bash
pip install mouse-cli
mouse-cli new project MyProject
```
- Copy ".env.example"
- Paste
- Rename the copy for ".env"
- python server.py
- If port 8080 is already in use:
    ```bash
    sudo fuser -k 8080/tcp
    ```

## Cloning Procedure

- ```bash
    git clone https://github.com/Dolotboy/Mouse
    ```
- ```bash
    cd mouse
    ```
- Copy ".env.example"
- Paste
- Rename the copy for ".env"


## Dependencies

- [Python 3.12](https://www.python.org/downloads/)
- [Python DotEnv](https://pypi.org/project/python-dotenv/)
    - ```bash 
        pip install python-dotenv
        ```
- [MySQL Connector/Python](https://pypi.org/project/mysql-connector-python/) for MySQL connections

## Framework structure
[Documentation](/framework/readme.md)

## Database and migrations

Configure the database in `.env` with `DB_CONNECTION=mysql` or `DB_CONNECTION=sqlite`.
```bash
mouse-cli new db
mouse-cli new migration create_users_table
mouse-cli migrate
mouse-cli migrate:rollback
```

Migration files are created in `web/database/migrations`.

## Migrations (DSL)

This project provides a small migration DSL so you don't need to write driver-specific SQL in migration files. Migrations are Python classes placed in `web/database/migrations` and expose `up(self, db)` and `down(self, db)` methods.

Basic usage examples:

- Create a table

```python
class Migration:
    def up(self, db):
        def table(t):
            t.increments('id')
            t.string('name')
            t.string('email').unique()
            t.string('password')
            t.timestamps()

        db.table('users', table)

    def down(self, db):
        db.schema.drop_table('users')
```

- Column with multiple attributes

```python
def up(self, db):
    def table(t):
        t.increments('id')
        t.string('username', 100).unique().nullable()
        t.string('email').unique().default('')
        t.integer('age').nullable().default(0)
        t.integer('role_id').foreign('roles', 'id')

    db.table('accounts', table)
```

- Add a column to an existing table (ALTER TABLE ADD COLUMN)

```python
def up(self, db):
    def add(t):
        t.string('nickname').nullable()

    db.alter('users', add)
```

- Drop a column from a table

```python
def up(self, db):
    # preferred helper (works for MySQL; for SQLite this will attempt
    # a native DROP COLUMN or fall back to recreating the table)
    db.drop_column('users', 'nickname')
```

Notes:

- The DSL supports: `increments`, `integer`, `string`, `text`, `boolean`, `timestamp`, `timestamps`, `nullable()`, `default(value)`, `unique()`, `foreign(table, column)`, and column chaining.
- Adding columns (`ALTER TABLE ADD COLUMN`) is supported.
- Dropping a column is supported via `db.drop_column(table, column)` (or `db.schema.drop_column(table, column)`).
    - MySQL: runs `ALTER TABLE ... DROP COLUMN`.
    - SQLite: will try `ALTER TABLE ... DROP COLUMN` (if the SQLite version supports it) otherwise it recreates the table without the dropped column. Some complex table constraints/indexes may not be preserved by the automated fallback; test carefully and prefer raw SQL for complex migrations.
- You can still run raw SQL via `db.execute(sql)` when necessary; use this for driver-specific operations.
- Raw SQL (when you need driver-specific operations)
```python
def up(self, db):
    # example: modify column type in MySQL
    db.execute("ALTER TABLE users MODIFY COLUMN age INT NOT NULL DEFAULT 0")

    # example: run any raw statement (returns a cursor-like object)
    cur = db.execute("UPDATE users SET name = 'anonymous' WHERE name IS NULL")
```

Migration files should follow the existing naming convention and are discovered by the framework's migrator.

## Views

## Models

## Controllers
