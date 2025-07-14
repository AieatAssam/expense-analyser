# Auth0 Configuration Documentation

## Overview
This document describes the setup and configuration of Auth0 authentication for the Expense Analyser backend, including environment variables, deployment steps, security best practices, callback URL configuration, troubleshooting, and multi-account support architecture.

---

## 1. Auth0 Setup Guide

### Step 1: Create Auth0 Application
- Log in to [Auth0 Dashboard](https://manage.auth0.com/).
- Create a new Application (Regular Web Application).
- Note the **Client ID** and **Client Secret**.
- Set the **Allowed Callback URLs** to your backend/frontend endpoints (e.g., `http://localhost:8000/callback`).
- Set **Allowed Logout URLs** and **Allowed Web Origins** as needed.

### Step 2: Configure Environment Variables
Add the following to your `.env` or environment configuration:
```
AUTH0_DOMAIN=your-auth0-domain.auth0.com
AUTH0_CLIENT_ID=your-client-id
AUTH0_CLIENT_SECRET=your-client-secret
AUTH0_API_AUDIENCE=your-api-identifier
AUTH0_CALLBACK_URL=http://localhost:8000/callback
```

### Step 3: Backend Integration
- Use the Auth0 client library for Python (e.g., `python-jose`, `authlib`).
- Implement JWT token validation in FastAPI middleware.
- Configure CORS to allow Auth0 requests.

---

## 2. Security Best Practices
- Always validate JWT tokens using Auth0 public keys.
- Use HTTPS for all callback and logout URLs in production.
- Rotate client secrets regularly.
- Restrict allowed origins and callback URLs to trusted domains.
- Log authentication events and monitor for suspicious activity.

---

## 3. Callback URL Configuration
- Ensure callback URLs match those set in Auth0 dashboard.
- For local development, use `http://localhost:8000/callback`.
- For production, use your deployed backend/frontend URLs.
- Update Auth0 dashboard if URLs change.

---

## 4. Troubleshooting Common Issues
- **Invalid Token**: Check JWT validation logic and public key configuration.
- **Callback URL Mismatch**: Ensure URLs in Auth0 dashboard and environment variables match.
- **CORS Errors**: Update allowed origins in both backend and Auth0 settings.
- **User Not Found**: Verify user creation logic and account linking implementation.

---

## 5. Multi-Account Support Architecture
- Each user can link multiple Auth0 provider accounts.
- User and Account models are related via foreign keys.
- Invitation system allows existing users to invite new accounts.
- First Auth0 login is auto-accepted if no users exist.
- Endpoints support account association, switching, and management.

---

## 6. Deployment Considerations
- Store secrets securely (use environment variables, not source code).
- Use container orchestration (Docker Compose) for consistent environment.
- Ensure database migrations are applied before enabling Auth0 integration.
- Monitor authentication logs and set up alerts for failed logins.

---

## 7. References
- [Auth0 Docs](https://auth0.com/docs/)
- [FastAPI Auth0 Integration](https://auth0.com/docs/quickstart/backend/python)
- [JWT Validation in Python](https://pyjwt.readthedocs.io/en/stable/)
