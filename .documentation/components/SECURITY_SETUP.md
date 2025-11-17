# Security Setup Guide

This guide explains how to securely configure the Village platform for production use.

## Overview

The Village platform now uses secure credential management to prevent hardcoded passwords and API keys from being exposed in the codebase.

## Key Security Features

### 1. Environment-Based Credential Management
- All sensitive credentials are loaded from environment variables or Streamlit secrets
- No hardcoded passwords in the source code
- Secure fallbacks for development vs production

### 2. Demo Mode Controls  
Demo accounts and hardcoded credentials are only created when explicitly enabled:
- `VILLAGE_DEMO_MODE=true` - Enables demo login and relaxed security
- `VILLAGE_CREATE_DEMO_ACCOUNTS=true` - Creates RIDOT demo accounts
- `VILLAGE_CREATE_ADMIN_ACCOUNT=true` - Creates fallback admin account

### 3. Secure Secret Management
The system checks for credentials in this order:
1. Streamlit secrets (`secrets.toml`)
2. Environment variables
3. Secure random generation (production)
4. Fallback values (demo mode only)

## Production Setup

### Step 1: Configure Secrets

Copy the template and configure your secrets:
```bash
cp .streamlit/secrets.toml.template .streamlit/secrets.toml
```

Edit `secrets.toml` with your secure values:
```toml
# Required for production
JWT_SECRET_KEY = "your-256-bit-secret-key"
TOMTOM_API_KEY = "your-tomtom-api-key"
PERPLEXITY_API_KEY = "your-perplexity-api-key"

# Demo credentials (if demo mode needed)
RIDOT_DEMO_PASSWORD = "YourSecurePassword123!"
VILLAGE_ADMIN_PASSWORD = "AnotherSecurePassword456!"
```

### Step 2: Environment Variables

For deployment, set these environment variables:
```bash
export JWT_SECRET_KEY="your-256-bit-secret-key"
export TOMTOM_API_KEY="your-tomtom-api-key"
export PERPLEXITY_API_KEY="your-perplexity-api-key"

# Security settings for production
export VILLAGE_DEMO_MODE="false"
export VILLAGE_CREATE_DEMO_ACCOUNTS="false"
export VILLAGE_CREATE_ADMIN_ACCOUNT="false"
```

### Step 3: Secure JWT Secret Generation

Generate a secure JWT secret key:
```python
import secrets
jwt_secret = secrets.token_urlsafe(32)
print(f"JWT_SECRET_KEY={jwt_secret}")
```

## Demo Mode Setup

For demonstrations and development:

```bash
# Enable demo mode
export VILLAGE_DEMO_MODE="true"
export VILLAGE_CREATE_DEMO_ACCOUNTS="true"

# Set demo credentials
export RIDOT_DEMO_PASSWORD="Demo2024!"
export VILLAGE_DEMO_USERNAME="admin@ridot.ri.gov"
```

## Security Best Practices

### 1. Never Commit Secrets
- Add `secrets.toml` to `.gitignore`
- Never commit passwords or API keys
- Use environment variables in CI/CD

### 2. Use Strong Passwords
- Minimum 12 characters
- Include uppercase, lowercase, numbers, and symbols
- Use unique passwords for each account

### 3. Regular Key Rotation
- Rotate JWT secret keys periodically
- Update API keys when they expire
- Monitor for credential leaks

### 4. Access Control
- Limit demo mode to development environments
- Disable unnecessary admin accounts in production
- Use role-based access control

## Troubleshooting

### "JWT_SECRET_KEY must be set" Error
This means you're running in production mode without proper secrets configured.

**Solution:** Set the JWT secret key in `secrets.toml` or environment variables.

### "No fallback available for security reasons" Error
The system is refusing to use fallback credentials in production mode.

**Solution:** Either:
1. Set the required environment variable
2. Enable demo mode with `VILLAGE_DEMO_MODE=true`

### Demo Login Not Working
Check that demo mode is enabled and credentials are properly set:
```bash
echo $VILLAGE_DEMO_MODE
echo $RIDOT_DEMO_PASSWORD
```

## Migration from Old System

If upgrading from a version with hardcoded credentials:

1. **Set environment variables** for all previously hardcoded values
2. **Enable demo mode** if needed: `VILLAGE_DEMO_MODE=true`
3. **Test authentication** with your configured credentials
4. **Remove any hardcoded passwords** from your local config files

## Security Audit

Regular security checks:
- [ ] No hardcoded credentials in code
- [ ] All secrets in environment variables or secrets.toml
- [ ] Demo mode disabled in production
- [ ] Strong passwords used for all accounts
- [ ] JWT secret key is secure and rotated
- [ ] API keys are valid and within usage limits

## Support

For security-related questions or issues:
1. Check this documentation first
2. Review error messages for specific guidance
3. Contact the development team for assistance

**Remember:** Security is everyone's responsibility. When in doubt, err on the side of caution.