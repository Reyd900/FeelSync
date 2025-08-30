#!/usr/bin/env python3
"""
Database setup script for FeelSync platform
Creates tables, indexes, and sample data for development
"""

import os
import sys
import json
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
import numpy as np

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models.database_models import db, User, GameSession, BehaviorAnalysis, ConsentRecord
from config import DevelopmentConfig

def create_database():
    """Create database tables"""
    print("Creating database tables...")
    
    with app.app_context():
        # Drop all tables (use with caution!)
        db.drop_all()
        
        # Create all tables
        db.create_all()
        
        print("✅ Database tables created successfully!")

def create_indexes():
    """Create database indexes for better performance"""
    print("Creating database indexes...")
    
    with app.app_context():
        # Create indexes for common queries
        db.engine.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_email ON users(email);
            CREATE INDEX IF NOT EXISTS idx_user_created_at ON users(created_at);
            CREATE INDEX IF NOT EXISTS idx_session_user_id ON game_sessions(user_id);
            CREATE INDEX IF NOT EXISTS idx_session_created_at ON game_sessions(created_at);
            CREATE INDEX IF NOT EXISTS idx_analysis_user_id ON behavior_analyses(user_id);
            CREATE INDEX IF NOT EXISTS idx_analysis_created_at ON behavior_analyses(created_at);
        """)
        
        print("✅ Database indexes created successfully!")

def create_sample_users():
    """Create sample users for development"""
    print("Creating sample users...")
    
    sample_users = [
        {
            'username': 'alice_teen',
            'email': 'alice@example.com',
            'password': 'password123',
            'age': 16,
            'gender': 'female',
            'consent_given': True,
            'parental_consent': True
        },
        {
            'username': 'bob_student',
            'email': 'bob@example.com',
            'password': 'password123',
            'age': 17,
            'gender': 'male',
            'consent_given': True,
            'parental_consent': True
        },
        {
            'username': 'charlie_user',
            'email': 'charlie@example.com',
            'password': 'password123',
            'age': 15,
            'gender': 'non-binary',
            'consent_given': True,
            'parental_consent': True
        },
        {
            'username': 'dr_therapist',
            'email': 'therapist@example.com',
            'password': 'therapist123',
            'age': 35,
            'gender': 'female',
            'consent_given': True,
            'parental_consent': True,
            'is_therapist': True
        },
        {
            'username': 'demo_user',
            'email': 'demo@example.com',
            'password': 'demo123',
            'age': 16,
            'gender': 'prefer_not_to_say',
            'consent_given': True,
            'parental_consent': True
        }
    ]
    
    with app.app_context():
        for user_data in sample_users:
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                password_hash=generate_password_hash(user_data['password']),
                age=user_data['age'],
                gender=user_data['gender'],
                consent_given=user_data['consent_given'],
                parental_consent=user_data['parental_consent'],
                is_therapist=user_data.get('is_therapist', False),
                anonymized_id=f"anon_{user_data['username']}"
            )
            
            db.session.add(user)
        
        db.session.commit()
        print("✅ Sample users created successfully!")

def create_sample_game_sessions():
    """Create sample game sessions with realistic behavioral data"""
    print("Creating sample game sessions...")
    
    with app.app_context():
        users = User.query.filter_by(is_therapist=False).all()
        
        game_types = ['catch_thought', 'stat_balance', 'decision_maker']
        
        for user in users:
            # Create 5-10 sessions per user over the past 30 days
            num_sessions = np.random.randint(5, 11)
            
            for i in range(num_sessions):
                # Random date in the past 30 days
                days_ago = np.random.randint(0, 31)
                session_date = datetime.utcnow() - timedelta(days=days_ago)
                
                game_type = np.random.choice(game_types)
                
                # Generate realistic behavioral data based on game type
                behavioral_data = generate_sample_behavioral_data(game_type, user.age)
                
                session = GameSession(
                    user_id=user.id,
                    game_type=game_type,
                    start_time=session_date,
                    end_time=session_date + timedelta(seconds=behavioral_data['duration']),
                    duration=behavioral_data['duration'],
                    completed=True,
                    score=behavioral_data['score'],
                    accuracy=behavioral_data['accuracy'],
                    game_data=json.dumps(behavioral_data),
                    created_at=session_date
                )
                
                db.session.add(session)
        
        db.session.commit()
        print("✅ Sample game sessions created successfully!")

def generate_sample_behavioral_data(game_type, user_age):
    """Generate realistic behavioral data for different game types"""
    
    base_data = {
        'duration': 0,
        'score': 0,
        'accuracy': 0.0,
        'reactionTimes': [],
        'mistakes': 0,
        'totalClicks': 0,
        'hesitationTimes': [],
        'emotionalChoices': {'positive': 0, 'negative': 0, 'neutral': 0}
    }
    
    if game_type == 'catch_thought':
        # Catch the Thought specific data
        duration = 60  # 60 seconds
        total_bubbles = np.random.randint(15, 25)
        caught_bubbles = np.random.randint(int(total_bubbles * 0.6), total_bubbles)
        
        # Generate reaction times (influenced by age - younger might be faster but less consistent)
        if user_age < 16:
            base_rt = np.random.normal(600, 200)  # Faster but more variable
        else:
            base_rt = np.random.normal(750, 150)  # Slightly slower but more consistent
        
        reaction_times = [max(200, int(np.random.normal(base_rt, 150))) for _ in range(caught_bubbles)]
        
        # Generate hesitation times (longer reaction times)
        hesitation_times = [rt for rt in reaction_times if rt > 1000]
        
        # Emotional choices (random distribution)
        pos_choices = np.random.randint(0, caught_bubbles // 2)
        neg_choices = np.random.randint(0, caught_bubbles - pos_choices)
        neu_choices = caught_bubbles - pos_choices - neg_choices
        
        base_data.update({
            'duration': duration,
            'score': caught_bubbles * 10,
            'accuracy': caught_bubbles / total_bubbles,
            'reactionTimes': reaction_times,
            'mistakes': total_bubbles - caught_bubbles,
            'totalClicks': caught_bubbles,
            'hesitationTimes': hesitation_times,
            'emotionalChoices': {
                'positive': pos_choices,
                'negative': neg_choices,
                'neutral': neu_choices
            }
        })
    
    elif game_type == 'stat_balance':
        # Stat Balance specific data
        duration = 120  # 120 seconds
        total_decisions = np.random.randint(20, 35)
        correct_decisions = np.random.randint(int(total_decisions * 0.5), total_decisions)
        
        # Decision times (typically longer than reaction times)
        decision_times = [max(500, int(np.random.normal(1200, 400))) for _ in range(total_decisions)]
        
        base_data.update({
            'duration': duration,
            'score': correct_decisions * 5,
            'accuracy': correct_decisions / total_decisions,
            'reactionTimes': decision_times,
            'decisionTimes': decision_times,
            'mistakes': total_decisions - correct_decisions,
            'totalClicks': total_decisions,
            'hesitationTimes': [dt for dt in decision_times if dt > 2000],
            'balanceEvents': np.random.randint(5, 15)
        })
    
    elif game_type == 'decision_maker':
        # Decision Maker specific data
        duration = np.random.randint(180, 300)  # 3-5 minutes
        total_scenarios = 10
        completed_scenarios = np.random.randint(8, 11)
        
        # Scenario response times
        response_times = [max(2000, int(np.random.normal(8000, 3000))) for _ in range(completed_scenarios)]
        
        # Generate scenario choices (A, B, C, D options)
        scenario_choices = [np.random.choice(['A', 'B', 'C', 'D']) for _ in range(completed_scenarios)]
        
        # Confidence ratings (1-5 scale)
        confidence_ratings = [np.random.randint(1, 6) for _ in range(completed_scenarios)]
        
        base_data.update({
            'duration': duration,
            'score': completed_scenarios * 10,
            'accuracy': 1.0,  # No wrong answers in decision making
            'reactionTimes': response_times,
            'decisionTimes': response_times,
            'mistakes': 0,
            'totalClicks': completed_scenarios,
            'hesitationTimes': [rt for rt in response_times if rt > 15000],  # Very long decisions
            'scenarioChoices': scenario_choices,
            'confidenceRatings': confidence_ratings,
            'completedScenarios': completed_scenarios
        })
    
    return base_data

def create_sample_analyses():
    """Create sample behavioral analyses for the sessions"""
    print("Creating sample behavioral analyses...")
    
    with app.app_context():
        from models.behavior_analyzer import BehaviorAnalyzer
        
        analyzer = BehaviorAnalyzer()
        sessions = GameSession.query.filter_by(completed=True).all()
        
        for session in sessions:
            if session.game_data:
                # Analyze the session
                analysis_result = analyzer.analyze_session(session.game_data)
                
                # Create analysis record
                analysis = BehaviorAnalysis(
                    user_id=session.user_id,
                    session_id=session.id,
                    anxiety_score=analysis_result['anxiety_score'],
                    depression_score=analysis_result['depression_score'],
                    attention_score=analysis_result['attention_score'],
                    impulsivity_score=analysis_result['impulsivity_score'],
                    emotional_regulation_score=analysis_result['emotional_regulation_score'],
                    predicted_cluster=analysis_result['predicted_cluster'],
                    confidence_score=analysis_result['confidence_score'],
                    risk_level=analysis_result['risk_level'],
                    requires_attention=analysis_result['requires_attention'],
                    analysis_data=json.dumps(analysis_result['detailed_metrics']),
                    insights=json.dumps(analysis_result['insights']),
                    created_at=session.created_at
                )
                
                db.session.add(analysis)
        
        db.session.commit()
        print("✅ Sample behavioral analyses created successfully!")

def create_consent_records():
    """Create consent records for sample users"""
    print("Creating consent records...")
    
    with app.app_context():
        users = User.query.all()
        
        consent_types = ['data_collection', 'behavioral_analysis', 'research_participation']
        
        for user in users:
            for consent_type in consent_types:
                consent = ConsentRecord(
                    user_id=user.id,
                    consent_type=consent_type,
                    consent_given=True,
                    consent_text=f"I consent to {consent_type.replace('_', ' ')} for the FeelSync platform.",
                    ip_address='127.0.0.1',
                    user_agent='Sample Data Generator',
                    timestamp=user.created_at
                )
                
                db.session.add(consent)
        
        db.session.commit()
        print("✅ Consent records created successfully!")

def verify_setup():
    """Verify that the database setup was successful"""
    print("\nVerifying database setup...")
    
    with app.app_context():
        user_count = User.query.count()
        session_count = GameSession.query.count()
        analysis_count = BehaviorAnalysis.query.count()
        consent_count = ConsentRecord.query.count()
        
        print(f"📊 Database Statistics:")
        print(f"   Users: {user_count}")
        print(f"   Game Sessions: {session_count}")
        print(f"   Behavioral Analyses: {analysis_count}")
        print(f"   Consent Records: {consent_count}")
        
        # Test a sample query
        sample_user = User.query.filter_by(username='demo_user').first()
        if sample_user:
            user_sessions = GameSession.query.filter_by(user_id=sample_user.id).count()
            print(f"   Sample user sessions: {user_sessions}")
        
        print("\n✅ Database setup verification completed!")

def main():
    """Main setup function"""
    print("🚀 Setting up FeelSync database...")
    print("=" * 50)
    
    # Configure app for development
    app.config.from_object(DevelopmentConfig)
    
    try:
        # Create database and tables
        create_database()
        
        # Create indexes for performance
        create_indexes()
        
        # Create sample data
        create_sample_users()
        create_sample_game_sessions()
        create_sample_analyses()
        create_consent_records()
        
        # Verify setup
        verify_setup()
        
        print("\n🎉 Database setup completed successfully!")
        print("\nSample login credentials:")
        print("  Email: demo@example.com")
        print("  Password: demo123")
        print("\n  Therapist login:")
        print("  Email: therapist@example.com") 
        print("  Password: therapist123")
        
    except Exception as e:
        print(f"\n❌ Error during setup: {e}")
        print("Please check your database configuration and try again.")
        sys.exit(1)

if __name__ == '__main__':
    main()
