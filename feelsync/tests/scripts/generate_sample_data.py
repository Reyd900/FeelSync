#!/usr/bin/env python3
"""
Sample Data Generation Script for FeelSync
Generates realistic sample data for testing and development.
"""

import os
import sys
import random
import argparse
from datetime import datetime, timedelta
import json
import uuid
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from config.settings import DATABASE_CONFIG

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample emotion data templates
EMOTION_TEMPLATES = {
    'happy': {
        'descriptions': [
            "Had an amazing day at work! Everything went perfectly.",
            "Just got great news about my promotion!",
            "Spent quality time with family and friends today.",
            "Beautiful weather made me feel so energized!",
            "Accomplished all my goals for today.",
            "Received unexpected good news that made my day.",
            "Had a wonderful conversation that lifted my spirits.",
            "Feeling grateful for all the positive things in my life.",
            "Just finished a workout and feeling fantastic!",
            "Celebrated a milestone achievement today."
        ],
        'intensity_range': (7, 10),
        'contexts': ['work', 'personal', 'health', 'social', 'achievement']
    },
    'sad': {
        'descriptions': [
            "Feeling down after receiving disappointing news.",
            "Missing someone special today.",
            "Things didn't go as planned and I'm feeling low.",
            "Had a difficult conversation that left me upset.",
            "Feeling overwhelmed by recent challenges.",
            "Reflecting on past mistakes and feeling regretful.",
            "Received news that made me feel melancholy.",
            "Struggling with feelings of loneliness today.",
            "Disappointed by an outcome I was hoping for.",
            "Feeling emotionally drained after a tough day."
        ],
        'intensity_range': (6, 9),
        'contexts': ['personal', 'work', 'relationships', 'health', 'loss']
    },
    'angry': {
        'descriptions': [
            "Frustrated by unfair treatment at work today.",
            "Traffic was terrible and made me late for everything.",
            "Someone was disrespectful and it really bothered me.",
            "Dealing with technical issues that won't resolve.",
            "Upset about a decision that affects me negatively.",
            "Feeling irritated by people not keeping their promises.",
            "Annoyed by constant interruptions during important tasks.",
            "Frustrated with bureaucracy and red tape.",
            "Mad about being misunderstood in an important conversation.",
            "Irritated by noise and distractions in my environment."
        ],
        'intensity_range': (6, 9),
        'contexts': ['work', 'traffic', 'social', 'technology', 'injustice']
    },
    'anxious': {
        'descriptions': [
            "Worried about an upcoming important presentation.",
            "Feeling nervous about meeting new people tomorrow.",
            "Concerned about financial responsibilities this month.",
            "Anxious about a medical appointment next week.",
            "Stressed about deadline pressures at work.",
            "Feeling uneasy about traveling to unfamiliar places.",
            "Worried about making the right decision in a difficult situation.",
            "Nervous about performance in an upcoming exam.",
            "Anxious about relationship changes happening soon.",
            "Feeling overwhelmed by too many responsibilities."
        ],
        'intensity_range': (5, 8),
        'contexts': ['work', 'health', 'social', 'financial', 'future']
    },
    'excited': {
        'descriptions': [
            "Can't wait for my vacation next week!",
            "So excited about the new project I'm starting.",
            "Looking forward to seeing old friends this weekend.",
            "Thrilled about the concert tickets I just bought.",
            "Excited to try the new restaurant everyone's talking about.",
            "Can't contain my enthusiasm for the upcoming event.",
            "Feeling energetic about new opportunities ahead.",
            "Excited about learning a new skill I've always wanted.",
            "Thrilled about the surprise I'm planning for someone.",
            "Looking forward to the adventure trip I booked."
        ],
        'intensity_range': (7, 10),
        'contexts': ['travel', 'social', 'entertainment', 'learning', 'adventure']
    },
    'neutral': {
        'descriptions': [
            "Having a regular day, nothing particularly special.",
            "Feeling calm and balanced today.",
            "Just going through my normal routine.",
            "Nothing eventful happened, just a typical day.",
            "Feeling steady and focused on my tasks.",
            "Had a quiet day with some productive moments.",
            "Feeling content with the current pace of things.",
            "Just maintaining my usual energy levels today.",
            "Nothing particularly emotional, just existing peacefully.",
            "Having an ordinary day with mixed small moments."
        ],
        'intensity_range': (3, 6),
        'contexts': ['routine', 'work', 'rest', 'reflection', 'maintenance']
    },
    'grateful': {
        'descriptions': [
            "Thankful for the support I received from friends today.",
            "Appreciating the small moments that made me smile.",
            "Grateful for my health and wellbeing.",
            "Thankful for the opportunities I have in life.",
            "Appreciating the beautiful nature around me.",
            "Grateful for the progress I've made recently.",
            "Thankful for the kindness strangers showed me.",
            "Appreciating the comfort of home after a long day.",
            "Grateful for the lessons learned from recent experiences.",
            "Thankful for the time I had to relax and recharge."
        ],
        'intensity_range': (6, 9),
        'contexts': ['relationships', 'nature', 'health', 'growth', 'comfort']
    }
}

# Sample user profiles
USER_PROFILES = [
    {'name': 'Alice Johnson', 'age': 28, 'occupation': 'Software Engineer', 'location': 'San Francisco'},
    {'name': 'Bob Smith', 'age': 35, 'occupation': 'Teacher', 'location': 'Chicago'},
    {'name': 'Carol Davis', 'age': 42, 'occupation': 'Marketing Manager', 'location': 'New York'},
    {'name': 'David Wilson', 'age': 31, 'occupation': 'Freelance Designer', 'location': 'Austin'},
    {'name': 'Emma Brown', 'age': 26, 'occupation': 'Student', 'location': 'Boston'},
    {'name': 'Frank Miller', 'age': 45, 'occupation': 'Sales Director', 'location': 'Seattle'},
    {'name': 'Grace Taylor', 'age': 33, 'occupation': 'Nurse', 'location': 'Denver'},
    {'name': 'Henry Garcia', 'age': 29, 'occupation': 'Data Scientist', 'location': 'Portland'},
    {'name': 'Ivy Anderson', 'age': 37, 'occupation': 'Consultant', 'location': 'Miami'},
    {'name': 'Jack Thomas', 'age': 24, 'occupation': 'Graduate Student', 'location': 'Philadelphia'}
]

def generate_users(db_manager: DatabaseManager, count: int = 10) -> list:
    """Generate sample users."""
    logger.info(f"Generating {count} sample users...")
    
    users = []
    
    for i in range(count):
        if i < len(USER_PROFILES):
            profile = USER_PROFILES[i]
        else:
            # Generate additional users with random data
            profile = {
                'name': f'User {i+1}',
                'age': random.randint(18, 65),
                'occupation': random.choice(['Engineer', 'Teacher', 'Designer', 'Manager', 'Student']),
                'location': random.choice(['New York', 'San Francisco', 'Chicago', 'Boston', 'Seattle'])
            }
        
        user_data = {
            'username': f"user{i+1}",
            'email': f"user{i+1}@example.com",
            'name': profile['name'],
            'age': profile['age'],
            'occupation': profile['occupation'],
            'location': profile['location'],
            'created_at': datetime.now() - timedelta(days=random.randint(1, 365))
        }
        
        # Insert user
        user_id = db_manager.execute(
            """INSERT INTO users (username, email, name, age, occupation, location, created_at) 
               VALUES (%(username)s, %(email)s, %(name)s, %(age)s, %(occupation)s, %(location)s, %(created_at)s)
               RETURNING id""",
            user_data
        )
        
        if user_id:
            user_data['id'] = user_id[0][0] if isinstance(user_id[0], tuple) else user_id[0]
            users.append(user_data)
            logger.debug(f"Created user: {user_data['username']}")
    
    logger.info(f"Successfully created {len(users)} users")
    return users

def generate_emotions(db_manager: DatabaseManager, users: list, count: int = 1000) -> list:
    """Generate sample emotion entries."""
    logger.info(f"Generating {count} sample emotions...")
    
    emotions = []
    start_date = datetime.now() - timedelta(days=90)  # Last 90 days
    
    for i in range(count):
        user = random.choice(users)
        emotion_type = random.choice(list(EMOTION_TEMPLATES.keys()))
        template = EMOTION_TEMPLATES[emotion_type]
        
        # Generate timestamp (more recent entries more likely)
        days_ago = random.triangular(0, 90, 5)  # Bias towards recent days
        timestamp = start_date + timedelta(days=days_ago, hours=random.randint(6, 23), minutes=random.randint(0, 59))
        
        emotion_data = {
            'user_id': user['id'],
            'emotion': emotion_type,
            'intensity': random.randint(*template['intensity_range']),
            'description': random.choice(template['descriptions']),
            'context': random.choice(template['contexts']),
            'timestamp': timestamp
        }
        
        # Insert emotion
        emotion_id = db_manager.execute(
            """INSERT INTO emotions (user_id, emotion, intensity, description, context, timestamp) 
               VALUES (%(user_id)s, %(emotion)s, %(intensity)s, %(description)s, %(context)s, %(timestamp)s)
               RETURNING id""",
            emotion_data
        )
        
        if emotion_id:
            emotion_data['id'] = emotion_id[0][0] if isinstance(emotion_id[0], tuple) else emotion_id[0]
            emotions.append(emotion_data)
    
    logger.info(f"Successfully created {len(emotions)} emotion entries")
    return emotions

def generate_mood_patterns(db_manager: DatabaseManager, users: list, days: int = 30) -> list:
    """Generate daily mood pattern entries."""
    logger.info(f"Generating {days} days of mood patterns for {len(users)} users...")
    
    patterns = []
    
    for user in users:
        for day in range(days):
            date = datetime.now().date() - timedelta(days=day)
            
            # Generate realistic mood progression throughout the day
            morning_mood = random.randint(4, 8)
            afternoon_mood = morning_mood + random.randint(-2, 3)
            evening_mood = afternoon_mood + random.randint(-2, 2)
            
            # Clamp values between 1 and 10
            afternoon_mood = max(1, min(10, afternoon_mood))
            evening_mood = max(1, min(10, evening_mood))
            
            pattern_data = {
                'user_id': user['id'],
                'date': date,
                'morning_mood': morning_mood,
                'afternoon_mood': afternoon_mood,
                'evening_mood': evening_mood,
                'average_mood': round((morning_mood + afternoon_mood + evening_mood) / 3, 1),
                'notes': f"Generated pattern for {date}"
            }
            
            # Insert mood pattern
            db_manager.execute(
                """INSERT INTO mood_patterns (user_id, date, morning_mood, afternoon_mood, evening_mood, average_mood, notes) 
                   VALUES (%(user_id)s, %(date)s, %(morning_mood)s, %(afternoon_mood)s, %(evening_mood)s, %(average_mood)s, %(notes)s)""",
                pattern_data
            )
            
            patterns.append(pattern_data)
    
    logger.info(f"Successfully created {len(patterns)} mood pattern entries")
    return patterns

def generate_audio_logs(db_manager: DatabaseManager, emotions: list, percentage: int = 30) -> list:
    """Generate sample audio log entries for a percentage of emotions."""
    logger.info(f"Generating audio logs for {percentage}% of emotions...")
    
    audio_logs = []
    emotions_with_audio = random.sample(emotions, int(len(emotions) * percentage / 100))
    
    for emotion in emotions_with_audio:
        # Generate mock audio file path
        audio_filename = f"audio_{emotion['id']}_{uuid.uuid4().hex[:8]}.wav"
        audio_path = os.path.join("audio_data", "recordings", audio_filename)
        
        audio_data = {
            'emotion_id': emotion['id'],
            'file_path': audio_path,
            'duration': random.uniform(2.0, 30.0),  # 2-30 seconds
            'file_size': random.randint(50000, 500000),  # 50KB - 500KB
            'sample_rate': random.choice([44100, 48000]),
            'format': 'wav',
            'recorded_at': emotion['timestamp']
        }
        
        # Insert audio log
        db_manager.execute(
            """INSERT INTO audio_logs (emotion_id, file_path, duration, file_size, sample_rate, format, recorded_at) 
               VALUES (%(emotion_id)s, %(file_path)s, %(duration)s, %(file_size)s, %(sample_rate)s, %(format)s, %(recorded_at)s)""",
            audio_data
        )
        
        audio_logs.append(audio_data)
    
    logger.info(f"Successfully created {len(audio_logs)} audio log entries")
    return audio_logs

def generate_analytics_data(db_manager: DatabaseManager, users: list) -> list:
    """Generate sample analytics data."""
    logger.info("Generating analytics data...")
    
    analytics = []
    
    for user in users:
        # Generate weekly analytics for the last 12 weeks
        for week in range(12):
            week_start = datetime.now().date() - timedelta(weeks=week)
            
            analytics_data = {
                'user_id': user['id'],
                'period_type': 'weekly',
                'period_start': week_start,
                'period_end': week_start + timedelta(days=6),
                'total_entries': random.randint(3, 21),  # 3-21 entries per week
                'avg_mood': random.uniform(4.0, 8.0),
                'mood_variance': random.uniform(0.5, 3.0),
                'dominant_emotion': random.choice(list(EMOTION_TEMPLATES.keys())),
                'emotion_distribution': json.dumps({
                    emotion: random.uniform(0.05, 0.4) 
                    for emotion in random.sample(list(EMOTION_TEMPLATES.keys()), 4)
                }),
                'insights': json.dumps([
                    f"Most active on {random.choice(['Monday', 'Wednesday', 'Friday'])}",
                    f"Mood tends to be higher in the {random.choice(['morning', 'evening'])}",
                    f"Strong correlation with {random.choice(['work', 'social', 'health'])} context"
                ])
            }
            
            # Insert analytics
            db_manager.execute(
                """INSERT INTO analytics (user_id, period_type, period_start, period_end, total_entries, 
                   avg_mood, mood_variance, dominant_emotion, emotion_distribution, insights) 
                   VALUES (%(user_id)s, %(period_type)s, %(period_start)s, %(period_end)s, %(total_entries)s,
                   %(avg_mood)s, %(mood_variance)s, %(dominant_emotion)s, %(emotion_distribution)s, %(insights)s)""",
                analytics_data
            )
            
            analytics.append(analytics_data)
    
    logger.info(f"Successfully created {len(analytics)} analytics entries")
    return analytics

def generate_all_sample_data(db_manager: DatabaseManager, 
                           num_users: int = 10,
                           num_emotions: int = 1000,
                           mood_days: int = 30,
                           audio_percentage: int = 30):
    """Generate all types of sample data."""
    logger.info("Starting sample data generation...")
    
    # Generate users
    users = generate_users(db_manager, num_users)
    
    # Generate emotions
    emotions = generate_emotions(db_manager, users, num_emotions)
    
    # Generate mood patterns
    mood_patterns = generate_mood_patterns(db_manager, users, mood_days)
    
    # Generate audio logs
    audio_logs = generate_audio_logs(db_manager, emotions, audio_percentage)
    
    # Generate analytics
    analytics = generate_analytics_data(db_manager, users)
    
    # Summary
    summary = {
        'users': len(users),
        'emotions': len(emotions),
        'mood_patterns': len(mood_patterns),
        'audio_logs': len(audio_logs),
        'analytics': len(analytics),
        'generation_timestamp': datetime.now().isoformat()
    }
    
    logger.info("\n" + "="*50)
    logger.info("SAMPLE DATA GENERATION COMPLETE")
    logger.info("="*50)
    for key, value in summary.items():
        if key != 'generation_timestamp':
            logger.info(f"{key.replace('_', ' ').title()}: {value}")
    
    return summary

def clear_existing_data(db_manager: DatabaseManager):
    """Clear existing sample data."""
    logger.info("Clearing existing sample data...")
    
    tables = ['analytics', 'audio_logs', 'mood_patterns', 'emotions', 'users']
    
    for table in tables:
        db_manager.execute(f"DELETE FROM {table}")
        logger.info(f"Cleared {table} table")
    
    # Reset sequences
    for table in tables:
        db_manager.execute(f"ALTER SEQUENCE {table}_id_seq RESTART WITH 1")
    
    logger.info("All sample data cleared")

def export_sample_data(db_manager: DatabaseManager, output_file: str):
    """Export generated sample data to JSON file."""
    logger.info(f"Exporting sample data to {output_file}...")
    
    export_data = {}
    
    # Export all tables
    tables = ['users', 'emotions', 'mood_patterns', 'audio_logs', 'analytics']
    
    for table in tables:
        data = db_manager.fetch_all(f"SELECT * FROM {table}")
        if data:
            # Get column names
            columns = [desc[0] for desc in db_manager.cursor.description]
            # Convert to list of dictionaries
            export_data[table] = [
                dict(zip(columns, row)) for row in data
            ]
        else:
            export_data[table] = []
    
    # Convert datetime objects to strings for JSON serialization
    def json_serial(obj):
        if isinstance(obj, (datetime, datetime.date)):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")
    
    with open(output_file, 'w') as f:
        json.dump(export_data, f, indent=2, default=json_serial)
    
    logger.info(f"Sample data exported to {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Generate sample data for FeelSync")
    parser.add_argument('--users', type=int, default=10, help='Number of users to generate')
    parser.add_argument('--emotions', type=int, default=1000, help='Number of emotion entries to generate')
    parser.add_argument('--mood-days', type=int, default=30, help='Number of days of mood patterns')
    parser.add_argument('--audio-percentage', type=int, default=30, help='Percentage of emotions with audio')
    parser.add_argument('--clear', action='store_true', help='Clear existing data first')
    parser.add_argument('--export', type=str, help='Export data to JSON file')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be generated without creating data')
    
    args = parser.parse_args()
    
    if args.dry_run:
        logger.info("DRY RUN - No data will be generated")
        logger.info(f"Would generate:")
        logger.info(f"  - {args.users} users")
        logger.info(f"  - {args.emotions} emotion entries")
        logger.info(f"  - {args.mood_days * args.users} mood pattern entries")
        logger.info(f"  - ~{int(args.emotions * args.audio_percentage / 100)} audio logs")
        logger.info(f"  - {12 * args.users} analytics entries")
        return
    
    try:
        # Initialize database connection
        db_manager = DatabaseManager()
        db_manager.connect()
        
        if args.clear:
            clear_existing_data(db_manager)
        
        # Generate sample data
        summary = generate_all_sample_data(
            db_manager=db_manager,
            num_users=args.users,
            num_emotions=args.emotions,
            mood_days=args.mood_days,
            audio_percentage=args.audio_percentage
        )
        
        # Export if requested
        if args.export:
            export_sample_data(db_manager, args.export)
        
        logger.info("Sample data generation completed successfully!")
        
    except Exception as e:
        logger.error(f"Sample data generation failed: {str(e)}")
        raise
    
    finally:
        if 'db_manager' in locals():
            db_manager.disconnect()

if __name__ == "__main__":
    main()
