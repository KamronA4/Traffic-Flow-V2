# Secrets Setup Guide for Village Platform

## Overview

The Village platform uses multiple secrets and API keys for various services. This guide explains how to properly configure all required secrets for production use.

## Required Secrets

### 1. 🔐 **JWT_SECRET_KEY** (CRITICAL)
- **Purpose**: Signs and validates JWT tokens for user authentication
- **Security Level**: Critical - must be changed for production
- **How to generate**: Run `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- **Example**: `abcdef1234567890abcdef1234567890abcdef`

### 2. 🔐 **API_SECRET_KEY** (CRITICAL)
- **Purpose**: Secures API key generation and validation
- **Security Level**: Critical - must be changed for production
- **How to generate**: Run `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- **Example**: `xyz789123456789xyz789123456789xyz789`

### 3. 🤖 **PERPLEXITY_API_KEY** (REQUIRED)
- **Purpose**: Enables AI-powered traffic incident analysis
- **How to get**: Sign up at https://www.perplexity.ai/
- **Documentation**: https://docs.perplexity.ai/
- **Example**: `pplx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### 4. 🗺️ **TOMTOM_API_KEY** (REQUIRED)
- **Purpose**: Fetches real-time traffic data and incidents
- **How to get**: Sign up at https://developer.tomtom.com/
- **Free tier**: 50,000 requests/day
- **Example**: `abcdef1234567890abcdef1234567890abcdef`

## Optional Secrets (Future Features)

### 5. 💳 **STRIPE_PUBLISHABLE_KEY** & **STRIPE_SECRET_KEY** (OPTIONAL)
- **Purpose**: Payment processing for subscriptions
- **When needed**: When implementing payment processing
- **How to get**: Sign up at https://stripe.com/

### 6. 📧 **Email Configuration** (OPTIONAL)
- **Purpose**: Send notification emails
- **When needed**: When implementing email notifications

## Setup Instructions

### Step 1: Locate Your Secrets File
Your secrets file should be at:
```
/Users/kamronaggor/Desktop/Manual Library/Coding stuff/Data Science Projects/Perplexity-Hackathon/code/.streamlit/secrets.toml
```

### Step 2: Generate Secure Keys

#### For JWT and API Secret Keys:
```bash
# Generate JWT secret key
python -c "import secrets; print('JWT_SECRET_KEY =', '\"' + secrets.token_urlsafe(32) + '\"')"

# Generate API secret key  
python -c "import secrets; print('API_SECRET_KEY =', '\"' + secrets.token_urlsafe(32) + '\"')"
```

#### For API Keys:
1. **TomTom API**: Visit https://developer.tomtom.com/ and create an account
2. **Perplexity AI**: Visit https://www.perplexity.ai/ and get an API key

### Step 3: Update secrets.toml

Replace the placeholder values in your `secrets.toml` file:

```toml
# Replace these with your actual values
JWT_SECRET_KEY = "your-generated-jwt-secret-key"
API_SECRET_KEY = "your-generated-api-secret-key"
PERPLEXITY_API_KEY = "your-actual-perplexity-api-key"
TOMTOM_API_KEY = "your-actual-tomtom-api-key"
```

### Step 4: Verify Configuration

Run this test to verify your secrets are properly configured:

```bash
cd code
python -c "
import streamlit as st
try:
    jwt_key = st.secrets.get('JWT_SECRET_KEY')
    api_key = st.secrets.get('API_SECRET_KEY')
    perplexity = st.secrets.get('PERPLEXITY_API_KEY')
    tomtom = st.secrets.get('TOMTOM_API_KEY')
    
    print('✅ JWT_SECRET_KEY configured:', bool(jwt_key and jwt_key != 'village-production-jwt-secret-key-change-this-in-production-2024'))
    print('✅ API_SECRET_KEY configured:', bool(api_key and api_key != 'village-api-management-secret-key-change-this-in-production-2024'))
    print('✅ PERPLEXITY_API_KEY configured:', bool(perplexity and perplexity != 'your-perplexity-api-key-here'))
    print('✅ TOMTOM_API_KEY configured:', bool(tomtom and tomtom != 'your-tomtom-api-key-here'))
except Exception as e:
    print('❌ Error reading secrets:', e)
"
```

## Security Best Practices

### ✅ DO:
- Generate strong, unique secret keys for JWT and API secrets
- Keep secrets.toml in .gitignore (already configured)
- Use different secret keys for different environments (dev/prod)
- Rotate secret keys periodically
- Monitor API usage and quotas

### ❌ DON'T:
- Use default secret keys in production
- Share secrets via email or messaging
- Commit secrets to version control
- Use the same secret key for multiple purposes
- Store secrets in plain text files outside of .streamlit/

## Testing Your Setup

### Test Authentication:
1. Run `streamlit run main.py` from the `code/` directory
2. Try logging in with default credentials: `admin` / `admin123`
3. Check that JWT tokens are working properly

### Test API Integrations:
1. **TomTom API**: Check the Live Traffic page for incident data
2. **Perplexity AI**: Try the AI analysis features on traffic incidents

## Troubleshooting

### Common Issues:

1. **"cannot import name 'is_authenticated'"**
   - Solution: Install PyJWT: `pip install PyJWT`

2. **"Invalid API key" errors**
   - Check that your API keys are correctly formatted
   - Verify quotas haven't been exceeded

3. **JWT token errors**
   - Ensure JWT_SECRET_KEY is set and not the default value
   - Check that PyJWT is installed

4. **No traffic data appearing**
   - Verify TOMTOM_API_KEY is correct
   - Check TomTom API quota limits

## Support

If you encounter issues:
1. Check the console for error messages
2. Verify all secrets are properly configured
3. Test API keys individually
4. Check API provider documentation for rate limits

## Environment Variables (Alternative)

If you prefer using environment variables instead of secrets.toml, you can also set:
```bash
export JWT_SECRET_KEY="your-jwt-secret"
export API_SECRET_KEY="your-api-secret"
export PERPLEXITY_API_KEY="your-perplexity-key"
export TOMTOM_API_KEY="your-tomtom-key"
```

The application will automatically use `st.secrets.get()` which checks both secrets.toml and environment variables.