# Installation Instructions

## Prerequisites
- Python 3.8 or higher
- pip package manager

## Installation Steps

1. **Clone or download the repository**
   ```bash
   cd /path/to/your/project
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize databases**
   ```bash
   cd code
   python initialize_databases.py
   ```

4. **Run the application**
   ```bash
   streamlit run main.py
   ```

## Troubleshooting

### If you get "cannot import name 'is_authenticated'" error:
This means the PyJWT library is not installed. Run:
```bash
pip install PyJWT
```

### If you get other import errors:
Make sure all dependencies are installed:
```bash
pip install -r requirements.txt
```

### If you get "unable to open database file" error:
This means the database directories don't exist or aren't writable. Run the database initialization script:
```bash
cd code
python initialize_databases.py
```

### If you get "hashlib pbkdf2_hex" error:
This has been fixed in the latest version. Make sure you have the updated code.

### If you get authentication errors:
Test the authentication system:
```bash
cd code
python verify_auth.py
```

### If you get other database errors:
The application will automatically create the necessary database files in the `data/` directory. Make sure the directory exists and is writable.

## Default Login Credentials

- **Username:** admin
- **Password:** admin123

You can also click "Demo Login" button on the login page for quick access.

## Features Available

- **Authentication System**: Multi-tenant user management
- **Subscription Management**: Tier-based feature access
- **API Management**: Key generation and usage tracking
- **Onboarding System**: Guided setup process
- **Live Traffic Monitoring**: Real-time incident tracking
- **Analytics Dashboard**: Traffic pattern analysis
- **Professional Reporting**: Export capabilities

## Support

If you encounter any issues, please check:
1. All dependencies are installed
2. Python version is 3.8+
3. You're running from the correct directory (`code/`)
4. The `data/` directory exists and is writable