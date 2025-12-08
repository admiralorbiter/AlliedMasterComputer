# Allied Master Computer

A personal utility suite built with Flask to help streamline various tasks in daily life. This application provides a secure, user-friendly platform for managing utilities and tools with comprehensive admin capabilities.

## Features

- **Secure Authentication**: User login system with role-based access control
- **Admin Dashboard**: Comprehensive admin panel for user management and system monitoring
- **Utility Tools**: Platform for hosting various utility applications and tools
- **Logging & Monitoring**: Built-in logging and error tracking system
- **Modern UI**: Clean, responsive interface with a professional design

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd AlliedMasterComputer
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
   - Create a `.env` file in the root directory
   - Configure your database and secret key settings

4. Initialize the database:
```bash
python app.py
```

5. Create an admin user:
```bash
python create_admin.py
```

### Running the Application

```bash
python app.py
```

The application will be available at `http://localhost:5000` (or the port specified in your environment).

## Project Structure

```
AlliedMasterComputer/
├── app.py                 # Main application entry point
├── config/                # Configuration files
├── flask_app/
│   ├── forms/            # WTForms form definitions
│   ├── models/           # Database models
│   ├── routes/            # Route handlers
│   └── utils/            # Utility functions (logging, monitoring, error handling)
├── static/
│   └── css/              # Stylesheets
├── templates/             # Jinja2 templates
└── tests/                # Test suite
```

## Configuration

The application supports multiple environments:
- **Development**: Default configuration for local development
- **Testing**: Configuration for running tests
- **Production**: Production-ready configuration

Set the `FLASK_ENV` environment variable to switch between environments.

## Testing

Run the test suite:
```bash
python run_tests.py
```

Or use pytest directly:
```bash
pytest
```

## License

This project is for personal use.

## Contributing

This is a personal utility project. Contributions and suggestions are welcome!
