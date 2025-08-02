# Auth0 Configuration Documentation

## Overview
This document describes the setup and configuration of Auth0 authentication for the Expense Analyser using the **free tier** with client ID and secret authentication. This setup is suitable for non-enterprise applications and uses Auth0's standard JWKS endpoint for token validation.

---

## 1. Auth0 Setup Guide

### Step 1: Create Auth0 Application
- Log in to [Auth0 Dashboard](https://manage.auth0.com/).
- Create a new Application and select **Single Page Application** for the frontend.
- Note the **Client ID** from the application settings.
- For the backend API, create an **API** in Auth0 Dashboard and note the **API Identifier**.

### Step 2: Configure Auth0 Application Settings
- **Allowed Callback URLs**: `http://localhost:3000` (for development)
- **Allowed Logout URLs**: `http://localhost:3000`
- **Allowed Web Origins**: `http://localhost:3000`
- **Allowed Origins (CORS)**: `http://localhost:3000`

### Step 3: Configure Environment Variables

#### Single Root .env File
Copy `.env.template` to `.env` in the project root and configure:
```bash
# Backend Auth0 Configuration
AUTH0_DOMAIN=your-auth0-domain.auth0.com
AUTH0_CLIENT_ID=your-auth0-client-id
AUTH0_CLIENT_SECRET=your-auth0-client-secret  # Not used in current implementation but available for future use
AUTH0_API_AUDIENCE=your-api-identifier

# Frontend Auth0 Configuration (React App)
REACT_APP_AUTH0_DOMAIN=your-auth0-domain.auth0.com
REACT_APP_AUTH0_CLIENT_ID=your-auth0-client-id
REACT_APP_AUTH0_AUDIENCE=your-api-identifier
REACT_APP_API_URL=http://localhost:8000
```

**Note**: Both backend and frontend use the same root `.env` file. React automatically reads environment variables from the project root.

### Step 4: Backend Integration
- The backend automatically fetches JWKS from `https://{AUTH0_DOMAIN}/.well-known/jwks.json`
- No manual JWKS configuration required
- JWT tokens are validated using Auth0's public keys
- CORS is configured to allow Auth0 requests

---

## 2. Authentication Flow

1. **Frontend Login**: User clicks login → redirected to Auth0
2. **Auth0 Authentication**: User authenticates with Auth0
3. **Token Issuance**: Auth0 issues JWT access token
4. **API Requests**: Frontend sends token in Authorization header
5. **Backend Validation**: Backend validates token using JWKS from Auth0
6. **User Creation**: First user is auto-created as admin

---

## 3. Security Features

- **Automatic JWKS Fetching**: No hardcoded keys or manual JWKS management
- **Token Validation**: Full JWT signature and claims validation
- **Audience Validation**: Ensures tokens are intended for this API
- **Issuer Validation**: Verifies tokens come from your Auth0 domain
- **Comprehensive Logging**: All authentication events are logged
- **Auto User Creation**: First user becomes admin automatically

---

## 4. Free Tier Compatibility

This setup is fully compatible with Auth0's free tier:
- ✅ Uses standard JWKS endpoint (no enterprise features)
- ✅ No custom domains required
- ✅ Works with up to 7,000 active users
- ✅ No advanced features like custom claims required

---

## 5. Troubleshooting

### Common Issues

**Token Validation Fails**
- Verify `AUTH0_DOMAIN` matches your Auth0 domain exactly
- Ensure `AUTH0_API_AUDIENCE` matches your API identifier
- Check that JWKS endpoint is accessible: `https://{domain}/.well-known/jwks.json`

**CORS Errors**
- Add your frontend URL to Auth0 application settings
- Verify CORS_ORIGINS in backend configuration

**User Not Found**
- First user is auto-created as admin
- Subsequent users need to be invited or linked manually

### Logs to Check
- Backend logs: Authentication events and JWT validation
- Browser console: Auth0 client errors
- Network tab: Token requests and API calls

---

## 6. Production Deployment

For production deployment:
1. Update callback URLs in Auth0 dashboard to production URLs
2. Use HTTPS for all URLs
3. Set strong `API_SECRET_KEY` in environment
4. Monitor authentication logs
5. Consider rate limiting on authentication endpoints
