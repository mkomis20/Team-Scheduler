"""
Migration script to clean up leave_balances.csv and ensure consistency with employees.json
"""
import json
import pandas as pd
from pathlib import Path

# Define paths
DATA_DIR = Path("wfh_data")
EMPLOYEES_FILE = DATA_DIR / "employees.json"
LEAVE_BALANCES_FILE = DATA_DIR / "leave_balances.csv"

# Load employees
with open(EMPLOYEES_FILE, 'r') as f:
    employees = json.load(f)

# Get employee IDs from employees.json
employee_ids = set(emp['id'] for emp in employees)

# Create clean leave_balances.csv with only employees that exist in employees.json
clean_data = {
    'employee_id': [],
    'annual_leave_balance': []
}

# Try to load existing leave_balances.csv to preserve custom balances
existing_balances = {}
if LEAVE_BALANCES_FILE.exists():
    try:
        df = pd.read_csv(LEAVE_BALANCES_FILE)
        for _, row in df.iterrows():
            emp_id = str(row['employee_id']).strip()
            # Only keep if employee still exists
            if emp_id in employee_ids:
                existing_balances[emp_id] = int(row['annual_leave_balance'])
    except Exception as e:
        print(f"Error reading existing leave_balances.csv: {e}")

# Build clean leave_balances
for emp_id in sorted(employee_ids):
    clean_data['employee_id'].append(emp_id)
    clean_data['annual_leave_balance'].append(existing_balances.get(emp_id, 20))

# Save clean leave_balances.csv
df_clean = pd.DataFrame(clean_data)
df_clean.to_csv(LEAVE_BALANCES_FILE, index=False)

print("Migration complete!")
print(f"Cleaned leave_balances.csv with {len(clean_data['employee_id'])} employees")
print("\nFinal leave_balances.csv contents:")
print(df_clean)
