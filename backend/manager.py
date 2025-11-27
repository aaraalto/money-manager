import argparse
import json
import csv
import sys
import os
from datetime import date
from pathlib import Path
from typing import List, Type, TypeVar, Union
from uuid import UUID

# Add the project root to sys.path so imports work
sys.path.append(str(Path(__file__).parent.parent))

from backend.models import Asset, Liability, Transaction, AssetType, LiquidityStatus

DATA_DIR = Path("data")
ASSETS_FILE = DATA_DIR / "assets.json"
LIABILITIES_FILE = DATA_DIR / "liabilities.json"
TRANSACTIONS_FILE = DATA_DIR / "transactions.csv"

T = TypeVar("T", bound=Union[Asset, Liability])

def load_json(file_path: Path, model: Type[T]) -> List[T]:
    if not file_path.exists():
        return []
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
            return [model(**item) for item in data]
    except json.JSONDecodeError:
        print(f"Error: {file_path} contains invalid JSON.")
        return []

def save_json(file_path: Path, items: List[T]):
    # Ensure directory exists
    file_path.parent.mkdir(exist_ok=True)
    with open(file_path, "w") as f:
        # Use mode_dump or dict()
        json.dump([json.loads(item.json()) for item in items], f, indent=2)

def load_transactions() -> List[Transaction]:
    if not TRANSACTIONS_FILE.exists():
        return []
    transactions = []
    try:
        with open(TRANSACTIONS_FILE, "r") as f:
            # Check if file is empty
            f.seek(0, os.SEEK_END)
            if f.tell() == 0:
                return []
            f.seek(0)
            
            reader = csv.DictReader(f)
            for row in reader:
                if not row: continue # Skip empty rows
                try:
                    transactions.append(Transaction(**row))
                except Exception as e:
                    print(f"Skipping invalid transaction row: {row} - {e}")
    except Exception as e:
        print(f"Error reading transactions file: {e}")
        return []
        
    return transactions

def save_transaction(transaction: Transaction):
    TRANSACTIONS_FILE.parent.mkdir(exist_ok=True)
    file_exists = TRANSACTIONS_FILE.exists()
    
    with open(TRANSACTIONS_FILE, "a", newline="") as f:
        fieldnames = ["date", "amount", "category", "merchant"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
            
        writer.writerow({
            "date": transaction.date.isoformat(),
            "amount": transaction.amount,
            "category": transaction.category,
            "merchant": transaction.merchant
        })

def add_asset(args):
    assets = load_json(ASSETS_FILE, Asset)
    new_asset = Asset(
        name=args.name,
        type=args.type,
        value=args.value,
        apy=args.apy,
        liquidity=args.liquidity
    )
    assets.append(new_asset)
    save_json(ASSETS_FILE, assets)
    print(f"Asset '{new_asset.name}' added successfully.")

def add_liability(args):
    liabilities = load_json(LIABILITIES_FILE, Liability)
    new_liability = Liability(
        name=args.name,
        balance=args.balance,
        interest_rate=args.interest_rate,
        min_payment=args.min_payment
    )
    liabilities.append(new_liability)
    save_json(LIABILITIES_FILE, liabilities)
    print(f"Liability '{new_liability.name}' added successfully.")

def add_transaction(args):
    new_tx = Transaction(
        date=args.date or date.today(),
        amount=args.amount,
        category=args.category,
        merchant=args.merchant
    )
    save_transaction(new_tx)
    print(f"Transaction '{new_tx.merchant}' added successfully.")

def audit(args):
    print("Running System Audit...")
    assets = load_json(ASSETS_FILE, Asset)
    liabilities = load_json(LIABILITIES_FILE, Liability)
    transactions = load_transactions()
    
    print(f"Found {len(assets)} assets.")
    print(f"Found {len(liabilities)} liabilities.")
    print(f"Found {len(transactions)} transactions.")
    
    # Simple integrity checks
    errors = []
    for a in assets:
        if a.value < 0: errors.append(f"Asset {a.name} has negative value.")
    for l in liabilities:
        if l.balance < 0: errors.append(f"Liability {l.name} has negative balance.")
    
    if errors:
        print("\nFAILED: Integrity violations found:")
        for e in errors:
            print(f" - {e}")
    else:
        print("\nPASSED: Data integrity verified.")

def serve(args):
    print("Starting Wealth OS Server...")
    import uvicorn
    uvicorn.run("backend.server:app", host="0.0.0.0", port=8000, reload=True)

def main():
    parser = argparse.ArgumentParser(description="Wealth OS CLI Manager")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Add Asset
    asset_parser = subparsers.add_parser("add-asset", help="Add a new asset")
    asset_parser.add_argument("--name", required=True)
    asset_parser.add_argument("--type", choices=[e.value for e in AssetType], required=True)
    asset_parser.add_argument("--value", type=float, required=True)
    asset_parser.add_argument("--apy", type=float, default=0.0)
    asset_parser.add_argument("--liquidity", choices=[e.value for e in LiquidityStatus], default=LiquidityStatus.LIQUID)
    asset_parser.set_defaults(func=add_asset)

    # Add Liability
    liab_parser = subparsers.add_parser("add-liability", help="Add a new liability")
    liab_parser.add_argument("--name", required=True)
    liab_parser.add_argument("--balance", type=float, required=True)
    liab_parser.add_argument("--interest-rate", type=float, required=True, help="Annual rate (e.g., 0.05 for 5%)")
    liab_parser.add_argument("--min-payment", type=float, required=True)
    liab_parser.set_defaults(func=add_liability)

    # Add Transaction
    tx_parser = subparsers.add_parser("add-transaction", help="Add a new transaction")
    tx_parser.add_argument("--amount", type=float, required=True)
    tx_parser.add_argument("--merchant", required=True)
    tx_parser.add_argument("--category", required=True)
    tx_parser.add_argument("--date", type=date.fromisoformat, help="YYYY-MM-DD", default=None)
    tx_parser.set_defaults(func=add_transaction)

    # Audit
    audit_parser = subparsers.add_parser("audit", help="Audit data integrity")
    audit_parser.set_defaults(func=audit)
    
    # Serve
    serve_parser = subparsers.add_parser("serve", help="Start the web server")
    serve_parser.set_defaults(func=serve)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

