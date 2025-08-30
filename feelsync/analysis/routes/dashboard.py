from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from models.database_models import User, GameSession, BehaviorData, AnalysisReport, TherapistAccess, db
from models.behavior_analyzer import BehaviorAnalyzer
from datetime import datetime, timedelta
from sqlalchemy import func, desc
import json

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/')
@login_required
def index():
    """Main dashboard page"""
    # Get user statistics
    total_sessions = current_user.game_sessions.count()
    total_playtime = current_user.get_total_playtime()
    
    # Get recent sessions (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_sessions = current_user.game_sessions.filter(
        GameSession.started_at >= week_ago
    ).order_by(desc(GameSession.started_at)).limit(5).all()
    
    # Get game type statistics
    game_stats = db.session.query(
        GameSession.game_type,
        func.count(GameSession.id).label('count'),
        func.avg(GameSession.score).label('avg_score'),
        func.sum(GameSession.duration).label('total_time')
    ).filter_by(user_id=current_user.id).group_by(GameSession.game_type).all()
    
    # Get latest analysis report
    latest_report = current_user.analysis_reports.order_by(
        desc(AnalysisReport.generated_at)
    ).first()
    
    # Check if user has enough data for analysis
    can_generate_report = current_user.is_eligible_for_analysis()
    
    # Prepare data for charts
    chart_data = {
        'weekly_activity': get_weekly_activity_data(current_user.id),
        'game_performance': get_game_performance_data(current_user.id),
        'mood_trends': get_mood_trends_data(current_user.id)
    }
    
    return render_template('dashboard.html',
                         total_sessions=total_sessions,
                         total_playtime=total_playtime,
                         recent_sessions=recent_sessions,
                         game_stats=game_stats,
                         latest_report=latest_report,
                         can_generate_report=can_generate_report,
                         chart_data=chart_data)

@dashboard_bp.route('/games')
@login_required
def games():
    """Games selection page"""
    # Get user's game statistics
    game_stats = {}
    for game_type in ['catch_thought', 'stat_balance', 'decision_maker']:
        stats = db.session.query(
            func.count(GameSession.id).label('sessions'),
            func.max(GameSession.score).label('best_score'),
            func.avg(GameSession.score).label('avg_score'),
            func.sum(GameSession.duration).label('total_time')
        ).filter_by(user_id=current_user.id, game_type=game_type).first()
        
        game_stats[game_type] = {
            'sessions': stats.sessions or 0,
            'best_score': int(stats.best_score) if stats.best_score else 0,
            'avg_score': round(stats.avg_score, 1) if stats.avg_score else 0,
            'total_time': int(stats.total_time) if stats.total_time else 0
        }
    
    return render_template('games/games_menu.html', game_stats=game_stats)

@dashboard_bp.route('/progress')
@login_required
def progress():
    """Progress tracking page"""
    # Get progress data for different time periods
    periods = {
        'week': 7,
        'month': 30,
        'quarter': 90
    }
    
    progress_data = {}
    for period_name, days in periods.items():
        start_date = datetime.utcnow() - timedelta(days=days)
        
        sessions = current_user.game_sessions.filter(
            GameSession.started_at >= start_date
        ).all()
        
        if sessions:
            progress_data[period_name] = {
                'session_count': len(sessions),
                'avg_score': sum(s.score for s in sessions if s.score) / len([s for s in sessions if s.score]) if [s for s in sessions if s.score] else 0,
                'total_time': sum(s.duration for s in sessions if s.duration) or 0,
                'completion_rate': len([s for s in sessions if s.completed]) / len(sessions) * 100 if sessions else 0
            }
        else:
            progress_data[period_name] = {
                'session_count': 0,
                'avg_score': 0,
                'total_time': 0,
                'completion_rate': 0
            }
    
    # Get detailed performance trends
    performance_trends = get_performance_trends(current_user.id)
    
    return render_template('dashboard/progress.html',
                         progress_data=progress_data,
                         performance_trends=performance_trends)

@dashboard_bp.route('/insights')
@login_required
def insights():
    """Personal insights page"""
    if not current_user.is_eligible_for_analysis():
        flash('You need to complete at least 3 game sessions to view insights.', 'info')
        return redirect(url_for('dashboard.games'))
    
    # Get or generate latest insights
    analyzer = BehaviorAnalyzer()
    insights = analyzer.generate_personal_insights(current_user.id)
    
    # Get historical reports for comparison
    historical_reports = current_user.analysis_reports.order_by(
        desc(AnalysisReport.generated_at)
    ).limit(5).all()
    
    return render_template('dashboard/insights.html',
                         insights=insights,
                         historical_reports=historical_reports)

@dashboard_bp.route('/generate_report', methods=['POST'])
@login_required
def generate_report():
    """Generate a new analysis report"""
    if not current_user.is_eligible_for_analysis():
        return jsonify({'error': 'Insufficient data for analysis'}), 400
    
    try:
        analyzer = BehaviorAnalyzer()
        report = analyzer.generate_comprehensive_report(current_user.id)
        
        flash('New analysis report generated successfully!', 'success')
        return jsonify({'success': True, 'report_id': report.id})
        
    except Exception as e:
        current_app.logger.error(f"Report generation failed: {str(e)}")
        return jsonify({'error': 'Report generation failed'}), 500

@dashboard_bp.route('/report/<int:report_id>')
@login_required
def view_report(report_id):
    """View specific analysis report"""
    report = AnalysisReport.query.filter_by(
        id=report_id, user_id=current_user.id
    ).first_or_404()
    
    return render_template('analysis/personal_report.html', report=report)

@dashboard_bp.route('/therapist_access')
@login_required
def therapist_access():
    """Manage therapist access permissions"""
    access_permissions = TherapistAccess.query.filter_by(
        user_id=current_user.id
    ).all()
    
    return render_template('dashboard/therapist_access.html',
                         permissions=access_permissions)

@dashboard_bp.route('/grant_therapist_access', methods=['POST'])
@login_required
def grant_therapist_access():
    """Grant therapist access to user data"""
    therapist_email = request.form.get('therapist_email', '').strip().lower()
    duration_days = request.form.get('duration', type=int, default=30)
    
    if not therapist_email:
        flash('Please enter therapist email address.', 'error')
        return redirect(url_for('dashboard.therapist_access'))
    
    # Check if access already exists
    existing_access = TherapistAccess.query.filter_by(
        user_id=current_user.id,
        therapist_email=therapist_email
    ).first()
    
    if existing_access and existing_access.is_valid():
        flash('Active access already exists for this therapist.', 'warning')
        return redirect(url_for('dashboard.therapist_access'))
    
    # Create new access permission
    access = TherapistAccess(
        user_id=current_user.id,
        therapist_email=therapist_email,
        expires_at=datetime.utcnow() + timedelta(days=duration_days)
    )
    
    try:
        db.session.add(access)
        db.session.commit()
        flash(f'Access granted to {therapist_email} for {duration_days} days.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to grant therapist access: {str(e)}")
        flash('Failed to grant access. Please try again.', 'error')
    
    return redirect(url_for('dashboard.therapist_access'))

@dashboard_bp.route('/revoke_therapist_access/<int:access_id>', methods=['POST'])
@login_required
def revoke_therapist_access(access_id):
    """Revoke therapist access"""
    access = TherapistAccess.query.filter_by(
        id=access_id, user_id=current_user.id
    ).first_or_404()
    
    access.is_active = False
    
    try:
        db.session.commit()
        flash('Therapist access revoked successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to revoke therapist access: {str(e)}")
        flash('Failed to revoke access. Please try again.', 'error')
    
    return redirect(url_for('dashboard.therapist_access'))

@dashboard_bp.route('/api/activity_data')
@login_required
def api_activity_data():
    """API endpoint for activity chart data"""
    days = request.args.get('days', 30, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    activity_data = get_daily_activity_data(current_user.id, start_date)
    
    return jsonify(activity_data)

@dashboard_bp.route('/api/performance_data')
@login_required
def api_performance_data():
    """API endpoint for performance chart data"""
    game_type = request.args.get('game_type', 'all')
    
    performance_data = get_game_performance_data(current_user.id, game_type)
    
    return jsonify(performance_data)

def get_weekly_activity_data(user_id):
    """Get weekly activity data for charts"""
    week_ago = datetime.utcnow() - timedelta(days=7)
    
    daily_data = db.session.query(
        func.date(GameSession.started_at).label('date'),
        func.count(GameSession.id).label('sessions'),
        func.sum(GameSession.duration).label('total_time')
    ).filter(
        GameSession.user_id == user_id,
        GameSession.started_at >= week_ago
    ).group_by(func.date(GameSession.started_at)).all()
    
    # Fill in missing days with zero values
    data = []
    for i in range(7):
        date = (datetime.utcnow() - timedelta(days=6-i)).date()
        day_data = next((d for d in daily_data if d.date == date), None)
        
        data.append({
            'date': date.strftime('%Y-%m-%d'),
            'sessions': day_data.sessions if day_data else 0,
            'total_time': day_data.total_time if day_data else 0
        })
    
    return data

def get_game_performance_data(user_id, game_type=None):
    """Get game performance data for charts"""
    query = GameSession.query.filter_by(user_id=user_id)
    
    if game_type and game_type != 'all':
        query = query.filter_by(game_type=game_type)
    
    sessions = query.order_by(GameSession.started_at).limit(50).all()
    
    data = []
    for session in sessions:
        data.append({
            'date': session.started_at.strftime('%Y-%m-%d %H:%M') if session.started_at else '',
            'score': session.score or 0,
            'accuracy': session.accuracy or 0,
            'reaction_time': session.average_reaction_time or 0,
            'game_type': session.game_type
        })
    
    return data

def get_mood_trends_data(user_id):
    """Get mood trends from behavior data"""
    mood_data = db.session.query(
        func.date(BehaviorData.timestamp).label('date'),
        func.avg(BehaviorData.stress_level).label('avg_stress'),
        BehaviorData.emotional_state
    ).filter(
        BehaviorData.user_id == user_id,
        BehaviorData.emotional_state.isnot(None)
    ).group_by(
        func.date(BehaviorData.timestamp),
        BehaviorData.emotional_state
    ).order_by(func.date(BehaviorData.timestamp)).all()
    
    # Process mood data into chart format
    processed_data = {}
    for data_point in mood_data:
        date_str = data_point.date.strftime('%Y-%m-%d')
        if date_str not in processed_data:
            processed_data[date_str] = {'stress_level': 0, 'mood_distribution': {}}
        
        processed_data[date_str]['stress_level'] = data_point.avg_stress or 0
        processed_data[date_str]['mood_distribution'][data_point.emotional_state] = 1
    
    return [
        {
            'date': date,
            'stress_level': data['stress_level'],
            'mood_distribution': data['mood_distribution']
        }
        for date, data in sorted(processed_data.items())
    ]

def get_daily_activity_data(user_id, start_date):
    """Get daily activity data"""
    sessions = db.session.query(
        func.date(GameSession.started_at).label('date'),
        func.count(GameSession.id).label('session_count'),
        func.sum(GameSession.duration).label('total_duration'),
        func.avg(GameSession.score).label('avg_score')
    ).filter(
        GameSession.user_id == user_id,
        GameSession.started_at >= start_date
    ).group_by(func.date(GameSession.started_at)).all()
    
    return [
        {
            'date': session.date.strftime('%Y-%m-%d'),
            'session_count': session.session_count,
            'total_duration': session.total_duration or 0,
            'avg_score': round(session.avg_score, 2) if session.avg_score else 0
        }
        for session in sessions
    ]

def get_performance_trends(user_id):
    """Get performance trends over time"""
    sessions = GameSession.query.filter_by(
        user_id=user_id
    ).order_by(GameSession.started_at).all()
    
    if len(sessions) < 5:
        return None
    
    # Calculate rolling averages
    window_size = min(5, len(sessions) // 3)
    trends = []
    
    for i in range(window_size, len(sessions)):
        window_sessions = sessions[i-window_size:i]
        avg_score = sum(s.score for s in window_sessions if s.score) / len([s for s in window_sessions if s.score])
        avg_reaction_time = sum(s.average_reaction_time for s in window_sessions if s.average_reaction_time) / len([s for s in window_sessions if s.average_reaction_time])
        
        trends.append({
            'session_number': i + 1,
            'avg_score': avg_score,
            'avg_reaction_time': avg_reaction_time,
            'date': sessions[i].started_at.strftime('%Y-%m-%d') if sessions[i].started_at else ''
        })
    
    return trends
