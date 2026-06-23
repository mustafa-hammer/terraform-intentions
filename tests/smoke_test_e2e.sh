#!/bin/bash
# E2E smoke test for the webhook
# Tests that the server starts and responds correctly

set -e

echo "🧪 Running E2E Smoke Tests"
echo "=========================="

# Port to use for testing
TEST_PORT=8768

# Check if port is already in use
if lsof -Pi :$TEST_PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "❌ ERROR: Port $TEST_PORT is already in use"
    echo "Please stop any existing servers on this port and try again."
    echo "You can find the process with: lsof -i :$TEST_PORT"
    exit 1
fi

# Cleanup function - must be defined before trap
cleanup() {
    echo ""
    echo "Cleaning up..."
    
    # Kill the server process if it exists
    if [ -n "$SERVER_PID" ] && kill -0 $SERVER_PID 2>/dev/null; then
        echo "Stopping server (PID: $SERVER_PID)..."
        kill $SERVER_PID 2>/dev/null || true
        
        # Wait up to 5 seconds for graceful shutdown
        for i in {1..5}; do
            if ! kill -0 $SERVER_PID 2>/dev/null; then
                echo "Server stopped gracefully"
                break
            fi
            sleep 1
        done
        
        # Force kill if still running
        if kill -0 $SERVER_PID 2>/dev/null; then
            echo "Force killing server..."
            kill -9 $SERVER_PID 2>/dev/null || true
        fi
        
        # Wait for process to fully exit
        wait $SERVER_PID 2>/dev/null || true
    fi
    
    # Double-check port is free
    if lsof -Pi :$TEST_PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo "⚠️  Warning: Port $TEST_PORT still in use after cleanup"
        echo "Attempting to kill remaining processes..."
        lsof -ti :$TEST_PORT | xargs kill -9 2>/dev/null || true
        sleep 1
    fi
    
    echo "Cleanup complete"
}

# Set up trap for cleanup on exit (success or failure)
trap cleanup EXIT INT TERM

# Start server in background
echo "Starting server on port $TEST_PORT..."
uv run uvicorn terraform_intentions.app:app --host 127.0.0.1 --port $TEST_PORT > /tmp/smoke_server.log 2>&1 &
SERVER_PID=$!

echo "Server started with PID: $SERVER_PID"

# Wait for server to start and verify it's running
echo "Waiting for server to be ready..."
for i in {1..10}; do
    if kill -0 $SERVER_PID 2>/dev/null && curl -s http://127.0.0.1:$TEST_PORT/healthz >/dev/null 2>&1; then
        echo "Server is ready!"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "❌ ERROR: Server failed to start within 10 seconds"
        echo "Server logs:"
        cat /tmp/smoke_server.log
        exit 1
    fi
    sleep 1
done

# Test 1: Health check
echo ""
echo "Test 1: Health check endpoint"
HEALTH_RESPONSE=$(curl -s http://127.0.0.1:$TEST_PORT/healthz)
if [ "$HEALTH_RESPONSE" = '{"status":"ok"}' ]; then
    echo "✅ PASS: Health check returned correct response"
else
    echo "❌ FAIL: Health check returned: $HEALTH_RESPONSE"
    exit 1
fi

# Test 2: Verification event (null tokens)
echo ""
echo "Test 2: Verification event (null access_token)"
PAYLOAD='{"access_token":null,"task_result_callback_url":null}'
SIGNATURE=$(echo -n "$PAYLOAD" | python3 -c "import sys, hmac, hashlib; print(hmac.new(b'my-secret-key-123', sys.stdin.buffer.read(), hashlib.sha512).hexdigest())")

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST http://127.0.0.1:$TEST_PORT/run-task \
    -H "X-Tfc-Task-Signature: $SIGNATURE" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD")

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ PASS: Verification event accepted (200)"
else
    echo "❌ FAIL: Expected 200, got $HTTP_CODE"
    exit 1
fi

# Test 3: Invalid signature rejection
echo ""
echo "Test 3: Invalid signature rejection"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST http://127.0.0.1:$TEST_PORT/run-task \
    -H "X-Tfc-Task-Signature: invalid-signature" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD")

if [ "$HTTP_CODE" = "401" ]; then
    echo "✅ PASS: Invalid signature rejected (401)"
else
    echo "❌ FAIL: Expected 401, got $HTTP_CODE"
    exit 1
fi

echo ""
echo "=========================="
echo "✅ All smoke tests passed!"
echo ""
echo "Server logs:"
cat /tmp/smoke_server.log

# Made with Bob
