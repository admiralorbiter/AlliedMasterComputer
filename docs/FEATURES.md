# Features Overview

This document catalogs all major features of the Allied Master Computer application.

---

## Feature Summary

| Feature | Status | Documentation |
|---------|--------|---------------|
| [Authentication & Admin](#authentication--admin) | ✅ Complete | — |
| [Research Briefs](#research-briefs) | ✅ Complete | [research-brief-generator.md](research-brief-generator.md) |
| [Music Library](#music-library) | ✅ Complete | [music-library.md](music-library.md) |
| [Projects](#projects) | ✅ Complete | [projects.md](projects.md) |
| [Goals](#goals) | ✅ Complete | [goals.md](goals.md) |
| [Todo & Events](#todo--events) | ✅ Complete | [todo-events.md](todo-events.md) |
| [Infrastructure](#infrastructure) | ✅ Complete | — |

---

## Authentication & Admin

### User Authentication
- **Login/Logout**: Session-based authentication with Flask-Login
- **Password Security**: Werkzeug password hashing
- **Role-Based Access**: User and Admin roles
- **Protected Routes**: Login required for all features

### Admin Dashboard
- **User Management**: Create, edit, delete, activate/deactivate users
- **Password Reset**: Admin can change any user's password
- **User Viewing**: View user details and activity
- **System Stats**: Real-time system metrics via API

### Admin Logging
- **Action Audit**: All admin actions are logged
- **Log Viewing**: Paginated admin action history
- **Accountability**: Tracks who did what and when

**Routes**: `/admin/*`

---

## Research Briefs

> 📘 **[Full Documentation](research-brief-generator.md)**

AI-powered research document analysis using OpenAI.

### Key Capabilities
- **PDF Upload**: Extract text from PDFs (up to 25MB)
- **Text Input**: Direct text pasting for analysis
- **AI Analysis**: Generates structured briefs with:
  - Descriptive titles
  - Formatted citations
  - Organized summaries (Key Findings, Main Points, Methodology, Conclusions)
- **Tagging System**: Organize briefs with tags
- **PDF Download**: Retrieve original uploaded PDFs

### Workflow
1. Upload PDF or paste text
2. AI generates structured brief
3. Review and edit as needed
4. Tag and organize
5. Download original PDFs

**Routes**: `/research/*`

---

## Music Library

Personal music library with Spotify integration.

### Core Features
- **Song Library**: Paginated, searchable music collection
- **Song Details**: Modal view with full metadata
- **CSV Import**: Bulk import songs from CSV files
- **Background Processing**: Import jobs run asynchronously with status tracking

### Playlist Management
- **Create/Edit/Delete**: Full playlist CRUD
- **Add/Remove Songs**: Manage playlist contents
- **Drag & Drop Reorder**: Reorder songs within playlists
- **Bulk Add**: Add multiple songs at once

### Spotify Integration
- **OAuth Flow**: Secure Spotify account connection (admin-only setup)
- **Import Playlists**: Pull Spotify playlists into local library
- **Export Playlists**: Push local playlists to Spotify
- **Track Matching**: Matches local songs to Spotify tracks

**Routes**: `/music/*`

---

## Projects

Comprehensive project management system.

### Project Features
- **Project CRUD**: Create, update, delete projects
- **Status Tracking**: Mark projects with status
- **Description**: Rich project descriptions
- **List & Detail Views**: Browse and dive into projects

### Project Notes
- **Rich Notes**: Create notes attached to projects
- **Edit/Delete**: Full note management
- **Timestamps**: Track when notes were created/updated

### Project Links
- **URL Bookmarks**: Save relevant links per project
- **Titles & URLs**: Named link references
- **Quick Access**: All project resources in one place

### Research Brief Linking
- **Link Briefs**: Associate research briefs with projects
- **Unlink Briefs**: Remove associations
- **Cross-Reference**: View related research from project detail

### Project Todos
- **Task Lists**: Create todos within projects
- **Toggle Complete**: Mark tasks done/undone
- **Subtasks**: Break down todos into subtasks
- **Priority & Due Dates**: Organize by importance

**Routes**: `/projects/*`

---

## Goals

Personal goal tracking with project alignment.

### Goal Features
- **Goal CRUD**: Create, update, delete goals
- **Completion Toggle**: Mark goals complete/incomplete
- **Description**: Detailed goal descriptions
- **Project Linking**: Associate goals with projects
- **Todo Linking**: Link related tasks to goals

### Goal Views
- **List View**: All goals with status
- **JSON API**: Programmatic access to goals data

**Routes**: `/goals/*`

---

## Todo & Events

Task and event management system.

### Todo Features
- **Task CRUD**: Create, update, delete todos
- **Toggle Complete**: Quick completion toggle
- **Priority Levels**: Organize by importance
- **Due Dates**: Time-based organization
- **Goal Association**: Link todos to goals

### Subtasks
- **Nested Tasks**: Break todos into subtasks
- **Independent Toggle**: Complete subtasks separately
- **Subtask CRUD**: Full management

### Events
- **Event CRUD**: Create, update, delete events
- **Date/Time**: Scheduled events with times
- **Event Processing**: Handle past events with actions
- **Goal Association**: Link events to goals

### Single-Page Interface
- Combined todo and event management
- AJAX-powered for smooth interaction
- No page reloads for common actions

**Routes**: `/todo/*`

---

## Infrastructure

Backend services powering the application.

### Logging (`logging_config.py`)
- **Structured Logs**: JSON-formatted for parsing
- **Multiple Handlers**: Console, file, structured
- **Request Context**: Automatic user/request injection
- **File Rotation**: 10MB files, 5 backups
- **Security Logging**: Dedicated security event logging

### Monitoring (`monitoring.py`)
- **Health Checks**:
  - `/health` - Basic (load balancers)
  - `/health/detailed` - System metrics
  - `/health/ready` - Kubernetes readiness
  - `/health/live` - Kubernetes liveness
- **Performance Metrics**: Request timing, error rates
- **System Resources**: CPU, memory, disk (via psutil)

### Error Alerting (`error_handler.py`)
- **Multi-Channel**: Email, Slack, webhooks
- **Rate Limiting**: Prevents alert fatigue
- **Severity Levels**: Route by importance
- **Rich Context**: Full error details in alerts

### Configuration
- **Environment-Based**: Dev, Test, Prod configs
- **Monitoring Config**: Separate monitoring settings
- **External Keys**: `.env` file support

---

## API Patterns

### Common Patterns Across Features

| Pattern | Description |
|---------|-------------|
| **AJAX Support** | Most routes return JSON when requested via AJAX |
| **User Isolation** | Users only access their own data |
| **Flash Messages** | User feedback via Flask flash system |
| **Form Validation** | WTForms with CSRF protection |
| **Pagination** | List views are paginated |
| **Soft Updates** | Last-modified timestamps on edits |

### JSON Endpoints

Most list and toggle operations have JSON counterparts:
- `GET /goals/list/json` - Goals as JSON
- `POST /todo/<id>/toggle` - Returns JSON status
- `GET /projects/list/json` - Projects as JSON

---

## Documentation Complete

All major features now have comprehensive documentation:

| Feature | Documentation |
|---------|---------------|
| Music Library | [music-library.md](music-library.md) |
| Projects & Notes | [projects.md](projects.md) |
| Goals System | [goals.md](goals.md) |
| Todo & Events | [todo-events.md](todo-events.md) |
| Admin Dashboard | [admin-dashboard.md](admin-dashboard.md) |
| Research Briefs | [research-brief-generator.md](research-brief-generator.md) |

**Potential Future Additions:**
- API reference
- Developer setup guide

---

## Related Documentation

- [Architecture Overview](ARCHITECTURE.md) - System architecture
- [Research Brief Generator](research-brief-generator.md) - AI feature details
- [Main README](../README.md) - Setup and installation
