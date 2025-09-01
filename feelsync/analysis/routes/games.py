from flask import Blueprint, render_template, request, jsonify, session, current_app, redirect, url_for, flash
from flask_login import login_required, current_user
from models.database_models import db, GameSession, BehaviorData, SystemLog
from datetime import datetime, timedelta
import json
import random

games_bp = Blueprint('games', __name__, url_prefix='/games')

@games_bp.route('/')
@login_required
def index():
    """Games menu page"""
    # Check daily game limit
    today = datetime.utcnow().date()
    today_sessions = GameSession.query.filter(
        GameSession.user_id == current_user.id,
        db.func.date(GameSession.started_at) == today
    ).count()
    
    max_games_today = current_app.config.get('MAX_GAMES_PER_DAY', 10)
    games_remaining = max_games_today - today_sessions
    
    # Get user's game statistics
    game_stats = {}
    game_types = ['catch_thought', 'stat_balance', 'decision_maker']
    
    for game_type in game_types:
        stats = db.session.query(
            db.func.count(GameSession.id).label('sessions'),
            db.func.max(GameSession.score).label('best_score'),
            db.func.avg(GameSession.score).label('avg_score'),
            db.func.sum(GameSession.duration).label('total_time')
        ).filter_by(user_id=current_user.id, game_type=game_type).first()
        
        game_stats[game_type] = {
            'sessions': stats.sessions or 0,
            'best_score': int(stats.best_score) if stats.best_score else 0,
            'avg_score': round(stats.avg_score, 1) if stats.avg_score else 0,
            'total_time': int(stats.total_time) if stats.total_time else 0
        }
    
    return render_template('games/games_menu.html',
                         game_stats=game_stats,
                         games_remaining=games_remaining,
                         max_games=max_games_today)

@games_bp.route('/catch_thought')
@login_required
def catch_thought():
    """Catch the Thought game page"""
    return render_template('games/catch_thought.html')

@games_bp.route('/stat_balance')
@login_required
def stat_balance():
    """Stat Balancing game page"""
    return render_template('games/stat_balance.html')

@games_bp.route('/decision_maker')
@login_required
def decision_maker():
    """Decision Making game page"""
    return render_template('games/decision_maker.html')

@games_bp.route('/start_session', methods=['POST'])
@login_required
def start_session():
    """Start a new game session"""
    try:
        data = request.get_json()
        game_type = data.get('game_type')
        
        if not game_type or game_type not in ['catch_thought', 'stat_balance', 'decision_maker']:
            return jsonify({'error': 'Invalid game type'}), 400
        
        # Check daily limit
        today = datetime.utcnow().date()
        today_sessions = GameSession.query.filter(
            GameSession.user_id == current_user.id,
            db.func.date(GameSession.started_at) == today
        ).count()
        
        if today_sessions >= current_app.config.get('MAX_GAMES_PER_DAY', 10):
            return jsonify({'error': 'Daily game limit reached'}), 429
        
        # Create new session
        session_obj = GameSession(
            user_id=current_user.id,
            game_type=game_type,
            started_at=datetime.utcnow(),
            behavioral_data={}
        )
        
        db.session.add(session_obj)
        db.session.commit()
        
        # Store session ID in Flask session for tracking
        session['current_game_session_id'] = session_obj.id
        
        SystemLog.log('INFO', 'GAME_START', 
                     f'Game session started: {game_type}', 
                     user_id=current_user.id, session_id=session_obj.id)
        
        return jsonify({
            'success': True,
            'session_id': session_obj.id,
            'game_type': game_type
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to start game session: {str(e)}")
        return jsonify({'error': 'Failed to start game session'}), 500

@games_bp.route('/end_session', methods=['POST'])
@login_required
def end_session():
    """End current game session"""
    try:
        data = request.get_json()
        session_id = data.get('session_id') or session.get('current_game_session_id')
        
        if not session_id:
            return jsonify({'error': 'No active session found'}), 400
        
        # Get session
        session_obj = GameSession.query.filter_by(
            id=session_id, user_id=current_user.id
        ).first()
        
        if not session_obj:
            return jsonify({'error': 'Session not found'}), 404
        
        # Update session with final data
        session_obj.ended_at = datetime.utcnow()
        session_obj.score = data.get('final_score', 0)
        session_obj.completed = data.get('completed', True)
        session_obj.level_reached = data.get('level_reached', 1)
        session_obj.accuracy = data.get('accuracy', 0.0)
        session_obj.average_reaction_time = data.get('average_reaction_time', 0.0)
        session_obj.consistency_score = data.get('consistency_score', 0.0)
        session_obj.decisions_made = data.get('decisions_made', 0)
        
        # Calculate duration
        session_obj.calculate_duration()
        
        # Store additional behavioral data
        behavioral_metrics = data.get('behavioral_data', {})
        if behavioral_metrics:
            session_obj.behavioral_data.update(behavioral_metrics)
        
        db.session.commit()
        
        # Clear session tracking
        session.pop('current_game_session_id', None)
        
        SystemLog.log('INFO', 'GAME_END', 
                     f'Game session completed: {session_obj.game_type}', 
                     user_id=current_user.id, session_id=session_obj.id,
                     score=session_obj.score, duration=session_obj.duration)
        
        return jsonify({
            'success': True,
            'session_data': {
                'score': session_obj.score,
                'duration': session_obj.duration,
                'accuracy': session_obj.accuracy,
                'level_reached': session_obj.level_reached
            }
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to end game session: {str(e)}")
        return jsonify({'error': 'Failed to end game session'}), 500

@games_bp.route('/log_behavior', methods=['POST'])
@login_required
def log_behavior():
    """Log behavioral data point during gameplay"""
    try:
        data = request.get_json()
        session_id = data.get('session_id') or session.get('current_game_session_id')
        
        if not session_id:
            return jsonify({'error': 'No active session'}), 400
        
        # Verify session belongs to current user
        session_obj = GameSession.query.filter_by(
            id=session_id, user_id=current_user.id
        ).first()
        
        if not session_obj:
            return jsonify({'error': 'Invalid session'}), 404
        
        # Create behavior data entry
        behavior_data = BehaviorData(
            user_id=current_user.id,
            session_id=session_id,
            timestamp=datetime.utcnow(),
            reaction_time=data.get('reaction_time'),
            decision_type=data.get('decision_type'),
            decision_value=data.get('decision_value'),
            confidence_level=data.get('confidence_level'),
            emotional_state=data.get('emotional_state'),
            stress_level=data.get('stress_level'),
            accuracy=data.get('accuracy'),
            hesitation_time=data.get('hesitation_time'),
            game_level=data.get('game_level', 1),
            game_phase=data.get('game_phase'),
            difficulty=data.get('difficulty', 'normal'),
            metadata=data.get('metadata', {})
        )
        
        db.session.add(behavior_data)
        db.session.commit()
        
        return jsonify({'success': True, 'behavior_id': behavior_data.id})
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to log behavior data: {str(e)}")
        return jsonify({'error': 'Failed to log behavior data'}), 500

@games_bp.route('/get_scenarios/<game_type>')
@login_required
def get_scenarios(game_type):
    """Get game scenarios/content for specified game type"""
    try:
        scenarios = generate_game_scenarios(game_type, current_user)
        return jsonify({'scenarios': scenarios})
        
    except Exception as e:
        current_app.logger.error(f"Failed to get scenarios for {game_type}: {str(e)}")
        return jsonify({'error': 'Failed to load scenarios'}), 500

@games_bp.route('/leaderboard/<game_type>')
@login_required
def leaderboard(game_type):
    """Get leaderboard for specific game type"""
    if game_type not in ['catch_thought', 'stat_balance', 'decision_maker']:
        return jsonify({'error': 'Invalid game type'}), 400
    
    try:
        # Get top scores (anonymized)
        top_scores = db.session.query(
            GameSession.score,
            GameSession.accuracy,
            GameSession.level_reached
        ).filter(
            GameSession.game_type == game_type,
            GameSession.completed == True,
            GameSession.score.isnot(None)
        ).order_by(GameSession.score.desc()).limit(10).all()
        
        # Get user's best score and rank
        user_best = GameSession.query.filter_by(
            user_id=current_user.id,
            game_type=game_type,
            completed=True
        ).order_by(GameSession.score.desc()).first()
        
        user_rank = None
        if user_best:
            better_scores = GameSession.query.filter(
                GameSession.game_type == game_type,
                GameSession.completed == True,
                GameSession.score > user_best.score
            ).count()
            user_rank = better_scores + 1
        
        leaderboard_data = [
            {
                'rank': idx + 1,
                'score': score.score,
                'accuracy': round(score.accuracy, 1) if score.accuracy else 0,
                'level_reached': score.level_reached or 1
            }
            for idx, score in enumerate(top_scores)
        ]
        
        return jsonify({
            'leaderboard': leaderboard_data,
            'user_best_score': user_best.score if user_best else 0,
            'user_rank': user_rank
        })
        
    except Exception as e:
        current_app.logger.error(f"Failed to get leaderboard: {str(e)}")
        return jsonify({'error': 'Failed to load leaderboard'}), 500

@games_bp.route('/pause_session', methods=['POST'])
@login_required
def pause_session():
    """Pause current game session"""
    try:
        data = request.get_json()
        session_id = data.get('session_id') or session.get('current_game_session_id')
        
        if not session_id:
            return jsonify({'error': 'No active session'}), 400
        
        # Update session with pause data
        session_obj = GameSession.query.filter_by(
            id=session_id, user_id=current_user.id
        ).first()
        
        if not session_obj:
            return jsonify({'error': 'Session not found'}), 404
        
        # Store pause state in behavioral data
        pause_data = {
            'paused_at': datetime.utcnow().isoformat(),
            'current_score': data.get('current_score', 0),
            'current_level': data.get('current_level', 1),
            'time_played': data.get('time_played', 0)
        }
        
        if not session_obj.behavioral_data:
            session_obj.behavioral_data = {}
        session_obj.behavioral_data['pause_data'] = pause_data
        
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to pause session: {str(e)}")
        return jsonify({'error': 'Failed to pause session'}), 500

@games_bp.route('/resume_session', methods=['POST'])
@login_required
def resume_session():
    """Resume paused game session"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        session_obj = GameSession.query.filter_by(
            id=session_id, user_id=current_user.id
        ).first()
        
        if not session_obj:
            return jsonify({'error': 'Session not found'}), 404
        
        # Get pause data
        pause_data = session_obj.behavioral_data.get('pause_data', {}) if session_obj.behavioral_data else {}
        
        # Update session tracking
        session['current_game_session_id'] = session_id
        
        return jsonify({
            'success': True,
            'pause_data': pause_data
        })
        
    except Exception as e:
        current_app.logger.error(f"Failed to resume session: {str(e)}")
        return jsonify({'error': 'Failed to resume session'}), 500

def generate_game_scenarios(game_type, user):
    """Generate appropriate scenarios based on game type and user profile"""
    scenarios = {}
    
    if game_type == 'catch_thought':
        scenarios = {
            'positive_thoughts': [
                "I can handle this challenge",
                "I'm learning something new",
                "This is an opportunity to grow",
                "I have people who support me",
                "I'm doing my best"
            ],
            'negative_thoughts': [
                "This is too difficult for me",
                "I always mess things up",
                "Nobody understands me",
                "I can't do anything right",
                "Why do I even try?"
            ],
            'neutral_thoughts': [
                "I need to focus on this task",
                "What should I have for lunch?",
                "The weather is changing",
                "I should call my friend later",
                "Time to take a break"
            ]
        }
    
    elif game_type == 'stat_balance':
        scenarios = {
            'situations': [
                {
                    'title': 'Social Event Invitation',
                    'description': 'You\'re invited to a party where you don\'t know many people',
                    'stats': ['Social Energy', 'Anxiety', 'Confidence', 'Fun']
                },
                {
                    'title': 'Important Exam Tomorrow',
                    'description': 'You have a big exam tomorrow and feel unprepared',
                    'stats': ['Study Time', 'Stress', 'Sleep', 'Confidence']
                },
                {
                    'title': 'Friend Needs Help',
                    'description': 'Your friend asks for help when you\'re already overwhelmed',
                    'stats': ['Personal Time', 'Friendship', 'Stress', 'Guilt']
                }
            ]
        }
    
    elif game_type == 'decision_maker':
        scenarios = {
            'scenarios': [
                {
                    'id': 1,
                    'situation': 'On a crowded train, someone keeps talking loudly next to you',
                    'options': [
                        {'text': 'Quietly tolerate it', 'type': 'avoidant'},
                        {'text': 'Politely ask them to lower their voice', 'type': 'assertive'},
                        {'text': 'Give them an annoyed look', 'type': 'passive_aggressive'},
                        {'text': 'Move to another seat', 'type': 'practical'}
                    ]
                },
                {
                    'id': 2,
                    'situation': 'You see a classmate struggling with an assignment you understand well',
                    'options': [
                        {'text': 'Offer to help them', 'type': 'helpful'},
                        {'text': 'Mind your own business', 'type': 'avoidant'},
                        {'text': 'Wait for them to ask for help', 'type': 'passive'},
                        {'text': 'Give them a hint indirectly', 'type': 'indirect'}
                    ]
                },
                {
                    'id': 3,
                    'situation': 'Your friend cancels plans at the last minute for the third time',
                    'options': [
                        {'text': 'Tell them how disappointed you are', 'type': 'direct'},
                        {'text': 'Say it\'s okay and make new plans', 'type': 'accommodating'},
                        {'text': 'Stop making plans with them', 'type': 'withdrawing'},
                        {'text': 'Ask if everything is okay', 'type': 'caring'}
                    ]
                }
            ]
        }
    
    return scenarios

@games_bp.route('/game_feedback', methods=['POST'])
@login_required
def game_feedback():
    """Collect user feedback about game experience"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({'error': 'Session ID required'}), 400
        
        session_obj = GameSession.query.filter_by(
            id=session_id, user_id=current_user.id
        ).first()
        
        if not session_obj:
            return jsonify({'error': 'Session not found'}), 404
        
        # Store feedback in behavioral data
        feedback_data = {
            'enjoyment_rating': data.get('enjoyment_rating'),
            'difficulty_rating': data.get('difficulty_rating'),
            'engagement_level': data.get('engagement_level'),
            'comments': data.get('comments', ''),
            'would_play_again': data.get('would_play_again', False),
            'feedback_timestamp': datetime.utcnow().isoformat()
        }
        
        if not session_obj.behavioral_data:
            session_obj.behavioral_data = {}
        session_obj.behavioral_data['user_feedback'] = feedback_data
        
        db.session.commit()
        
        SystemLog.log('INFO', 'GAME_FEEDBACK', 
                     f'Feedback received for {session_obj.game_type}', 
                     user_id=current_user.id, session_id=session_id,
                     enjoyment=feedback_data['enjoyment_rating'])
        
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to save feedback: {str(e)}")
        return jsonify({'error': 'Failed to save feedback'}), 500
