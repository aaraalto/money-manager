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
sys.path.append(str(Path(__file__).parent))

from app.models import Asset, Liability, Transaction, IncomeSource, SpendingCategory, AssetType, LiquidityStatus, LiabilityTag

DATA_DIR = Path("data")
ASSETS_FILE = DATA_DIR / "assets.json"
LIABILITIES_FILE = DATA_DIR / "liabilities.json"
INCOME_FILE = DATA_DIR / "income.json"
SPENDING_FILE = DATA_DIR / "spending_plan.csv"
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

def load_spending_plan() -> List[SpendingCategory]:
    if not SPENDING_FILE.exists():
        return []
    items = []
    try:
        with open(SPENDING_FILE, "r") as f:
            # Handle spaces after delimiters by skipinitialspace=True
            reader = csv.DictReader(f, skipinitialspace=True)
            for row in reader:
                if not row or not row.get('category'): continue
                try:
                    # Handle potential whitespace in values if manual spacing was used
                    clean_row = {k: v.strip() if isinstance(v, str) else v for k, v in row.items()}
                    items.append(SpendingCategory(**clean_row))
                except Exception as e:
                    print(f"Skipping invalid spending row: {row} - {e}")
    except Exception as e:
        print(f"Error reading spending file: {e}")
        return []
    return items

def save_spending_plan(items: List[SpendingCategory]):
    SPENDING_FILE.parent.mkdir(exist_ok=True)
    with open(SPENDING_FILE, "w", newline="") as f:
        fieldnames = ["category", "amount", "type"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in items:
            writer.writerow(item.dict())


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
        min_payment=args.min_payment,
        credit_limit=args.credit_limit,
        tags=args.tags or []
    )
    liabilities.append(new_liability)
    save_json(LIABILITIES_FILE, liabilities)
    print(f"Liability '{new_liability.name}' added successfully.")

def update_liability(args):
    liabilities = load_json(LIABILITIES_FILE, Liability)
    target_name = args.name.lower()
    
    found = False
    for l in liabilities:
        if l.name.lower() == target_name:
            if args.interest_rate is not None:
                l.interest_rate = args.interest_rate
            if args.min_payment is not None:
                l.min_payment = args.min_payment
            if args.balance is not None:
                l.balance = args.balance
            if args.credit_limit is not None:
                l.credit_limit = args.credit_limit
            
            print(f"Updated liability: {l.name}")
            found = True
            # Don't break in case of duplicate names, update all matches? 
            # Standard behavior is usually update unique ID, but name is user facing.
            # Let's stop at first match for safety, or list multiple? 
            # Given the list, names seem distinct.
            break
            
    if found:
        save_json(LIABILITIES_FILE, liabilities)
    else:
        print(f"Error: No liability found with name matching '{args.name}'")

def bulk_update_liabilities(args):
    liabilities = load_json(LIABILITIES_FILE, Liability)
    print("Starting bulk update for liabilities (Press Ctrl+C to cancel anytime).")
    print("Press Enter to skip a value.")
    
    updated_count = 0
    for l in liabilities:
        print(f"\n--- {l.name} ---")
        print(f"Current Balance: {l.balance}, Rate: {l.interest_rate}, Min Payment: {l.min_payment}")
        
        # Balance
        new_bal = input(f"New Balance [{l.balance}]: ").strip()
        if new_bal:
            try:
                l.balance = float(new_bal)
            except ValueError:
                print("Invalid number, keeping original.")
        
        # Rate
        new_rate = input(f"New Interest Rate [{l.interest_rate}]: ").strip()
        if new_rate:
            try:
                l.interest_rate = float(new_rate)
            except ValueError:
                print("Invalid number, keeping original.")

        # Min Payment
        new_min = input(f"New Min Payment [{l.min_payment}]: ").strip()
        if new_min:
            try:
                l.min_payment = float(new_min)
            except ValueError:
                print("Invalid number, keeping original.")
        
        # Credit Limit (if Credit Card)
        if l.tags and LiabilityTag.CREDIT_CARD in l.tags:
            current_limit = l.credit_limit if l.credit_limit is not None else "None"
            new_limit = input(f"New Credit Limit [{current_limit}]: ").strip()
            if new_limit:
                try:
                    l.credit_limit = float(new_limit)
                except ValueError:
                    print("Invalid number, keeping original.")

        updated_count += 1

    if updated_count > 0:
        save_json(LIABILITIES_FILE, liabilities)
        print(f"\nSuccessfully updated {updated_count} liabilities.")

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
    print(RADIANT_BANNER)
    print("\n🚀 System Initialized. Starting Radiant Server...")
    print("   • Dashboard:     http://localhost:8000")
    print("   • API Docs:      http://localhost:8000/docs")
    print("\n   Use 'Ctrl+C' to stop the server.")
    print("-" * 60)
    
    import uvicorn
    # Configure logging to be cleaner if possible, or just run
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")

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
    liab_parser.add_argument("--credit-limit", type=float, help="Total credit limit")
    liab_parser.add_argument("--tags", nargs="*", choices=[e.value for e in LiabilityTag], help="Tags for the liability")
    liab_parser.set_defaults(func=add_liability)

    # Update Liability
    update_liab_parser = subparsers.add_parser("update-liability", aliases=["ul"], help="Update an existing liability")
    update_liab_parser.add_argument("-n", "--name", required=True, help="Name of the liability to update (case-insensitive match)")
    update_liab_parser.add_argument("-i", "--interest-rate", type=float, help="New annual rate (e.g., 0.05 for 5%)")
    update_liab_parser.add_argument("-m", "--min-payment", type=float, help="New minimum payment")
    update_liab_parser.add_argument("-b", "--balance", type=float, help="New balance")
    update_liab_parser.add_argument("-c", "--credit-limit", type=float, help="New credit limit")
    update_liab_parser.set_defaults(func=update_liability)

    # Bulk Update Liabilities
    bulk_liab_parser = subparsers.add_parser("bulk-update-liabilities", aliases=["bul"], help="Interactively update all liabilities")
    bulk_liab_parser.set_defaults(func=bulk_update_liabilities)

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
        print(RADIANT_BANNER)
        print("Welcome to Radiant - Your Personal Financial OS")
        print("Use './manage.sh --help' to see available commands.\n")
        parser.print_help()

RADIANT_BANNER = r"""
██████╗  █████╗ ██████╗ ██╗ █████╗ ███╗   ██╗████████╗
██╔══██╗██╔══██╗██╔══██╗██║██╔══██╗████╗  ██║╚══██╔══╝
██████╔╝███████║██║  ██║██║███████║██╔██╗ ██║   ██║   
██╔══██╗██╔══██║██║  ██║██║██╔══██║██║╚██╗██║   ██║   
██║  ██║██║  ██║██████╔╝██║██║  ██║██║ ╚████║   ██║   
╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝   
"""

if __name__ == "__main__":
    main()

