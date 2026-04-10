#!/bin/bash

# Chatbot endpoints test script

echo "========================================="
echo "Chatbot API Endpoint Tests"
echo "========================================="
echo ""

# Login and get token
echo "1. Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"testuser@example.com","password":"Test1234"}')

TOKEN=$(echo $LOGIN_RESPONSE | python -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

if [ -z "$TOKEN" ]; then
  echo "ERROR: Failed to get token"
  exit 1
fi

echo "SUCCESS: Got JWT token"
echo ""

# Get all questions
echo "2. Getting all questions..."
curl -s -X GET "http://localhost:8000/api/v1/chatbot/questions" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool | head -40
echo "..."
echo ""

# Start a session
echo "3. Starting assessment session..."
STUDENT_ID="3b735e60-b0b7-497e-9346-5d97f62739ee"
SESSION_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/chatbot/sessions/start" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"student_id\":\"$STUDENT_ID\"}")

echo $SESSION_RESPONSE | python -m json.tool
SESSION_ID=$(echo $SESSION_RESPONSE | python -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null)
echo ""

# Get first question
echo "4. Getting first question..."
FIRST_QUESTION=$(curl -s -X GET "http://localhost:8000/api/v1/chatbot/questions" \
  -H "Authorization: Bearer $TOKEN" | python -c "import sys, json; print(json.load(sys.stdin)[0]['id'])" 2>/dev/null)

echo "First question ID: $FIRST_QUESTION"
echo ""

# Submit an answer
echo "5. Submitting answer to first question..."
curl -s -X POST "http://localhost:8000/api/v1/chatbot/answer" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"session_id\":\"$SESSION_ID\",\"question_id\":\"$FIRST_QUESTION\",\"answer_data\":{\"score\":4}}" | python -m json.tool
echo ""

# Get session progress
echo "6. Getting session progress..."
curl -s -X GET "http://localhost:8000/api/v1/chatbot/sessions/$SESSION_ID/progress" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
echo ""

echo "========================================="
echo "All tests complete!"
echo "========================================="
