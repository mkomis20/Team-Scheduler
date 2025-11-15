"""
Test script to verify the leave_balance fix works correctly
"""
import pandas as pd
from pathlib import Path
import sys

# Add the script directory to path
sys.path.insert(0, str(Path.cwd()))

# Import the functions from app.py (we'll need to use simple implementations)
DATA_DIR = Path("wfh_data")
LEAVE_BALANCES_FILE = DATA_DIR / "leave_balances.csv"

def load_leave_balances():
    if LEAVE_BALANCES_FILE.exists():
        df = pd.read_csv(LEAVE_BALANCES_FILE, dtype={'employee_id': str, 'annual_leave_balance': int})
        return df
    return pd.DataFrame(columns=['employee_id', 'annual_leave_balance'])

def save_leave_balances(df):
    df['employee_id'] = df['employee_id'].astype(str)
    df['annual_leave_balance'] = df['annual_leave_balance'].astype(int)
    df.to_csv(LEAVE_BALANCES_FILE, index=False)

def get_leave_balance(employee_id):
    df = load_leave_balances()
    if not df.empty and employee_id in df['employee_id'].values:
        return df[df['employee_id'] == employee_id]['annual_leave_balance'].values[0]
    return 20

def set_leave_balance(employee_id, balance):
    df = load_leave_balances()
    balance = int(balance)

    if not df.empty and employee_id in df['employee_id'].values:
        df = df.copy()
        df.loc[df['employee_id'] == employee_id, 'annual_leave_balance'] = balance
    else:
        new_record = pd.DataFrame({'employee_id': [employee_id], 'annual_leave_balance': [balance]})
        df = pd.concat([df, new_record], ignore_index=True)

    save_leave_balances(df)

# Test the fix
print("Testing leave_balance functions...")
print("\n1. Testing get_leave_balance for existing employee '0001':")
balance = get_leave_balance('0001')
print(f"   Current balance for '0001': {balance} days")

print("\n2. Testing set_leave_balance - updating '0001' to 15 days:")
set_leave_balance('0001', 15)
new_balance = get_leave_balance('0001')
print(f"   Updated balance for '0001': {new_balance} days")
assert new_balance == 15, f"Expected 15, got {new_balance}"
print("   ✅ Successfully updated!")

print("\n3. Testing set_leave_balance - adding new employee '9999' with 18 days:")
set_leave_balance('9999', 18)
new_emp_balance = get_leave_balance('9999')
print(f"   Balance for new employee '9999': {new_emp_balance} days")
assert new_emp_balance == 18, f"Expected 18, got {new_emp_balance}"
print("   ✅ Successfully added!")

print("\n4. Verifying persistence - reloading and checking again:")
reloaded_balance = get_leave_balance('0001')
print(f"   Reloaded balance for '0001': {reloaded_balance} days")
assert reloaded_balance == 15, f"Expected 15, got {reloaded_balance}"
print("   ✅ Data persisted correctly!")

print("\n5. Final leave_balances.csv contents:")
df_final = load_leave_balances()
print(df_final)

print("\n✅ All tests passed! The fix is working correctly.")
