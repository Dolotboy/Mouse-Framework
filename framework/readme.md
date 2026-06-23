## Framework structure

- `framework/` exposes the public framework APIs used by applications and external tools.
- `framework/nest/` is the core runtime layer for routing, rendering, database connections, and migrations.
- `framework/stubs/` contains the templates used by the framework generators.

## Migrations
 
This section documents the internal migration system used by the framework. It is intended for framework maintainers and contributors (not application authors).

### Overview

- Migration files live in the application folder: `web/database/migrations`.
- Each migration is a Python module; the framework discovers `*.py` files in that directory and loads them with `importlib`.
- A migration module can provide either:
	- a `Migration` class with `up(self, db)` and `down(self, db)` methods, or
	- top-level `up(database)` and `down(database)` functions. The loader wraps functions in a `FunctionMigration` adapter.

### Execution flow

1. The `Migrator` (see `framework/nest/database/migration.py`) creates a `MigrationRepository` and ensures the `migrations` table exists.
2. It collects migration files from the `web/database/migrations` directory and compares them to entries in the `migrations` table to determine which migrations haven't been run.
3. For each pending migration file:
	 - the migrator loads the module via `importlib.util.spec_from_file_location` and `spec.loader.exec_module`.
	 - if the module defines a `Migration` class, the migrator instantiates it and calls `migration.up(database)`.
	 - if the module defines `up`/`down` functions, the migrator wraps them in `FunctionMigration` and calls `up(database)`.
	 - after a migration runs, the migrator logs the migration filename (module stem) into the `migrations` table and groups it in a batch.
4. The migrator commits once a batch is completed. Rollbacks execute `down(database)` in reverse order and delete log entries for the rolled-back batch.

### Why migration files do not need imports

- Migration modules receive a `db`/`database` object when `up`/`down` is called; they do not need to import `Schema` or other helpers. The migrator attaches convenience helpers to that database object at runtime (for example `db.schema`, `db.table`, `db.alter`, `db.drop_column`). This makes migration files concise and driver-agnostic.

### Key implementation points

- The core code is in `framework/nest/database/migration.py`:
	- `MigrationRepository` manages the `migrations` table and uses driver-specific SQL where necessary.
	- `Migrator` discovers files, loads modules, calls `up`/`down`, and logs migration runs.
	- `FunctionMigration` is a small adapter to support procedural `up`/`down` functions.
	- `Schema`, `Table`, and `ColumnBuilder` provide a lightweight DSL for creating and altering tables in a driver-agnostic way.
- The migration file stub used by the generator is `framework/stubs/migration.stub` and is used by `framework/generators.py` to scaffold new migration files.

### Available APIs inside a migration

- `db` (the parameter passed to `up`/`down`) is an instance of `DatabaseConnection` (`framework/nest/database/connection.py`). It exposes:
	- `db.execute(sql, params=None)` — execute an SQL statement (returns a cursor-like object).
	- `db.query(sql, params=None)` — fetch rows as list-of-dicts.
	- `db.commit()`, `db.rollback()` — transaction control.
	- `db.close()` — close the connection.
	- `db.driver` — string identifying the driver (`mysql` or `sqlite`).

### Convenience helpers attached by the migrator

- `db.schema` — a `Schema` instance providing:
	- `create_table(name, callback)` — create a new table using the `Table` DSL.
	- `drop_table(name)` — drop a table.
	- `alter_table_add(name, callback)` — add columns to an existing table.
	- `drop_column(table, column)` — drop a column (MySQL runs `ALTER TABLE DROP COLUMN`; SQLite will attempt native support and otherwise rebuild the table without the column).
- `db.table(name, callback)` — shorthand for `db.schema.create_table(name, callback)`.
- `db.alter(name, callback)` — shorthand for `db.schema.alter_table_add(name, callback)`.
- `db.drop_column(table, column)` — shorthand for `db.schema.drop_column(table, column)`.

### Writing migration files (developer notes)

- File location and naming: migrations are placed under `web/database/migrations` and are discovered in alphanumeric order; the project generator stamps filenames with timestamps to avoid collisions.
- Minimal class-based migration (no imports required):

```python
class Migration:
		def up(self, db):
				def table(t):
						t.increments('id')
						t.string('name')
						t.string('email').unique()

				db.table('users', table)

		def down(self, db):
				db.schema.drop_table('users')
```

- Using raw SQL when necessary:

```python
class Migration:
		def up(self, db):
				# driver-specific change
				db.execute("ALTER TABLE users MODIFY COLUMN age INT NOT NULL DEFAULT 0")

		def down(self, db):
				# revert with raw SQL or more safe operations
				db.execute("ALTER TABLE users MODIFY COLUMN age INTEGER")
```

### Caveats and operational notes

- Because some SQL features differ between MySQL and SQLite, the DSL aims to handle common operations (create table, add column, drop column) in a driver-aware way. However complex schema rewrites, index migrations, or advanced foreign-key semantics may require raw SQL and manual testing.
- The SQLite `drop_column` fallback recreates the table and copies data. This may not preserve every constraint, index or trigger; test on a copy of the database before applying in production.
- The migrator monkeypatches helpers onto the `db` object when it instantiates; if you create your own `DatabaseConnection` instance outside the migrator and want the helpers available, instantiate `Migrator(database=your_db)` or attach `Schema(your_db)` yourself.

### Files of interest

- `framework/nest/database/migration.py` — migrator, repository, and DSL implementation.
- `framework/nest/database/connection.py` — DB connection and driver-specific behavior.
- `framework/stubs/migration.stub` — migration template used by the generator.
- `framework/generators.py` — code that scaffolds new migration files.

If you want, I can also add more examples (foreign key options like `onDelete`/`onUpdate`), unit tests for SQL generation, or an integration test exercising migration rollback across both drivers.