# FeelSync API Documentation

## Overview

FeelSync provides a comprehensive RESTful API for emotion tracking, mood analysis, and user management. The API supports JSON format for all requests and responses.

**Base URL:** `http://localhost:5000/api/v1`

**Authentication:** Bearer Token (JWT)

## Table of Contents

1. [Authentication](#authentication)
2. [User Management](#user-management)
3. [Emotion Tracking](#emotion-tracking)
4. [Mood Patterns](#mood-patterns)
5. [Audio Processing](#audio-processing)
6. [Analytics](#analytics)
7. [Games](#games)
8. [Error Handling](#error-handling)
9. [Rate Limiting](#rate-limiting)
10. [Examples](#examples)

---

## Authentication

### POST `/auth/register`
Register a new user account.

**Request Body:**
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "securepassword123",
  "name": "John Doe",
  "age": 28,
  "occupation": "Software Engineer",
  "location": "San Francisco"
}
```

**Response:**
```json
{
  "success": true,
  "leaderboard": [
    {
      "rank": 1,
      "username": "johndoe",
      "score": 2450,
      "level": 8,
      "achievements": 12,
      "last_played": "2024-01-20T15:30:00Z"
    },
    {
      "rank": 2,
      "username": "janedoe",
      "score": 2380,
      "level": 7,
      "achievements": 10,
      "last_played": "2024-01-20T14:20:00Z"
    }
  ],
  "user_rank": {
    "rank": 15,
    "score": 1840,
    "level": 5
  },
  "total_players": 156
}
```

### POST `/games/scores`
Submit game score.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "game": "emotional_balance",
  "level": 5,
  "score": 1250,
  "balance_achieved": 92,
  "moves_used": 18,
  "time_taken": 180,
  "achievements_unlocked": ["efficient", "level5"]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Score submitted successfully",
  "game_session": {
    "id": 789,
    "score": 1250,
    "level": 5,
    "rank_improvement": 3,
    "new_achievements": ["efficient"],
    "personal_best": true
  }
}
```

### GET `/games/stats`
Get user's game statistics.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "success": true,
  "stats": {
    "emotional_balance": {
      "total_games": 45,
      "highest_level": 8,
      "best_score": 2450,
      "total_playtime": 1800,
      "achievements_unlocked": 12,
      "average_balance": 87.5,
      "completion_rate": 0.82
    }
  },
  "overall": {
    "total_games": 45,
    "total_playtime": 1800,
    "rank": 15,
    "achievements": 12
  }
}
```

---

## Error Handling

All API endpoints return consistent error responses:

### Error Response Format
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "email",
      "reason": "Invalid email format"
    }
  },
  "timestamp": "2024-01-20T15:30:00Z",
  "request_id": "req_123456"
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `AUTHENTICATION_REQUIRED` | 401 | No valid token provided |
| `INVALID_TOKEN` | 401 | Token is expired or invalid |
| `INSUFFICIENT_PERMISSIONS` | 403 | User lacks required permissions |
| `RESOURCE_NOT_FOUND` | 404 | Requested resource doesn't exist |
| `VALIDATION_ERROR` | 400 | Request data validation failed |
| `DUPLICATE_RESOURCE` | 409 | Resource already exists |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error occurred |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

### Validation Errors
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": {
      "emotion": ["Invalid emotion type. Must be one of: happy, sad, angry, anxious, calm, neutral"],
      "intensity": ["Intensity must be between 1 and 10"]
    }
  }
}
```

---

## Rate Limiting

The API implements rate limiting to ensure fair usage:

- **General endpoints:** 1000 requests per hour per user
- **Authentication endpoints:** 10 requests per minute
- **Audio upload:** 50 requests per hour
- **Analytics:** 100 requests per hour

Rate limit headers are included in all responses:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 995
X-RateLimit-Reset: 1642694400
```

When rate limit is exceeded:
```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Try again in 3600 seconds",
    "retry_after": 3600
  }
}
```

---

## Examples

### Complete Emotion Tracking Flow

1. **Register User:**
```bash
curl -X POST http://localhost:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123",
    "name": "Test User"
  }'
```

2. **Login and Get Token:**
```bash
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass123"
  }'
```

3. **Record Emotion:**
```bash
curl -X POST http://localhost:5000/api/v1/emotions \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "emotion": "happy",
    "intensity": 8,
    "description": "Great presentation at work today!",
    "context": "work"
  }'
```

4. **Get Emotion History:**
```bash
curl -X GET "http://localhost:5000/api/v1/emotions?limit=10&start_date=2024-01-01" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

5. **Get Analytics:**
```bash
curl -X GET "http://localhost:5000/api/v1/analytics/summary?period=month" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Audio Processing Flow

1. **Upload Audio:**
```bash
curl -X POST http://localhost:5000/api/v1/audio/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "audio_file=@emotion_recording.wav" \
  -F "emotion_id=123"
```

2. **Analyze Audio:**
```bash
curl -X POST http://localhost:5000/api/v1/audio/analyze \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"audio_log_id": 45}'
```

### Game Integration

1. **Submit Game Score:**
```bash
curl -X POST http://localhost:5000/api/v1/games/scores \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "game": "emotional_balance",
    "level": 3,
    "score": 750,
    "balance_achieved": 88,
    "moves_used": 22
  }'
```

2. **Check Leaderboard:**
```bash
curl -X GET "http://localhost:5000/api/v1/games/leaderboard?game=emotional_balance&period=weekly" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## SDK and Libraries

### JavaScript SDK Example
```javascript
import FeelSyncAPI from 'feelsync-sdk';

const client = new FeelSyncAPI({
  baseURL: 'http://localhost:5000/api/v1',
  token: 'your_jwt_token'
});

// Record emotion
const emotion = await client.emotions.create({
  emotion: 'happy',
  intensity: 8,
  description: 'Great day at work!'
});

// Get analytics
const analytics = await client.analytics.getSummary('month');
```

### Python SDK Example
```python
from feelsync import FeelSyncClient

client = FeelSyncClient(
    base_url='http://localhost:5000/api/v1',
    token='your_jwt_token'
)

# Record emotion
emotion = client.emotions.create(
    emotion='happy',
    intensity=8,
    description='Great day at work!'
)

# Get analytics
analytics = client.analytics.get_summary(period='month')
```

---

## Webhooks

FeelSync supports webhooks for real-time notifications:

### Webhook Events
- `emotion.created` - New emotion recorded
- `mood.pattern_detected` - Mood pattern identified
- `achievement.unlocked` - Game achievement unlocked
- `insight.generated` - New insight available

### Webhook Configuration
```bash
curl -X POST http://localhost:5000/api/v1/webhooks \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-app.com/webhooks/feelsync",
    "events": ["emotion.created", "achievement.unlocked"],
    "secret": "your_webhook_secret"
  }'
```

### Webhook Payload Example
```json
{
  "event": "emotion.created",
  "data": {
    "emotion": {
      "id": 123,
      "emotion": "happy",
      "intensity": 8,
      "user_id": 1,
      "timestamp": "2024-01-20T15:30:00Z"
    }
  },
  "timestamp": "2024-01-20T15:30:01Z",
  "signature": "sha256=..."
}
```

---

## API Versioning

The API uses URL-based versioning:
- Current version: `v1`
- Base URL: `http://localhost:5000/api/v1`

When breaking changes are made, a new version will be released (e.g., `v2`). Previous versions will be supported for at least 12 months.

---

## Support and Resources

- **API Status:** [https://status.feelsync.com](https://status.feelsync.com)
- **Interactive Docs:** [http://localhost:5000/docs](http://localhost:5000/docs)
- **GitHub Repository:** [https://github.com/feelsync/api](https://github.com/feelsync/api)
- **Support Email:** api-support@feelsync.com

---

## Changelog

### v1.2.0 (2024-01-20)
- Added game leaderboard endpoints
- Enhanced analytics with trend analysis
- Improved audio processing accuracy
- Added webhook support

### v1.1.0 (2024-01-10)
- Added mood pattern tracking
- Enhanced emotion analytics
- Added audio analysis features
- Improved error handling

### v1.0.0 (2024-01-01)
- Initial API release
- Basic emotion tracking
- User authentication
- Core analytics features"success": true,
  "message": "User registered successfully",
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "name": "John Doe",
    "created_at": "2024-01-15T10:30:00Z"
  },
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### POST `/auth/login`
Authenticate user and receive access token.

**Request Body:**
```json
{
  "username": "johndoe",
  "password": "securepassword123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Login successful",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "username": "johndoe",
    "name": "John Doe"
  }
}
```

### POST `/auth/refresh`
Refresh access token.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_at": "2024-01-16T10:30:00Z"
}
```

### POST `/auth/logout`
Logout user and invalidate token.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "success": true,
  "message": "Logout successful"
}
```

---

## User Management

### GET `/users/profile`
Get current user profile.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "success": true,
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "name": "John Doe",
    "age": 28,
    "occupation": "Software Engineer",
    "location": "San Francisco",
    "created_at": "2024-01-15T10:30:00Z",
    "last_active": "2024-01-20T14:45:00Z"
  }
}
```

### PUT `/users/profile`
Update user profile.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "name": "John Smith",
  "age": 29,
  "occupation": "Senior Software Engineer",
  "location": "Seattle"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Profile updated successfully",
  "user": {
    "id": 1,
    "username": "johndoe",
    "name": "John Smith",
    "age": 29,
    "occupation": "Senior Software Engineer",
    "location": "Seattle"
  }
}
```

### DELETE `/users/profile`
Delete user account.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "password": "securepassword123",
  "confirmation": "DELETE"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Account deleted successfully"
}
```

---

## Emotion Tracking

### POST `/emotions`
Record a new emotion entry.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "emotion": "happy",
  "intensity": 8,
  "description": "Had a great day at work, completed an important project!",
  "context": "work",
  "triggers": ["achievement", "recognition"],
  "location": "office"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Emotion recorded successfully",
  "emotion": {
    "id": 123,
    "emotion": "happy",
    "intensity": 8,
    "description": "Had a great day at work, completed an important project!",
    "context": "work",
    "triggers": ["achievement", "recognition"],
    "location": "office",
    "timestamp": "2024-01-20T15:30:00Z",
    "user_id": 1
  }
}
```

### GET `/emotions`
Get user's emotion history.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `limit` (optional): Number of records to return (default: 50, max: 200)
- `offset` (optional): Number of records to skip (default: 0)
- `start_date` (optional): Filter from date (YYYY-MM-DD)
- `end_date` (optional): Filter to date (YYYY-MM-DD)
- `emotion` (optional): Filter by emotion type
- `context` (optional): Filter by context

**Example:** `GET /emotions?limit=20&emotion=happy&start_date=2024-01-01`

**Response:**
```json
{
  "success": true,
  "emotions": [
    {
      "id": 123,
      "emotion": "happy",
      "intensity": 8,
      "description": "Had a great day at work!",
      "context": "work",
      "timestamp": "2024-01-20T15:30:00Z"
    }
  ],
  "pagination": {
    "total": 150,
    "limit": 20,
    "offset": 0,
    "has_next": true,
    "has_prev": false
  }
}
```

### GET `/emotions/{id}`
Get specific emotion entry.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "success": true,
  "emotion": {
    "id": 123,
    "emotion": "happy",
    "intensity": 8,
    "description": "Had a great day at work!",
    "context": "work",
    "triggers": ["achievement"],
    "timestamp": "2024-01-20T15:30:00Z",
    "audio_logs": [
      {
        "id": 45,
        "file_path": "/audio/emotion_123.wav",
        "duration": 15.2,
        "analysis": {
          "tone": "positive",
          "confidence": 0.85
        }
      }
    ]
  }
}
```

### PUT `/emotions/{id}`
Update emotion entry.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "intensity": 9,
  "description": "Had an amazing day at work, got promoted!",
  "context": "work",
  "triggers": ["achievement", "promotion"]
}
```

### DELETE `/emotions/{id}`
Delete emotion entry.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "success": true,
  "message": "Emotion deleted successfully"
}
```

---

## Mood Patterns

### GET `/mood-patterns`
Get user's mood patterns.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `period` (optional): "daily", "weekly", "monthly" (default: "daily")
- `start_date` (optional): Filter from date
- `end_date` (optional): Filter to date
- `limit` (optional): Number of records

**Response:**
```json
{
  "success": true,
  "patterns": [
    {
      "date": "2024-01-20",
      "morning_mood": 7,
      "afternoon_mood": 8,
      "evening_mood": 6,
      "average_mood": 7.0,
      "dominant_emotions": ["happy", "calm"],
      "notes": "Productive day overall"
    }
  ],
  "summary": {
    "average_mood": 7.2,
    "mood_variance": 1.5,
    "trend": "stable",
    "best_time": "afternoon"
  }
}
```

### POST `/mood-patterns`
Record daily mood pattern.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "date": "2024-01-20",
  "morning_mood": 7,
  "afternoon_mood": 8,
  "evening_mood": 6,
  "notes": "Good productive day"
}
```

---

## Audio Processing

### POST `/audio/upload`
Upload audio file for emotion analysis.

**Headers:** 
- `Authorization: Bearer <token>`
- `Content-Type: multipart/form-data`

**Form Data:**
- `audio_file`: Audio file (wav, mp3, m4a)
- `emotion_id` (optional): Link to emotion entry
- `context` (optional): Recording context

**Response:**
```json
{
  "success": true,
  "message": "Audio uploaded successfully",
  "audio_log": {
    "id": 45,
    "file_path": "/audio/recordings/audio_123.wav",
    "duration": 15.2,
    "file_size": 245760,
    "format": "wav",
    "sample_rate": 44100,
    "recorded_at": "2024-01-20T15:30:00Z"
  }
}
```

### POST `/audio/analyze`
Analyze audio for emotional content.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "audio_log_id": 45
}
```

**Response:**
```json
{
  "success": true,
  "analysis": {
    "emotion_predictions": {
      "happy": 0.75,
      "calm": 0.15,
      "neutral": 0.08,
      "sad": 0.02
    },
    "dominant_emotion": "happy",
    "confidence": 0.75,
    "audio_features": {
      "pitch_mean": 180.5,
      "energy_level": 0.65,
      "tempo": 120,
      "tone": "positive"
    },
    "processed_at": "2024-01-20T15:35:00Z"
  }
}
```

### GET `/audio/{id}`
Get audio log details.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "success": true,
  "audio_log": {
    "id": 45,
    "emotion_id": 123,
    "file_path": "/audio/recordings/audio_123.wav",
    "duration": 15.2,
    "analysis": {
      "dominant_emotion": "happy",
      "confidence": 0.75
    },
    "recorded_at": "2024-01-20T15:30:00Z"
  }
}
```

---

## Analytics

### GET `/analytics/summary`
Get user's emotion analytics summary.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `period`: "week", "month", "quarter", "year"
- `start_date` (optional): Custom start date
- `end_date` (optional): Custom end date

**Response:**
```json
{
  "success": true,
  "analytics": {
    "period": "month",
    "period_start": "2024-01-01",
    "period_end": "2024-01-31",
    "total_entries": 85,
    "avg_mood": 7.2,
    "mood_variance": 1.8,
    "dominant_emotion": "happy",
    "emotion_distribution": {
      "happy": 0.35,
      "calm": 0.25,
      "neutral": 0.20,
      "anxious": 0.10,
      "sad": 0.10
    },
    "context_distribution": {
      "work": 0.40,
      "personal": 0.30,
      "social": 0.20,
      "health": 0.10
    },
    "trends": {
      "mood_trend": "improving",
      "most_active_day": "Wednesday",
      "best_time": "morning",
      "emotional_stability": "stable"
    },
    "insights": [
      "Your mood tends to be highest in the morning",
      "Work context shows the most emotional entries",
      "Your emotional stability has improved this month"
    ]
  }
}
```

### GET `/analytics/trends`
Get detailed trend analysis.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "success": true,
  "trends": {
    "daily_averages": [
      {"date": "2024-01-01", "avg_mood": 6.5, "entry_count": 3},
      {"date": "2024-01-02", "avg_mood": 7.2, "entry_count": 4}
    ],
    "weekly_patterns": {
      "Monday": 6.8,
      "Tuesday": 7.1,
      "Wednesday": 7.5,
      "Thursday": 7.2,
      "Friday": 7.8,
      "Saturday": 7.0,
      "Sunday": 6.5
    },
    "hourly_patterns": {
      "6": 6.5, "7": 7.0, "8": 7.2,
      "12": 7.5, "18": 7.0, "22": 6.8
    },
    "emotion_correlations": {
      "happy_confidence": 0.78,
      "stress_energy": -0.65
    }
  }
}
```

### GET `/analytics/insights`
Get personalized insights and recommendations.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "success": true,
  "insights": {
    "behavioral_patterns": [
      "You tend to feel happier in the morning",
      "Work-related entries show higher intensity emotions"
    ],
    "recommendations": [
      "Consider morning activities for mood boost",
      "Take breaks during work for emotional balance"
    ],
    "achievements": [
      "7-day consistent tracking streak",
      "Emotional awareness improvement"
    ],
    "goals": [
      {
        "type": "mood_stability",
        "target": 8.0,
        "current": 7.2,
        "progress": 0.72
      }
    ]
  }
}
```

---

## Games

### GET `/games/leaderboard`
Get game leaderboard.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `game`: "emotional_balance" (required)
- `period`: "daily", "weekly", "monthly", "all_time"

**Response:**
```json
{
