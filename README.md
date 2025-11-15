# Business Analytics Team Scheduler

A comprehensive Streamlit-based web application for managing team Work From Home (WFH) schedules, Annual Leave tracking, and Seminar attendance for the Business Analytics Team.

## Recent Updates (v2.1.4 - Sunday 16/11/2025)

### 🆕 Latest Features

- **Backup & Export Screen**: New admin-only screen to backup and export all CSV data for record-keeping
- **Individual and Bulk Export**: Export WFH records, Annual Leave, Seminars, and Leave Balances individually or as complete backup
- **Timestamped Backups**: All exports include timestamps for version tracking and organization
- **Fixed Leave Balance Persistence**: Resolved critical bug where migration code was overwriting updated balances
- **Previous Updates**: Role-Based Access Control, Configure Roles, Enhanced Permissions, Scrollable Occupancy, Security improvements

## Features

### User Authentication

- Secure login system with password hashing (SHA-256)
- Role-based access control with configurable permissions
- Password change functionality
- Default password for new users: `1234` (displayed only during employee creation)

### Dashboard

- Interactive calendar view showing WFH, Annual Leave, and Seminar schedules
- **Month navigation**: Browse previous and future months with arrow buttons ◀ ▶ (calendar and occupancy chart)
- 5-week calendar display starting from selected month
- **Scrollable office occupancy**: Navigate through different months in occupancy chart with arrow buttons
- Office occupancy visualization with stacked area charts
- Low occupancy alerts (below 30% threshold)
- Color-coded schedule indicators:
  - Green: Work From Home (WFH:)
  - Red: Annual Leave (AL:)
  - Blue: Seminar attendance (S:)
  - Gray: Past events

### WFH Scheduling

**User Access**: Users can schedule their own WFH days
**Admin Access**: Can schedule WFH days for all team members

- Schedule and remove WFH days
- **Date range support**: Select single date or date range for batch scheduling
- **Conflict detection**: Prevents overlapping entries with Annual Leave or Seminars
- Monthly calendar view of WFH records
- Real-time occupancy checks when scheduling
- Warnings for low office occupancy
- Employee-specific WFH day counters

### Annual Leave Management

**User Access**: Users can schedule their own annual leave
**Admin Access**: Can schedule annual leave for all team members

- Schedule and track annual leave
- **Date range support**: Select single date or date range for batch scheduling
- **Conflict detection**: Prevents overlapping entries with WFH or Seminars
- **Balance warnings**: Alerts when scheduling exceeds available leave balance
- Leave balance tracking per employee
- Visual indicators for over-scheduled leave
- Monthly calendar view of annual leave records
- Automatic calculation of remaining leave days

### Seminar Attendance Tracking

**User Access**: Users can register themselves for seminars
**Admin Access**: Can register any team member for seminars

- Schedule and track seminar attendance
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
  - Password, role assignment, and screen permissions
- Edit existing employee information including screen permissions
- Remove employees (cascades to WFH/AL/Seminar records)
- View complete team roster with leave balances

### Configure Roles (Admin Only)

- Manage default role permissions for Admin and User roles
- Configure which screens are available for each role
- View current permissions for all roles
- Customize permissions for specific roles
- Individual user permissions override role defaults
- Persistent configuration saved across sessions

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

### Backup & Export (Admin Only)

- **Individual exports**: Download specific data types as CSV files
  - Export WFH Records with full scheduling history
  - Export Annual Leave Records with all leave entries
  - Export Seminar Attendance Records with seminar names and dates
  - Export Leave Balances for each employee
- **Complete Backup**: Single-file backup containing all data
  - Combines all records into one downloadable file
  - Includes backup summary with record counts and timestamp
  - Perfect for system backups and disaster recovery
- **Timestamped Files**: All exports include date/time stamps for version control
- **Recommended Use**:
  - Daily backups for active teams
  - Weekly backups for minimal activity
  - Before system updates or migrations
  - Regular testing of restoration procedures

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

### User Roles & Permissions

**Admin Role (Default Permissions):**

- Access to: Dashboard, Reports, Schedule WFH, Schedule Annual Leave, Schedule Seminars, Manage Employees, Configure Roles, Backup & Export
- Can schedule WFH, Annual Leave, and Seminars for any team member
- Can manage employees (add, edit, remove) and customize their permissions
- Can view detailed reports and analytics
- Can configure default role permissions
- Can backup and export all system data for record-keeping and disaster recovery

**User Role (Default Permissions):**

- Access to: Dashboard, Schedule WFH, Schedule Annual Leave, Schedule Seminars
- Can schedule WFH, Annual Leave, and Seminars for themselves only
- Cannot view Reports or manage employees
- Cannot access Configure Roles

**Custom Permissions:**
- Admins can customize screen permissions for individual users
- Individual user permissions override their role's default permissions

## Data Storage

The application uses local file storage with the following structure:

```
wfh_data/
├── employees.json             # Employee information (names, IDs, passwords, roles, screen permissions, leave balances)
├── wfh_records.csv            # Work From Home schedule records
├── annual_leave_records.csv   # Annual Leave schedule records
├── seminar_records.csv        # Seminar attendance records (with seminar names)
└── role_permissions.json      # Default role permissions configuration (new in v2.1.3)
```

These files are automatically created on first run. The `role_permissions.json` file stores the default screen permissions for each role.

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
