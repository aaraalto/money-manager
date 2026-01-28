#!/usr/bin/env python3
"""
mnm - Radiant Money Manager CLI

Entry point for the interactive TUI application.
"""
import argparse
import json
import csv
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def get_password(first_time: bool = False) -> str:
    """Prompt for database password."""
    import getpass

    if first_time:
        print("\n  Welcome to Radiant Money Manager!")
        print("  Please set a password to encrypt your financial data.\n")
        while True:
            password = getpass.getpass("  Password: ")
            if len(password) < 8:
                print("  Password must be at least 8 characters.")
                continue
            confirm = getpass.getpass("  Confirm password: ")
            if password != confirm:
                print("  Passwords do not match. Try again.")
                continue
            return password
    else:
        return getpass.getpass("  Password: ")


def export_data(format: str, data_dir: Path, output_dir: Path) -> None:
    """Export data to JSON or CSV."""
    from app.data.database import SecureDatabase

    db = SecureDatabase(data_dir, encrypted=True)

    # Check if database exists
    if not db.db_path.exists():
        print(f"Error: No database found at {db.db_path}")
        sys.exit(1)

    password = get_password(first_time=False)

    try:
        db.connect(password)
    except Exception as e:
        print(f"Error: Could not open database. Wrong password? {e}")
        sys.exit(1)

    data = db.export_all()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_dir.mkdir(parents=True, exist_ok=True)

    if format == "json":
        output_path = output_dir / f"radiant_export_{timestamp}.json"
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2, default=str)
        print(f"Exported to {output_path}")
    else:
        export_dir = output_dir / f"radiant_export_{timestamp}"
        export_dir.mkdir(parents=True, exist_ok=True)

        for key, items in data.items():
            if items and isinstance(items, list):
                csv_path = export_dir / f"{key}.csv"
                if items:
                    fieldnames = list(items[0].keys())
                    with open(csv_path, "w", newline="") as f:
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        for item in items:
                            writer.writerow({k: str(v) if v is not None else "" for k, v in item.items()})

        print(f"Exported to {export_dir}/")

    db.close()


def run_tui(data_dir: Path, encrypted: bool = True) -> None:
    """Launch the TUI application."""
    from app.cli.app import RadiantApp

    app = RadiantApp(data_dir=data_dir, encrypted=encrypted)
    app.run()


def main():
    parser = argparse.ArgumentParser(
        prog="mnm",
        description="Radiant Money Manager - Interactive Financial Dashboard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  mnm                    Launch the interactive TUI
  mnm --export json      Export all data to JSON
  mnm --export csv       Export all data to CSV files
        """
    )
    parser.add_argument(
        "--no-encryption",
        action="store_true",
        help="Disable database encryption (not recommended)"
    )
    parser.add_argument(
        "--export",
        choices=["json", "csv"],
        metavar="FORMAT",
        help="Export data and exit (json or csv)"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("."),
        help="Output directory for exports (default: current directory)"
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data"),
        help="Data directory path (default: ./data)"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0.0"
    )
    parser.add_argument(
        "--migrate",
        action="store_true",
        help="Migrate existing JSON data to the database"
    )

    args = parser.parse_args()

    if args.export:
        export_data(args.export, args.data_dir, args.output_dir)
        return

    if args.migrate:
        from app.data.database import SecureDatabase
        db = SecureDatabase(args.data_dir, encrypted=not args.no_encryption)
        first_time = not db.db_path.exists()
        password = None if args.no_encryption else get_password(first_time=first_time)
        db.connect(password)
        counts = db.migrate_from_json(args.data_dir)
        print(f"Migration complete:")
        print(f"  Assets: {counts['assets']}")
        print(f"  Liabilities: {counts['liabilities']}")
        print(f"  Income: {counts['income']}")
        print(f"  Spending: {counts['spending']}")
        print(f"  User profile: {'Yes' if counts['user'] else 'No'}")
        db.close()
        return

    # Launch TUI
    run_tui(args.data_dir, encrypted=not args.no_encryption)


if __name__ == "__main__":
    main()
