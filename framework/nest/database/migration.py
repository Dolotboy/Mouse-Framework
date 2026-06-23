import importlib.util
from pathlib import Path

from .connection import db
from .config import project_path, root_directory


class Migration:
    def up(self, database):
        raise NotImplementedError

    def down(self, database):
        raise NotImplementedError


class MigrationRepository:
    def __init__(self, database):
        self.database = database

    def create_table(self):
        if self.database.driver == "mysql":
            self.database.execute(
                """
                CREATE TABLE IF NOT EXISTS migrations (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    migration VARCHAR(255) NOT NULL,
                    batch INT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        else:
            self.database.execute(
                """
                CREATE TABLE IF NOT EXISTS migrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    migration TEXT NOT NULL,
                    batch INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        self.database.commit()

    def ran(self):
        rows = self.database.query("SELECT migration FROM migrations ORDER BY id")
        return [row["migration"] for row in rows]

    def last_batch(self):
        rows = self.database.query("SELECT MAX(batch) as batch FROM migrations")
        return rows[0]["batch"] or 0

    def log(self, migration, batch):
        self.database.execute(
            "INSERT INTO migrations (migration, batch) VALUES (%s, %s)"
            if self.database.driver == "mysql"
            else "INSERT INTO migrations (migration, batch) VALUES (?, ?)",
            (migration, batch),
        )

    def delete(self, migration):
        self.database.execute(
            "DELETE FROM migrations WHERE migration = %s"
            if self.database.driver == "mysql"
            else "DELETE FROM migrations WHERE migration = ?",
            (migration,),
        )

    def migrations_for_batch(self, batch):
        rows = self.database.query(
            "SELECT migration FROM migrations WHERE batch = %s ORDER BY id DESC"
            if self.database.driver == "mysql"
            else "SELECT migration FROM migrations WHERE batch = ? ORDER BY id DESC",
            (batch,),
        )
        return [row["migration"] for row in rows]


class Migrator:
    def __init__(self, database=None, migrations_path=None):
        self.database = database or db()
        self.migrations_path = Path(
            migrations_path or project_path(root_directory(), "database", "migrations")
        )
        self.repository = MigrationRepository(self.database)
        # attach schema helpers to the database connection for easy use in migrations
        try:
            # avoid overwriting if already present
            if not hasattr(self.database, "schema"):
                self.database.schema = Schema(self.database)
            if not hasattr(self.database, "table"):
                self.database.table = lambda name, cb: self.database.schema.create_table(name, cb)
            if not hasattr(self.database, "alter"):
                self.database.alter = lambda name, cb: self.database.schema.alter_table_add(name, cb)
            if not hasattr(self.database, "drop_column"):
                self.database.drop_column = lambda name, column: self.database.schema.drop_column(name, column)
        except Exception:
            # defensive: do not break migrator if monkeypatching fails
            pass

    def run(self):
        self.repository.create_table()
        ran = set(self.repository.ran())
        migrations = [
            path for path in self._migration_files()
            if path.stem not in ran
        ]

        if not migrations:
            return []

        batch = self.repository.last_batch() + 1
        migrated = []

        for path in migrations:
            migration = self._load_migration(path)
            migration.up(self.database)
            self.repository.log(path.stem, batch)
            migrated.append(path.stem)

        self.database.commit()
        return migrated

    def rollback(self):
        self.repository.create_table()
        batch = self.repository.last_batch()
        if not batch:
            return []

        migrations = self.repository.migrations_for_batch(batch)
        rolled_back = []

        for migration_name in migrations:
            path = self.migrations_path.joinpath(f"{migration_name}.py")
            migration = self._load_migration(path)
            migration.down(self.database)
            self.repository.delete(migration_name)
            rolled_back.append(migration_name)

        self.database.commit()
        return rolled_back

    def _migration_files(self):
        self.migrations_path.mkdir(parents=True, exist_ok=True)
        return sorted(self.migrations_path.glob("*.py"))

    def _load_migration(self, path):
        if not path.exists():
            raise FileNotFoundError(f"Migration not found: {path}")

        module_name = f"mouse_migration_{path.stem}"
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if hasattr(module, "Migration"):
            return module.Migration()

        if hasattr(module, "up") and hasattr(module, "down"):
            return FunctionMigration(module.up, module.down)

        raise AttributeError(
            f"{path.name} must define a Migration class or up/down functions."
        )


class FunctionMigration(Migration):
    def __init__(self, up, down):
        self._up = up
        self._down = down

    def up(self, database):
        self._up(database)

    def down(self, database):
        self._down(database)


class ColumnBuilder:
    def __init__(self, name, col_type, length=None):
        self.name = name
        self.type = col_type
        self.length = length
        self._nullable = False
        self._default = None
        self._primary = False
        self._auto_increment = False
        self._unique = False
        self._foreign = None  # tuple (table, column)

    def nullable(self):
        self._nullable = True
        return self

    def default(self, value):
        self._default = value
        return self

    def primary(self):
        self._primary = True
        return self

    def increments(self):
        self._auto_increment = True
        self._primary = True
        return self

    def unique(self):
        self._unique = True
        return self

    def foreign(self, table, column="id"):
        self._foreign = (table, column)
        return self

    def compile(self, driver):
        t = self.type.upper()
        if t == "STRING":
            length = self.length or 255
            col_type = f"VARCHAR({length})"
        elif t == "INTEGER":
            col_type = "INT" if driver == "mysql" else "INTEGER"
        elif t == "TEXT":
            col_type = "TEXT"
        elif t == "BOOLEAN":
            col_type = "TINYINT(1)" if driver == "mysql" else "INTEGER"
        elif t == "TIMESTAMP":
            col_type = "TIMESTAMP"
        else:
            col_type = t

        parts = [f"{self.name} {col_type}"]

        if self._auto_increment:
            if driver == "mysql":
                parts.append("AUTO_INCREMENT")
            else:
                # SQLite: use INTEGER PRIMARY KEY AUTOINCREMENT on the column
                pass

        if self._primary and not (self._auto_increment and driver != "mysql"):
            parts.append("PRIMARY KEY")

        if not self._nullable:
            parts.append("NOT NULL")

        if self._default is not None:
            default_val = (
                f"'{self._default}'" if isinstance(self._default, str) else str(self._default)
            )
            parts.append(f"DEFAULT {default_val}")

        return " ".join(parts)


class Table:
    def __init__(self, name):
        self.name = name
        self.columns = []
        self.foreign_constraints = []

    def add_column(self, name, col_type, length=None):
        col = ColumnBuilder(name, col_type, length)
        self.columns.append(col)
        return col

    # convenience methods
    def increments(self, name="id"):
        return self.add_column(name, "INTEGER").increments()

    def integer(self, name):
        return self.add_column(name, "INTEGER")

    def string(self, name, length=255):
        return self.add_column(name, "STRING", length)

    def text(self, name):
        return self.add_column(name, "TEXT")

    def boolean(self, name):
        return self.add_column(name, "BOOLEAN")

    def timestamp(self, name):
        return self.add_column(name, "TIMESTAMP")

    def timestamps(self):
        self.timestamp("created_at").default("CURRENT_TIMESTAMP")
        self.timestamp("updated_at").default("CURRENT_TIMESTAMP")

    def compile_create(self, driver):
        column_defs = []
        table_constraints = []

        for col in self.columns:
            # Handle sqlite autoincrement primary key special case
            if col._auto_increment and driver != "mysql":
                # SQLite requires: name INTEGER PRIMARY KEY AUTOINCREMENT
                column_defs.append(f"{col.name} INTEGER PRIMARY KEY AUTOINCREMENT")
            else:
                column_defs.append(col.compile(driver))

            if col._unique:
                table_constraints.append(f"UNIQUE({col.name})")

            if col._foreign:
                ref_table, ref_col = col._foreign
                fk_name = f"fk_{self.name}_{col.name}_{ref_table}_{ref_col}"
                if driver == "mysql":
                    table_constraints.append(
                        f"CONSTRAINT {fk_name} FOREIGN KEY ({col.name}) REFERENCES {ref_table}({ref_col})"
                    )
                else:
                    table_constraints.append(
                        f"FOREIGN KEY ({col.name}) REFERENCES {ref_table}({ref_col})"
                    )

        joined = ",\n    ".join(column_defs + table_constraints)
        return f"CREATE TABLE IF NOT EXISTS {self.name} (\n    {joined}\n)"


class Schema:
    def __init__(self, database):
        self.db = database

    def create_table(self, name, callback):
        table = Table(name)
        callback(table)
        sql = table.compile_create(self.db.driver)
        self.db.execute(sql)
        # commit handled by caller (migrator)

    def drop_table(self, name):
        self.db.execute(f"DROP TABLE IF EXISTS {name}")

    def drop_column(self, table, column):
        """
        Drop a column from a table.
        - MySQL: executes ALTER TABLE DROP COLUMN
        - SQLite: attempts to use ALTER TABLE DROP COLUMN (if supported) or falls back to a table-recreate strategy
        """
        driver = self.db.driver

        if driver == "mysql":
            sql = f"ALTER TABLE {table} DROP COLUMN {column}"
            self.db.execute(sql)
            return

        # sqlite path
        try:
            # try native DROP COLUMN first (works on modern SQLite)
            sql = f"ALTER TABLE {table} DROP COLUMN {column}"
            self.db.execute(sql)
            return
        except Exception:
            # fallback: recreate table without the column
            pass

        # Rebuild table without the dropped column
        # 1. read current columns
        cur = self.db.execute(f"PRAGMA table_info({table})")
        cols = cur.fetchall()
        # sqlite3 cursor returns tuples; convert to dict-like if possible
        cols_info = []
        for row in cols:
            # row: cid, name, type, notnull, dflt_value, pk
            cid, name, ctype, notnull, dflt_value, pk = row
            cols_info.append({
                "name": name,
                "type": ctype,
                "notnull": bool(notnull),
                "dflt_value": dflt_value,
                "pk": bool(pk),
            })

        keep_cols = [c for c in cols_info if c["name"] != column]
        if not keep_cols:
            raise ValueError(f"Cannot drop column {column}: table would have no columns")

        # build column definitions
        col_defs = []
        col_names = []
        for c in keep_cols:
            name = c["name"]
            ctype = c["type"] or "TEXT"
            parts = [f"{name} {ctype}"]
            if c["pk"]:
                parts.append("PRIMARY KEY")
            if c["notnull"]:
                parts.append("NOT NULL")
            if c["dflt_value"] is not None:
                parts.append(f"DEFAULT {c['dflt_value']}")
            col_defs.append(" ".join(parts))
            col_names.append(name)

        new_table = f"{table}__new__"

        create_sql = f"CREATE TABLE {new_table} ({', '.join(col_defs)})"
        # disable foreign keys while rewriting
        try:
            self.db.execute("PRAGMA foreign_keys=OFF")
        except Exception:
            pass

        self.db.execute(create_sql)
        cols_csv = ", ".join(col_names)
        self.db.execute(f"INSERT INTO {new_table} ({cols_csv}) SELECT {cols_csv} FROM {table}")
        self.db.execute(f"DROP TABLE {table}")
        self.db.execute(f"ALTER TABLE {new_table} RENAME TO {table}")

        try:
            self.db.execute("PRAGMA foreign_keys=ON")
        except Exception:
            pass

    def alter_table_add(self, name, callback):
        table = Table(name)
        callback(table)
        for col in table.columns:
            # compile single column for alter
            if self.db.driver == "mysql":
                col_sql = col.compile(self.db.driver)
                sql = f"ALTER TABLE {name} ADD COLUMN {col_sql}"
            else:
                # sqlite supports only simple ALTER TABLE ADD COLUMN
                # omit PRIMARY KEY/constraints for sqlite alter
                pieces = [f"{col.name} " + ("VARCHAR(%d)" % (col.length or 255) if col.type.upper()=="STRING" else "INTEGER")]
                if not col._nullable:
                    pieces.append("NOT NULL")
                if col._default is not None:
                    default_val = (
                        f"'{col._default}'" if isinstance(col._default, str) else str(col._default)
                    )
                    pieces.append(f"DEFAULT {default_val}")
                col_sql = " ".join(pieces)
                sql = f"ALTER TABLE {name} ADD COLUMN {col_sql}"

            self.db.execute(sql)


def schema(database):
    return Schema(database)

