"""
Encrypted SQLite database repository for the mnm CLI.

Uses SQLCipher for AES-256 encryption at rest.
"""
import json
import os
import sqlite3
from pathlib import Path
from typing import List, Optional
from datetime import date
from uuid import UUID

from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

from app.models import (
    Asset, Liability, FinancialTask, UpcomingExpense,
    UserProfile, IncomeSource, SpendingCategory, Transaction
)
from app.core.logging import get_logger

logger = get_logger("database")

SALT_FILE = ".radiant_salt"
ITERATIONS = 600_000  # OWASP 2023 recommendation


def get_or_create_salt(data_dir: Path) -> bytes:
    """Get existing salt or create new one."""
    salt_path = data_dir / SALT_FILE
    if salt_path.exists():
        return salt_path.read_bytes()

    salt = os.urandom(32)
    data_dir.mkdir(parents=True, exist_ok=True)
    salt_path.write_bytes(salt)
    return salt


def derive_key(password: str, salt: bytes) -> bytes:
    """Derive encryption key from password using PBKDF2."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=ITERATIONS,
    )
    return kdf.derive(password.encode())


class SecureDatabase:
    """
    SQLite repository with SQLCipher encryption.

    Provides persistent storage for financial data with encryption at rest.
    """

    SCHEMA_VERSION = 1

    def __init__(self, data_dir: Path, encrypted: bool = True):
        self.data_dir = Path(data_dir)
        self.db_path = self.data_dir / "radiant.db"
        self.encrypted = encrypted
        self._connection: Optional[sqlite3.Connection] = None
        self._password: Optional[str] = None

    @property
    def is_connected(self) -> bool:
        return self._connection is not None

    def connect(self, password: Optional[str] = None) -> None:
        """
        Establish database connection.

        For encrypted databases, password is required.
        """
        self.data_dir.mkdir(parents=True, exist_ok=True)

        if self.encrypted:
            if not password:
                raise ValueError("Password required for encrypted database")

            try:
                import sqlcipher3
                self._connection = sqlcipher3.connect(str(self.db_path))
                salt = get_or_create_salt(self.data_dir)
                key = derive_key(password, salt)
                self._connection.execute(f"PRAGMA key = \"x'{key.hex()}'\";")
                self._password = password
                logger.info("Connected to encrypted database")
            except ImportError:
                logger.warning("sqlcipher3 not available, falling back to unencrypted SQLite")
                self._connection = sqlite3.connect(str(self.db_path))
                self.encrypted = False
        else:
            self._connection = sqlite3.connect(str(self.db_path))
            logger.info("Connected to unencrypted database")

        self._connection.row_factory = sqlite3.Row
        self._run_migrations()

    def close(self) -> None:
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
            self._password = None

    def _run_migrations(self) -> None:
        """Run database migrations to ensure schema is up to date."""
        cursor = self._connection.cursor()

        # Create schema version table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY
            )
        """)

        # Get current version
        cursor.execute("SELECT MAX(version) FROM schema_version")
        row = cursor.fetchone()
        current_version = row[0] if row[0] else 0

        if current_version < 1:
            self._migrate_v1(cursor)
            cursor.execute("INSERT INTO schema_version (version) VALUES (1)")

        self._connection.commit()

    def _migrate_v1(self, cursor: sqlite3.Cursor) -> None:
        """Initial schema migration."""
        # Assets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assets (
                id TEXT PRIMARY KEY,
                data TEXT NOT NULL
            )
        """)

        # Liabilities table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS liabilities (
                id TEXT PRIMARY KEY,
                data TEXT NOT NULL
            )
        """)

        # Income table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS income (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT NOT NULL
            )
        """)

        # Spending plan table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS spending_plan (
                id TEXT PRIMARY KEY,
                data TEXT NOT NULL
            )
        """)

        # Financial tasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                due_date TEXT,
                completed INTEGER DEFAULT 0
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_completed ON tasks(completed)")

        # Upcoming expenses table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS upcoming_expenses (
                id TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                due_date TEXT NOT NULL
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_expenses_due_date ON upcoming_expenses(due_date)")

        # User profile table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_profile (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                data TEXT NOT NULL
            )
        """)

        # Transactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT NOT NULL,
                date TEXT NOT NULL
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date)")

        logger.info("Database schema v1 created")

    def _serialize(self, model) -> str:
        """Serialize a Pydantic model to JSON."""
        try:
            return model.model_dump_json()
        except AttributeError:
            return json.dumps(model.dict(), default=str)

    def _deserialize(self, data: str, model_class):
        """Deserialize JSON to a Pydantic model."""
        return model_class(**json.loads(data))

    # === Asset Operations ===

    def get_assets(self) -> List[Asset]:
        """Get all assets."""
        cursor = self._connection.execute("SELECT data FROM assets")
        return [self._deserialize(row[0], Asset) for row in cursor.fetchall()]

    def save_asset(self, asset: Asset) -> None:
        """Save or update an asset."""
        self._connection.execute(
            "INSERT OR REPLACE INTO assets (id, data) VALUES (?, ?)",
            (str(asset.id), self._serialize(asset))
        )
        self._connection.commit()

    def save_assets(self, assets: List[Asset]) -> None:
        """Save multiple assets."""
        cursor = self._connection.cursor()
        for asset in assets:
            cursor.execute(
                "INSERT OR REPLACE INTO assets (id, data) VALUES (?, ?)",
                (str(asset.id), self._serialize(asset))
            )
        self._connection.commit()

    def delete_asset(self, asset_id: UUID) -> None:
        """Delete an asset."""
        self._connection.execute("DELETE FROM assets WHERE id = ?", (str(asset_id),))
        self._connection.commit()

    # === Liability Operations ===

    def get_liabilities(self) -> List[Liability]:
        """Get all liabilities."""
        cursor = self._connection.execute("SELECT data FROM liabilities")
        return [self._deserialize(row[0], Liability) for row in cursor.fetchall()]

    def save_liability(self, liability: Liability) -> None:
        """Save or update a liability."""
        self._connection.execute(
            "INSERT OR REPLACE INTO liabilities (id, data) VALUES (?, ?)",
            (str(liability.id), self._serialize(liability))
        )
        self._connection.commit()

    def save_liabilities(self, liabilities: List[Liability]) -> None:
        """Save multiple liabilities."""
        cursor = self._connection.cursor()
        for liability in liabilities:
            cursor.execute(
                "INSERT OR REPLACE INTO liabilities (id, data) VALUES (?, ?)",
                (str(liability.id), self._serialize(liability))
            )
        self._connection.commit()

    # === Task Operations ===

    def get_tasks(self, include_completed: bool = False) -> List[FinancialTask]:
        """Get financial tasks."""
        if include_completed:
            cursor = self._connection.execute(
                "SELECT data FROM tasks ORDER BY due_date"
            )
        else:
            cursor = self._connection.execute(
                "SELECT data FROM tasks WHERE completed = 0 ORDER BY due_date"
            )
        return [self._deserialize(row[0], FinancialTask) for row in cursor.fetchall()]

    def get_upcoming_tasks(self, days: int = 7) -> List[FinancialTask]:
        """Get tasks due within the specified number of days."""
        cursor = self._connection.execute("""
            SELECT data FROM tasks
            WHERE completed = 0
            AND (due_date IS NULL OR date(due_date) <= date('now', '+' || ? || ' days'))
            ORDER BY due_date
        """, (days,))
        return [self._deserialize(row[0], FinancialTask) for row in cursor.fetchall()]

    def save_task(self, task: FinancialTask) -> None:
        """Save or update a financial task."""
        due_date_str = task.due_date.isoformat() if task.due_date else None
        self._connection.execute(
            "INSERT OR REPLACE INTO tasks (id, data, due_date, completed) VALUES (?, ?, ?, ?)",
            (str(task.id), self._serialize(task), due_date_str, 1 if task.completed else 0)
        )
        self._connection.commit()

    def complete_task(self, task_id: UUID) -> None:
        """Mark a task as completed."""
        from datetime import datetime
        cursor = self._connection.execute(
            "SELECT data FROM tasks WHERE id = ?", (str(task_id),)
        )
        row = cursor.fetchone()
        if row:
            task = self._deserialize(row[0], FinancialTask)
            task.completed = True
            task.completed_at = datetime.now()
            self.save_task(task)

    # === Upcoming Expense Operations ===

    def get_upcoming_expenses(self, days: int = 30) -> List[UpcomingExpense]:
        """Get expenses due within the specified number of days."""
        cursor = self._connection.execute("""
            SELECT data FROM upcoming_expenses
            WHERE date(due_date) <= date('now', '+' || ? || ' days')
            ORDER BY due_date
        """, (days,))
        return [self._deserialize(row[0], UpcomingExpense) for row in cursor.fetchall()]

    def get_all_expenses(self) -> List[UpcomingExpense]:
        """Get all upcoming expenses."""
        cursor = self._connection.execute(
            "SELECT data FROM upcoming_expenses ORDER BY due_date"
        )
        return [self._deserialize(row[0], UpcomingExpense) for row in cursor.fetchall()]

    def save_expense(self, expense: UpcomingExpense) -> None:
        """Save or update an upcoming expense."""
        self._connection.execute(
            "INSERT OR REPLACE INTO upcoming_expenses (id, data, due_date) VALUES (?, ?, ?)",
            (str(expense.id), self._serialize(expense), expense.due_date.isoformat())
        )
        self._connection.commit()

    def delete_expense(self, expense_id: UUID) -> None:
        """Delete an upcoming expense."""
        self._connection.execute(
            "DELETE FROM upcoming_expenses WHERE id = ?", (str(expense_id),)
        )
        self._connection.commit()

    # === User Profile Operations ===

    def get_user_profile(self) -> Optional[UserProfile]:
        """Get the user profile."""
        cursor = self._connection.execute("SELECT data FROM user_profile WHERE id = 1")
        row = cursor.fetchone()
        if row:
            return self._deserialize(row[0], UserProfile)
        return None

    def save_user_profile(self, profile: UserProfile) -> None:
        """Save the user profile."""
        self._connection.execute(
            "INSERT OR REPLACE INTO user_profile (id, data) VALUES (1, ?)",
            (self._serialize(profile),)
        )
        self._connection.commit()

    # === Income Operations ===

    def get_income(self) -> List[IncomeSource]:
        """Get all income sources."""
        cursor = self._connection.execute("SELECT data FROM income")
        return [self._deserialize(row[0], IncomeSource) for row in cursor.fetchall()]

    def save_income(self, sources: List[IncomeSource]) -> None:
        """Save income sources (replaces all)."""
        cursor = self._connection.cursor()
        cursor.execute("DELETE FROM income")
        for source in sources:
            cursor.execute(
                "INSERT INTO income (data) VALUES (?)",
                (self._serialize(source),)
            )
        self._connection.commit()

    # === Spending Plan Operations ===

    def get_spending_plan(self) -> List[SpendingCategory]:
        """Get the spending plan."""
        cursor = self._connection.execute("SELECT data FROM spending_plan")
        return [self._deserialize(row[0], SpendingCategory) for row in cursor.fetchall()]

    def save_spending_plan(self, categories: List[SpendingCategory]) -> None:
        """Save spending categories."""
        cursor = self._connection.cursor()
        cursor.execute("DELETE FROM spending_plan")
        for category in categories:
            cursor.execute(
                "INSERT INTO spending_plan (id, data) VALUES (?, ?)",
                (str(category.id), self._serialize(category))
            )
        self._connection.commit()

    # === Migration from FileRepository ===

    def migrate_from_json(self, json_data_dir: Path) -> dict:
        """
        Import existing data from JSON files.

        Returns a dict with counts of migrated items.
        """
        from app.data.repository import FileRepository
        import asyncio

        counts = {
            "assets": 0,
            "liabilities": 0,
            "income": 0,
            "spending": 0,
            "user": False
        }

        file_repo = FileRepository(json_data_dir)

        # Run async methods synchronously
        loop = asyncio.new_event_loop()

        try:
            # Migrate assets
            assets = loop.run_until_complete(file_repo.get_assets())
            if assets:
                self.save_assets(assets)
                counts["assets"] = len(assets)

            # Migrate liabilities
            liabilities = loop.run_until_complete(file_repo.get_liabilities())
            if liabilities:
                self.save_liabilities(liabilities)
                counts["liabilities"] = len(liabilities)

            # Migrate income
            income = loop.run_until_complete(file_repo.get_income())
            if income:
                self.save_income(income)
                counts["income"] = len(income)

            # Migrate spending plan
            spending = loop.run_until_complete(file_repo.get_spending_plan())
            if spending:
                self.save_spending_plan(spending)
                counts["spending"] = len(spending)

            # Migrate user profile
            try:
                profile = loop.run_until_complete(file_repo.get_user_profile())
                if profile:
                    self.save_user_profile(profile)
                    counts["user"] = True
            except Exception as e:
                logger.warning(f"Could not migrate user profile: {e}")
        finally:
            loop.close()

        logger.info(f"Migration complete: {counts}")
        return counts

    # === Export Operations ===

    def export_all(self) -> dict:
        """Export all data as a dictionary."""
        return {
            "assets": [a.model_dump() if hasattr(a, 'model_dump') else a.dict()
                      for a in self.get_assets()],
            "liabilities": [l.model_dump() if hasattr(l, 'model_dump') else l.dict()
                           for l in self.get_liabilities()],
            "tasks": [t.model_dump() if hasattr(t, 'model_dump') else t.dict()
                     for t in self.get_tasks(include_completed=True)],
            "upcoming_expenses": [e.model_dump() if hasattr(e, 'model_dump') else e.dict()
                                  for e in self.get_all_expenses()],
            "income": [i.model_dump() if hasattr(i, 'model_dump') else i.dict()
                      for i in self.get_income()],
            "spending_plan": [s.model_dump() if hasattr(s, 'model_dump') else s.dict()
                             for s in self.get_spending_plan()],
            "user_profile": (self.get_user_profile().model_dump()
                            if self.get_user_profile() and hasattr(self.get_user_profile(), 'model_dump')
                            else self.get_user_profile().dict() if self.get_user_profile() else None)
        }
