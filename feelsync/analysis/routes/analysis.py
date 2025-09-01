from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app, send_file
from flask_login import login_required, current_user
from models.database_models import db, AnalysisReport, GameSession, BehaviorData, TherapistAccess, SystemLog
from models.behavior_analyzer import BehaviorAnalyzer
from utils.report_generator import ReportGenerator
from datetime import datetime, timedelta
from sqlalchemy import desc, func
import json
import io
import base64

analysis_bp = Blueprint('analysis', __name__, url_prefix='/analysis')

@analysis_bp.route('/')
@login_required
def index():
    """Analysis dashboard"""
    # Check if user has enough data for analysis
    if not current_user.is_eligible_for_analysis():
        flash('You need to complete at least 3 game sessions to view your analysis.', 'info')
        return redirect(url_for('games.index'))
    
    # Get recent reports
    recent_reports = current_user.analysis_reports.order_by(
        desc(AnalysisReport.generated_at)
    ).limit(5).all()
    
    # Get analysis statistics
    total_reports = current_user.analysis_reports.count()
    last_analysis = recent_reports[0] if recent_reports else None
    
    # Get session statistics for analysis
    total_sessions = current_user.game_sessions.count()
    analyzed_sessions = sum(report.sessions_analyzed for report in recent_reports)
    
    # Quick insights from latest report
    latest_insights = None
    if last_analysis and last_analysis.insights:
        latest_insights = extract_key_insights(last_analysis.insights)
    
    return render_template('analysis/index.html',
                         recent_reports=recent_reports,
                         total_reports=total_reports,
                         last_analysis=last_analysis,
                         total_sessions=total_sessions,
                         analyzed_sessions=analyzed_sessions,
                         latest_insights=latest_insights)

@analysis_bp.route('/generate', methods=['POST'])
@login_required
def generate_analysis():
    """Generate new behavioral analysis report"""
    try:
        # Check eligibility
        if not current_user.is_eligible_for_analysis():
            return jsonify({'error': 'Insufficient data for analysis'}), 400
        
        # Check rate limiting (max 3 reports per day)
        today = datetime.utcnow().date()
        today_reports = current_user.analysis_reports.filter(
            func.date(AnalysisReport.generated_at) == today
        ).count()
        
        if today_reports >= 3:
            return jsonify({'error': 'Daily report limit reached'}), 429
        
        # Get analysis parameters
        data = request.get_json() or {}
        days_back = data.get('days_back', 30)
        report_type = data.get('report_type', 'personal')
        include_recommendations = data.get('include_recommendations', True)
        
        # Initialize analyzer
        analyzer = BehaviorAnalyzer()
        
        # Generate comprehensive analysis
        report = analyzer.generate_comprehensive_report(
            user_id=current_user.id,
            days_back=days_back,
            report_type=report_type,
            include_recommendations=include_recommendations
        )
        
        if not report:
            return jsonify({'error': 'Analysis generation failed'}), 500
        
        SystemLog.log('INFO', 'ANALYSIS_GENERATED', 
                     f'Analysis report generated for user: {current_user.username}',
                     user_id=current_user.id, report_id=report.id)
        
        return jsonify({
            'success': True,
            'report_id': report.id,
            'message': 'Analysis report generated successfully!'
        })
        
    except Exception as e:
        current_app.logger.error(f"Analysis generation failed: {str(e)}")
        SystemLog.log('ERROR', 'ANALYSIS_FAILED', 
                     f'Analysis generation failed: {str(e)}',
                     user_id=current_user.id)
        return jsonify({'error': 'Analysis generation failed'}), 500

@analysis_bp.route('/report/<int:report_id>')
@login_required
def view_report(report_id):
    """View specific analysis report"""
    report = AnalysisReport.query.filter_by(
        id=report_id, user_id=current_user.id
    ).first_or_404()
    
    # Process insights for visualization
    processed_insights = process_insights_for_display(report.insights)
    processed_recommendations = process_recommendations_for_display(report.recommendations)
    
    # Get comparison with previous reports
    previous_report = current_user.analysis_reports.filter(
        AnalysisReport.generated_at < report.generated_at
    ).order_by(desc(AnalysisReport.generated_at)).first()
    
    comparison_data = None
    if previous_report:
        comparison_data = generate_comparison_data(previous_report, report)
    
    return render_template('analysis/personal_report.html',
                         report=report,
                         insights=processed_insights,
                         recommendations=processed_recommendations,
                         comparison_data=comparison_data)

@analysis_bp.route('/export_report/<int:report_id>')
@login_required
def export_report(report_id):
    """Export analysis report as PDF"""
    report = AnalysisReport.query.filter_by(
        id=report_id, user_id=current_user.id
    ).first_or_404()
    
    try:
        # Generate PDF report
        report_generator = ReportGenerator()
        pdf_content = report_generator.generate_pdf_report(report)
        
        # Create file-like object
        pdf_file = io.BytesIO(pdf_content)
        pdf_file.seek(0)
        
        filename = f"feelsync_report_{report.id}_{datetime.utcnow().strftime('%Y%m%d')}.pdf"
        
        SystemLog.log('INFO', 'REPORT_EXPORT', 
                     f'Report exported: {report_id}',
                     user_id=current_user.id, report_id=report_id)
        
        return send_file(
            pdf_file,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        current_app.logger.error(f"Report export failed: {str(e)}")
        flash('Report export failed. Please try again.', 'error')
        return redirect(url_for('analysis.view_report', report_id=report_id))

@analysis_bp.route('/share_with_therapist', methods=['POST'])
@login_required
def share_with_therapist():
    """Share analysis report with therapist"""
    try:
        data = request.get_json()
        report_id = data.get('report_id')
        therapist_email = data.get('therapist_email', '').strip().lower()
        
        if not report_id or not therapist_email:
            return jsonify({'error': 'Report ID and therapist email required'}), 400
        
        # Verify report ownership
        report = AnalysisReport.query.filter_by(
            id=report_id, user_id=current_user.id
        ).first()
        
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        # Check if therapist access exists
        therapist_access = TherapistAccess.query.filter_by(
            user_id=current_user.id,
            therapist_email=therapist_email,
            is_active=True
        ).first()
        
        if not therapist_access or not therapist_access.is_valid():
            return jsonify({'error': 'No valid therapist access found'}), 403
        
        # Update report sharing status
        report.is_shareable = True
        report.shared_with_therapist = True
        
        # Record access
        therapist_access.record_access()
        
        db.session.commit()
        
        SystemLog.log('INFO', 'REPORT_SHARED', 
                     f'Report shared with therapist: {therapist_email}',
                     user_id=current_user.id, report_id=report_id)
        
        return jsonify({'success': True, 'message': 'Report shared successfully!'})
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Report sharing failed: {str(e)}")
        return jsonify({'error': 'Report sharing failed'}), 500

@analysis_bp.route('/therapist_view/<therapist_email>')
def therapist_view(therapist_email):
    """Therapist view of patient data (with proper authentication)"""
    # Note: In production, this should have proper therapist authentication
    # For now, we'll use a simple access token system
    
    access_token = request.args.get('token')
    if not access_token:
        return render_template('errors/403.html'), 403
    
    # Verify access token (implement proper token validation)
    # This is a simplified version - use proper JWT or similar in production
    try:
        # Find active therapist access
        therapist_accesses = TherapistAccess.query.filter_by(
            therapist_email=therapist_email.lower(),
            is_active=True
        ).all()
        
        valid_accesses = [access for access in therapist_accesses if access.is_valid()]
        
        if not valid_accesses:
            return render_template('errors/403.html'), 403
        
        # Get patient data from all accessible users
        patient_data = []
        for access in valid_accesses:
            user = User.query.get(access.user_id)
            if not user:
                continue
                
            # Get shared reports
            shared_reports = user.analysis_reports.filter_by(
                shared_with_therapist=True
            ).order_by(desc(AnalysisReport.generated_at)).all()
            
            # Get basic statistics
            total_sessions = user.game_sessions.count()
            recent_activity = user.game_sessions.filter(
                GameSession.started_at >= datetime.utcnow() - timedelta(days=30)
            ).count()
            
            patient_data.append({
                'user_id': user.id,
                'username': user.username,  # Consider anonymizing
                'age': user.age,
                'total_sessions': total_sessions,
                'recent_activity': recent_activity,
                'shared_reports': shared_reports,
                'last_activity': user.last_login,
                'access_granted': access.granted_at
            })
        
        return render_template('analysis/therapist_view.html',
                             therapist_email=therapist_email,
                             patient_data=patient_data)
        
    except Exception as e:
        current_app.logger.error(f"Therapist view error: {str(e)}")
        return render_template('errors/500.html'), 500

@analysis_bp.route('/api/insights_data/<int:report_id>')
@login_required
def api_insights_data(report_id):
    """API endpoint for insights visualization data"""
    report = AnalysisReport.query.filter_by(
        id=report_id, user_id=current_user.id
    ).first_or_404()
    
    if not report.insights:
        return jsonify({'error': 'No insights data available'}), 404
    
    # Process insights for charts
    chart_data = {
        'anxiety_trends': extract_trend_data(report.anxiety_indicators),
        'depression_indicators': extract_indicator_data(report.depression_indicators),
        'attention_patterns': extract_pattern_data(report.attention_indicators),
        'overall_wellbeing': {
            'score': report.overall_wellbeing_score,
            'confidence': report.confidence_score,
            'trend': calculate_wellbeing_trend(current_user.id)
        }
    }
    
    return jsonify(chart_data)

@analysis_bp.route('/api/behavioral_patterns')
@login_required
def api_behavioral_patterns():
    """API endpoint for behavioral patterns over time"""
    days_back = request.args.get('days', 30, type=int)
    start_date = datetime.utcnow() - timedelta(days=days_back)
    
    # Get behavioral data
    behavior_data = BehaviorData.query.filter(
        BehaviorData.user_id == current_user.id,
        BehaviorData.timestamp >= start_date
    ).order_by(BehaviorData.timestamp).all()
    
    # Process data for visualization
    patterns = {
        'reaction_times': [],
        'stress_levels': [],
        'decision_patterns': {},
        'emotional_states': {}
    }
    
    for data_point in behavior_data:
        timestamp = data_point.timestamp.isoformat() if data_point.timestamp else None
        
        if data_point.reaction_time:
            patterns['reaction_times'].append({
                'timestamp': timestamp,
                'value': data_point.reaction_time,
                'game_type': data_point.session.game_type if data_point.session else None
            })
        
        if data_point.stress_level:
            patterns['stress_levels'].append({
                'timestamp': timestamp,
                'value': data_point.stress_level
            })
        
        if data_point.decision_type:
            if data_point.decision_type not in patterns['decision_patterns']:
                patterns['decision_patterns'][data_point.decision_type] = 0
            patterns['decision_patterns'][data_point.decision_type] += 1
        
        if data_point.emotional_state:
            if data_point.emotional_state not in patterns['emotional_states']:
                patterns['emotional_states'][data_point.emotional_state] = 0
            patterns['emotional_states'][data_point.emotional_state] += 1
    
    return jsonify(patterns)

@analysis_bp.route('/recommendations')
@login_required
def recommendations():
    """Personalized recommendations page"""
    if not current_user.is_eligible_for_analysis():
        flash('Complete more game sessions to receive personalized recommendations.', 'info')
        return redirect(url_for('games.index'))
    
    # Get latest analysis report
    latest_report = current_user.analysis_reports.order_by(
        desc(AnalysisReport.generated_at)
    ).first()
    
    if not latest_report:
        flash('No analysis available. Generate your first report to see recommendations.', 'info')
        return redirect(url_for('analysis.index'))
    
    # Process recommendations
    recommendations = process_recommendations_for_display(latest_report.recommendations)
    
    # Get user's recent activity to customize recommendations
    recent_sessions = current_user.game_sessions.filter(
        GameSession.started_at >= datetime.utcnow() - timedelta(days=7)
    ).all()
    
    activity_context = {
        'recent_session_count': len(recent_sessions),
        'preferred_games': get_preferred_games(recent_sessions),
        'activity_pattern': analyze_activity_pattern(recent_sessions)
    }
    
    return render_template('analysis/recommendations.html',
                         recommendations=recommendations,
                         activity_context=activity_context,
                         latest_report=latest_report)

@analysis_bp.route('/trends')
@login_required
def trends():
    """Long-term trends analysis page"""
    if current_user.analysis_reports.count() < 2:
        flash('You need at least 2 analysis reports to view trends.', 'info')
        return redirect(url_for('analysis.index'))
    
    # Get all user reports for trend analysis
    all_reports = current_user.analysis_reports.order_by(
        AnalysisReport.generated_at
    ).all()
    
    # Generate trend data
    trend_data = {
        'wellbeing_trend': [],
        'anxiety_trend': [],
        'depression_trend': [],
        'attention_trend': [],
        'confidence_trend': []
    }
    
    for report in all_reports:
        date = report.generated_at.strftime('%Y-%m-%d')
        
        trend_data['wellbeing_trend'].append({
            'date': date,
            'score': report.overall_wellbeing_score or 0
        })
        
        trend_data['confidence_trend'].append({
            'date': date,
            'score': report.confidence_score or 0
        })
        
        # Extract indicator trends
        if report.anxiety_indicators:
            anxiety_score = calculate_indicator_score(report.anxiety_indicators)
            trend_data['anxiety_trend'].append({'date': date, 'score': anxiety_score})
        
        if report.depression_indicators:
            depression_score = calculate_indicator_score(report.depression_indicators)
            trend_data['depression_trend'].append({'date': date, 'score': depression_score})
        
        if report.attention_indicators:
            attention_score = calculate_indicator_score(report.attention_indicators)
            trend_data['attention_trend'].append({'date': date, 'score': attention_score})
    
    return render_template('analysis/trends.html',
                         trend_data=trend_data,
                         report_count=len(all_reports))

# Helper functions

def extract_key_insights(insights_data):
    """Extract key insights for dashboard display"""
    if not insights_data:
        return {}
    
    key_insights = {}
    
    for category, data in insights_data.items():
        if isinstance(data, dict):
            if 'summary' in data:
                key_insights[category] = data['summary']
            elif 'score' in data:
                key_insights[category] = f"Score: {data['score']:.1f}"
    
    return key_insights

def process_insights_for_display(insights_data):
    """Process insights data for template display"""
    if not insights_data:
        return {}
    
    processed = {}
    
    for category, data in insights_data.items():
        if isinstance(data, dict):
            processed[category] = {
                'summary': data.get('summary', ''),
                'score': data.get('score', 0),
                'confidence': data.get('confidence', 0),
                'details': data.get('details', []),
                'recommendations': data.get('recommendations', [])
            }
    
    return processed

def process_recommendations_for_display(recommendations_data):
    """Process recommendations data for template display"""
    if not recommendations_data:
        return []
    
    processed = []
    
    for category, recs in recommendations_data.items():
        if isinstance(recs, list):
            for rec in recs:
                processed.append({
                    'category': category,
                    'title': rec.get('title', ''),
                    'description': rec.get('description', ''),
                    'priority': rec.get('priority', 'medium'),
                    'action_items': rec.get('action_items', [])
                })
    
    return sorted(processed, key=lambda x: {'high': 3, 'medium': 2, 'low': 1}.get(x['priority'], 0), reverse=True)

def generate_comparison_data(previous_report, current_report):
    """Generate comparison data between two reports"""
    comparison = {}
    
    # Compare wellbeing scores
    if previous_report.overall_wellbeing_score and current_report.overall_wellbeing_score:
        wellbeing_change = current_report.overall_wellbeing_score - previous_report.overall_wellbeing_score
        comparison['wellbeing_change'] = {
            'value': wellbeing_change,
            'direction': 'improved' if wellbeing_change > 0 else 'declined' if wellbeing_change < 0 else 'stable',
            'magnitude': abs(wellbeing_change)
        }
    
    # Compare confidence scores
    if previous_report.confidence_score and current_report.confidence_score:
        confidence_change = current_report.confidence_score - previous_report.confidence_score
        comparison['confidence_change'] = {
            'value': confidence_change,
            'direction': 'increased' if confidence_change > 0 else 'decreased' if confidence_change < 0 else 'stable',
            'magnitude': abs(confidence_change)
        }
    
    return comparison

def extract_trend_data(indicator_data):
    """Extract trend data from indicators"""
    if not indicator_data:
        return []
    
    trends = []
    if isinstance(indicator_data, dict) and 'trends' in indicator_data:
        trends = indicator_data['trends']
    
    return trends

def extract_indicator_data(indicator_data):
    """Extract indicator data for visualization"""
    if not indicator_data:
        return {}
    
    if isinstance(indicator_data, dict):
        return {
            'score': indicator_data.get('score', 0),
            'level': indicator_data.get('level', 'normal'),
            'factors': indicator_data.get('factors', [])
        }
    
    return {}

def extract_pattern_data(pattern_data):
    """Extract pattern data for visualization"""
    if not pattern_data:
        return []
    
    patterns = []
    if isinstance(pattern_data, dict) and 'patterns' in pattern_data:
        patterns = pattern_data['patterns']
    
    return patterns

def calculate_wellbeing_trend(user_id):
    """Calculate wellbeing trend direction"""
    recent_reports = AnalysisReport.query.filter_by(
        user_id=user_id
    ).order_by(desc(AnalysisReport.generated_at)).limit(3).all()
    
    if len(recent_reports) < 2:
        return 'stable'
    
    scores = [r.overall_wellbeing_score for r in reversed(recent_reports) if r.overall_wellbeing_score]
    
    if len(scores) < 2:
        return 'stable'
    
    trend = scores[-1] - scores[0]
    
    if trend > 0.1:
        return 'improving'
    elif trend < -0.1:
        return 'declining'
    else:
        return 'stable'

def get_preferred_games(sessions):
    """Analyze preferred games from recent sessions"""
    if not sessions:
        return []
    
    game_counts = {}
    for session in sessions:
        game_counts[session.game_type] = game_counts.get(session.game_type, 0) + 1
    
    return sorted(game_counts.items(), key=lambda x: x[1], reverse=True)

def analyze_activity_pattern(sessions):
    """Analyze user's activity pattern"""
    if not sessions:
        return 'inactive'
    
    if len(sessions) >= 5:
        return 'very_active'
    elif len(sessions) >= 3:
        return 'active'
    elif len(sessions) >= 1:
        return 'moderate'
    else:
        return 'inactive'

def calculate_indicator_score(indicator_data):
    """Calculate a numeric score from indicator data"""
    if not indicator_data:
        return 0
    
    if isinstance(indicator_data, dict):
        if 'score' in indicator_data:
            return indicator_data['score']
        elif 'level' in indicator_data:
            level_map = {'low': 0.2, 'normal': 0.5, 'moderate': 0.7, 'high': 0.9}
            return level_map.get(indicator_data['level'], 0.5)
    
    return 0
