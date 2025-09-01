# FeelSync API Documentation

## Overview

FeelSync provides a RESTful API for managing user accounts, game sessions, behavioral data collection, and mental health analysis. This documentation covers all available endpoints, request/response formats, and authentication requirements.

## Base URL

```
Development: http://localhost:5000
Production: https://api.feelsync.com
```

## Authentication

FeelSync uses session-based authentication with CSRF protection enabled in production.

### Login
```http
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username_or_email=user@example.com&password=secretpassword
```

### Logout
```http
GET /auth/logout
```

## API Endpoints

### User Management

#### Register New User
```http
POST /auth/register
Content-Type: application/x-www-form-urlencoded

username=johndoe&email=john@example.com&password=SecurePass123&confirm_password=SecurePass123&age=20&gender=male
```

**Response:**
```json
{
  "success": true,
  "message": "Registration successful",
  "redirect": "/auth/login"
}
```

#### Get User Profile
```http
GET /auth/profile
Authorization: Required (session-based)
```

**Response:**
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "age": 20,
  "gender": "male",
  "created_at": "2025-01-15T10:30:00Z",
  "total_sessions": 15,
  "is_eligible_for_analysis": true
}
```

#### Update Profile
```http
POST /auth/profile/edit
Content-Type: application/x-www-form-urlencoded
Authorization: Required

gender=other&data_sharing_consent=true&analytics_consent=true
```

### Game Sessions

#### Start Game Session
```http
POST /games/start_session
Content-Type: application/json
Authorization: Required

{
  "game_type": "catch_thought"
}
```

**Response:**
```json
{
  "success": true,
  "session_id": 12345,
  "game_type": "catch_thought",
  "started_at": "2025-01-15T14:30:00Z"
}
```

#### End Game Session
```http
POST /games/end_session
Content-Type: application/json
Authorization: Required

{
  "session_id": 12345,
  "final_score": 150,
  "level_reached": 3,
  "accuracy": 0.85,
  "average_reaction_time": 245.2,
  "consistency_score": 0.78,
  "decisions_made": 25,
  "completed": true,
  "behavioral_data": {
    "total_positive_catches": 18,
    "total_negative_catches": 12,
    "missed_thoughts": 5
  }
}
```

**Response:**
```json
{
  "success": true,
  "session_data": {
    "score": 150,
    "duration": 420,
    "accuracy": 0.85,
    "level_reached": 3
  }
}
```

#### Log Behavioral Data
```http
POST /games/log_behavior
Content-Type: application/json
Authorization: Required

{
  "session_id": 12345,
  "reaction_time": 275.5,
  "decision_type": "positive_catch",
  "decision_value": "caught_positive_thought",
  "confidence_level": 0.8,
  "emotional_state": "focused",
  "stress_level": 3,
  "accuracy": true,
  "hesitation_time": 150.2,
  "game_level": 2,
  "game_phase": "active_play",
  "difficulty": "normal",
  "metadata": {
    "thought_category": "self_confidence",
    "response_pattern": "quick_decisive"
  }
}
```

#### Get Game Scenarios
```http
GET /games/get_scenarios/{game_type}
Authorization: Required
```

**Response for catch_thought:**
```json
{
  "scenarios": {
    "positive_thoughts": [
      "I can handle this challenge",
      "I'm learning something new",
      "This is an opportunity to grow"
    ],
    "negative_thoughts": [
      "This is too difficult for me",
      "I always mess things up",
      "Nobody understands me"
    ],
    "neutral_thoughts": [
      "I need to focus on this task",
      "What should I have for lunch?",
      "The weather is changing"
    ]
  }
}
```

#### Get Leaderboard
```http
GET /games/leaderboard/{game_type}
Authorization: Required
```

**Response:**
```json
{
  "leaderboard": [
    {
      "rank": 1,
      "score": 250,
      "accuracy": 0.92,
      "level_reached": 5
    },
    {
      "rank": 2,
      "score": 230,
      "accuracy": 0.88,
      "level_reached": 4
    }
  ],
  "user_best_score": 180,
  "user_rank": 15
}
```

### Analysis & Reports

#### Generate Analysis Report
```http
POST /analysis/generate
Content-Type: application/json
Authorization: Required

{
  "days_back": 30,
  "report_type": "personal",
  "include_recommendations": true
}
```

**Response:**
```json
{
  "success": true,
  "report_id": 67,
  "message": "Analysis report generated successfully!",
  "estimated_processing_time": "2-3 minutes"
}
```

#### Get Analysis Report
```http
GET /analysis/report/{report_id}
Authorization: Required
```

**Response:**
```json
{
  "id": 67,
  "user_id": 1,
  "generated_at": "2025-01-15T15:45:00Z",
  "report_type": "personal",
  "sessions_analyzed": 12,
  "analysis_period": {
    "start_date": "2024-12-15T00:00:00Z",
    "end_date": "2025-01-15T00:00:00Z"
  },
  "overall_wellbeing_score": 0.75,
  "confidence_score": 0.82,
  "insights": {
    "anxiety_indicators": {
      "score": 0.35,
      "level": "moderate",
      "confidence": 0.69,
      "key_patterns": [
        "Inconsistent performance across difficulty levels",
        "Attention lapses during longer sessions"
      ]
    }
  },
  "recommendations": [
    {
      "category": "stress_management",
      "title": "Mindfulness Practice",
      "description": "Consider incorporating 5-10 minutes of daily mindfulness meditation",
      "priority": "high",
      "action_items": [
        "Try guided meditation apps",
        "Practice deep breathing exercises",
        "Set reminders for mindful moments"
      ]
    }
  ],
  "summary": "Overall positive mental health indicators with some areas for improvement in stress management and attention consistency."
}
```

#### Get Behavioral Patterns
```http
GET /analysis/api/behavioral_patterns?days=30
Authorization: Required
```

**Response:**
```json
{
  "reaction_times": [
    {
      "timestamp": "2025-01-15T10:30:00Z",
      "value": 245.2,
      "game_type": "catch_thought"
    }
  ],
  "stress_levels": [
    {
      "timestamp": "2025-01-15T10:30:00Z",
      "value": 4
    }
  ],
  "decision_patterns": {
    "assertive_choice": 15,
    "avoidant_choice": 8,
    "aggressive_choice": 3
  },
  "emotional_states": {
    "focused": 12,
    "calm": 8,
    "anxious": 5,
    "distracted": 3
  }
}
```

### Dashboard APIs

#### Get Activity Data
```http
GET /dashboard/api/activity_data?days=7
Authorization: Required
```

**Response:**
```json
[
  {
    "date": "2025-01-15",
    "session_count": 3,
    "total_duration": 1250,
    "avg_score": 162.5
  },
  {
    "date": "2025-01-14",
    "session_count": 2,
    "total_duration": 780,
    "avg_score": 145.0
  }
]
```

#### Get Performance Data
```http
GET /dashboard/api/performance_data?game_type=all
Authorization: Required
```

**Response:**
```json
[
  {
    "date": "2025-01-15 14:30",
    "score": 150,
    "accuracy": 0.85,
    "reaction_time": 245.2,
    "game_type": "catch_thought"
  },
  {
    "date": "2025-01-15 16:45",
    "score": 180,
    "accuracy": 0.92,
    "reaction_time": 220.8,
    "game_type": "stat_balance"
  }
]
```

### Therapist Access

#### Grant Therapist Access
```http
POST /dashboard/grant_therapist_access
Content-Type: application/x-www-form-urlencoded
Authorization: Required

therapist_email=therapist@clinic.com&duration=30
```

#### Revoke Therapist Access
```http
POST /dashboard/revoke_therapist_access/{access_id}
Authorization: Required
```

#### Therapist Dashboard
```http
GET /analysis/therapist_view/{therapist_email}?token={access_token}
```

**Response:**
```json
{
  "therapist_email": "therapist@clinic.com",
  "patients": [
    {
      "user_id": 1,
      "username": "patient_001", 
      "age": 20,
      "total_sessions": 15,
      "recent_activity": 8,
      "shared_reports": [
        {
          "id": 67,
          "generated_at": "2025-01-15T15:45:00Z",
          "overall_wellbeing_score": 0.75,
          "summary": "Positive indicators with moderate stress levels"
        }
      ],
      "last_activity": "2025-01-15T14:30:00Z"
    }
  ]
}
```

## Error Handling

### Standard Error Response Format
```json
{
  "error": "Error description",
  "code": "ERROR_CODE",
  "details": "Additional error details",
  "timestamp": "2025-01-15T12:00:00Z"
}
```

### Common Error Codes

| Status Code | Error Code | Description |
|-------------|------------|-------------|
| 400 | `INVALID_REQUEST` | Malformed request data |
| 401 | `UNAUTHORIZED` | Authentication required |
| 403 | `FORBIDDEN` | Insufficient permissions |
| 404 | `NOT_FOUND` | Resource not found |
| 429 | `RATE_LIMIT_EXCEEDED` | Too many requests |
| 500 | `INTERNAL_ERROR` | Server error |

### Game-Specific Errors

| Error Code | Description |
|------------|-------------|
| `DAILY_LIMIT_REACHED` | Maximum daily games played |
| `INVALID_GAME_TYPE` | Unsupported game type |
| `SESSION_NOT_FOUND` | Game session doesn't exist |
| `INSUFFICIENT_DATA` | Not enough data for analysis |

## Rate Limiting

| Endpoint Category | Limit | Window |
|------------------|-------|---------|
| Authentication | 10 requests | 1 minute |
| Game Sessions | 50 requests | 1 hour |
| Analysis Generation | 3 requests | 1 day |
| General API | 100 requests | 1 hour |

## Data Models

### User Model
```json
{
  "id": "integer",
  "username": "string",
  "email": "string",
  "age": "integer",
  "gender": "string",
  "is_minor": "boolean",
  "parental_consent": "boolean",
  "created_at": "datetime",
  "last_login": "datetime"
}
```

### Game Session Model
```json
{
  "id": "integer",
  "user_id": "integer",
  "game_type": "string",
  "started_at": "datetime",
  "ended_at": "datetime",
  "duration": "integer (seconds)",
  "score": "integer",
  "level_reached": "integer",
  "accuracy": "float (0-1)",
  "average_reaction_time": "float (milliseconds)",
  "consistency_score": "float (0-1)",
  "decisions_made": "integer",
  "completed": "boolean",
  "behavioral_data": "json object"
}
```

### Behavior Data Model
```json
{
  "id": "integer",
  "user_id": "integer",
  "session_id": "integer",
  "timestamp": "datetime",
  "reaction_time": "float (milliseconds)",
  "decision_type": "string",
  "decision_value": "string",
  "confidence_level": "float (0-1)",
  "emotional_state": "string",
  "stress_level": "integer (1-10)",
  "accuracy": "boolean",
  "hesitation_time": "float (milliseconds)",
  "game_level": "integer",
  "game_phase": "string",
  "difficulty": "string",
  "metadata": "json object"
}
```

## Webhooks

FeelSync supports webhooks for real-time notifications of important events.

### Webhook Events

| Event | Description |
|-------|-------------|
| `analysis.completed` | New analysis report generated |
| `session.completed` | Game session finished |
| `user.registered` | New user registration |
| `alert.triggered` | Mental health alert triggered |

### Webhook Payload Example
```json
{
  "event": "analysis.completed",
  "timestamp": "2025-01-15T15:45:00Z",
  "data": {
    "user_id": 1,
    "report_id": 67,
    "report_type": "personal",
    "overall_score": 0.75,
    "alerts": []
  }
}
```

## SDKs and Libraries

### JavaScript SDK
```javascript
import FeelSyncSDK from '@feelsync/sdk-js';

const client = new FeelSyncSDK({
  baseUrl: 'https://api.feelsync.com',
  apiKey: 'your_api_key'
});

// Start game session
const session = await client.games.startSession('catch_thought');

// Log behavioral data
await client.games.logBehavior(session.id, {
  reactionTime: 245.2,
  decisionType: 'positive_catch',
  accuracy: true
});
```

### Python SDK
```python
from feelsync import FeelSyncClient

client = FeelSyncClient(
    base_url='https://api.feelsync.com',
    api_key='your_api_key'
)

# Generate analysis
report = client.analysis.generate_report(
    days_back=30,
    report_type='personal'
)
```

## Testing

### Test Environment
```
Base URL: https://test-api.feelsync.com
```

### Test Credentials
```
Username: test_user
Password: TestPassword123
```

### Sample API Calls

Use our Postman collection or curl examples:

```bash
# Login
curl -X POST https://test-api.feelsync.com/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username_or_email=test_user&password=TestPassword123"

# Start game session
curl -X POST https://test-api.feelsync.com/games/start_session \
  -H "Content-Type: application/json" \
  -H "Cookie: session=your_session_cookie" \
  -d '{"game_type": "catch_thought"}'
```

## Changelog

### Version 1.0.0 (January 2025)
- Initial API release
- User management endpoints
- Game session management
- Basic behavioral analysis
- Dashboard APIs

### Planned Features
- Real-time game streaming
- Advanced ML model APIs
- Group therapy session support
- Integration with external health platforms

## Support

For API support and questions:
- Documentation: https://docs.feelsync.com
- Support: support@feelsync.com
- Discord: https://discord.gg/feelsync
- GitHub Issues: https://github.com/feelsync/api/issues0.78,
      "key_patterns": [
        "Increased reaction time variability in social scenarios",
        "Higher stress levels during decision-making tasks"
      ]
    },
    "depression_indicators": {
      "score": 0.25,
      "level": "low",
      "confidence": 0.71,
      "key_patterns": [
        "Consistent engagement across sessions",
        "Positive emotional state majority of time"
      ]
    },
    "attention_indicators": {
      "score": 0.45,
      "level": "moderate",
      "confidence":
