import asyncio
import csv
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Type, TypeVar, Union, Any
from datetime import datetime

from backend.models import Asset, Liability, IncomeSource, SpendingCategory, Transaction, UserProfile

T = TypeVar("T", bound=Union[Asset, Liability, IncomeSource])

DATA_DIR = Path("data")
ASSETS_FILE = DATA_DIR / "assets.json"
LIABILITIES_FILE = DATA_DIR / "liabilities.json"
INCOME_FILE = DATA_DIR / "income.json"
SPENDING_FILE = DATA_DIR / "spending_plan.csv"
TRANSACTIONS_FILE = DATA_DIR / "transactions.csv"
USER_FILE = DATA_DIR / "user.json"

class FileRepository:
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._mtimes: Dict[str, float] = {}

    async def _load_json_async(self, file_path: Path, model: Type[T]) -> List[T]:
        """
        Loads JSON data asynchronously with caching based on file modification time.
        """
        file_str = str(file_path)
        
        # Check if file exists
        if not await asyncio.to_thread(file_path.exists):
            return []

        # Check modification time
        stats = await asyncio.to_thread(file_path.stat)
        mtime = stats.st_mtime

        # Return cached data if file hasn't changed
        if file_str in self._cache and self._mtimes.get(file_str) == mtime:
            return self._cache[file_str]

        # Load data
        try:
            def read_json():
                with open(file_path, "r") as f:
                    return json.load(f)

            data = await asyncio.to_thread(read_json)
            items = [model(**item) for item in data]
            
            # Update cache
            self._cache[file_str] = items
            self._mtimes[file_str] = mtime
            return items
        except (json.JSONDecodeError, OSError) as e:
            print(f"Error loading {file_path}: {e}")
            return []

    async def get_assets(self) -> List[Asset]:
        return await self._load_json_async(ASSETS_FILE, Asset)

    async def get_liabilities(self) -> List[Liability]:
        return await self._load_json_async(LIABILITIES_FILE, Liability)

    async def get_income(self) -> List[IncomeSource]:
        return await self._load_json_async(INCOME_FILE, IncomeSource)

    async def get_spending_plan(self) -> List[SpendingCategory]:
        file_str = str(SPENDING_FILE)
        
        if not await asyncio.to_thread(SPENDING_FILE.exists):
            return []

        stats = await asyncio.to_thread(SPENDING_FILE.stat)
        mtime = stats.st_mtime

        if file_str in self._cache and self._mtimes.get(file_str) == mtime:
            return self._cache[file_str]

        def read_csv():
            items = []
            try:
                with open(SPENDING_FILE, "r") as f:
                    reader = csv.DictReader(f, skipinitialspace=True)
                    for row in reader:
                        if not row or not row.get('category'): continue
                        clean_row = {k: v.strip() if isinstance(v, str) else v for k, v in row.items()}
                        items.append(SpendingCategory(**clean_row))
            except Exception as e:
                print(f"Error reading spending file: {e}")
            return items

        items = await asyncio.to_thread(read_csv)
        self._cache[file_str] = items
        self._mtimes[file_str] = mtime
        return items

    async def save_spending_plan(self, items: List[SpendingCategory]):
        def write_csv():
            SPENDING_FILE.parent.mkdir(exist_ok=True)
            with open(SPENDING_FILE, "w", newline="") as f:
                fieldnames = ["category", "amount", "type"]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for item in items:
                    writer.writerow(item.dict())
        
        await asyncio.to_thread(write_csv)
        # Invalidate cache
        if str(SPENDING_FILE) in self._mtimes:
            del self._mtimes[str(SPENDING_FILE)]

    async def get_transactions(self) -> List[Transaction]:
        # Similar logic for transactions if needed
        # For now, implementing basic loading
        def read_transactions():
            if not TRANSACTIONS_FILE.exists():
                return []
            transactions = []
            try:
                with open(TRANSACTIONS_FILE, "r") as f:
                    f.seek(0, os.SEEK_END)
                    if f.tell() == 0:
                        return []
                    f.seek(0)
                    reader = csv.DictReader(f)
                    for row in reader:
                        if not row: continue
                        transactions.append(Transaction(**row))
            except Exception as e:
                print(f"Error reading transactions: {e}")
            return transactions

        return await asyncio.to_thread(read_transactions)

    async def get_user_profile(self) -> UserProfile:
        file_str = str(USER_FILE)
        
        # Check if file exists
        if not await asyncio.to_thread(USER_FILE.exists):
            # Create default profile if missing
            default_profile = UserProfile(name="Euclid")
            await self.save_user_profile(default_profile)
            return default_profile

        # Check modification time
        stats = await asyncio.to_thread(USER_FILE.stat)
        mtime = stats.st_mtime

        # Return cached data if file hasn't changed
        if file_str in self._cache and self._mtimes.get(file_str) == mtime:
            return self._cache[file_str]

        # Load data
        try:
            def read_json():
                with open(USER_FILE, "r") as f:
                    return json.load(f)

            data = await asyncio.to_thread(read_json)
            profile = UserProfile(**data)
            
            # Update cache
            self._cache[file_str] = profile
            self._mtimes[file_str] = mtime
            return profile
        except (json.JSONDecodeError, OSError) as e:
            print(f"Error loading {USER_FILE}: {e}")
            # Fallback to default in case of error
            return UserProfile(name="Euclid")

    async def save_user_profile(self, profile: UserProfile):
        def write_json():
            USER_FILE.parent.mkdir(exist_ok=True)
            with open(USER_FILE, "w") as f:
                # Use mode='json' (or model_dump for Pydantic v2) to serialize
                # Since we might be on Pydantic v1 or v2, let's be safe. 
                # Assuming Pydantic v1 based on existing code using .dict()
                # If v2, use model_dump()
                try:
                    data = profile.model_dump()
                except AttributeError:
                    data = profile.dict()
                # Handle UUID serialization
                json.dump(data, f, indent=2, default=str)
        
        await asyncio.to_thread(write_json)
        # Update cache immediately
        file_str = str(USER_FILE)
        if await asyncio.to_thread(USER_FILE.exists):
            stats = await asyncio.to_thread(USER_FILE.stat)
            self._mtimes[file_str] = stats.st_mtime
            self._cache[file_str] = profile
