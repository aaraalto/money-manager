import asyncio
import csv
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Type, TypeVar, Union, Any
from datetime import datetime
from uuid import UUID

from app.models import Asset, Liability, IncomeSource, SpendingCategory, Transaction, UserProfile

T = TypeVar("T", bound=Union[Asset, Liability, IncomeSource, SpendingCategory, UserProfile])

# Singleton In-Memory Cache
# Key: file_path string, Value: data object
_GLOBAL_CACHE: Dict[str, Any] = {}
# Key: file_path string, Value: last modification timestamp
_GLOBAL_MTIMES: Dict[str, float] = {}

class FileRepository:
    def __init__(self, root_dir: Path = Path("data")):
        self.root_dir = root_dir

    @property
    def assets_file(self) -> Path:
        return self.root_dir / "assets.json"

    @property
    def liabilities_file(self) -> Path:
        return self.root_dir / "liabilities.json"

    @property
    def income_file(self) -> Path:
        return self.root_dir / "income.json"

    @property
    def spending_file(self) -> Path:
        return self.root_dir / "spending_plan.json"

    @property
    def spending_csv_file(self) -> Path:
        return self.root_dir / "spending_plan.csv"

    @property
    def transactions_file(self) -> Path:
        return self.root_dir / "transactions.csv"

    @property
    def user_file(self) -> Path:
        return self.root_dir / "user.json"

    async def _load_json_async(self, file_path: Path, model: Type[T], is_list: bool = True) -> Union[List[T], T]:
        """
        Loads JSON data asynchronously with caching based on file modification time.
        Uses a global cache to persist across requests.
        """
        file_str = str(file_path)
        
        # Check if file exists
        if not await asyncio.to_thread(file_path.exists):
            if is_list:
                return []
            # For single objects like UserProfile, we might need a default handler, 
            # but strictly following this generic method, we return None or let caller handle.
            # However, based on usage, we'll handle specifics in caller or return empty.
            return [] if is_list else None

        # Check modification time
        stats = await asyncio.to_thread(file_path.stat)
        mtime = stats.st_mtime

        # Return cached data if file hasn't changed
        if file_str in _GLOBAL_CACHE and _GLOBAL_MTIMES.get(file_str) == mtime:
            return _GLOBAL_CACHE[file_str]

        # Load data
        try:
            def read_json():
                with open(file_path, "r") as f:
                    return json.load(f)

            data = await asyncio.to_thread(read_json)
            
            # Helper function to clean up invalid UUID IDs
            def clean_item(item: dict) -> dict:
                """Remove invalid UUID IDs to let Pydantic generate new ones."""
                if 'id' in item:
                    try:
                        # Try to parse as UUID - if it fails, remove it
                        UUID(str(item['id']))
                    except (ValueError, TypeError):
                        # Not a valid UUID, remove it so model generates one
                        item = item.copy()
                        del item['id']
                return item
            
            if is_list:
                items = [model(**clean_item(item)) for item in data]
                result = items
            else:
                result = model(**clean_item(data))
            
            # Update cache
            _GLOBAL_CACHE[file_str] = result
            _GLOBAL_MTIMES[file_str] = mtime
            return result
        except (json.JSONDecodeError, OSError) as e:
            print(f"Error loading {file_path}: {e}")
            return [] if is_list else None

    async def get_assets(self) -> List[Asset]:
        return await self._load_json_async(self.assets_file, Asset)

    async def get_liabilities(self) -> List[Liability]:
        return await self._load_json_async(self.liabilities_file, Liability)

    async def get_income(self) -> List[IncomeSource]:
        return await self._load_json_async(self.income_file, IncomeSource)

    async def get_spending_plan(self) -> List[SpendingCategory]:
        # Check for CSV migration first
        if not await asyncio.to_thread(self.spending_file.exists) and await asyncio.to_thread(self.spending_csv_file.exists):
             return await self._migrate_spending_csv()

        return await self._load_json_async(self.spending_file, SpendingCategory)

    async def _migrate_spending_csv(self) -> List[SpendingCategory]:
        def read_csv():
            items = []
            try:
                with open(self.spending_csv_file, "r") as f:
                    reader = csv.DictReader(f, skipinitialspace=True)
                    for row in reader:
                        if not row or not row.get('category'): continue
                        clean_row = {k: v.strip() if isinstance(v, str) else v for k, v in row.items()}
                        if 'amount' in clean_row and isinstance(clean_row['amount'], str):
                            try:
                                clean_row['amount'] = float(clean_row['amount'])
                            except ValueError:
                                continue
                        items.append(SpendingCategory(**clean_row))
            except Exception as e:
                print(f"Error reading spending file: {e}")
            return items
            
        items = await asyncio.to_thread(read_csv)
        await self.save_spending_plan(items)
        return items

    async def save_spending_plan(self, items: List[SpendingCategory]):
        def write_json():
            self.spending_file.parent.mkdir(exist_ok=True)
            with open(self.spending_file, "w") as f:
                data = [item.dict() for item in items]
                for d in data:
                    if 'id' in d and isinstance(d['id'], UUID):
                        d['id'] = str(d['id'])
                json.dump(data, f, indent=2, default=str)
        
        await asyncio.to_thread(write_json)
        # Invalidate cache
        if str(self.spending_file) in _GLOBAL_MTIMES:
            del _GLOBAL_MTIMES[str(self.spending_file)]

    async def get_transactions(self) -> List[Transaction]:
        def read_transactions():
            if not self.transactions_file.exists():
                return []
            transactions = []
            try:
                with open(self.transactions_file, "r") as f:
                    f.seek(0, os.SEEK_END)
                    if f.tell() == 0: return []
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
        if not await asyncio.to_thread(self.user_file.exists):
            default_profile = UserProfile(name="Euclid")
            await self.save_user_profile(default_profile)
            return default_profile

        profile = await self._load_json_async(self.user_file, UserProfile, is_list=False)
        if profile is None:
            return UserProfile(name="Euclid")
        return profile

    async def save_user_profile(self, profile: UserProfile):
        def write_json():
            self.user_file.parent.mkdir(exist_ok=True)
            with open(self.user_file, "w") as f:
                try:
                    data = profile.model_dump()
                except AttributeError:
                    data = profile.dict()
                json.dump(data, f, indent=2, default=str)
        
        await asyncio.to_thread(write_json)
        # Update cache immediately
        file_str = str(self.user_file)
        if await asyncio.to_thread(self.user_file.exists):
            stats = await asyncio.to_thread(self.user_file.stat)
            _GLOBAL_MTIMES[file_str] = stats.st_mtime
            _GLOBAL_CACHE[file_str] = profile
