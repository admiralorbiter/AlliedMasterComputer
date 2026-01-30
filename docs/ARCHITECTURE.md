# Architecture Overview

This document provides a high-level architectural overview of the Allied Master Computer application.

## Technology Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3.8+, Flask |
| **Database** | SQLAlchemy ORM, SQLite (dev) / PostgreSQL (prod) |
| **Authentication** | Flask-Login, Werkzeug password hashing |
| **Frontend** | Jinja2 templates, HTML/CSS/JavaScript |
| **AI Integration** | OpenAI API (GPT-4) |
| **External APIs** | Spotify Web API (OAuth 2.0) |
| **Migrations** | Flask-Migrate (Alembic) |

---

## Application Structure

```
AlliedMasterComputer/
├── app.py                      # Application entry point & factory
├── config/                     # Configuration modules
│   ├── __init__.py            # Base configs (Dev/Test/Prod)
│   └── monitoring.py          # Monitoring-specific configs
├── flask_app/                  # Main application package
│   ├── forms/                 # WTForms definitions
│   ├── models/                # SQLAlchemy models
│   ├── routes/                # Blueprint route handlers
│   └── utils/                 # Utility services
├── templates/                  # Jinja2 templates
├── static/                     # CSS, JS, images
├── tests/                      # Test suite
├── migrations/                 # Alembic database migrations
└── docs/                       # Documentation
```

---

## Core Components

### 1. Application Factory (`app.py`)

The entry point initializes all Flask extensions and services:

- **Database**: SQLAlchemy with Flask-Migrate
- **Authentication**: Flask-Login with user session management
- **Logging**: Structured logging with file rotation
- **Monitoring**: Health checks and performance tracking
- **Error Alerting**: Multi-channel error notifications

### 2. Configuration System (`config/`)

Environment-based configuration with three profiles:

| Profile | Use Case |
|---------|----------|
| `DevelopmentConfig` | Local development with debug mode |
| `TestingConfig` | Automated test runs |
| `ProductionConfig` | Production deployment |

Set via `FLASK_ENV` environment variable.

### 3. Database Models (`flask_app/models/`)

SQLAlchemy models organized by domain:

| Model | Purpose |
|-------|---------|
| `User` | User accounts with role-based access |
| `AdminLog` | Admin action audit trail |
| `SystemMetrics` | Performance metrics storage |
| `ResearchBrief` | AI-generated research summaries |
| `Tag` | Tagging system for research briefs |
| `Song` | Music library entries |
| `Playlist` | User playlists with song associations |
| `MusicImportJob` | Background CSV import tracking |
| `SpotifyAuth` | OAuth token storage |
| `Project` | Project containers |
| `ProjectNote` | Rich text notes for projects |
| `ProjectLink` | URL bookmarks for projects |
| `Goal` | Personal goals with project linking |
| `Todo` | Task items with priority/due dates |
| `SubTask` | Nested subtasks under todos |
| `Event` | Calendar events with time tracking |

**Base Model Pattern**: All models inherit from `BaseModel` which provides:
- `id` (primary key)
- `created_at` / `updated_at` timestamps
- Common utility methods

### 4. Route Handlers (`flask_app/routes/`)

Modular route registration pattern:

| Module | Prefix | Description |
|--------|--------|-------------|
| `auth.py` | `/` | Login, logout, authentication |
| `admin.py` | `/admin` | User management, logs, stats |
| `research.py` | `/research` | Research brief CRUD, tagging |
| `music.py` | `/music` | Library, playlists, Spotify |
| `projects.py` | `/projects` | Project management, notes, links |
| `goals.py` | `/goals` | Goal tracking |
| `todo.py` | `/todo` | Tasks, subtasks, events |
| `main.py` | `/` | Home page, static routes |

**Route Pattern**: Each module exports a `register_*_routes(app)` function called during initialization.

### 5. Utility Services (`flask_app/utils/`)

| Module | Purpose |
|--------|---------|
| `openai_service.py` | OpenAI API integration for research briefs |
| `spotify_service.py` | Spotify API client with OAuth handling |
| `music_importer.py` | Background CSV import processor |
| `logging_config.py` | Structured logging with JSON support |
| `monitoring.py` | Health checks, performance metrics |
| `error_handler.py` | Multi-channel error alerting |
| `html_sanitizer.py` | Safe HTML content processing |

---

## Infrastructure Services

### Logging System

Multi-handler logging with:
- **Console**: Development debugging
- **File**: Rotating file logs (10MB, 5 backups)
- **JSON**: Structured logs for parsing
- **Request Context**: Automatic user/request ID injection

### Monitoring System

Two core components:

1. **HealthChecker**: Exposes health endpoints
   - `/health` - Basic health (load balancers)
   - `/health/detailed` - Full system status
   - `/health/ready` - Kubernetes readiness
   - `/health/live` - Kubernetes liveness

2. **PerformanceMonitor**: Tracks request metrics
   - Response times
   - Error rates by endpoint
   - Resource utilization

### Error Alerting

`ErrorAlertingSystem` with configurable channels:
- **Email**: SMTP-based alerts
- **Slack**: Webhook notifications
- **Webhooks**: Custom HTTP endpoints

Features rate limiting to prevent alert fatigue.

---

## Authentication & Authorization

### User Roles

| Role | Capabilities |
|------|--------------|
| `user` | Access own data, create content |
| `admin` | Full user management, system access, Spotify configuration |

### Security Features

- Password hashing via Werkzeug
- Session-based authentication with Flask-Login
- CSRF protection on forms
- User isolation (users only see own data)
- Admin action logging

---

## External Integrations

### OpenAI API

Used for research brief generation:
- Model: Configurable (default: `gpt-4-turbo`)
- JSON mode for structured outputs
- PDF text extraction via `pdfplumber`

### Spotify API

Full OAuth 2.0 flow with:
- Token storage in database
- Automatic token refresh
- Playlist import/export
- Track search and matching

---

## Data Flow Patterns

### AJAX-Enabled Routes

Most CRUD operations support both HTML and JSON responses:
```
POST /projects/create → Returns JSON for AJAX, redirects for form submit
```

### Background Processing

Long-running tasks (CSV import) use threading:
```
Request → Queue Job → Background Thread → Poll Status → Complete
```

---

## Directory Reference

| Path | Contents |
|------|----------|
| `templates/admin/` | Admin dashboard views |
| `templates/music/` | Music library views |
| `templates/research/` | Research brief views |
| `templates/projects/` | Project management views |
| `templates/goals/` | Goal tracking views |
| `templates/todo/` | Task management views |
| `static/css/` | Stylesheets |
| `logs/` | Application log files |
| `instance/` | Instance-specific SQLite database |
| `data/` | Data files (imports, exports) |

---

## Related Documentation

- [Features Overview](FEATURES.md) - Detailed feature descriptions
- [Research Brief Generator](research-brief-generator.md) - AI feature deep dive
- [Main README](../README.md) - Setup and installation
