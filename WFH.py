import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import hashlib

# Page configuration
st.set_page_config(page_title="WFH Team Scheduler", layout="wide", page_icon="🏠")

# Data file paths
DATA_DIR = Path("wfh_data")
DATA_DIR.mkdir(exist_ok=True)
EMPLOYEES_FILE = DATA_DIR / "employees.json"
WFH_RECORDS_FILE = DATA_DIR / "wfh_records.csv"
ANNUAL_LEAVE_RECORDS_FILE = DATA_DIR / "annual_leave_records.csv"

# Initialize data files
def init_data_files():
    if not EMPLOYEES_FILE.exists():
        with open(EMPLOYEES_FILE, 'w') as f:
            json.dump([], f)

    if not WFH_RECORDS_FILE.exists():
        df = pd.DataFrame(columns=['employee_name', 'date', 'status'])
        df.to_csv(WFH_RECORDS_FILE, index=False)

    if not ANNUAL_LEAVE_RECORDS_FILE.exists():
        df = pd.DataFrame(columns=['employee_name', 'date', 'status'])
        df.to_csv(ANNUAL_LEAVE_RECORDS_FILE, index=False)

# Hash password
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Load employees
def load_employees():
    with open(EMPLOYEES_FILE, 'r') as f:
        employees = json.load(f)
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
            for emp in employees:
                if 'password' not in emp:
                    emp['password'] = hash_password('1234')  # Default password
                if 'role' not in emp:
                    # Set Marios Komis as admin, others as users
                    emp['role'] = 'Admin' if emp['name'] == 'Marios Komis' else 'User'
            save_employees(employees)
        return employees

# Save employees
def save_employees(employees):
    with open(EMPLOYEES_FILE, 'w') as f:
        json.dump(employees, f, indent=2)

# Load WFH records
def load_wfh_records():
    df = pd.read_csv(WFH_RECORDS_FILE)
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
    return df

# Save WFH records
def save_wfh_records(df):
    df.to_csv(WFH_RECORDS_FILE, index=False)

# Add WFH record
def add_wfh_record(employee, date, status='WFH'):
    df = load_wfh_records()
    
    # Remove existing record for same employee and date
    df = df[~((df['employee_name'] == employee) & (df['date'] == pd.to_datetime(date)))]
    
    # Add new record
    new_record = pd.DataFrame({
        'employee_name': [employee],
        'date': [pd.to_datetime(date)],
        'status': [status]
    })
    df = pd.concat([df, new_record], ignore_index=True)
    save_wfh_records(df)

# Remove WFH record
def remove_wfh_record(employee, date):
    df = load_wfh_records()
    df = df[~((df['employee_name'] == employee) & (df['date'] == pd.to_datetime(date)))]
    save_wfh_records(df)

# Load Annual Leave records
def load_annual_leave_records():
    df = pd.read_csv(ANNUAL_LEAVE_RECORDS_FILE)
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
    return df

# Save Annual Leave records
def save_annual_leave_records(df):
    df.to_csv(ANNUAL_LEAVE_RECORDS_FILE, index=False)

# Add Annual Leave record
def add_annual_leave_record(employee, date, status='Annual Leave'):
    df = load_annual_leave_records()

    # Remove existing record for same employee and date
    df = df[~((df['employee_name'] == employee) & (df['date'] == pd.to_datetime(date)))]

    # Add new record
    new_record = pd.DataFrame({
        'employee_name': [employee],
        'date': [pd.to_datetime(date)],
        'status': [status]
    })
    df = pd.concat([df, new_record], ignore_index=True)
    save_annual_leave_records(df)

# Remove Annual Leave record
def remove_annual_leave_record(employee, date):
    df = load_annual_leave_records()
    df = df[~((df['employee_name'] == employee) & (df['date'] == pd.to_datetime(date)))]
    save_annual_leave_records(df)

# Get Annual Leave count per employee
def get_annual_leave_counts():
    df = load_annual_leave_records()
    employees = load_employees()
    employee_names = [emp['name'] for emp in employees]

    if df.empty:
        return pd.DataFrame({'employee_name': employee_names, 'al_days': [0] * len(employee_names)})

    counts = df.groupby('employee_name').size().reset_index(name='al_days')

    # Add employees with 0 AL days
    all_employees = pd.DataFrame({'employee_name': employee_names})
    counts = all_employees.merge(counts, on='employee_name', how='left').fillna(0)
    counts['al_days'] = counts['al_days'].astype(int)

    return counts

# Get WFH count per employee
def get_wfh_counts():
    df = load_wfh_records()
    employees = load_employees()
    employee_names = [emp['name'] for emp in employees]

    if df.empty:
        return pd.DataFrame({'employee_name': employee_names, 'wfh_days': [0] * len(employee_names)})

    counts = df.groupby('employee_name').size().reset_index(name='wfh_days')

    # Add employees with 0 WFH days
    all_employees = pd.DataFrame({'employee_name': employee_names})
    counts = all_employees.merge(counts, on='employee_name', how='left').fillna(0)
    counts['wfh_days'] = counts['wfh_days'].astype(int)

    return counts

# Get office occupancy for date range
def get_office_occupancy(start_date, end_date):
    df_wfh = load_wfh_records()
    df_al = load_annual_leave_records()
    employees = load_employees()
    total_employees = len(employees)

    if total_employees == 0:
        return pd.DataFrame()

    # Filter by date range
    if not df_wfh.empty:
        df_wfh = df_wfh[(df_wfh['date'] >= pd.to_datetime(start_date)) & (df_wfh['date'] <= pd.to_datetime(end_date))]

    if not df_al.empty:
        df_al = df_al[(df_al['date'] >= pd.to_datetime(start_date)) & (df_al['date'] <= pd.to_datetime(end_date))]

    # Count WFH per day
    daily_wfh = df_wfh.groupby('date').size().reset_index(name='wfh_count') if not df_wfh.empty else pd.DataFrame(columns=['date', 'wfh_count'])

    # Count Annual Leave per day
    daily_al = df_al.groupby('date').size().reset_index(name='al_count') if not df_al.empty else pd.DataFrame(columns=['date', 'al_count'])

    # Merge WFH and AL counts
    if not daily_wfh.empty and not daily_al.empty:
        daily_combined = pd.merge(daily_wfh, daily_al, on='date', how='outer').fillna(0)
    elif not daily_wfh.empty:
        daily_combined = daily_wfh.copy()
        daily_combined['al_count'] = 0
    elif not daily_al.empty:
        daily_combined = daily_al.copy()
        daily_combined['wfh_count'] = 0
    else:
        return pd.DataFrame()

    daily_combined['wfh_count'] = daily_combined['wfh_count'].astype(int)
    daily_combined['al_count'] = daily_combined['al_count'].astype(int)
    daily_combined['out_of_office'] = daily_combined['wfh_count'] + daily_combined['al_count']
    daily_combined['in_office'] = total_employees - daily_combined['out_of_office']
    daily_combined['wfh_percentage'] = (daily_combined['wfh_count'] / total_employees * 100).round(1)
    daily_combined['al_percentage'] = (daily_combined['al_count'] / total_employees * 100).round(1)

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

        st.info("ℹ️ Default password for new users is: **1234**")

    st.stop()

# User is logged in - show the application
# Title
st.title("📊 Business Analytics Team Scheduler")
st.markdown("---")

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

    # Show different menus based on role
    if st.session_state.user_role == "Admin":
        page = st.radio("Menu", ["Dashboard", "Schedule WFH", "Schedule Annual Leave", "Manage Employees", "Reports"])
    else:
        # Users only see Dashboard
        page = st.radio("Menu", ["Dashboard"])
        st.info("ℹ️ Contact admin for access to other features")

    st.markdown("---")
    st.markdown("### Quick Stats")
    employees = load_employees()
    st.metric("Total Employees", len(employees))

    df_records = load_wfh_records()
    if not df_records.empty:
        future_wfh = df_records[df_records['date'] >= pd.to_datetime(datetime.now().date())]
        st.metric("Upcoming WFH Days", len(future_wfh))

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
    st.header("📊 Dashboard")

    if not employees:
        st.warning("⚠️ No employees added yet. Go to 'Manage Employees' to add team members.")
    else:
        today = datetime.now().date()

        # WFH & AL Schedule - Calendar View
        st.subheader("📅 WFH & AL Schedule (Current Week + 4 Weeks)")

        # Load both WFH and Annual Leave records
        df_al_records = load_annual_leave_records()

        if not df_records.empty or not df_al_records.empty:
            # Get data from start of current week to 5 weeks ahead
            start_of_week = today - timedelta(days=today.weekday())  # Start from Monday of current week
            calendar_end = start_of_week + timedelta(days=35)  # 5 weeks from start of week

            # Group WFH employees by date
            wfh_by_date = df_records.groupby('date')['employee_name'].apply(list).to_dict()

            # Group Annual Leave employees by date
            al_by_date = df_al_records.groupby('date')['employee_name'].apply(list).to_dict() if not df_al_records.empty else {}

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

                    calendar_html += '</div>'

            calendar_html += '</div>'

            st.markdown(calendar_html, unsafe_allow_html=True)
        else:
            st.info("No WFH or Annual Leave days scheduled")

        # Charts section
        st.markdown("---")

        # Office Occupancy
        st.subheader("Office Occupancy (Next 30 Days)")

        end_date = today + timedelta(days=30)
        occupancy = get_office_occupancy(today, end_date)

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

            fig.update_layout(
                title='Daily Office vs WFH vs Annual Leave',
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
            st.info("No WFH or Annual Leave days scheduled in the next 30 days")

# SCHEDULE WFH PAGE
elif page == "Schedule WFH":
    st.header("📅 Schedule Work From Home")
    
    if not employees:
        st.warning("⚠️ No employees added yet. Go to 'Manage Employees' to add team members.")
    else:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Add WFH Day")

            employee_options = [f"{emp['name']} (ID: {emp['id']})" for emp in employees]
            selected_employee_display = st.selectbox("Select Employee", employee_options)
            # Extract employee name from display string
            selected_employee = selected_employee_display.split(" (ID:")[0]
            selected_date = st.date_input("Select Date", value=datetime.now().date())
            
            # Check current occupancy for that date
            occupancy_check = get_office_occupancy(selected_date, selected_date)
            if not occupancy_check.empty:
                wfh_on_date = occupancy_check.iloc[0]['wfh_count']
                in_office = occupancy_check.iloc[0]['in_office']
                st.info(f"📊 On {selected_date}: **{in_office}** in office, **{wfh_on_date}** working from home")
                
                if in_office <= len(employees) * 0.3:
                    st.warning("⚠️ Warning: Adding this WFH day will result in low office occupancy (<30%)")
            
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("➕ Add WFH Day", type="primary", use_container_width=True):
                    add_wfh_record(selected_employee, selected_date)
                    st.success(f"✅ WFH day added for {selected_employee} on {selected_date}")
                    st.rerun()
            
            with col_b:
                if st.button("🗑️ Remove WFH Day", use_container_width=True):
                    remove_wfh_record(selected_employee, selected_date)
                    st.success(f"✅ WFH day removed for {selected_employee} on {selected_date}")
                    st.rerun()
        
        with col2:
            st.subheader("Quick Stats")
            counts_df = get_wfh_counts()
            employee_count = counts_df[counts_df['employee_name'] == selected_employee]['wfh_days'].values
            
            if len(employee_count) > 0:
                st.metric(f"{selected_employee}'s WFH Days", int(employee_count[0]))
        
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
                calendar_df = calendar_df.sort_values('date')
                calendar_df['date'] = calendar_df['date'].dt.strftime('%Y-%m-%d')
                calendar_df = calendar_df.rename(columns={
                    'employee_name': 'Employee',
                    'date': 'Date',
                    'status': 'Status'
                })

                # Show count
                st.info(f"📋 Showing {len(calendar_df)} WFH record(s) for {view_month.strftime('%B %Y')}")
                st.dataframe(calendar_df, use_container_width=True, hide_index=True)
            else:
                st.info(f"No WFH days recorded for {view_month.strftime('%B %Y')}")
        else:
            st.info("No WFH days scheduled")

# ANNUAL LEAVE PAGE
elif page == "Schedule Annual Leave":
    st.header("🌴 Annual Leave Scheduler")

    if not employees:
        st.warning("⚠️ No employees added yet. Go to 'Manage Employees' to add team members.")
    else:
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("Schedule Annual Leave")

            employee_options = [f"{emp['name']} (ID: {emp['id']})" for emp in employees]
            selected_employee_display = st.selectbox("Select Employee", employee_options, key="al_employee")
            # Extract employee name from display string
            selected_employee = selected_employee_display.split(" (ID:")[0]

            # Get employee's annual leave balance
            selected_emp_obj = next((emp for emp in employees if emp['name'] == selected_employee), None)
            leave_balance = selected_emp_obj.get('annual_leave_balance', 20) if selected_emp_obj else 20

            # Get scheduled leave days for this employee
            al_df = load_annual_leave_records()
            if not al_df.empty:
                emp_scheduled = al_df[al_df['employee_name'] == selected_employee]
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
                st.error(f"⚠️ Warning: {selected_employee} has scheduled more leave days than available!")

            selected_date = st.date_input("Select Date", value=datetime.now().date(), key="al_date")

            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("➕ Add Annual Leave Day", type="primary", use_container_width=True):
                    add_annual_leave_record(selected_employee, selected_date)
                    st.success(f"✅ Annual Leave day added for {selected_employee} on {selected_date}")
                    st.rerun()

            with col_b:
                if st.button("🗑️ Remove Annual Leave Day", use_container_width=True):
                    remove_annual_leave_record(selected_employee, selected_date)
                    st.success(f"✅ Annual Leave day removed for {selected_employee} on {selected_date}")
                    st.rerun()

        with col2:
            st.subheader("Quick Stats")
            al_counts_df = get_annual_leave_counts()
            employee_al_count = al_counts_df[al_counts_df['employee_name'] == selected_employee]['al_days'].values

            if len(employee_al_count) > 0:
                st.metric(f"{selected_employee}'s AL Days", int(employee_al_count[0]))

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
                calendar_df = calendar_df.sort_values('date')
                calendar_df['date'] = calendar_df['date'].dt.strftime('%Y-%m-%d')
                calendar_df = calendar_df.rename(columns={
                    'employee_name': 'Employee',
                    'date': 'Date',
                    'status': 'Status'
                })

                # Show count
                st.info(f"📋 Showing {len(calendar_df)} Annual Leave record(s) for {view_month.strftime('%B %Y')}")
                st.dataframe(calendar_df, use_container_width=True, hide_index=True)
            else:
                st.info(f"No Annual Leave days recorded for {view_month.strftime('%B %Y')}")
        else:
            st.info("No Annual Leave days scheduled")

# MANAGE EMPLOYEES PAGE
elif page == "Manage Employees":
    st.header("👥 Manage Employees")

    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        st.subheader("Add New Employee")
        new_employee = st.text_input("Employee Name")
        new_employee_id = st.text_input("Employee ID (4 characters)", max_chars=4)
        new_annual_leave = st.number_input("Annual Leave Balance (days)", min_value=0, max_value=365, value=20, step=1)
        new_password = st.text_input("Password", value="1234", type="password", key="new_password")
        new_role = st.selectbox("Role", ["User", "Admin"])

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
                        'annual_leave_balance': new_annual_leave,
                        'password': hash_password(new_password),
                        'role': new_role
                    })
                    save_employees(employees)
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
                # Display current values
                st.info(f"**Current Name:** {selected_emp['name']}  \n**Current ID:** {selected_emp['id'] if selected_emp['id'] else 'Not Set'}  \n**Role:** {selected_emp.get('role', 'User')}  \n**Annual Leave:** {selected_emp.get('annual_leave_balance', 20)} days")

                # Use unique keys based on employee name to reset fields when selection changes
                edited_name = st.text_input("New Name", value=selected_emp['name'], key=f"edit_name_{selected_emp_name}")
                edited_id = st.text_input("New ID (4 characters)", value=selected_emp['id'] if selected_emp['id'] else "", max_chars=4, key=f"edit_id_{selected_emp_name}")
                edited_leave = st.number_input("Annual Leave Balance (days)", min_value=0, max_value=365, value=selected_emp.get('annual_leave_balance', 20), step=1, key=f"edit_leave_{selected_emp_name}")
                edited_password = st.text_input("New Password (leave empty to keep current)", type="password", key=f"edit_password_{selected_emp_name}")
                edited_role = st.selectbox("Role", ["User", "Admin"], index=0 if selected_emp.get('role', 'User') == 'User' else 1, key=f"edit_role_{selected_emp_name}")

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
                        # Update WFH and AL records if name changed
                        if edited_name != selected_emp['name']:
                            df_wfh = load_wfh_records()
                            df_wfh.loc[df_wfh['employee_name'] == selected_emp['name'], 'employee_name'] = edited_name
                            save_wfh_records(df_wfh)

                            df_al = load_annual_leave_records()
                            df_al.loc[df_al['employee_name'] == selected_emp['name'], 'employee_name'] = edited_name
                            save_annual_leave_records(df_al)

                        # Update employee record
                        for emp in employees:
                            if emp['name'] == selected_emp['name']:
                                emp['name'] = edited_name
                                emp['id'] = edited_id
                                emp['annual_leave_balance'] = edited_leave
                                emp['role'] = edited_role
                                # Update password only if new one is provided
                                if edited_password:
                                    emp['password'] = hash_password(edited_password)
                                break

                        save_employees(employees)
                        st.success(f"✅ Updated employee to {edited_name} (ID: {edited_id}, Role: {edited_role}, Leave: {edited_leave} days)")
                        st.rerun()
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
                employees = [emp for emp in employees if emp['name'] != emp_name]
                save_employees(employees)

                # Also remove their WFH records
                df = load_wfh_records()
                df = df[df['employee_name'] != emp_name]
                save_wfh_records(df)

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
    st.header("📈 Reports & Analytics")
    
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
                    unique_employees = period_records['employee_name'].nunique()
                    st.metric("Employees Using WFH", unique_employees)
                
                with col_c:
                    avg_per_employee = len(period_records) / len(employees)
                    st.metric("Avg WFH Days/Employee", f"{avg_per_employee:.1f}")
                
                st.markdown("---")
                
                # Detailed breakdown
                st.subheader("Detailed Breakdown by Employee")

                employee_stats = period_records.groupby('employee_name').agg({
                    'date': 'count'
                }).reset_index()
                employee_stats.columns = ['Employee', 'WFH Days']
                employee_stats = employee_stats.sort_values('WFH Days', ascending=False)

                # Add employees with 0 days and include IDs
                all_emp = pd.DataFrame([
                    {'Employee': emp['name'], 'Employee ID': emp['id']}
                    for emp in employees
                ])
                employee_stats = all_emp.merge(employee_stats, on='Employee', how='left').fillna(0)
                employee_stats['WFH Days'] = employee_stats['WFH Days'].astype(int)

                st.dataframe(employee_stats, use_container_width=True, hide_index=True)

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
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        'Monday': st.column_config.NumberColumn('Monday', format='%d', help='WFH count on Monday'),
                        'Tuesday': st.column_config.NumberColumn('Tuesday', format='%d', help='WFH count on Tuesday'),
                        'Wednesday': st.column_config.NumberColumn('Wednesday', format='%d', help='WFH count on Wednesday'),
                        'Thursday': st.column_config.NumberColumn('Thursday', format='%d', help='WFH count on Thursday'),
                        'Friday': st.column_config.NumberColumn('Friday', format='%d', help='WFH count on Friday'),
                        'Total': st.column_config.NumberColumn('Total', format='%d', help='Total WFH days')
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
                emp_al_records = al_df[al_df['employee_name'] == emp_name]
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

        st.dataframe(
            balance_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                'Leave Balance': st.column_config.NumberColumn('Leave Balance', format='%d days'),
                'Scheduled': st.column_config.NumberColumn('Scheduled', format='%d days'),
                'Remaining': st.column_config.NumberColumn('Remaining', format='%d days')
            }
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

# Footer
st.markdown("---")
st.markdown("*Business Analytics Team Scheduler - Manage the team's Annual Leave and Work-from-home days efficiently*")