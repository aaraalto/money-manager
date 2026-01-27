import asyncio
import csv
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Type, TypeVar, Union, Any
from datetime import datetime
from uuid import UUID

from app.models import Asset, Liability, IncomeSource, SpendingCategory, Transaction, UserProfile, AssetType
from app.core.logging import get_logger

# Module logger
logger = get_logger("repository")

T = TypeVar("T", bound=Union[Asset, Liability, IncomeSource])

class FileRepository:
    def __init__(self, root_dir: Path = Path("data")):
        self.root_dir = root_dir
        self._cache: Dict[str, Any] = {}
        self._mtimes: Dict[str, float] = {}

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
            if not isinstance(data, list):
                logger.warning(f"File {file_path} does not contain a list, got {type(data)}")
                return []
            
            items = []
            for item in data:
                try:
                    items.append(model(**item))
                except Exception as e:
                    logger.warning(f"Skipping invalid item in {file_path}: {e}")
                    continue
            
            # Update cache
            self._cache[file_str] = items
            self._mtimes[file_str] = mtime
            return items
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Error loading {file_path}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error loading {file_path}: {e}")
            return []

    async def get_assets(self) -> List[Asset]:
        return await self._load_json_async(self.assets_file, Asset)

    async def get_liabilities(self) -> List[Liability]:
        return await self._load_json_async(self.liabilities_file, Liability)

    async def get_income(self) -> List[IncomeSource]:
        return await self._load_json_async(self.income_file, IncomeSource)

    async def get_spending_plan(self) -> List[SpendingCategory]:
        file_str = str(self.spending_file)
        
        # 1. Try loading JSON first
        if await asyncio.to_thread(self.spending_file.exists):
            stats = await asyncio.to_thread(self.spending_file.stat)
            mtime = stats.st_mtime

            if file_str in self._cache and self._mtimes.get(file_str) == mtime:
                return self._cache[file_str]
            
            items = await self._load_json_async(self.spending_file, SpendingCategory)
            self._cache[file_str] = items
            self._mtimes[file_str] = mtime
            return items

        # 2. Fallback to CSV migration
        if await asyncio.to_thread(self.spending_csv_file.exists):
             def read_csv():
                items = []
                try:
                    with open(self.spending_csv_file, "r") as f:
                        reader = csv.DictReader(f, skipinitialspace=True)
                        for row in reader:
                            if not row or not row.get('category'): continue
                            clean_row = {k: v.strip() if isinstance(v, str) else v for k, v in row.items()}
                            # Convert amount to float if it's a string
                            if 'amount' in clean_row and isinstance(clean_row['amount'], str):
                                try:
                                    clean_row['amount'] = float(clean_row['amount'])
                                except ValueError:
                                    logger.warning(f"Could not convert amount '{clean_row['amount']}' to float, skipping row")
                                    continue
                            items.append(SpendingCategory(**clean_row))
                except Exception as e:
                    logger.error(f"Error reading spending file: {e}")
                return items
             
             items = await asyncio.to_thread(read_csv)
             # Save as JSON to complete migration
             await self.save_spending_plan(items)
             return items

        return []

    async def save_spending_plan(self, items: List[SpendingCategory]):
        def write_json():
            self.spending_file.parent.mkdir(exist_ok=True)
            with open(self.spending_file, "w") as f:
                 # Handle serialization safely
                data = [item.dict() for item in items]
                # Convert UUIDs to strings for JSON
                for d in data:
                    if 'id' in d and isinstance(d['id'], UUID):
                        d['id'] = str(d['id'])
                json.dump(data, f, indent=2, default=str)
        
        await asyncio.to_thread(write_json)
        # Invalidate cache
        if str(self.spending_file) in self._mtimes:
            del self._mtimes[str(self.spending_file)]

    async def get_transactions(self) -> List[Transaction]:
        # Similar logic for transactions if needed
        # For now, implementing basic loading
        def read_transactions():
            if not self.transactions_file.exists():
                return []
            transactions = []
            try:
                with open(self.transactions_file, "r") as f:
                    f.seek(0, os.SEEK_END)
                    if f.tell() == 0:
                        return []
                    f.seek(0)
                    reader = csv.DictReader(f)
                    for row in reader:
                        if not row: continue
                        transactions.append(Transaction(**row))
            except Exception as e:
                logger.error(f"Error reading transactions: {e}")
            return transactions

        return await asyncio.to_thread(read_transactions)

    async def get_user_profile(self) -> UserProfile:
        file_str = str(self.user_file)
        
        # Check if file exists
        if not await asyncio.to_thread(self.user_file.exists):
            # Create default profile if missing
            default_profile = UserProfile(name="Euclid")
            await self.save_user_profile(default_profile)
            return default_profile

        # Check modification time
        stats = await asyncio.to_thread(self.user_file.stat)
        mtime = stats.st_mtime

        # Return cached data if file hasn't changed
        if file_str in self._cache and self._mtimes.get(file_str) == mtime:
            return self._cache[file_str]

        # Load data
        try:
            def read_json():
                with open(self.user_file, "r") as f:
                    return json.load(f)

            data = await asyncio.to_thread(read_json)
            profile = UserProfile(**data)
            
            # Update cache
            self._cache[file_str] = profile
            self._mtimes[file_str] = mtime
            return profile
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Error loading {self.user_file}: {e}")
            # Fallback to default in case of error
            return UserProfile(name="Euclid")

    async def save_user_profile(self, profile: UserProfile):
        def write_json():
            self.user_file.parent.mkdir(exist_ok=True)
            with open(self.user_file, "w") as f:
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
        file_str = str(self.user_file)
        if await asyncio.to_thread(self.user_file.exists):
            stats = await asyncio.to_thread(self.user_file.stat)
            self._mtimes[file_str] = stats.st_mtime
            self._cache[file_str] = profile

    async def save_income(self, items: List[IncomeSource]):
        """Save income sources to JSON file."""
        def write_json():
            self.income_file.parent.mkdir(exist_ok=True)
            with open(self.income_file, "w") as f:
                data = []
                for item in items:
                    try:
                        d = item.model_dump()
                    except AttributeError:
                        d = item.dict()
                    data.append(d)
                json.dump(data, f, indent=2, default=str)
        
        await asyncio.to_thread(write_json)
        # Invalidate cache
        file_str = str(self.income_file)
        if file_str in self._mtimes:
            del self._mtimes[file_str]
        if file_str in self._cache:
            del self._cache[file_str]

    async def save_liabilities(self, items: List[Liability]):
        """Save liabilities to JSON file."""
        def write_json():
            self.liabilities_file.parent.mkdir(exist_ok=True)
            with open(self.liabilities_file, "w") as f:
                data = []
                for item in items:
                    try:
                        d = item.model_dump()
                    except AttributeError:
                        d = item.dict()
                    # Convert UUIDs to strings
                    if 'id' in d and isinstance(d['id'], UUID):
                        d['id'] = str(d['id'])
                    # Convert enum values to strings
                    if 'tags' in d:
                        d['tags'] = [t.value if hasattr(t, 'value') else t for t in d['tags']]
                    data.append(d)
                json.dump(data, f, indent=2, default=str)
        
        await asyncio.to_thread(write_json)
        # Invalidate cache
        file_str = str(self.liabilities_file)
        if file_str in self._mtimes:
            del self._mtimes[file_str]
        if file_str in self._cache:
            del self._cache[file_str]

    async def save_assets(self, items: List[Asset]):
        """Save assets to JSON file."""
        def write_json():
            self.assets_file.parent.mkdir(exist_ok=True)
            with open(self.assets_file, "w") as f:
                data = []
                for item in items:
                    try:
                        d = item.model_dump()
                    except AttributeError:
                        d = item.dict()
                    # Convert UUIDs to strings
                    if 'id' in d and isinstance(d['id'], UUID):
                        d['id'] = str(d['id'])
                    # Convert enum values to strings
                    if 'type' in d and hasattr(d['type'], 'value'):
                        d['type'] = d['type'].value
                    if 'liquidity' in d and hasattr(d['liquidity'], 'value'):
                        d['liquidity'] = d['liquidity'].value
                    data.append(d)
                json.dump(data, f, indent=2, default=str)
        
        await asyncio.to_thread(write_json)
        # Invalidate cache
        file_str = str(self.assets_file)
        if file_str in self._mtimes:
            del self._mtimes[file_str]
        if file_str in self._cache:
            del self._cache[file_str]
