import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import hashlib

# Application version
APP_VERSION = "2.3.1 - Sunday 16/11/2025"

# Define all available screens
ALL_SCREENS = ["Dashboard", "Reports", "Schedule WFH", "Schedule Annual Leave", "Schedule Seminars", "Manage Employees", "Configure Roles", "Backup & Export"]

# Default role permissions (can be customized per user)
DEFAULT_ROLE_PERMISSIONS = {
    "Admin": ["Dashboard", "Reports", "Schedule WFH", "Schedule Annual Leave", "Schedule Seminars", "Manage Employees", "Configure Roles", "Backup & Export"],
    "User": ["Dashboard", "Schedule WFH", "Schedule Annual Leave", "Schedule Seminars"]
}

# Page configuration
st.set_page_config(page_title="Business Analytics Team Scheduler", layout="wide", page_icon="📊")

# Data file paths
DATA_DIR = Path("wfh_data")
DATA_DIR.mkdir(exist_ok=True)
EMPLOYEES_FILE = DATA_DIR / "employees.json"
WFH_RECORDS_FILE = DATA_DIR / "wfh_records.csv"
ANNUAL_LEAVE_RECORDS_FILE = DATA_DIR / "annual_leave_records.csv"
SEMINAR_RECORDS_FILE = DATA_DIR / "seminar_records.csv"
ROLE_PERMISSIONS_FILE = DATA_DIR / "role_permissions.json"
LEAVE_BALANCES_FILE = DATA_DIR / "leave_balances.csv"

# Load role permissions
def load_role_permissions():
    if ROLE_PERMISSIONS_FILE.exists():
        try:
            with open(ROLE_PERMISSIONS_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, ValueError) as e:
            import sys
            print(f"ERROR loading role_permissions.json: {e}", file=sys.stderr)
            return DEFAULT_ROLE_PERMISSIONS.copy()
    return DEFAULT_ROLE_PERMISSIONS.copy()

# Save role permissions
def save_role_permissions(permissions):
    # Write to a temporary file first, then rename (atomic operation)
    import tempfile
    temp_fd, temp_path = tempfile.mkstemp(dir=DATA_DIR, suffix='.json')
    try:
        with os.fdopen(temp_fd, 'w') as f:
            json.dump(permissions, f, indent=2)
        # Atomic rename
        os.replace(temp_path, ROLE_PERMISSIONS_FILE)
    except Exception as e:
        # Clean up temp file if write failed
        try:
            os.unlink(temp_path)
        except:
            pass
        raise e

# Load leave balances
def load_leave_balances():
    if LEAVE_BALANCES_FILE.exists():
        try:
            df = pd.read_csv(LEAVE_BALANCES_FILE, dtype={'employee_id': str, 'annual_leave_balance': int})
            return df
        except Exception as e:
            import sys
            print(f"ERROR load_leave_balances: {e}", file=sys.stderr)
            return pd.DataFrame(columns=['employee_id', 'annual_leave_balance'])
    return pd.DataFrame(columns=['employee_id', 'annual_leave_balance'])

# Save leave balances
def save_leave_balances(df):
    # Ensure correct data types before saving
    df['employee_id'] = df['employee_id'].astype(str)
    df['annual_leave_balance'] = df['annual_leave_balance'].astype(int)

    # Write to CSV
    df.to_csv(LEAVE_BALANCES_FILE, index=False)

    # Force OS to flush the file to disk (important on Windows)
    try:
        import time
        time.sleep(0.1)  # Brief pause before flushing
        import os
        if os.path.exists(LEAVE_BALANCES_FILE):
            # Open and close to ensure flush
            with open(LEAVE_BALANCES_FILE, 'r') as f:
                f.read(1)  # Read a byte to trigger buffer flush
    except Exception:
        pass  # Non-critical, continue anyway

# Get leave balance for an employee
def get_leave_balance(employee_id):
    employee_id = str(employee_id).strip()
    df = load_leave_balances()
    if not df.empty:
        # Convert all IDs to string and strip whitespace for comparison
        df_ids_clean = df['employee_id'].astype(str).str.strip()
        if employee_id in df_ids_clean.values:
            return int(df[df_ids_clean == employee_id]['annual_leave_balance'].values[0])
    return 20  # Default balance

# Set leave balance for an employee
def set_leave_balance(employee_id, balance):
    try:
        # Ensure employee_id is always a string
        employee_id = str(employee_id).strip()
        balance = int(balance)

        df = load_leave_balances()

        # Check if employee exists using case-insensitive and whitespace-tolerant comparison
        employee_exists = False
        if not df.empty:
            # Convert all IDs to string and strip whitespace for comparison
            df_ids_clean = df['employee_id'].astype(str).str.strip()
            employee_exists = employee_id in df_ids_clean.values

        if employee_exists:
            # Use a copy to avoid SettingWithCopyWarning
            df = df.copy()
            # Update using the cleaned employee_id
            df.loc[df['employee_id'].astype(str).str.strip() == employee_id, 'annual_leave_balance'] = balance
        else:
            # Add new record
            new_record = pd.DataFrame({'employee_id': [employee_id], 'annual_leave_balance': [balance]})
            df = pd.concat([df, new_record], ignore_index=True)

        save_leave_balances(df)
        return True
    except Exception as e:
        import sys
        print(f"ERROR in set_leave_balance: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return False

# Initialize data files
def init_data_files():
    if not EMPLOYEES_FILE.exists():
        with open(EMPLOYEES_FILE, 'w') as f:
            json.dump([], f)

    if not WFH_RECORDS_FILE.exists():
        df = pd.DataFrame(columns=['employee_id', 'date', 'status'])
        df.to_csv(WFH_RECORDS_FILE, index=False)

    if not ANNUAL_LEAVE_RECORDS_FILE.exists():
        df = pd.DataFrame(columns=['employee_id', 'date', 'status'])
        df.to_csv(ANNUAL_LEAVE_RECORDS_FILE, index=False)

    if not SEMINAR_RECORDS_FILE.exists():
        df = pd.DataFrame(columns=['employee_id', 'date', 'status', 'seminar_name'])
        df.to_csv(SEMINAR_RECORDS_FILE, index=False)

    if not ROLE_PERMISSIONS_FILE.exists():
        save_role_permissions(DEFAULT_ROLE_PERMISSIONS.copy())

    if not LEAVE_BALANCES_FILE.exists():
        save_leave_balances(pd.DataFrame(columns=['employee_id', 'annual_leave_balance']))

# Hash password
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Load employees
def load_employees():
    try:
        with open(EMPLOYEES_FILE, 'r') as f:
            employees = json.load(f)
    except (json.JSONDecodeError, ValueError) as e:
        import sys
        print(f"ERROR loading employees.json: {e}", file=sys.stderr)
        # Return empty list if file is corrupted
        employees = []
        # Handle legacy format (list of strings)
        if employees and isinstance(employees[0], str):
            employees = [{'name': emp, 'id': '', 'annual_leave_balance': 20, 'password': hash_password('1234'), 'role': 'User'} for emp in employees]
            save_employees(employees)
        # Handle format without annual leave balance
        elif employees and 'annual_leave_balance' not in employees[0]:
            for emp in employees:
                emp['annual_leave_balance'] = 20
            save_employees(employees)
        # Handle format without password and role
        if employees:
            needs_save = False
            leave_balances_to_migrate = []
            for emp in employees:
                if 'password' not in emp:
                    emp['password'] = hash_password('1234')  # Default password
                    needs_save = True
                if 'role' not in emp:
                    # Set Marios Komis as admin, others as users
                    emp['role'] = 'Admin' if emp['name'] == 'Marios Komis' else 'User'
                    needs_save = True
                # Handle format without screen_permissions
                if 'screen_permissions' not in emp:
                    role = emp.get('role', 'User')
                    role_permissions = load_role_permissions()
                    emp['screen_permissions'] = role_permissions.get(role, [])
                    needs_save = True
                # Migrate annual_leave_balance to CSV file
                if 'annual_leave_balance' in emp:
                    leave_balances_to_migrate.append({
                        'employee_id': emp['id'],
                        'annual_leave_balance': emp['annual_leave_balance']
                    })
                    del emp['annual_leave_balance']  # Remove from JSON
                    needs_save = True

            # Save migrated leave balances to CSV
            if leave_balances_to_migrate:
                df_existing = load_leave_balances()
                df_new = pd.DataFrame(leave_balances_to_migrate)
                # IMPORTANT: Only add new records that don't already exist in CSV
                # Don't overwrite existing CSV values with old JSON values
                # This prevents the migration from overwriting updated balances
                for _, new_row in df_new.iterrows():
                    emp_id = new_row['employee_id']
                    # Only add if employee_id doesn't already exist in CSV
                    if emp_id not in df_existing['employee_id'].values:
                        df_existing = pd.concat([df_existing, pd.DataFrame([new_row])], ignore_index=True)
                save_leave_balances(df_existing)

            if needs_save:
                save_employees(employees)
        return employees

# Save employees
def save_employees(employees):
    # Write to a temporary file first, then rename (atomic operation)
    import tempfile
    temp_fd, temp_path = tempfile.mkstemp(dir=DATA_DIR, suffix='.json')
    try:
        with os.fdopen(temp_fd, 'w') as f:
            json.dump(employees, f, indent=2)
        # Atomic rename
        os.replace(temp_path, EMPLOYEES_FILE)
    except Exception as e:
        # Clean up temp file if write failed
        try:
            os.unlink(temp_path)
        except:
            pass
        raise e

# Helper function to get employee ID from name
def get_employee_id_by_name(employee_name):
    employees = load_employees()
    emp = next((e for e in employees if e['name'] == employee_name), None)
    return emp['id'] if emp else None

# Helper function to get employee name from ID
def get_employee_name_by_id(employee_id):
    employees = load_employees()
    emp = next((e for e in employees if e['id'] == employee_id), None)
    return emp['name'] if emp else f"Unknown ({employee_id})"

# Helper function to get allowed screens for a user
def get_allowed_screens(employee_name):
    employees = load_employees()
    emp = next((e for e in employees if e['name'] == employee_name), None)
    if emp:
        # If employee has custom screen permissions, use those
        if 'screen_permissions' in emp:
            return emp['screen_permissions']
        # Otherwise use default permissions based on role
        role = emp.get('role', 'User')
        role_permissions = load_role_permissions()
        return role_permissions.get(role, [])
    return []

# Helper function to check if a user can manage another user's records
def can_manage_user(current_user_name, target_user_name):
    """
    Check if the current user can manage records for the target user.
    - Admins can manage all users
    - Regular users can only manage their own records
    """
    employees = load_employees()
    current_user = next((e for e in employees if e['name'] == current_user_name), None)

    if not current_user:
        return False

    # Admins can manage anyone
    if current_user.get('role') == 'Admin':
        return True

    # Users can only manage themselves
    return current_user_name == target_user_name

# Load WFH records
def load_wfh_records():
    df = pd.read_csv(WFH_RECORDS_FILE, dtype={'employee_id': str})
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
    return df

# Save WFH records
def save_wfh_records(df):
    df.to_csv(WFH_RECORDS_FILE, index=False)

# Add WFH record
def add_wfh_record(employee_id, date, status='WFH'):
    df = load_wfh_records()

    # Remove existing record for same employee and date
    df = df[~((df['employee_id'] == employee_id) & (df['date'] == pd.to_datetime(date)))]

    # Add new record
    new_record = pd.DataFrame({
        'employee_id': [employee_id],
        'date': [pd.to_datetime(date)],
        'status': [status]
    })
    df = pd.concat([df, new_record], ignore_index=True)
    save_wfh_records(df)

# Remove WFH record
def remove_wfh_record(employee_id, date):
    df = load_wfh_records()
    df = df[~((df['employee_id'] == employee_id) & (df['date'] == pd.to_datetime(date)))]
    save_wfh_records(df)

# Load Annual Leave records
def load_annual_leave_records():
    df = pd.read_csv(ANNUAL_LEAVE_RECORDS_FILE, dtype={'employee_id': str})
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
    return df

# Save Annual Leave records
def save_annual_leave_records(df):
    df.to_csv(ANNUAL_LEAVE_RECORDS_FILE, index=False)

# Add Annual Leave record
def add_annual_leave_record(employee_id, date, status='Annual Leave'):
    df = load_annual_leave_records()

    # Remove existing record for same employee and date
    df = df[~((df['employee_id'] == employee_id) & (df['date'] == pd.to_datetime(date)))]

    # Add new record
    new_record = pd.DataFrame({
        'employee_id': [employee_id],
        'date': [pd.to_datetime(date)],
        'status': [status]
    })
    df = pd.concat([df, new_record], ignore_index=True)
    save_annual_leave_records(df)

# Remove Annual Leave record
def remove_annual_leave_record(employee_id, date):
    df = load_annual_leave_records()
    df = df[~((df['employee_id'] == employee_id) & (df['date'] == pd.to_datetime(date)))]
    save_annual_leave_records(df)

# Get Annual Leave count per employee
def get_annual_leave_counts():
    df = load_annual_leave_records()
    employees = load_employees()
    employee_ids = [emp['id'] for emp in employees]
    employee_names = [emp['name'] for emp in employees]

    if df.empty:
        return pd.DataFrame({'employee_id': employee_ids, 'employee_name': employee_names, 'al_days': [0] * len(employee_ids)})

    counts = df.groupby('employee_id').size().reset_index(name='al_days')

    # Add employees with 0 AL days
    all_employees = pd.DataFrame({'employee_id': employee_ids, 'employee_name': employee_names})
    counts = all_employees.merge(counts, on='employee_id', how='left').fillna(0)
    counts['al_days'] = counts['al_days'].astype(int)

    return counts

# Load Seminar records
def load_seminar_records():
    df = pd.read_csv(SEMINAR_RECORDS_FILE, dtype={'employee_id': str})
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
    return df

# Save Seminar records
def save_seminar_records(df):
    df.to_csv(SEMINAR_RECORDS_FILE, index=False)

# Add Seminar record
def add_seminar_record(employee_id, date, seminar_name, status='Seminar'):
    df = load_seminar_records()

    # Remove existing record for same employee and date
    df = df[~((df['employee_id'] == employee_id) & (df['date'] == pd.to_datetime(date)))]

    # Add new record
    new_record = pd.DataFrame({
        'employee_id': [employee_id],
        'date': [pd.to_datetime(date)],
        'status': [status],
        'seminar_name': [seminar_name]
    })
    df = pd.concat([df, new_record], ignore_index=True)
    save_seminar_records(df)

# Remove Seminar record
def remove_seminar_record(employee_id, date):
    df = load_seminar_records()
    df = df[~((df['employee_id'] == employee_id) & (df['date'] == pd.to_datetime(date)))]
    save_seminar_records(df)

# Get Seminar count per employee
def get_seminar_counts():
    df = load_seminar_records()
    employees = load_employees()
    employee_ids = [emp['id'] for emp in employees]
    employee_names = [emp['name'] for emp in employees]

    if df.empty:
        return pd.DataFrame({'employee_id': employee_ids, 'employee_name': employee_names, 'seminar_days': [0] * len(employee_ids)})

    counts = df.groupby('employee_id').size().reset_index(name='seminar_days')

    # Add employees with 0 Seminar days
    all_employees = pd.DataFrame({'employee_id': employee_ids, 'employee_name': employee_names})
    counts = all_employees.merge(counts, on='employee_id', how='left').fillna(0)
    counts['seminar_days'] = counts['seminar_days'].astype(int)

    return counts

# Check if employee has existing entry for a specific date
def check_existing_entry(employee_id, date):
    """
    Check if an employee already has an entry (WFH, Annual Leave, or Seminar) for a given date.
    Returns: tuple (has_entry: bool, entry_type: str or None, details: str or None)
    """
    date_pd = pd.to_datetime(date)

    # Check WFH records
    df_wfh = load_wfh_records()
    if not df_wfh.empty:
        wfh_match = df_wfh[(df_wfh['employee_id'] == employee_id) & (df_wfh['date'] == date_pd)]
        if not wfh_match.empty:
            return (True, 'WFH', 'Work From Home')

    # Check Annual Leave records
    df_al = load_annual_leave_records()
    if not df_al.empty:
        al_match = df_al[(df_al['employee_id'] == employee_id) & (df_al['date'] == date_pd)]
        if not al_match.empty:
            return (True, 'Annual Leave', 'Annual Leave')

    # Check Seminar records
    df_seminar = load_seminar_records()
    if not df_seminar.empty:
        seminar_match = df_seminar[(df_seminar['employee_id'] == employee_id) & (df_seminar['date'] == date_pd)]
        if not seminar_match.empty:
            seminar_name = seminar_match.iloc[0]['seminar_name']
            return (True, 'Seminar', f'Seminar: {seminar_name}')

    return (False, None, None)

# Get WFH count per employee
def get_wfh_counts():
    df = load_wfh_records()
    employees = load_employees()
    employee_ids = [emp['id'] for emp in employees]
    employee_names = [emp['name'] for emp in employees]

    if df.empty:
        return pd.DataFrame({'employee_id': employee_ids, 'employee_name': employee_names, 'wfh_days': [0] * len(employee_ids)})

    counts = df.groupby('employee_id').size().reset_index(name='wfh_days')

    # Add employees with 0 WFH days
    all_employees = pd.DataFrame({'employee_id': employee_ids, 'employee_name': employee_names})
    counts = all_employees.merge(counts, on='employee_id', how='left').fillna(0)
    counts['wfh_days'] = counts['wfh_days'].astype(int)

    return counts

# Get office occupancy for date range
def get_office_occupancy(start_date, end_date):
    df_wfh = load_wfh_records()
    df_al = load_annual_leave_records()
    df_seminar = load_seminar_records()
    employees = load_employees()
    total_employees = len(employees)

    if total_employees == 0:
        return pd.DataFrame()

    # Filter by date range
    if not df_wfh.empty:
        df_wfh = df_wfh[(df_wfh['date'] >= pd.to_datetime(start_date)) & (df_wfh['date'] <= pd.to_datetime(end_date))]

    if not df_al.empty:
        df_al = df_al[(df_al['date'] >= pd.to_datetime(start_date)) & (df_al['date'] <= pd.to_datetime(end_date))]

    if not df_seminar.empty:
        df_seminar = df_seminar[(df_seminar['date'] >= pd.to_datetime(start_date)) & (df_seminar['date'] <= pd.to_datetime(end_date))]

    # Count WFH per day
    daily_wfh = df_wfh.groupby('date').size().reset_index(name='wfh_count') if not df_wfh.empty else pd.DataFrame(columns=['date', 'wfh_count'])

    # Count Annual Leave per day
    daily_al = df_al.groupby('date').size().reset_index(name='al_count') if not df_al.empty else pd.DataFrame(columns=['date', 'al_count'])

    # Count Seminar per day
    daily_seminar = df_seminar.groupby('date').size().reset_index(name='seminar_count') if not df_seminar.empty else pd.DataFrame(columns=['date', 'seminar_count'])

    # Merge all counts
    all_dfs = [daily_wfh, daily_al, daily_seminar]
    non_empty_dfs = [df for df in all_dfs if not df.empty]

    if not non_empty_dfs:
        return pd.DataFrame()

    daily_combined = non_empty_dfs[0]
    for df in non_empty_dfs[1:]:
        daily_combined = pd.merge(daily_combined, df, on='date', how='outer')

    daily_combined = daily_combined.fillna(0)

    # Ensure all columns exist
    if 'wfh_count' not in daily_combined.columns:
        daily_combined['wfh_count'] = 0
    if 'al_count' not in daily_combined.columns:
        daily_combined['al_count'] = 0
    if 'seminar_count' not in daily_combined.columns:
        daily_combined['seminar_count'] = 0

    daily_combined['wfh_count'] = daily_combined['wfh_count'].astype(int)
    daily_combined['al_count'] = daily_combined['al_count'].astype(int)
    daily_combined['seminar_count'] = daily_combined['seminar_count'].astype(int)
    daily_combined['out_of_office'] = daily_combined['wfh_count'] + daily_combined['al_count'] + daily_combined['seminar_count']
    daily_combined['in_office'] = total_employees - daily_combined['out_of_office']
    daily_combined['wfh_percentage'] = (daily_combined['wfh_count'] / total_employees * 100).round(1)
    daily_combined['al_percentage'] = (daily_combined['al_count'] / total_employees * 100).round(1)
    daily_combined['seminar_percentage'] = (daily_combined['seminar_count'] / total_employees * 100).round(1)

    return daily_combined

# Initialize
init_data_files()

# Initialize session state for authentication
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_name' not in st.session_state:
    st.session_state.user_name = None
if 'user_role' not in st.session_state:
    st.session_state.user_role = None

# Login screen
if not st.session_state.logged_in:
    st.title("🔐 Login")
    st.markdown("---")

    employees = load_employees()

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.subheader("Please log in to continue")

        # Create dropdown with employee names
        employee_names = [emp['name'] for emp in employees]
        selected_name = st.selectbox("Select your name", employee_names)

        password = st.text_input("Password", type="password")

        if st.button("Login", type="primary", use_container_width=True):
            # Find the employee
            user = next((emp for emp in employees if emp['name'] == selected_name), None)

            if user:
                # Check password
                if user['password'] == hash_password(password):
                    st.session_state.logged_in = True
                    st.session_state.user_name = user['name']
                    st.session_state.user_role = user['role']
                    st.success(f"Welcome, {user['name']}!")
                    st.rerun()
                else:
                    st.error("❌ Incorrect password")
            else:
                st.error("❌ User not found")

    st.stop()

# User is logged in - show the application
# Title will be set dynamically based on the page

# Sidebar
with st.sidebar:
    # Display logged in user info
    st.markdown(f"👤 **Logged in as:** {st.session_state.user_name}")
    st.markdown(f"🔑 **Role:** {st.session_state.user_role}")

    # Change Password button
    if st.button("🔒 Change Password", use_container_width=True):
        st.session_state.show_change_password = True

    # Logout button
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user_name = None
        st.session_state.user_role = None
        st.rerun()

    st.markdown("---")

    st.header("📋 Navigation")

    # Get allowed screens for the logged-in user
    allowed_screens = get_allowed_screens(st.session_state.user_name)

    if not allowed_screens:
        st.error("❌ No screens assigned to your role. Contact admin.")
        st.stop()

    page = st.radio("Menu", allowed_screens)

    # Show info if user doesn't have all screens
    if len(allowed_screens) < len(ALL_SCREENS):
        st.info("ℹ️ Contact admin to request additional screen access")

    st.markdown("---")
    st.markdown("### Quick Stats")
    employees = load_employees()
    st.metric("Total Employees", len(employees))

    df_records = load_wfh_records()
    if not df_records.empty:
        future_wfh = df_records[df_records['date'] >= pd.to_datetime(datetime.now().date())]
        st.metric("Upcoming WFH Days", len(future_wfh))

    # Display version at the bottom of sidebar
    st.markdown("---")
    st.markdown(f"<div style='text-align: center; color: gray; font-size: 0.8em;'>v{APP_VERSION}</div>", unsafe_allow_html=True)

# Change Password Dialog
if 'show_change_password' not in st.session_state:
    st.session_state.show_change_password = False

if st.session_state.show_change_password:
    st.header("🔒 Change Password")
    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.subheader(f"Change password for: {st.session_state.user_name}")

        current_password = st.text_input("Current Password", type="password", key="current_pwd")
        new_password = st.text_input("New Password", type="password", key="new_pwd")
        confirm_password = st.text_input("Confirm New Password", type="password", key="confirm_pwd")

        col_a, col_b = st.columns(2)

        with col_a:
            if st.button("💾 Update Password", type="primary", use_container_width=True):
                if not current_password or not new_password or not confirm_password:
                    st.error("❌ Please fill in all fields")
                elif new_password != confirm_password:
                    st.error("❌ New passwords do not match")
                elif len(new_password) < 4:
                    st.error("❌ Password must be at least 4 characters")
                else:
                    # Load employees and verify current password
                    employees = load_employees()
                    user = next((emp for emp in employees if emp['name'] == st.session_state.user_name), None)

                    if user and user['password'] == hash_password(current_password):
                        # Update password
                        user['password'] = hash_password(new_password)
                        save_employees(employees)
                        st.success("✅ Password updated successfully!")
                        st.session_state.show_change_password = False
                        st.rerun()
                    else:
                        st.error("❌ Current password is incorrect")

        with col_b:
            if st.button("Cancel", use_container_width=True):
                st.session_state.show_change_password = False
                st.rerun()

    st.stop()

# DASHBOARD PAGE
if page == "Dashboard":
    st.title("📊 Business Analytics Team Scheduler - Dashboard")
    st.markdown("---")

    if not employees:
        st.warning("⚠️ No employees added yet. Go to 'Manage Employees' to add team members.")
    else:
        today = datetime.now().date()

        # Initialize calendar month offset in session state
        if 'calendar_month_offset' not in st.session_state:
            st.session_state.calendar_month_offset = 0

        # Initialize occupancy month offset in session state
        if 'occupancy_month_offset' not in st.session_state:
            st.session_state.occupancy_month_offset = 0

        # WFH, AL & Seminar Schedule - Calendar View
        col_title, col_nav = st.columns([3, 1])
        with col_title:
            st.subheader("📅 WFH, AL & Seminar Schedule")
        with col_nav:
            col_left, col_center, col_right = st.columns([1, 2, 1])
            with col_left:
                if st.button("◀", key="cal_prev", help="Previous month"):
                    st.session_state.calendar_month_offset -= 1
                    st.rerun()
            with col_center:
                # Calculate the viewing month based on offset
                viewing_date = today + timedelta(days=30 * st.session_state.calendar_month_offset)
                st.markdown(f"**{viewing_date.strftime('%B %Y')}**")
            with col_right:
                if st.button("▶", key="cal_next", help="Next month"):
                    st.session_state.calendar_month_offset += 1
                    st.rerun()

        # Load WFH, Annual Leave, and Seminar records
        df_al_records = load_annual_leave_records()
        df_seminar_records = load_seminar_records()

        if not df_records.empty or not df_al_records.empty or not df_seminar_records.empty:
            # Calculate the start of the viewing month
            viewing_date = today + timedelta(days=30 * st.session_state.calendar_month_offset)
            start_of_month = viewing_date.replace(day=1)

            # Calculate first Monday to show (may be in previous month)
            start_of_week = start_of_month - timedelta(days=start_of_month.weekday())

            # Show 5 weeks
            calendar_end = start_of_week + timedelta(days=35)

            # Group WFH employees by date (convert IDs to names for display)
            if not df_records.empty:
                df_records_display = df_records.copy()
                df_records_display['employee_name'] = df_records_display['employee_id'].apply(get_employee_name_by_id)
                wfh_by_date = df_records_display.groupby('date')['employee_name'].apply(list).to_dict()
            else:
                wfh_by_date = {}

            # Group Annual Leave employees by date (convert IDs to names for display)
            if not df_al_records.empty:
                df_al_display = df_al_records.copy()
                df_al_display['employee_name'] = df_al_display['employee_id'].apply(get_employee_name_by_id)
                al_by_date = df_al_display.groupby('date')['employee_name'].apply(list).to_dict()
            else:
                al_by_date = {}

            # Group Seminar employees by date (with seminar names, convert IDs to names for display)
            if not df_seminar_records.empty:
                df_seminar_display = df_seminar_records.copy()
                df_seminar_display['employee_name'] = df_seminar_display['employee_id'].apply(get_employee_name_by_id)
                seminar_by_date = df_seminar_display.groupby('date').apply(
                    lambda x: list(zip(x['employee_name'], x['seminar_name']))
                ).to_dict()
            else:
                seminar_by_date = {}

            # Create HTML calendar
            calendar_html = """
            <style>
            .calendar-grid {
                display: grid;
                grid-template-columns: repeat(7, 1fr);
                gap: 5px;
                margin: 10px 0;
            }
            .calendar-day {
                border: 1px solid #ddd;
                padding: 8px;
                min-height: 80px;
                background-color: #f9f9f9;
                border-radius: 4px;
            }
            .calendar-day-header {
                font-weight: bold;
                font-size: 12px;
                color: #555;
                margin-bottom: 4px;
            }
            .calendar-day-past {
                background-color: #e8e8e8;
            }
            .calendar-day-weekend {
                background-color: #f0f0f0;
            }
            .wfh-employee {
                font-size: 11px;
                background-color: #4CAF50;
                color: white;
                padding: 2px 4px;
                margin: 2px 0;
                border-radius: 3px;
                display: block;
            }
            .wfh-employee-past {
                font-size: 11px;
                background-color: #888;
                color: white;
                padding: 2px 4px;
                margin: 2px 0;
                border-radius: 3px;
                display: block;
            }
            .al-employee {
                font-size: 11px;
                background-color: #f44336;
                color: white;
                padding: 2px 4px;
                margin: 2px 0;
                border-radius: 3px;
                display: block;
            }
            .al-employee-past {
                font-size: 11px;
                background-color: #c62828;
                color: white;
                padding: 2px 4px;
                margin: 2px 0;
                border-radius: 3px;
                display: block;
            }
            .seminar-employee {
                font-size: 11px;
                background-color: #2196F3;
                color: white;
                padding: 2px 4px;
                margin: 2px 0;
                border-radius: 3px;
                display: block;
            }
            .seminar-employee-past {
                font-size: 11px;
                background-color: #1565C0;
                color: white;
                padding: 2px 4px;
                margin: 2px 0;
                border-radius: 3px;
                display: block;
            }
            .day-header {
                background-color: #333;
                color: white;
                padding: 8px;
                text-align: center;
                font-weight: bold;
                font-size: 12px;
            }
            </style>
            <div class="calendar-grid">
                <div class="day-header">Mon</div>
                <div class="day-header">Tue</div>
                <div class="day-header">Wed</div>
                <div class="day-header">Thu</div>
                <div class="day-header">Fri</div>
                <div class="day-header">Sat</div>
                <div class="day-header">Sun</div>
            """

            # Generate 5 weeks
            current_date = start_of_week
            for week in range(5):
                for day in range(7):
                    date_to_show = current_date + timedelta(days=week * 7 + day)
                    is_past = date_to_show < today
                    is_weekend = date_to_show.weekday() >= 5

                    day_class = "calendar-day"
                    if is_past:
                        day_class += " calendar-day-past"
                    elif is_weekend:
                        day_class += " calendar-day-weekend"

                    calendar_html += f'<div class="{day_class}">'
                    calendar_html += f'<div class="calendar-day-header">{date_to_show.strftime("%b %d")}</div>'

                    # Add WFH employees for this date (show both past and future)
                    date_key = pd.to_datetime(date_to_show)
                    if date_key in wfh_by_date:
                        emp_class = "wfh-employee-past" if is_past else "wfh-employee"
                        for emp in wfh_by_date[date_key]:
                            calendar_html += f'<span class="{emp_class}">WFH: {emp}</span>'

                    # Add Annual Leave employees for this date
                    if date_key in al_by_date:
                        al_class = "al-employee-past" if is_past else "al-employee"
                        for emp in al_by_date[date_key]:
                            calendar_html += f'<span class="{al_class}">AL: {emp}</span>'

                    # Add Seminar employees for this date
                    if date_key in seminar_by_date:
                        seminar_class = "seminar-employee-past" if is_past else "seminar-employee"
                        for emp, seminar_name in seminar_by_date[date_key]:
                            calendar_html += f'<span class="{seminar_class}">S: {emp}</span>'

                    calendar_html += '</div>'

            calendar_html += '</div>'

            st.markdown(calendar_html, unsafe_allow_html=True)
        else:
            st.info("No WFH, Annual Leave, or Seminar days scheduled")

        # Charts section
        st.markdown("---")

        # Office Occupancy with scrolling
        col_occ_title, col_occ_nav = st.columns([3, 1])
        with col_occ_title:
            st.subheader("Office Occupancy")
        with col_occ_nav:
            col_occ_left, col_occ_center, col_occ_right = st.columns([1, 2, 1])
            with col_occ_left:
                if st.button("◀", key="occ_prev", help="Previous month"):
                    st.session_state.occupancy_month_offset -= 1
                    st.rerun()
            with col_occ_center:
                # Calculate the viewing month based on offset
                occ_viewing_date = today + timedelta(days=30 * st.session_state.occupancy_month_offset)
                st.markdown(f"**{occ_viewing_date.strftime('%B %Y')}**")
            with col_occ_right:
                if st.button("▶", key="occ_next", help="Next month"):
                    st.session_state.occupancy_month_offset += 1
                    st.rerun()

        # Calculate date range for occupancy (30 days from offset month)
        occ_viewing_date = today + timedelta(days=30 * st.session_state.occupancy_month_offset)
        occ_start_date = occ_viewing_date
        occ_end_date = occ_start_date + timedelta(days=29)
        occupancy = get_office_occupancy(occ_start_date, occ_end_date)

        if not occupancy.empty:
            # Create stacked area chart
            fig = go.Figure()

            # Add traces in order for stacking
            fig.add_trace(go.Scatter(
                x=occupancy['date'],
                y=occupancy['in_office'],
                mode='lines',
                name='In Office',
                line=dict(color='green', width=0),
                fillcolor='rgba(76, 175, 80, 0.5)',
                fill='tozeroy',
                stackgroup='one'
            ))
            fig.add_trace(go.Scatter(
                x=occupancy['date'],
                y=occupancy['wfh_count'],
                mode='lines',
                name='Working from Home',
                line=dict(color='orange', width=0),
                fillcolor='rgba(255, 152, 0, 0.5)',
                fill='tonexty',
                stackgroup='one'
            ))
            fig.add_trace(go.Scatter(
                x=occupancy['date'],
                y=occupancy['al_count'],
                mode='lines',
                name='Annual Leave',
                line=dict(color='red', width=0),
                fillcolor='rgba(244, 67, 54, 0.5)',
                fill='tonexty',
                stackgroup='one'
            ))
            fig.add_trace(go.Scatter(
                x=occupancy['date'],
                y=occupancy['seminar_count'],
                mode='lines',
                name='Seminar',
                line=dict(color='blue', width=0),
                fillcolor='rgba(33, 150, 243, 0.5)',
                fill='tonexty',
                stackgroup='one'
            ))

            fig.update_layout(
                title='Daily Office vs WFH vs Annual Leave vs Seminar',
                xaxis_title='Date',
                yaxis_title='Number of Employees',
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)

            # Show alerts
            low_occupancy = occupancy[occupancy['in_office'] < len(employees) * 0.3]
            if not low_occupancy.empty:
                st.warning(f"⚠️ **Low office occupancy alert:** {len(low_occupancy)} day(s) with less than 30% in office")
        else:
            st.info(f"No WFH, Annual Leave, or Seminar days scheduled in {occ_viewing_date.strftime('%B %Y')}")

# SCHEDULE WFH PAGE
elif page == "Schedule WFH":
    st.title("📊 Business Analytics Team Scheduler - Schedule WFH")
    st.markdown("---")

    if not employees:
        st.warning("⚠️ No employees added yet. Go to 'Manage Employees' to add team members.")
    else:
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("Add WFH Day(s)")

            # Get current user role
            current_user_role = st.session_state.user_role

            # If user is not admin, filter employees to only show themselves
            if current_user_role != "Admin":
                # Regular users can only manage their own WFH
                filterable_employees = [emp for emp in employees if emp['name'] == st.session_state.user_name]
                if not filterable_employees:
                    st.error("❌ Your account is not found in the employee list.")
                    st.stop()
            else:
                # Admins can see all employees
                filterable_employees = employees

            employee_options = [f"{emp['name']} (ID: {emp['id']})" for emp in filterable_employees]
            selected_employee_display = st.selectbox("Select Employee", employee_options)
            # Extract employee name and ID from display string
            selected_employee_name = selected_employee_display.split(" (ID:")[0]
            selected_employee_id = selected_employee_display.split("ID: ")[1].rstrip(")")

            # Date range or single date selection
            date_mode = st.radio("Select date mode:", ["Single Date", "Date Range"], horizontal=True)

            if date_mode == "Single Date":
                selected_date = st.date_input("Select Date", value=datetime.now().date())
                date_range = [selected_date]
            else:
                st.write("Select start and end dates:")
                col_date1, col_date2 = st.columns(2)
                with col_date1:
                    start_date = st.date_input("Start Date", value=datetime.now().date(), key="wfh_start")
                with col_date2:
                    end_date = st.date_input("End Date", value=datetime.now().date(), key="wfh_end")

                if start_date > end_date:
                    st.error("❌ Start date must be before or equal to end date")
                    date_range = []
                else:
                    # Generate date range
                    date_range = pd.date_range(start=start_date, end=end_date).date.tolist()
                    st.info(f"📅 Selected {len(date_range)} day(s)")

            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("➕ Add WFH Day(s)", type="primary", use_container_width=True):
                    if date_range:
                        # Check for conflicts
                        conflicts = []
                        for date in date_range:
                            has_entry, entry_type, details = check_existing_entry(selected_employee_id, date)
                            if has_entry and entry_type != 'WFH':
                                conflicts.append((date, entry_type, details))

                        if conflicts:
                            st.error(f"❌ Cannot add WFH day(s). {selected_employee_name} already has the following conflicting entries:")
                            for conf_date, conf_type, conf_details in conflicts:
                                st.warning(f"📅 {conf_date}: **{conf_details}**")
                            st.info("ℹ️ Please remove the existing entry first, then add the new WFH day.")
                        else:
                            for date in date_range:
                                add_wfh_record(selected_employee_id, date)
                            if len(date_range) == 1:
                                st.success(f"✅ WFH day added for {selected_employee_name} on {date_range[0]}")
                            else:
                                st.success(f"✅ {len(date_range)} WFH days added for {selected_employee_name}")
                            st.rerun()

            with col_b:
                if st.button("🗑️ Remove WFH Day(s)", use_container_width=True):
                    if date_range:
                        for date in date_range:
                            remove_wfh_record(selected_employee_id, date)
                        if len(date_range) == 1:
                            st.success(f"✅ WFH day removed for {selected_employee_name} on {date_range[0]}")
                        else:
                            st.success(f"✅ {len(date_range)} WFH days removed for {selected_employee_name}")
                        st.rerun()
        
        with col2:
            st.subheader("Quick Stats")
            counts_df = get_wfh_counts()
            employee_count = counts_df[counts_df['employee_id'] == selected_employee_id]['wfh_days'].values

            if len(employee_count) > 0:
                st.metric(f"{selected_employee_name}'s WFH Days", int(employee_count[0]))
        
        st.markdown("---")

        # Calendar view
        st.subheader("📆 WFH Calendar View")

        view_month = st.date_input("Select Month to View", datetime.now().date(), key="month_view")
        start_of_month = view_month.replace(day=1)
        if view_month.month == 12:
            end_of_month = start_of_month.replace(year=view_month.year + 1, month=1) - timedelta(days=1)
        else:
            end_of_month = start_of_month.replace(month=view_month.month + 1) - timedelta(days=1)

        month_records = load_wfh_records()
        if not month_records.empty:
            month_records = month_records[
                (month_records['date'] >= pd.to_datetime(start_of_month)) &
                (month_records['date'] <= pd.to_datetime(end_of_month))
            ]

            if not month_records.empty:
                calendar_df = month_records.copy()
                calendar_df['Employee'] = calendar_df['employee_id'].apply(get_employee_name_by_id)
                calendar_df = calendar_df.sort_values('date')
                calendar_df['Date'] = calendar_df['date'].dt.strftime('%Y-%m-%d')
                calendar_df = calendar_df[['Employee', 'Date', 'status']].rename(columns={'status': 'Status'})

                # Show count
                st.info(f"📋 Showing {len(calendar_df)} WFH record(s) for {view_month.strftime('%B %Y')}")
                st.dataframe(calendar_df, use_container_width=True, hide_index=True)
            else:
                st.info(f"No WFH days recorded for {view_month.strftime('%B %Y')}")
        else:
            st.info("No WFH days scheduled")

# ANNUAL LEAVE PAGE
elif page == "Schedule Annual Leave":
    st.title("📊 Business Analytics Team Scheduler - Annual Leave")
    st.markdown("---")

    if not employees:
        st.warning("⚠️ No employees added yet. Go to 'Manage Employees' to add team members.")
    else:
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("Schedule Annual Leave")

            # Get current user role
            current_user_role = st.session_state.user_role

            # If user is not admin, filter employees to only show themselves
            if current_user_role != "Admin":
                # Regular users can only manage their own Annual Leave
                filterable_employees = [emp for emp in employees if emp['name'] == st.session_state.user_name]
                if not filterable_employees:
                    st.error("❌ Your account is not found in the employee list.")
                    st.stop()
            else:
                # Admins can see all employees
                filterable_employees = employees

            employee_options = [f"{emp['name']} (ID: {emp['id']})" for emp in filterable_employees]
            selected_employee_display = st.selectbox("Select Employee", employee_options, key="al_employee")
            # Extract employee name and ID from display string
            selected_employee_name = selected_employee_display.split(" (ID:")[0]
            selected_employee_id = selected_employee_display.split("ID: ")[1].rstrip(")")

            # Get employee's annual leave balance from CSV
            leave_balance = get_leave_balance(selected_employee_id)

            # Get scheduled leave days for this employee
            al_df = load_annual_leave_records()
            if not al_df.empty:
                emp_scheduled = al_df[al_df['employee_id'] == selected_employee_id]
                scheduled_days = len(emp_scheduled)
            else:
                scheduled_days = 0

            remaining_days = leave_balance - scheduled_days

            # Display leave balance info
            col_info1, col_info2, col_info3 = st.columns(3)
            with col_info1:
                st.metric("Leave Balance", f"{leave_balance} days")
            with col_info2:
                st.metric("Scheduled", f"{scheduled_days} days", delta=f"-{scheduled_days}")
            with col_info3:
                color = "normal" if remaining_days >= 0 else "inverse"
                st.metric("Remaining", f"{remaining_days} days", delta=None if remaining_days >= 0 else "⚠️ Over limit")

            if remaining_days < 0:
                st.error(f"⚠️ Warning: {selected_employee_name} has scheduled more leave days than available!")

            # Date range or single date selection
            date_mode = st.radio("Select date mode:", ["Single Date", "Date Range"], horizontal=True, key="al_date_mode")

            if date_mode == "Single Date":
                selected_date = st.date_input("Select Date", value=datetime.now().date(), key="al_date")
                date_range = [selected_date]
            else:
                st.write("Select start and end dates:")
                col_date1, col_date2 = st.columns(2)
                with col_date1:
                    start_date = st.date_input("Start Date", value=datetime.now().date(), key="al_start")
                with col_date2:
                    end_date = st.date_input("End Date", value=datetime.now().date(), key="al_end")

                if start_date > end_date:
                    st.error("❌ Start date must be before or equal to end date")
                    date_range = []
                else:
                    # Generate date range
                    date_range = pd.date_range(start=start_date, end=end_date).date.tolist()
                    st.info(f"📅 Selected {len(date_range)} day(s)")

                    # Warn if exceeding balance
                    new_scheduled = scheduled_days + len(date_range)
                    if new_scheduled > leave_balance:
                        st.warning(f"⚠️ Warning: Adding {len(date_range)} days will exceed leave balance by {new_scheduled - leave_balance} day(s)")

            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("➕ Add Annual Leave Day(s)", type="primary", use_container_width=True):
                    if date_range:
                        # Check for conflicts
                        conflicts = []
                        for date in date_range:
                            has_entry, entry_type, details = check_existing_entry(selected_employee_id, date)
                            if has_entry and entry_type != 'Annual Leave':
                                conflicts.append((date, entry_type, details))

                        if conflicts:
                            st.error(f"❌ Cannot add Annual Leave day(s). {selected_employee_name} already has the following conflicting entries:")
                            for conf_date, conf_type, conf_details in conflicts:
                                st.warning(f"📅 {conf_date}: **{conf_details}**")
                            st.info("ℹ️ Please remove the existing entry first, then add the Annual Leave.")
                        else:
                            for date in date_range:
                                add_annual_leave_record(selected_employee_id, date)
                            if len(date_range) == 1:
                                st.success(f"✅ Annual Leave day added for {selected_employee_name} on {date_range[0]}")
                            else:
                                st.success(f"✅ {len(date_range)} Annual Leave days added for {selected_employee_name}")
                            st.rerun()

            with col_b:
                if st.button("🗑️ Remove Annual Leave Day(s)", use_container_width=True):
                    if date_range:
                        for date in date_range:
                            remove_annual_leave_record(selected_employee_id, date)
                        if len(date_range) == 1:
                            st.success(f"✅ Annual Leave day removed for {selected_employee_name} on {date_range[0]}")
                        else:
                            st.success(f"✅ {len(date_range)} Annual Leave days removed for {selected_employee_name}")
                        st.rerun()

        with col2:
            st.subheader("Quick Stats")
            al_counts_df = get_annual_leave_counts()
            employee_al_count = al_counts_df[al_counts_df['employee_id'] == selected_employee_id]['al_days'].values

            if len(employee_al_count) > 0:
                st.metric(f"{selected_employee_name}'s AL Days", int(employee_al_count[0]))

        st.markdown("---")

        # Calendar view
        st.subheader("📆 Annual Leave Calendar View")

        view_month = st.date_input("Select Month to View", datetime.now().date(), key="al_month_view")
        start_of_month = view_month.replace(day=1)
        if view_month.month == 12:
            end_of_month = start_of_month.replace(year=view_month.year + 1, month=1) - timedelta(days=1)
        else:
            end_of_month = start_of_month.replace(month=view_month.month + 1) - timedelta(days=1)

        month_al_records = load_annual_leave_records()
        if not month_al_records.empty:
            month_al_records = month_al_records[
                (month_al_records['date'] >= pd.to_datetime(start_of_month)) &
                (month_al_records['date'] <= pd.to_datetime(end_of_month))
            ]

            if not month_al_records.empty:
                calendar_df = month_al_records.copy()
                calendar_df['Employee'] = calendar_df['employee_id'].apply(get_employee_name_by_id)
                calendar_df = calendar_df.sort_values('date')
                calendar_df['Date'] = calendar_df['date'].dt.strftime('%Y-%m-%d')
                calendar_df = calendar_df[['Employee', 'Date', 'status']].rename(columns={'status': 'Status'})

                # Show count
                st.info(f"📋 Showing {len(calendar_df)} Annual Leave record(s) for {view_month.strftime('%B %Y')}")
                st.dataframe(calendar_df, use_container_width=True, hide_index=True)
            else:
                st.info(f"No Annual Leave days recorded for {view_month.strftime('%B %Y')}")
        else:
            st.info("No Annual Leave days scheduled")

# SCHEDULE SEMINARS PAGE
elif page == "Schedule Seminars":
    st.title("📊 Business Analytics Team Scheduler - Seminars")
    st.markdown("---")

    if not employees:
        st.warning("⚠️ No employees added yet. Go to 'Manage Employees' to add team members.")
    else:
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("Schedule Seminar Attendance")

            # Get current user role
            current_user_role = st.session_state.user_role

            # If user is not admin, filter employees to only show themselves
            if current_user_role != "Admin":
                # Regular users can only manage their own seminars
                filterable_employees = [emp for emp in employees if emp['name'] == st.session_state.user_name]
                if not filterable_employees:
                    st.error("❌ Your account is not found in the employee list.")
                    st.stop()
            else:
                # Admins can see all employees
                filterable_employees = employees

            employee_options = [f"{emp['name']} (ID: {emp['id']})" for emp in filterable_employees]
            selected_employee_display = st.selectbox("Select Employee", employee_options, key="seminar_employee")
            # Extract employee name and ID from display string
            selected_employee_name = selected_employee_display.split(" (ID:")[0]
            selected_employee_id = selected_employee_display.split("ID: ")[1].rstrip(")")

            seminar_name = st.text_input("Seminar Name", placeholder="e.g., Data Analytics Workshop")

            # Date range or single date selection
            date_mode = st.radio("Select date mode:", ["Single Date", "Date Range"], horizontal=True, key="seminar_date_mode")

            if date_mode == "Single Date":
                selected_date = st.date_input("Select Date", value=datetime.now().date(), key="seminar_date")
                date_range = [selected_date]
            else:
                st.write("Select start and end dates:")
                col_date1, col_date2 = st.columns(2)
                with col_date1:
                    start_date = st.date_input("Start Date", value=datetime.now().date(), key="seminar_start")
                with col_date2:
                    end_date = st.date_input("End Date", value=datetime.now().date(), key="seminar_end")

                if start_date > end_date:
                    st.error("❌ Start date must be before or equal to end date")
                    date_range = []
                else:
                    # Generate date range
                    date_range = pd.date_range(start=start_date, end=end_date).date.tolist()
                    st.info(f"📅 Selected {len(date_range)} day(s) for the seminar")

            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("➕ Add Seminar Day(s)", type="primary", use_container_width=True):
                    if not seminar_name:
                        st.error("❌ Please enter seminar name")
                    elif date_range:
                        # Check for conflicts
                        conflicts = []
                        for date in date_range:
                            has_entry, entry_type, details = check_existing_entry(selected_employee_id, date)
                            if has_entry and entry_type != 'Seminar':
                                conflicts.append((date, entry_type, details))

                        if conflicts:
                            st.error(f"❌ Cannot add Seminar day(s). {selected_employee_name} already has the following conflicting entries:")
                            for conf_date, conf_type, conf_details in conflicts:
                                st.warning(f"📅 {conf_date}: **{conf_details}**")
                            st.info("ℹ️ Please remove the existing entry first, then add the Seminar.")
                        else:
                            for date in date_range:
                                add_seminar_record(selected_employee_id, date, seminar_name)
                            if len(date_range) == 1:
                                st.success(f"✅ Seminar day added for {selected_employee_name} on {date_range[0]}")
                            else:
                                st.success(f"✅ {len(date_range)} Seminar days added for {selected_employee_name}")
                            st.rerun()

            with col_b:
                if st.button("🗑️ Remove Seminar Day(s)", use_container_width=True):
                    if date_range:
                        for date in date_range:
                            remove_seminar_record(selected_employee_id, date)
                        if len(date_range) == 1:
                            st.success(f"✅ Seminar day removed for {selected_employee_name} on {date_range[0]}")
                        else:
                            st.success(f"✅ {len(date_range)} Seminar days removed for {selected_employee_name}")
                        st.rerun()

        with col2:
            st.subheader("Quick Stats")
            seminar_counts_df = get_seminar_counts()
            employee_seminar_count = seminar_counts_df[seminar_counts_df['employee_id'] == selected_employee_id]['seminar_days'].values

            if len(employee_seminar_count) > 0:
                st.metric(f"{selected_employee_name}'s Seminar Days", int(employee_seminar_count[0]))

        st.markdown("---")

        # Calendar view
        st.subheader("📆 Seminar Calendar View")

        view_month = st.date_input("Select Month to View", datetime.now().date(), key="seminar_month_view")
        start_of_month = view_month.replace(day=1)
        if view_month.month == 12:
            end_of_month = start_of_month.replace(year=view_month.year + 1, month=1) - timedelta(days=1)
        else:
            end_of_month = start_of_month.replace(month=view_month.month + 1) - timedelta(days=1)

        month_seminar_records = load_seminar_records()
        if not month_seminar_records.empty:
            month_seminar_records = month_seminar_records[
                (month_seminar_records['date'] >= pd.to_datetime(start_of_month)) &
                (month_seminar_records['date'] <= pd.to_datetime(end_of_month))
            ]

            if not month_seminar_records.empty:
                calendar_df = month_seminar_records.copy()
                calendar_df['Employee'] = calendar_df['employee_id'].apply(get_employee_name_by_id)
                calendar_df = calendar_df.sort_values('date')
                calendar_df['Date'] = calendar_df['date'].dt.strftime('%Y-%m-%d')
                calendar_df = calendar_df[['Employee', 'Date', 'status', 'seminar_name']].rename(columns={
                    'status': 'Status',
                    'seminar_name': 'Seminar Name'
                })

                # Show count
                st.info(f"📋 Showing {len(calendar_df)} Seminar record(s) for {view_month.strftime('%B %Y')}")
                st.dataframe(calendar_df, use_container_width=True, hide_index=True)
            else:
                st.info(f"No Seminar days recorded for {view_month.strftime('%B %Y')}")
        else:
            st.info("No Seminar days scheduled")

# MANAGE EMPLOYEES PAGE
elif page == "Manage Employees":
    st.title("📊 Business Analytics Team Scheduler - Manage Employees")
    st.markdown("---")

    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        st.subheader("Add New Employee")
        new_employee = st.text_input("Employee Name")
        new_employee_id = st.text_input("Employee ID (4 characters)", max_chars=4)
        new_annual_leave = st.number_input("Annual Leave Balance (days)", min_value=0, max_value=365, value=20, step=1)
        new_password = st.text_input("Password", value="1234", type="password", key="new_password")
        new_role = st.selectbox("Role", ["User", "Admin"])

        # Screen permissions based on role
        st.write("**Screen Permissions:**")
        role_perms = load_role_permissions()
        default_screens = role_perms.get(new_role, [])
        selected_screens = st.multiselect(
            "Select screens to allow (defaults based on role):",
            options=ALL_SCREENS,
            default=default_screens,
            key="new_emp_screens"
        )

        if st.button("➕ Add Employee", type="primary"):
            if new_employee and new_employee_id and new_password:
                if len(new_employee_id) != 4:
                    st.error("❌ Employee ID must be exactly 4 characters")
                elif any(emp['name'] == new_employee for emp in employees):
                    st.error("❌ Employee already exists")
                elif any(emp['id'] == new_employee_id for emp in employees):
                    st.error("❌ Employee ID already exists")
                else:
                    employees.append({
                        'name': new_employee,
                        'id': new_employee_id,
                        'password': hash_password(new_password),
                        'role': new_role,
                        'screen_permissions': selected_screens
                    })
                    save_employees(employees)
                    # Save leave balance to separate CSV file
                    set_leave_balance(new_employee_id, new_annual_leave)
                    st.success(f"✅ Added {new_employee} (ID: {new_employee_id}, Role: {new_role}, Leave: {new_annual_leave} days)")
                    st.rerun()
            else:
                st.error("❌ Please enter name, ID, and password")

    with col2:
        st.subheader("Edit Employee")
        if employees:
            # Create list of employee names for selectbox
            employee_options = [emp['name'] for emp in employees]

            selected_emp_name = st.selectbox("Select Employee to Edit", employee_options, key="edit_select")

            # Find the selected employee
            selected_emp = next((emp for emp in employees if emp['name'] == selected_emp_name), None)

            if selected_emp:
                # Get current leave balance from CSV
                current_leave_balance = get_leave_balance(selected_emp['id'])

                # Display current values
                st.info(f"**Current Name:** {selected_emp['name']}  \n**Current ID:** {selected_emp['id'] if selected_emp['id'] else 'Not Set'}  \n**Role:** {selected_emp.get('role', 'User')}  \n**Annual Leave:** {current_leave_balance} days")

                # Use unique keys based on employee name to reset fields when selection changes
                edited_name = st.text_input("New Name", value=selected_emp['name'], key=f"edit_name_{selected_emp_name}")
                edited_id = st.text_input("New ID (4 characters)", value=selected_emp['id'] if selected_emp['id'] else "", max_chars=4, key=f"edit_id_{selected_emp_name}")
                edited_leave = st.number_input("Annual Leave Balance (days)", min_value=0, max_value=365, value=current_leave_balance, step=1, key=f"edit_leave_{selected_emp_name}")
                edited_password = st.text_input("New Password (leave empty to keep current)", type="password", key=f"edit_password_{selected_emp_name}")
                edited_role = st.selectbox("Role", ["User", "Admin"], index=0 if selected_emp.get('role', 'User') == 'User' else 1, key=f"edit_role_{selected_emp_name}")

                # Screen permissions
                st.write("**Screen Permissions:**")
                role_perms_edit = load_role_permissions()
                current_screens = selected_emp.get('screen_permissions', role_perms_edit.get(selected_emp.get('role', 'User'), []))
                edited_screens = st.multiselect(
                    "Select screens to allow:",
                    options=ALL_SCREENS,
                    default=current_screens,
                    key=f"edit_screens_{selected_emp_name}"
                )

                if st.button("💾 Save Changes", type="primary", key="save_edit"):
                    if not edited_name or not edited_id:
                        st.error("❌ Please enter both name and ID")
                    elif len(edited_id) != 4:
                        st.error("❌ Employee ID must be exactly 4 characters")
                    elif edited_name != selected_emp['name'] and any(emp['name'] == edited_name for emp in employees):
                        st.error("❌ Employee name already exists")
                    elif edited_id != selected_emp['id'] and any(emp['id'] == edited_id for emp in employees):
                        st.error("❌ Employee ID already exists")
                    else:
                        # Update WFH, AL, and Seminar records if ID changed
                        if edited_id != selected_emp['id']:
                            df_wfh = load_wfh_records()
                            df_wfh.loc[df_wfh['employee_id'] == selected_emp['id'], 'employee_id'] = edited_id
                            save_wfh_records(df_wfh)

                            df_al = load_annual_leave_records()
                            df_al.loc[df_al['employee_id'] == selected_emp['id'], 'employee_id'] = edited_id
                            save_annual_leave_records(df_al)

                            df_seminar = load_seminar_records()
                            df_seminar.loc[df_seminar['employee_id'] == selected_emp['id'], 'employee_id'] = edited_id
                            save_seminar_records(df_seminar)

                        # Update employee record
                        old_id = selected_emp['id']
                        for emp in employees:
                            if emp['name'] == selected_emp['name']:
                                emp['name'] = edited_name
                                emp['id'] = edited_id
                                emp['role'] = edited_role
                                emp['screen_permissions'] = edited_screens
                                # Update password only if new one is provided
                                if edited_password:
                                    emp['password'] = hash_password(edited_password)
                                break

                        save_employees(employees)

                        # Update leave balance in CSV
                        if edited_id != old_id:
                            # If ID changed, update the leave balance record
                            df_balances = load_leave_balances()
                            df_balances = df_balances.copy()  # Important: copy before modifying
                            df_balances.loc[df_balances['employee_id'] == old_id, 'employee_id'] = edited_id
                            save_leave_balances(df_balances)

                        # Update leave balance and verify it was saved
                        success = set_leave_balance(edited_id, edited_leave)
                        if success:
                            # Verify the save by reading back from disk
                            import time
                            time.sleep(0.3)  # Wait longer to ensure file is fully written

                            verified_balance = get_leave_balance(edited_id)
                            if verified_balance == edited_leave:
                                st.success(f"✅ Updated employee to {edited_name} (ID: {edited_id}, Role: {edited_role}, Leave: {edited_leave} days)")
                            else:
                                st.warning(f"⚠️ Updated employee but balance verification shows {verified_balance} instead of {edited_leave}. Retrying...")
                                # Retry the save
                                success = set_leave_balance(edited_id, edited_leave)
                                if success:
                                    st.success(f"✅ Successfully updated after retry")

                            time.sleep(0.2)
                            st.rerun()
                        else:
                            st.error(f"❌ Failed to update leave balance. Please try again.")
        else:
            st.info("No employees to edit")

    with col3:
        st.subheader("Remove Employee")
        if employees:
            employee_names = [f"{emp['name']} (ID: {emp['id']})" for emp in employees]
            employee_to_remove = st.selectbox("Select Employee to Remove", employee_names, key="remove_select")
            if st.button("🗑️ Remove Employee", type="secondary"):
                # Extract the employee name from the display string
                emp_name = employee_to_remove.split(" (ID:")[0]
                # Find the employee to get their ID
                emp_to_remove = next((emp for emp in employees if emp['name'] == emp_name), None)
                if emp_to_remove:
                    emp_id = emp_to_remove['id']

                    employees = [emp for emp in employees if emp['name'] != emp_name]
                    save_employees(employees)

                    # Also remove their WFH, AL, and Seminar records by employee_id
                    df = load_wfh_records()
                    df = df[df['employee_id'] != emp_id]
                    save_wfh_records(df)

                    df_al = load_annual_leave_records()
                    df_al = df_al[df_al['employee_id'] != emp_id]
                    save_annual_leave_records(df_al)

                    df_seminar = load_seminar_records()
                    df_seminar = df_seminar[df_seminar['employee_id'] != emp_id]
                    save_seminar_records(df_seminar)

                    st.success(f"✅ Removed {employee_to_remove}")
                    st.rerun()
        else:
            st.info("No employees to remove")
    
    st.markdown("---")
    
    # Display current employees
    st.subheader("Current Team Members")
    if employees:
        # Create display dataframe with ID and annual leave
        employee_display = pd.DataFrame([
            {
                'Employee Name': emp['name'],
                'Employee ID': emp['id'],
                'Annual Leave Balance': emp.get('annual_leave_balance', 20)
            }
            for emp in employees
        ])

        # Get WFH counts
        counts_df = get_wfh_counts()
        employee_display = employee_display.merge(
            counts_df.rename(columns={'employee_name': 'Employee Name'}),
            on='Employee Name',
            how='left'
        ).fillna(0)
        employee_display['wfh_days'] = employee_display['wfh_days'].astype(int)

        # Rename WFH column for clarity
        employee_display = employee_display.rename(columns={'wfh_days': 'WFH Days'})

        st.dataframe(
            employee_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                'Annual Leave Balance': st.column_config.NumberColumn('Annual Leave Balance', format='%d days'),
                'WFH Days': st.column_config.NumberColumn('WFH Days', format='%d')
            }
        )
    else:
        st.info("No employees added yet")

# REPORTS PAGE
elif page == "Reports":
    st.title("📊 Business Analytics Team Scheduler - Reports")
    st.markdown("---")
    
    if not employees:
        st.warning("⚠️ No employees added yet. Go to 'Manage Employees' to add team members.")
    else:
        # Date range selector
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", datetime.now().date() - timedelta(days=90))
        with col2:
            end_date = st.date_input("End Date", datetime.now().date() + timedelta(days=30))
        
        st.markdown("---")
        
        # WFH Summary Report
        st.subheader("WFH Summary Report")
        
        df_records = load_wfh_records()
        if not df_records.empty:
            period_records = df_records[
                (df_records['date'] >= pd.to_datetime(start_date)) & 
                (df_records['date'] <= pd.to_datetime(end_date))
            ]
            
            if not period_records.empty:
                col_a, col_b, col_c = st.columns(3)
                
                with col_a:
                    st.metric("Total WFH Days", len(period_records))
                
                with col_b:
                    unique_employees = period_records['employee_id'].nunique()
                    st.metric("Employees Using WFH", unique_employees)
                
                with col_c:
                    avg_per_employee = len(period_records) / len(employees)
                    st.metric("Avg WFH Days/Employee", f"{avg_per_employee:.1f}")
                
                st.markdown("---")
                
                # Detailed breakdown
                st.subheader("Detailed Breakdown by Employee")

                employee_stats = period_records.groupby('employee_id').agg({
                    'date': 'count'
                }).reset_index()
                employee_stats.columns = ['employee_id', 'WFH Days']
                employee_stats = employee_stats.sort_values('WFH Days', ascending=False)

                # Add employees with 0 days and include names and IDs
                all_emp = pd.DataFrame([
                    {'employee_id': emp['id'], 'Employee': emp['name'], 'Employee ID': emp['id']}
                    for emp in employees
                ])
                employee_stats = all_emp.merge(employee_stats, on='employee_id', how='left').fillna(0)
                employee_stats['WFH Days'] = employee_stats['WFH Days'].astype(int)
                employee_stats = employee_stats[['Employee', 'Employee ID', 'WFH Days']]

                # Use a container with limited width (40% of page)
                col1, col2 = st.columns([2, 3])
                with col1:
                    st.dataframe(
                        employee_stats,
                        hide_index=True,
                        column_config={
                            'Employee': st.column_config.TextColumn('Employee'),
                            'Employee ID': st.column_config.TextColumn('Employee ID'),
                            'WFH Days': st.column_config.NumberColumn('WFH Days')
                        },
                        use_container_width=True
                    )

                # WFH Days Balance Chart
                st.markdown("---")
                st.subheader("WFH Days Balance")

                counts_df = get_wfh_counts()

                fig = px.bar(counts_df, x='employee_name', y='wfh_days',
                            title='WFH Days Used per Employee',
                            labels={'employee_name': 'Employee', 'wfh_days': 'WFH Days'},
                            color='wfh_days',
                            color_continuous_scale='Blues')
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

                # Show stats
                if counts_df['wfh_days'].sum() > 0:
                    avg_days = counts_df['wfh_days'].mean()
                    max_days = counts_df['wfh_days'].max()
                    min_days = counts_df['wfh_days'].min()

                    col_stat1, col_stat2, col_stat3 = st.columns(3)
                    col_stat1.metric("Average", f"{avg_days:.1f}")
                    col_stat2.metric("Max", int(max_days))
                    col_stat3.metric("Min", int(min_days))

                # WFH by Day of Week Report
                st.markdown("---")
                st.subheader("WFH Days by Day of Week")

                # Add day of week to period records
                period_records_copy = period_records.copy()
                period_records_copy['employee_name'] = period_records_copy['employee_id'].apply(get_employee_name_by_id)
                period_records_copy['day_of_week'] = period_records_copy['date'].dt.day_name()

                # Create pivot table: employees vs days of week (workdays only)
                day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

                # Count WFH days per employee per day of week
                wfh_by_day = period_records_copy.groupby(['employee_name', 'day_of_week']).size().reset_index(name='count')

                # Pivot to get employees as rows and days as columns
                pivot_table = wfh_by_day.pivot(index='employee_name', columns='day_of_week', values='count').fillna(0).astype(int)

                # Reorder columns to match day order and add missing days
                for day in day_order:
                    if day not in pivot_table.columns:
                        pivot_table[day] = 0
                pivot_table = pivot_table[day_order]

                # Add all employees even if they have 0 WFH days
                all_employee_names = [emp['name'] for emp in employees]
                for emp_name in all_employee_names:
                    if emp_name not in pivot_table.index:
                        pivot_table.loc[emp_name] = 0

                # Add a Total column
                pivot_table['Total'] = pivot_table.sum(axis=1)

                # Reset index to make employee_name a column
                pivot_table = pivot_table.reset_index()
                pivot_table = pivot_table.rename(columns={'employee_name': 'Employee'})

                # Display with centered alignment for day columns
                st.dataframe(
                    pivot_table,
                    hide_index=True,
                    column_config={
                        'Employee': st.column_config.TextColumn('Employee', width='medium'),
                        'Monday': st.column_config.NumberColumn('Monday', format='%d', help='WFH count on Monday', width='small'),
                        'Tuesday': st.column_config.NumberColumn('Tuesday', format='%d', help='WFH count on Tuesday', width='small'),
                        'Wednesday': st.column_config.NumberColumn('Wednesday', format='%d', help='WFH count on Wednesday', width='small'),
                        'Thursday': st.column_config.NumberColumn('Thursday', format='%d', help='WFH count on Thursday', width='small'),
                        'Friday': st.column_config.NumberColumn('Friday', format='%d', help='WFH count on Friday', width='small'),
                        'Total': st.column_config.NumberColumn('Total', format='%d', help='Total WFH days', width='small')
                    }
                )

                # Export functionality
                st.markdown("---")
                st.subheader("📥 Export Data")

                csv = period_records.to_csv(index=False)
                st.download_button(
                    label="Download WFH Records (CSV)",
                    data=csv,
                    file_name=f"wfh_records_{start_date}_{end_date}.csv",
                    mime="text/csv"
                )
            else:
                st.info("No WFH records found for the selected date range")
        else:
            st.info("No WFH records available")

        # Annual Leave Balance Report
        st.markdown("---")
        st.subheader("🌴 Annual Leave Balance Report")

        al_df = load_annual_leave_records()

        # Create balance report for all employees
        balance_report = []
        for emp in employees:
            emp_name = emp['name']
            emp_id = emp['id']
            leave_balance = emp.get('annual_leave_balance', 20)

            # Count scheduled leave days
            if not al_df.empty:
                emp_al_records = al_df[al_df['employee_id'] == emp_id]
                scheduled_days = len(emp_al_records)
            else:
                scheduled_days = 0

            remaining_days = leave_balance - scheduled_days

            balance_report.append({
                'Employee': emp_name,
                'Employee ID': emp_id,
                'Leave Balance': leave_balance,
                'Scheduled': scheduled_days,
                'Remaining': remaining_days
            })

        balance_df = pd.DataFrame(balance_report)

        # Color code the dataframe
        def highlight_negative(val):
            if isinstance(val, (int, float)) and val < 0:
                return 'background-color: #ffcccc'
            return ''

        # Use a container with limited width (50% of page)
        col1, col2 = st.columns([1, 1])
        with col1:
            st.dataframe(
                balance_df,
                hide_index=True,
                column_config={
                    'Employee': st.column_config.TextColumn('Employee'),
                    'Employee ID': st.column_config.TextColumn('Employee ID'),
                    'Leave Balance': st.column_config.NumberColumn('Leave Balance', format='%d days'),
                    'Scheduled': st.column_config.NumberColumn('Scheduled', format='%d days'),
                    'Remaining': st.column_config.NumberColumn('Remaining', format='%d days')
                },
                use_container_width=True
            )

        # Show warnings for negative balances
        negative_balances = balance_df[balance_df['Remaining'] < 0]
        if not negative_balances.empty:
            st.warning(f"⚠️ {len(negative_balances)} employee(s) have scheduled more leave than available:")
            for _, row in negative_balances.iterrows():
                st.error(f"**{row['Employee']}**: {row['Remaining']} days (over by {abs(row['Remaining'])} days)")

        # Visualization
        st.markdown("---")
        st.subheader("Annual Leave Balance Visualization")

        col_viz1, col_viz2 = st.columns(2)

        with col_viz1:
            # Bar chart for balance vs scheduled
            fig_balance = go.Figure()
            fig_balance.add_trace(go.Bar(
                x=balance_df['Employee'],
                y=balance_df['Leave Balance'],
                name='Leave Balance',
                marker_color='lightblue'
            ))
            fig_balance.add_trace(go.Bar(
                x=balance_df['Employee'],
                y=balance_df['Scheduled'],
                name='Scheduled',
                marker_color='orange'
            ))
            fig_balance.update_layout(
                title='Leave Balance vs Scheduled',
                xaxis_title='Employee',
                yaxis_title='Days',
                barmode='group',
                showlegend=True
            )
            st.plotly_chart(fig_balance, use_container_width=True)

        with col_viz2:
            # Remaining leave chart
            colors = ['red' if x < 0 else 'green' for x in balance_df['Remaining']]
            fig_remaining = go.Figure(go.Bar(
                x=balance_df['Employee'],
                y=balance_df['Remaining'],
                name='Remaining Leave',
                marker_color=colors
            ))
            fig_remaining.update_layout(
                title='Remaining Leave Days',
                xaxis_title='Employee',
                yaxis_title='Days',
                showlegend=False
            )
            st.plotly_chart(fig_remaining, use_container_width=True)

        # Seminar Summary Report
        st.markdown("---")
        st.subheader("📚 Seminar Attendance Report")

        df_seminar = load_seminar_records()
        if not df_seminar.empty:
            period_seminar_records = df_seminar[
                (df_seminar['date'] >= pd.to_datetime(start_date)) &
                (df_seminar['date'] <= pd.to_datetime(end_date))
            ]

            if not period_seminar_records.empty:
                col_sem_a, col_sem_b, col_sem_c = st.columns(3)

                with col_sem_a:
                    st.metric("Total Seminar Days", len(period_seminar_records))

                with col_sem_b:
                    unique_seminars = period_seminar_records['seminar_name'].nunique()
                    st.metric("Unique Seminars", unique_seminars)

                with col_sem_c:
                    unique_attendees = period_seminar_records['employee_id'].nunique()
                    st.metric("Employees Attending", unique_attendees)

                st.markdown("---")

                # Seminar attendance breakdown
                st.subheader("Seminar Attendance by Employee")

                seminar_stats = period_seminar_records.groupby('employee_id').agg({
                    'date': 'count'
                }).reset_index()
                seminar_stats.columns = ['employee_id', 'Seminar Days']
                seminar_stats = seminar_stats.sort_values('Seminar Days', ascending=False)

                # Add employees with 0 days
                all_emp_seminar = pd.DataFrame([
                    {'employee_id': emp['id'], 'Employee': emp['name'], 'Employee ID': emp['id']}
                    for emp in employees
                ])
                seminar_stats = all_emp_seminar.merge(seminar_stats, on='employee_id', how='left').fillna(0)
                seminar_stats['Seminar Days'] = seminar_stats['Seminar Days'].astype(int)
                seminar_stats = seminar_stats[['Employee', 'Employee ID', 'Seminar Days']]

                # Use a container with limited width (40% of page)
                col1, col2 = st.columns([2, 3])
                with col1:
                    st.dataframe(
                        seminar_stats,
                        hide_index=True,
                        column_config={
                            'Employee': st.column_config.TextColumn('Employee'),
                            'Employee ID': st.column_config.TextColumn('Employee ID'),
                            'Seminar Days': st.column_config.NumberColumn('Seminar Days')
                        },
                        use_container_width=True
                    )

                # Seminar list with attendees
                st.markdown("---")
                st.subheader("Seminar Details")

                seminar_details = period_seminar_records.copy()
                seminar_details['Employee'] = seminar_details['employee_id'].apply(get_employee_name_by_id)
                seminar_details['Date'] = seminar_details['date'].dt.strftime('%Y-%m-%d')
                seminar_details = seminar_details[['Employee', 'Date', 'seminar_name', 'status']].rename(columns={
                    'seminar_name': 'Seminar Name',
                    'status': 'Status'
                })
                seminar_details = seminar_details.sort_values('Date', ascending=False)

                # Use a container with limited width (60% of page for this wider table)
                col1, col2 = st.columns([3, 2])
                with col1:
                    st.dataframe(
                        seminar_details,
                        hide_index=True,
                        column_config={
                            'Employee': st.column_config.TextColumn('Employee'),
                            'Date': st.column_config.TextColumn('Date'),
                            'Seminar Name': st.column_config.TextColumn('Seminar Name'),
                            'Status': st.column_config.TextColumn('Status')
                        },
                        use_container_width=True
                    )

                # Chart
                st.markdown("---")
                st.subheader("Seminar Attendance Chart")

                counts_seminar_df = get_seminar_counts()

                fig_seminar = px.bar(counts_seminar_df, x='employee_name', y='seminar_days',
                            title='Seminar Days per Employee',
                            labels={'employee_name': 'Employee', 'seminar_days': 'Seminar Days'},
                            color='seminar_days',
                            color_continuous_scale='Blues')
                fig_seminar.update_layout(showlegend=False)
                st.plotly_chart(fig_seminar, use_container_width=True)
            else:
                st.info("No seminar records found for the selected date range")
        else:
            st.info("No seminar records available")

# CONFIGURE ROLES PAGE
elif page == "Configure Roles":
    st.title("📊 Business Analytics Team Scheduler - Configure Roles")
    st.markdown("---")

    # Check if user is Admin
    if st.session_state.user_role != "Admin":
        st.error("❌ Access Denied: Only Admins can configure roles")
        st.stop()

    st.subheader("Role Permissions Configuration")
    st.write("Configure which screens are available for each role by default.")

    # Load current role permissions
    role_permissions = load_role_permissions()

    # Create tabs for each role
    roles = list(role_permissions.keys())
    if roles:
        tabs = st.tabs([f"🔑 {role}" for role in roles])

        for idx, role in enumerate(roles):
            with tabs[idx]:
                st.write(f"**Configure screens for {role} role:**")

                current_screens = role_permissions.get(role, [])
                updated_screens = st.multiselect(
                    f"Select screens for {role}:",
                    options=ALL_SCREENS,
                    default=current_screens,
                    key=f"role_screens_{role}"
                )

                # Display current assignment
                st.info(f"Currently assigned screens: **{', '.join(current_screens) if current_screens else 'None'}**")

                # Save button for this role
                col1, col2 = st.columns([1, 3])
                with col1:
                    if st.button(f"💾 Save {role} Permissions", type="primary", key=f"save_role_{role}"):
                        role_permissions[role] = updated_screens
                        save_role_permissions(role_permissions)
                        st.success(f"✅ {role} permissions updated successfully!")
                        st.rerun()

                st.markdown("---")

        # Summary section
        st.subheader("📋 Permissions Summary")
        summary_data = []
        for role in roles:
            screens = role_permissions.get(role, [])
            summary_data.append({
                'Role': role,
                'Screens': ', '.join(screens) if screens else 'None',
                'Screen Count': len(screens)
            })

        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df, use_container_width=True, hide_index=True)

        st.info("💡 **Note:** Individual users can have custom screen permissions that override their role's default permissions.")
    else:
        st.warning("⚠️ No roles configured yet.")

# BACKUP & EXPORT PAGE
elif page == "Backup & Export":
    st.title("📊 Business Analytics Team Scheduler - Backup & Export")
    st.markdown("---")

    # Check if user is Admin
    if st.session_state.user_role != "Admin":
        st.error("❌ Access Denied: Only Admins can backup and export data")
        st.stop()

    st.subheader("📥 Backup & Export Data")
    st.write("Export all application data files as CSV for backup and record-keeping purposes.")

    # Create three columns for export options
    col1, col2, col3 = st.columns(3)

    # WFH Records Export
    with col1:
        st.write("**Work From Home Records**")
        if st.button("📥 Export WFH Records", use_container_width=True, key="export_wfh"):
            df_wfh = load_wfh_records()
            csv_wfh = df_wfh.to_csv(index=False)
            st.download_button(
                label="⬇️ Download WFH_Records.csv",
                data=csv_wfh,
                file_name=f"WFH_Records_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                key="download_wfh"
            )
            st.success(f"✅ WFH records ready for download ({len(df_wfh)} records)")

    # Annual Leave Records Export
    with col2:
        st.write("**Annual Leave Records**")
        if st.button("📥 Export Leave Records", use_container_width=True, key="export_al"):
            df_al = load_annual_leave_records()
            csv_al = df_al.to_csv(index=False)
            st.download_button(
                label="⬇️ Download Leave_Records.csv",
                data=csv_al,
                file_name=f"Leave_Records_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                key="download_al"
            )
            st.success(f"✅ Annual leave records ready for download ({len(df_al)} records)")

    # Seminar Records Export
    with col3:
        st.write("**Seminar Attendance Records**")
        if st.button("📥 Export Seminar Records", use_container_width=True, key="export_seminar"):
            df_seminar = load_seminar_records()
            csv_seminar = df_seminar.to_csv(index=False)
            st.download_button(
                label="⬇️ Download Seminar_Records.csv",
                data=csv_seminar,
                file_name=f"Seminar_Records_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                key="download_seminar"
            )
            st.success(f"✅ Seminar records ready for download ({len(df_seminar)} records)")

    st.markdown("---")

    # Leave Balances Export
    st.subheader("💰 Leave Balance Records")
    col_balance = st.columns(1)[0]
    with col_balance:
        if st.button("📥 Export Leave Balances", use_container_width=True, key="export_balances"):
            df_balances = load_leave_balances()
            csv_balances = df_balances.to_csv(index=False)
            st.download_button(
                label="⬇️ Download Leave_Balances.csv",
                data=csv_balances,
                file_name=f"Leave_Balances_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                key="download_balances"
            )
            st.success(f"✅ Leave balances ready for download ({len(df_balances)} records)")

    st.markdown("---")

    # Bulk Export
    st.subheader("📦 Bulk Export All Data")
    st.write("Export all records in a single operation for complete backup.")

    if st.button("📥 Export All Data", type="primary", use_container_width=True, key="export_all"):
        try:
            # Load all data
            df_wfh = load_wfh_records()
            df_al = load_annual_leave_records()
            df_seminar = load_seminar_records()
            df_balances = load_leave_balances()
            employees = load_employees()

            # Create a summary
            summary_text = f"""
BACKUP SUMMARY
==============
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Total Records:
- WFH Records: {len(df_wfh)}
- Annual Leave Records: {len(df_al)}
- Seminar Records: {len(df_seminar)}
- Leave Balances: {len(df_balances)}
- Total Employees: {len(employees)}

Files included in this backup:
1. WFH_Records.csv
2. Leave_Records.csv
3. Seminar_Records.csv
4. Leave_Balances.csv
5. Backup_Summary.txt
"""

            # Prepare multiple files as a formatted text
            backup_data = f"""
=== WFH RECORDS ===
{df_wfh.to_csv(index=False)}

=== ANNUAL LEAVE RECORDS ===
{df_al.to_csv(index=False)}

=== SEMINAR RECORDS ===
{df_seminar.to_csv(index=False)}

=== LEAVE BALANCES ===
{df_balances.to_csv(index=False)}

=== BACKUP SUMMARY ===
{summary_text}
"""

            st.download_button(
                label="⬇️ Download Complete Backup (All Data)",
                data=backup_data,
                file_name=f"Complete_Backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                key="download_all"
            )

            st.success("✅ Complete backup ready for download!")
            st.info(f"""
            📊 **Backup Contents:**
            - WFH Records: {len(df_wfh)} entries
            - Annual Leave Records: {len(df_al)} entries
            - Seminar Records: {len(df_seminar)} entries
            - Leave Balances: {len(df_balances)} employees
            - Total Employees: {len(employees)} users
            """)
        except Exception as e:
            st.error(f"❌ Error preparing backup: {e}")

    st.markdown("---")

    # RESTORE SECTION
    st.subheader("📤 Restore Data from Backup")
    st.write("Upload CSV files to restore data from previous backups. Select one or more files to restore.")

    # Create tabs for restoration options
    restore_tab1, restore_tab2, restore_tab3 = st.tabs(["Individual Restore", "Bulk Restore", "Restore Info"])

    with restore_tab1:
        st.write("**Restore Individual Data Types**")
        st.warning("⚠️ Restoring will overwrite existing data. Make sure you have a recent backup!")

        col_restore1, col_restore2 = st.columns(2)

        # WFH Records Restore
        with col_restore1:
            st.write("**Restore WFH Records**")
            wfh_file = st.file_uploader("Upload WFH Records CSV", type=["csv"], key="restore_wfh")
            if wfh_file is not None:
                if st.button("🔄 Restore WFH Records", type="primary", use_container_width=True, key="restore_wfh_btn"):
                    try:
                        df_wfh_restore = pd.read_csv(wfh_file, dtype={'employee_id': str})
                        save_wfh_records(df_wfh_restore)
                        st.success(f"✅ Successfully restored {len(df_wfh_restore)} WFH records!")
                        st.info("The page will refresh to load the restored data.")
                        import time
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error restoring WFH records: {e}")

        # Annual Leave Records Restore
        with col_restore2:
            st.write("**Restore Annual Leave Records**")
            al_file = st.file_uploader("Upload Annual Leave Records CSV", type=["csv"], key="restore_al")
            if al_file is not None:
                if st.button("🔄 Restore Leave Records", type="primary", use_container_width=True, key="restore_al_btn"):
                    try:
                        df_al_restore = pd.read_csv(al_file, dtype={'employee_id': str})
                        save_annual_leave_records(df_al_restore)
                        st.success(f"✅ Successfully restored {len(df_al_restore)} Annual Leave records!")
                        st.info("The page will refresh to load the restored data.")
                        import time
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error restoring Annual Leave records: {e}")

        col_restore3, col_restore4 = st.columns(2)

        # Seminar Records Restore
        with col_restore3:
            st.write("**Restore Seminar Records**")
            seminar_file = st.file_uploader("Upload Seminar Records CSV", type=["csv"], key="restore_seminar")
            if seminar_file is not None:
                if st.button("🔄 Restore Seminar Records", type="primary", use_container_width=True, key="restore_seminar_btn"):
                    try:
                        df_seminar_restore = pd.read_csv(seminar_file, dtype={'employee_id': str})
                        save_seminar_records(df_seminar_restore)
                        st.success(f"✅ Successfully restored {len(df_seminar_restore)} Seminar records!")
                        st.info("The page will refresh to load the restored data.")
                        import time
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error restoring Seminar records: {e}")

        # Leave Balances Restore
        with col_restore4:
            st.write("**Restore Leave Balances**")
            balances_file = st.file_uploader("Upload Leave Balances CSV", type=["csv"], key="restore_balances")
            if balances_file is not None:
                if st.button("🔄 Restore Leave Balances", type="primary", use_container_width=True, key="restore_balances_btn"):
                    try:
                        df_balances_restore = pd.read_csv(balances_file, dtype={'employee_id': str, 'annual_leave_balance': int})
                        save_leave_balances(df_balances_restore)
                        st.success(f"✅ Successfully restored {len(df_balances_restore)} Leave Balance records!")
                        st.info("The page will refresh to load the restored data.")
                        import time
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error restoring Leave Balances: {e}")

    with restore_tab2:
        st.write("**Bulk Restore All Data**")
        st.warning("⚠️ This will overwrite all existing data! Only use to restore from a complete backup.")

        bulk_file = st.file_uploader("Upload Complete Backup File", type=["txt"], key="restore_bulk")
        if bulk_file is not None:
            st.info("📋 File uploaded successfully. Click the button below to restore all data from this backup.")
            if st.button("🔄 Restore All Data", type="primary", use_container_width=True, key="restore_all_btn"):
                try:
                    backup_content = bulk_file.read().decode('utf-8')

                    # Parse the backup file sections
                    sections = backup_content.split('===')
                    restored_count = 0

                    # Process each section
                    for section in sections:
                        lines = section.strip().split('\n')
                        if not lines:
                            continue

                        section_title = lines[0].strip()

                        if 'WFH RECORDS' in section_title:
                            csv_data = '\n'.join(lines[1:])
                            if csv_data.strip():
                                from io import StringIO
                                df_wfh = pd.read_csv(StringIO(csv_data), dtype={'employee_id': str})
                                if not df_wfh.empty:
                                    save_wfh_records(df_wfh)
                                    st.success(f"✅ Restored {len(df_wfh)} WFH records")
                                    restored_count += len(df_wfh)

                        elif 'ANNUAL LEAVE' in section_title:
                            csv_data = '\n'.join(lines[1:])
                            if csv_data.strip():
                                from io import StringIO
                                df_al = pd.read_csv(StringIO(csv_data), dtype={'employee_id': str})
                                if not df_al.empty:
                                    save_annual_leave_records(df_al)
                                    st.success(f"✅ Restored {len(df_al)} Annual Leave records")
                                    restored_count += len(df_al)

                        elif 'SEMINAR RECORDS' in section_title:
                            csv_data = '\n'.join(lines[1:])
                            if csv_data.strip():
                                from io import StringIO
                                df_seminar = pd.read_csv(StringIO(csv_data), dtype={'employee_id': str})
                                if not df_seminar.empty:
                                    save_seminar_records(df_seminar)
                                    st.success(f"✅ Restored {len(df_seminar)} Seminar records")
                                    restored_count += len(df_seminar)

                        elif 'LEAVE BALANCES' in section_title:
                            csv_data = '\n'.join(lines[1:])
                            if csv_data.strip():
                                from io import StringIO
                                df_balances = pd.read_csv(StringIO(csv_data), dtype={'employee_id': str, 'annual_leave_balance': int})
                                if not df_balances.empty:
                                    save_leave_balances(df_balances)
                                    st.success(f"✅ Restored {len(df_balances)} Leave Balance records")
                                    restored_count += len(df_balances)

                    st.success(f"✅ Successfully restored all data! Total records restored: {restored_count}")
                    st.info("The page will refresh to load the restored data.")
                    import time
                    time.sleep(1)
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Error restoring backup: {e}")
                    st.info("Make sure the file is a valid backup from this application.")

    with restore_tab3:
        st.write("""
        **How to Restore Data:**

        1. **Individual Restore**: Use this for restoring specific data types
           - Upload the CSV file for the data type you want to restore
           - The system will validate the file format
           - Click "Restore" to overwrite existing data
           - The page will refresh automatically with restored data

        2. **Bulk Restore**: Use this for complete system recovery
           - Upload the complete backup file (generated from "Export All Data")
           - All records will be restored to the system
           - This overwrites ALL existing data
           - Use only for full system recovery or migration

        **Supported File Types:**
        - Individual restores: CSV files
        - Bulk restore: Text files (.txt) generated by "Export All Data"

        **Important Notes:**
        - Always verify the backup file is correct before restoring
        - Current data will be overwritten - make a backup first!
        - Restoration is immediate - there's no undo
        - Employee management (add/remove/edit) is still done in the Employee Management screen
        - Use this feature for data recovery only

        **Recommended Workflow:**
        1. Export all data before making major changes
        2. Make your changes or updates
        3. If something goes wrong, restore from the backup
        4. Keep multiple backup versions for safety
        """)

    st.markdown("---")

    # Information section
    st.subheader("ℹ️ Backup Information")
    st.write("""
    **What gets backed up:**
    - All WFH scheduling records
    - All annual leave records
    - All seminar attendance records
    - Employee leave balance data

    **Recommended backup frequency:**
    - Daily for active teams
    - Weekly for minimal activity
    - Before any system updates or migrations

    **Best practices:**
    - Store backups in a secure location
    - Keep multiple versions for recovery
    - Test restoration procedures regularly
    - Include timestamps in file names for version tracking
    """)

# Footer
st.markdown("---")
st.markdown("*Business Analytics Team Scheduler - Manage the team's Annual Leave, Work-from-home days, and Seminar attendance efficiently*")