"""
Data Migration Script: Convert employee_name to employee_id
This script migrates all CSV records from using employee_name to employee_id
"""
import pandas as pd
import json
from pathlib import Path

# File paths
DATA_DIR = Path("wfh_data")
EMPLOYEES_FILE = DATA_DIR / "employees.json"
WFH_RECORDS_FILE = DATA_DIR / "wfh_records.csv"
ANNUAL_LEAVE_RECORDS_FILE = DATA_DIR / "annual_leave_records.csv"
SEMINAR_RECORDS_FILE = DATA_DIR / "seminar_records.csv"

def load_employees():
    """Load employees from JSON file"""
    with open(EMPLOYEES_FILE, 'r') as f:
        return json.load(f)

def create_name_to_id_mapping(employees):
    """Create a mapping dictionary from employee name to employee ID"""
    return {emp['name']: emp['id'] for emp in employees}

def migrate_csv_file(file_path, name_to_id_mapping, has_seminar_column=False):
    """
    Migrate a CSV file from employee_name to employee_id

    Args:
        file_path: Path to the CSV file
        name_to_id_mapping: Dictionary mapping employee names to IDs
        has_seminar_column: Whether this CSV has a seminar_name column
    """
    print(f"\nMigrating {file_path.name}...")

    # Read the CSV file
    df = pd.read_csv(file_path)

    if df.empty:
        print(f"  {file_path.name} is empty, creating new schema...")
        if has_seminar_column:
            df = pd.DataFrame(columns=['employee_id', 'date', 'status', 'seminar_name'])
        else:
            df = pd.DataFrame(columns=['employee_id', 'date', 'status'])
        df.to_csv(file_path, index=False)
        print(f"  [OK] {file_path.name} schema updated")
        return

    print(f"  Found {len(df)} records")

    # Check if already migrated
    if 'employee_id' in df.columns and 'employee_name' not in df.columns:
        print(f"  Already migrated, skipping...")
        return

    # Map employee names to IDs
    df['employee_id'] = df['employee_name'].map(name_to_id_mapping)

    # Check for unmapped names (should not happen if data is clean)
    unmapped = df[df['employee_id'].isna()]
    if not unmapped.empty:
        print(f"  WARNING: Found {len(unmapped)} records with unmapped employee names:")
        for name in unmapped['employee_name'].unique():
            print(f"    - {name}")
        # Remove unmapped records
        df = df[df['employee_id'].notna()]
        print(f"  Removed {len(unmapped)} unmapped records")

    # Reorder columns: employee_id, date, status, [seminar_name]
    if has_seminar_column:
        df = df[['employee_id', 'date', 'status', 'seminar_name']]
    else:
        df = df[['employee_id', 'date', 'status']]

    # Save the migrated data
    df.to_csv(file_path, index=False)
    print(f"  [OK] Successfully migrated {len(df)} records")

def main():
    """Main migration function"""
    print("=" * 60)
    print("Starting Data Migration: employee_name -> employee_id")
    print("=" * 60)

    # Load employees
    print("\nLoading employees...")
    employees = load_employees()
    print(f"  Found {len(employees)} employees")

    # Check for empty IDs
    empty_ids = [emp['name'] for emp in employees if not emp.get('id')]
    if empty_ids:
        print(f"\n  ERROR: The following employees have empty IDs:")
        for name in empty_ids:
            print(f"    - {name}")
        print("\n  Please assign IDs to all employees before running this migration.")
        return

    # Create name-to-ID mapping
    name_to_id_mapping = create_name_to_id_mapping(employees)
    print("\nEmployee Name -> ID Mapping:")
    for name, emp_id in name_to_id_mapping.items():
        print(f"  {name} -> {emp_id}")

    # Migrate each CSV file
    print("\n" + "=" * 60)
    print("Migrating CSV Files")
    print("=" * 60)

    migrate_csv_file(WFH_RECORDS_FILE, name_to_id_mapping, has_seminar_column=False)
    migrate_csv_file(ANNUAL_LEAVE_RECORDS_FILE, name_to_id_mapping, has_seminar_column=False)
    migrate_csv_file(SEMINAR_RECORDS_FILE, name_to_id_mapping, has_seminar_column=True)

    print("\n" + "=" * 60)
    print("Migration Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Verify the migrated data in the CSV files")
    print("2. Update app.py to use employee_id instead of employee_name")
    print("3. Test the application thoroughly")

if __name__ == "__main__":
    main()
