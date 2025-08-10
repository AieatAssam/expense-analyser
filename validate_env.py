#!/usr/bin/env python3
"""
Environment Variable Validation Script
Validates that all required Auth0 and API settings are present in .env file
"""

import re
import os

def validate_env():
    """Validate that all required environment variables are present and properly configured"""
    env_file = '.env'
    
    if not os.path.exists(env_file):
        print(f"❌ {env_file} not found. Please copy .env.template to .env first.")
        return False
    
    # Read the current .env file
    with open(env_file, 'r') as f:
        content = f.read()
    
    # Required Auth0 variables (used by both frontend and backend)
    required_vars = {
        'AUTH0_DOMAIN': r'^AUTH0_DOMAIN=(.+)$',
        'AUTH0_CLIENT_ID': r'^AUTH0_CLIENT_ID=(.+)$', 
        'AUTH0_CLIENT_SECRET': r'^AUTH0_CLIENT_SECRET=(.+)$',
        'AUTH0_AUDIENCE': r'^AUTH0_AUDIENCE=(.+)$',
        'API_URL': r'^API_URL=(.+)$',
        'WS_URL': r'^WS_URL=(.+)$'
    }
    
    missing_vars = []
    placeholder_vars = []
    
    for var_name, pattern in required_vars.items():
        match = re.search(pattern, content, re.MULTILINE)
        if not match:
            missing_vars.append(var_name)
        elif match.group(1).startswith('your-') or match.group(1) == 'your_secret_key_here_min_32_chars':
            placeholder_vars.append(var_name)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    if placeholder_vars:
        print(f"⚠️  The following variables still have placeholder values: {', '.join(placeholder_vars)}")
        print("   Please update them with your actual Auth0 and API configuration.")
        return False
    
    print("✅ All required environment variables are properly configured")
    print("✅ Both frontend and backend will use the same Auth0 configuration")
    return True

if __name__ == '__main__':
    validate_env()
