# Admin Dashboard

Complete guide to the Admin Dashboard for user management, system monitoring, and action auditing.

## Overview

The Admin Dashboard provides administrative tools for managing the application:

- **User Management**: Create, edit, delete, and manage user accounts
- **Admin Logging**: Audit trail of all administrative actions
- **System Metrics**: Real-time statistics and monitoring
- **Role-Based Access**: Admin-only features with proper access control

> **Access**: Admin Dashboard is restricted to users with `is_admin=True`

---

## Features

### User Management

| Feature | Description |
|---------|-------------|
| **List Users** | Paginated user list (20 per page) |
| **Create User** | Add new users with all details |
| **View User** | See user details and action history |
| **Edit User** | Update user information and status |
| **Change Password** | Reset any user's password |
| **Delete User** | Remove user (with self-delete protection) |
| **Activate/Deactivate** | Toggle user active status |
| **Admin Promotion** | Grant or revoke admin privileges |

### Admin Action Logging

All administrative actions are automatically logged:

| Action | Logged Details |
|--------|----------------|
| `CREATE_USER` | Who created, new username |
| `UPDATE_USER` | Who updated, what changed |
| `DELETE_USER` | Who deleted, deleted username |
| `CHANGE_PASSWORD` | Who changed, target user |

Each log entry includes:
- Timestamp
- Admin user who performed action
- Target user affected
- Action details
- IP address
- User agent

### System Metrics

| Metric | Description |
|--------|-------------|
| `total_users` | Total registered users |
| `active_users` | Users with `is_active=True` |
| `admin_users` | Users with `is_admin=True` |
| `recent_users` | Users created in last 30 days |
| `recent_logins` | Users logged in within 7 days |

---

## Getting Started

### Requirements

1. **Admin Account**: You must have `is_admin=True` to access
2. **Login**: Be logged in to the application

### Accessing the Dashboard

1. Log in with an admin account
2. Navigate to `/admin`
3. View system statistics and recent actions
4. Use navigation to access other admin features

---

## Usage Guide

### Dashboard Overview

The main dashboard (`/admin`) shows:
- User statistics (total, active, admin, recent)
- Recent admin actions (last 10)
- Quick links to management features

### Managing Users

**View All Users**:
1. Navigate to `/admin/users`
2. Browse paginated user list
3. See username, email, status, admin status
4. Click any user for details

**Create a User**:
1. Navigate to `/admin/users/create`
2. Fill in required fields:
   - **Username**: Unique username
   - **Email**: Valid email address
   - **Password**: Secure password
   - **Confirm Password**: Match password
3. Optional fields:
   - **First Name** / **Last Name**
   - **Is Active**: Enable account immediately
   - **Is Admin**: Grant admin access
4. Click "Create User"

**Edit a User**:
1. Find user in `/admin/users`
2. Click to view user details
3. Click "Edit"
4. Update fields as needed
5. Save changes

**Change User Password**:
1. View the user's details
2. Click "Change Password"
3. Enter new password (twice)
4. Submit

**Delete a User**:
1. View the user's details
2. Click "Delete"
3. Confirm deletion
4. **Note**: Cannot delete your own account

### Viewing Admin Logs

1. Navigate to `/admin/logs`
2. Browse paginated log entries (50 per page)
3. See who did what and when
4. Filter by action type if needed

---

## Technical Details

### Database Models

**AdminLog** (`admin_logs` table):

| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer | Primary key |
| `admin_user_id` | Integer | Admin who performed action |
| `action` | String(100) | Action type |
| `target_user_id` | Integer | Affected user (nullable) |
| `details` | Text | Action description |
| `ip_address` | String(45) | Client IP |
| `user_agent` | Text | Browser/client info |
| `created_at` | DateTime | When action occurred |

**SystemMetrics** (`system_metrics` table):

| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer | Primary key |
| `metric_name` | String(100) | Unique metric name |
| `metric_value` | Float | Metric value |
| `metric_data` | Text | Optional JSON data |

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/admin` | GET | Dashboard with statistics |
| `/admin/users` | GET | Paginated user list |
| `/admin/users/create` | GET, POST | Create user form/action |
| `/admin/users/<id>` | GET | View user details |
| `/admin/users/<id>/edit` | GET, POST | Edit user form/action |
| `/admin/users/<id>/change-password` | GET, POST | Change password |
| `/admin/users/<id>/delete` | POST | Delete user |
| `/admin/logs` | GET | Paginated admin logs |
| `/admin/stats` | GET | System stats (JSON) |

### Access Control

The `admin_required` decorator enforces:
1. User must be authenticated
2. User must have `is_admin=True`
3. Non-admins are redirected with error message

```python
@login_required
@admin_required
def admin_only_route():
    # Only admins reach here
    pass
```

---

## Security Features

### Self-Protection

- Admins **cannot delete their own account**
- Prevents accidental lockout

### Audit Trail

- **All actions logged** with timestamps
- **IP address tracked** for security
- **User agent captured** for forensics
- **Logs persist** even after user deletion

### Password Security

- Passwords hashed with Werkzeug
- Never stored or logged in plain text
- Secure password change workflow

---

## Best Practices

1. **Use Descriptive Usernames**: Make accounts identifiable
2. **Review Logs Regularly**: Monitor for unusual activity
3. **Limit Admin Access**: Only grant admin to trusted users
4. **Deactivate vs Delete**: Prefer deactivation for audit purposes
5. **Strong Passwords**: Enforce when creating users
6. **Monitor Recent Activity**: Check dashboard regularly

---

## Troubleshooting

### Can't access admin dashboard

- Verify your account has `is_admin=True`
- Check that you're logged in
- Clear browser cache if issues persist

### User creation fails

- Check for duplicate username or email
- Ensure password meets requirements
- Verify all required fields are filled

### Can't delete a user

- Verify you're not trying to delete yourself
- Check for database errors in logs

### Admin logs not appearing

- Actions are logged automatically
- Check database connection
- Verify the action completed successfully

---

## Related Documentation

- [Architecture Overview](ARCHITECTURE.md) - System architecture
- [Features Overview](FEATURES.md) - All features
