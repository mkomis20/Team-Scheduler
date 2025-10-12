# Business Analytics Team Scheduler

A comprehensive Streamlit-based web application for managing team Work From Home (WFH) schedules, Annual Leave tracking, and Seminar attendance for the Business Analytics Team.

## Recent Updates

### 🆕 Latest Features

- **Month Navigation**: Calendar now supports browsing through different months with arrow buttons
- **Date Range Selection**: Schedule multiple days at once for WFH, Annual Leave, and Seminars
- **Conflict Detection**: System prevents overlapping entries - removes need to manually track conflicts
- **Optimized UI**: Compact table layouts and combined page titles save screen space
- **Enhanced Reports**: Fixed-width tables for professional appearance and better readability

## Features

### User Authentication

- Secure login system with password hashing (SHA-256)
- Role-based access control (Admin/User roles)
- Password change functionality
- Default password for new users: `1234`

### Dashboard

- Interactive calendar view showing WFH, Annual Leave, and Seminar schedules
- **Month navigation**: Browse previous and future months with arrow buttons ◀ ▶
- 5-week calendar display starting from selected month
- Office occupancy visualization with stacked area charts
- Low occupancy alerts (below 30% threshold)
- Color-coded schedule indicators:
  - Green: Work From Home (WFH:)
  - Red: Annual Leave (AL:)
  - Blue: Seminar attendance (S:)
  - Gray: Past events

### WFH Scheduling (Admin Only)

- Schedule and remove WFH days for team members
- **Date range support**: Select single date or date range for batch scheduling
- **Conflict detection**: Prevents overlapping entries with Annual Leave or Seminars
- Monthly calendar view of WFH records
- Real-time occupancy checks when scheduling
- Warnings for low office occupancy
- Employee-specific WFH day counters

### Annual Leave Management (Admin Only)

- Schedule and track annual leave for all employees
- **Date range support**: Select single date or date range for batch scheduling
- **Conflict detection**: Prevents overlapping entries with WFH or Seminars
- **Balance warnings**: Alerts when scheduling exceeds available leave balance
- Leave balance tracking per employee
- Visual indicators for over-scheduled leave
- Monthly calendar view of annual leave records
- Automatic calculation of remaining leave days

### Seminar Attendance Tracking (Admin Only)

- Schedule and track team member attendance at seminars and training events
- **Date range support**: Perfect for multi-day conferences and training programs
- **Conflict detection**: Prevents overlapping entries with WFH or Annual Leave
- Record seminar names and dates
- Monthly calendar view of seminar schedules
- Employee-specific seminar attendance counters
- Seminar history tracking with full details

### Employee Management (Admin Only)

- Add new employees with customizable:
  - Name and 4-character Employee ID
  - Annual leave balance (default: 20 days)
  - Password and role assignment
- Edit existing employee information
- Remove employees (cascades to WFH/AL/Seminar records)
- View complete team roster with leave balances

### Reports & Analytics (Admin Only)

- **Optimized table layouts**: Fixed-width tables for better readability
- Comprehensive WFH summary reports with date range filtering
- Employee-specific WFH usage statistics
- WFH distribution by day of week (Monday-Friday)
- Annual leave balance reports with visual indicators
- Seminar attendance reports:
  - Total seminar days per employee
  - Unique seminars attended
  - Detailed seminar records with dates and names
- Visual charts and graphs:
  - WFH days per employee
  - Leave balance vs scheduled comparison
  - Remaining leave visualization
  - Seminar attendance per employee
- CSV export functionality for WFH records

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Required Dependencies

```bash
pip install streamlit pandas plotly
```

Or install from requirements file (if available):

```bash
pip install -r requirements.txt
```

## Usage

### Starting the Application

Navigate to the application directory and run:

```bash
streamlit run app.py
```

The application will open in your default web browser at `http://localhost:8501`

### First-Time Setup

1. **Initial Login**: Log in with an existing employee account or have an admin add you
2. **Default Credentials**: New users have password `1234` (change immediately after first login)
3. **Admin Access**: The first user "Marios Team" is set as Admin by default in the code

### User Roles

**Admin Role:**

- Full access to all features
- Can schedule WFH, Annual Leave, and Seminars
- Can manage employees (add, edit, remove)
- Can view detailed reports and analytics

**User Role:**

- Read-only access to Dashboard
- Can view team schedules, office occupancy, and seminar attendance
- Cannot modify schedules or manage employees

## Data Storage

The application uses local file storage with the following structure:

```
wfh_data/
├── employees.json           # Employee information (names, IDs, passwords, roles, leave balances)
├── wfh_records.csv          # Work From Home schedule records
├── annual_leave_records.csv # Annual Leave schedule records
└── seminar_records.csv      # Seminar attendance records (with seminar names)
```

These files are automatically created on first run.

## Key Functionalities

### Office Occupancy Tracking

- Real-time calculation of in-office vs remote staff
- Accounts for WFH, Annual Leave, and Seminar attendance
- Automatic alerts when office occupancy falls below 30%
- 30-day forward-looking occupancy chart with all absence types

### Leave Balance Management

- Tracks annual leave balance per employee
- Displays scheduled vs remaining leave days
- Alerts for over-scheduled employees (negative balance)

### Seminar Tracking

- Track all team member seminar and training attendance
- Record seminar names for each attendance
- View seminar history per employee
- Analyze training participation across the team

### Calendar Integration

- Visual calendar displays for WFH, Annual Leave, and Seminars
- Month navigation with arrow buttons (◀ ▶)
- Color-coded status indicators (Green=WFH, Red=AL, Blue=Seminar)
- Historical data retention (past events shown in gray/muted colors)

### Conflict Prevention

- **Automatic validation**: System checks for existing entries before allowing new ones
- **Clear error messages**: Shows exactly which dates conflict and what type of entry exists
- **Forced resolution**: Users must remove existing entry before adding a new type
- **Smart updates**: Allows updating same entry type (e.g., changing WFH date is allowed)

## Security Features

- Password hashing using SHA-256
- Session-based authentication
- Role-based access control
- No plain-text password storage

## Customization

### Changing the Default Admin

Edit line 59 in [app.py](app.py#L59) to set a different default admin:

```python
emp['role'] = 'Admin' if emp['name'] == 'Your Name' else 'User'
```

### Adjusting Default Leave Balance

Modify the default annual leave balance (default: 20 days) in the employee management section.

### Low Occupancy Threshold

Change the 30% threshold in [app.py:558](app.py#L558) and [app.py:589](app.py#L589):

```python
low_occupancy = occupancy[occupancy['in_office'] < len(employees) * 0.3]  # Change 0.3 to desired threshold
```

## Troubleshooting

### Common Issues

**Application won't start:**

- Ensure all dependencies are installed: `pip install streamlit pandas plotly`
- Check Python version: `python --version` (should be 3.7+)

**Can't log in:**

- Default password for all new users is `1234`
- Check that employees.json exists in wfh_data folder
- Contact admin to reset your password

**Data not saving:**

- Ensure write permissions in the application directory
- Check that wfh_data folder is created and accessible

**Charts not displaying:**

- Verify plotly is installed: `pip install plotly`
- Clear browser cache and refresh

## Best Practices

1. **Regular Backups**: Backup the `wfh_data/` folder regularly
2. **Password Changes**: Change default passwords immediately after account creation
3. **Leave Planning**: Schedule annual leave well in advance
4. **Office Coordination**: Monitor occupancy alerts to maintain minimum office presence
5. **Data Export**: Regularly export CSV reports for record-keeping

## Technical Stack

- **Framework**: Streamlit
- **Data Processing**: Pandas
- **Visualizations**: Plotly (Express & Graph Objects)
- **Storage**: JSON and CSV files
- **Security**: Hashlib (SHA-256)

## License

This application is for internal team use by the Business Analytics Team.

## Support

For issues, feature requests, or questions, contact your system administrator or the application developer.

---

_Business Analytics Team Scheduler - Manage the team's Annual Leave, Work-from-home days, and Seminar attendance efficiently_
