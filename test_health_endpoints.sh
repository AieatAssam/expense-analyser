#!/bin/bash

# Example script showing health check behavior in different scenarios

echo "=== Testing Health Check System ==="

# Function to test an endpoint
test_endpoint() {
    local endpoint=$1
    local name=$2
    echo "Testing $name ($endpoint):"
    curl -s "http://localhost:8000$endpoint" | jq '.' 2>/dev/null || echo "  Error: Could not parse JSON response"
    echo ""
}

# Test all health endpoints
echo "1. Testing all health endpoints..."
test_endpoint "/health" "Root Health Check"
test_endpoint "/ping" "Root Ping"
test_endpoint "/ready" "Root Readiness"
test_endpoint "/live" "Root Liveness"
test_endpoint "/api/v1/health" "API Health Check"
test_endpoint "/api/v1/health?details=true" "API Health Check (detailed)"
test_endpoint "/api/v1/health/ready" "API Readiness Probe"
test_endpoint "/api/v1/health/live" "API Liveness Probe"
test_endpoint "/api/v1/health/status" "API Simple Status"
test_endpoint "/api/v1/ping" "API Ping"

echo "=== Health Check Testing Complete ==="
echo ""
echo "Usage in production:"
echo "  - Kubernetes Liveness:  /live"
echo "  - Kubernetes Readiness: /ready"
echo "  - Load Balancer:        /ready or /health"
echo "  - Monitoring/Alerting:  /health?details=true"
echo "  - Simple Connectivity:  /ping"
echo ""
echo "Expected HTTP Status Codes:"
echo "  - 200: Healthy/Ready/Alive"
echo "  - 503: Unhealthy/Not Ready/Dead"
