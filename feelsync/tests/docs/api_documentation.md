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
