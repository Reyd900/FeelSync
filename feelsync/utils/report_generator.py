import json
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
import base64
from io import BytesIO
import pandas as pd

class ReportGenerator:
    """Generates comprehensive behavioral analysis reports for users"""
    
    def __init__(self):
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
    
    def generate_comprehensive_report(self, user, analyses, sessions):
        """Generate a comprehensive behavioral report for a user"""
        
        report_data = {
            'user_info': self._extract_user_info(user),
            'report_metadata': {
                'generated_at': datetime.utcnow().isoformat(),
                'total_sessions': len(sessions),
                'analysis_period': self._get_analysis_period(sessions),
                'report_version': '1.0'
            },
            'summary': self._generate_summary(analyses),
            'detailed_analysis': self._generate_detailed_analysis(analyses, sessions),
            'trends': self._analyze_trends(analyses),
            'visualizations': self._generate_visualizations(analyses, sessions),
            'insights_and_recommendations': self._generate_insights_recommendations(analyses),
            'disclaimer': self._generate_disclaimer()
        }
        
        return report_data
    
    def _extract_user_info(self, user):
        """Extract anonymized user information for the report"""
        return {
            'user_id': user.anonymized_id or f"user_{user.id}",
            'age_group': self._categorize_age(user.age),
            'account_created': user.created_at.strftime('%Y-%m'),
            'is_minor': user.is_minor()
        }
    
    def _categorize_age(self, age):
        """Categorize age into groups"""
        if age < 13:
            return 'child'
        elif age < 18:
            return 'adolescent'
        elif age < 25:
            return 'young_adult'
        else:
            return 'adult'
    
    def _get_analysis_period(self, sessions):
        """Get the time period covered by the analysis"""
        if not sessions:
            return {'start': None, 'end': None, 'duration_days': 0}
        
        start_date = min(session.created_at for session in sessions)
        end_date = max(session.created_at for session in sessions)
        duration = (end_date - start_date).days
        
        return {
            'start': start_date.strftime('%Y-%m-%d'),
            'end': end_date.strftime('%Y-%m-%d'),
            'duration_days': duration
        }
    
    def _generate_summary(self, analyses):
        """Generate executive summary of the analysis"""
        if not analyses:
            return self._empty_summary()
        
        latest_analysis = analyses[0]  # Assuming sorted by date desc
        
        # Calculate averages across all analyses
        avg_anxiety = np.mean([a.anxiety_score for a in analyses])
        avg_depression = np.mean([a.depression_score for a in analyses])
        avg_attention = np.mean([a.attention_score for a in analyses])
        
        # Determine overall status
        overall_status = self._determine_overall_status(avg_anxiety, avg_depression, avg_attention)
        
        return {
            'overall_status': overall_status,
            'current_scores': {
                'anxiety': latest_analysis.anxiety_score,
                'depression': latest_analysis.depression_score,
                'attention': latest_analysis.attention_score,
                'impulsivity': latest_analysis.impulsivity_score,
                'emotional_regulation': latest_analysis.emotional_regulation_score
            },
            'average_scores': {
                'anxiety': round(avg_anxiety, 1),
                'depression': round(avg_depression, 1),
                'attention': round(avg_attention, 1)
            },
            'primary_behavioral_cluster': latest_analysis.predicted_cluster,
            'requires_attention': latest_analysis.requires_attention,
            'key_findings': self._extract_key_findings(analyses)
        }
    
    def _determine_overall_status(self, anxiety, depression, attention):
        """Determine overall mental health status"""
        concern_score = anxiety + depression + (100 - attention)
        
        if concern_score > 200:
            return 'high_concern'
        elif concern_score > 120:
            return 'moderate_concern'
        else:
            return 'low_concern'
    
    def _extract_key_findings(self, analyses):
        """Extract key findings from all analyses"""
        findings = []
        
        if not analyses:
            return findings
        
        # Most common insights
        all_insights = []
        for analysis in analyses:
            if hasattr(analysis, 'insights') and analysis.insights:
                try:
                    insights_data = json.loads(analysis.insights) if isinstance(analysis.insights, str) else analysis.insights
                    if isinstance(insights_data, list):
                        all_insights.extend(insights_data)
                except:
                    pass
        
        # Count frequency of insights
        insight_counts = {}
        for insight in all_insights:
            insight_counts[insight] = insight_counts.get(insight, 0) + 1
        
        # Get top 3 most common insights
        top_insights = sorted(insight_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        findings = [insight for insight, count in top_insights]
        
        # Add trend-based findings
        if len(analyses) >= 3:
            anxiety_trend = self._calculate_simple_trend([a.anxiety_score for a in analyses[-5:]])
            if anxiety_trend == 'increasing':
                findings.append("Increasing anxiety patterns over recent sessions")
            elif anxiety_trend == 'decreasing':
                findings.append("Decreasing anxiety patterns - positive trend")
        
        return findings[:5]  # Return top 5 findings
    
    def _generate_detailed_analysis(self, analyses, sessions):
        """Generate detailed analysis section"""
        if not analyses:
            return self._empty_detailed_analysis()
        
        # Game-specific analysis
        game_analysis = self._analyze_by_game_type(sessions, analyses)
        
        # Behavioral patterns
        behavioral_patterns = self._analyze_behavioral_patterns(analyses)
        
        # Risk assessment
        risk_assessment = self._comprehensive_risk_assessment(analyses)
        
        return {
            'game_performance': game_analysis,
            'behavioral_patterns': behavioral_patterns,
            'risk_assessment': risk_assessment,
            'session_details': self._generate_session_details(sessions, analyses)
        }
    
    def _analyze_by_game_type(self, sessions, analyses):
        """Analyze performance by game type"""
        game_stats = {}
        
        for session in sessions:
            game_type = session.game_type
            if game_type not in game_stats:
                game_stats[game_type] = {
                    'session_count': 0,
                    'avg_score': 0,
                    'avg_duration': 0,
                    'avg_accuracy': 0,
                    'completion_rate': 0
                }
            
            stats = game_stats[game_type]
            stats['session_count'] += 1
            stats['avg_score'] += session.score or 0
            stats['avg_duration'] += session.duration or 0
            stats['avg_accuracy'] += session.accuracy or 0
            if session.completed:
                stats['completion_rate'] += 1
        
        # Calculate averages
        for game_type, stats in game_stats.items():
            count = stats['session_count']
            if count > 0:
                stats['avg_score'] = round(stats['avg_score'] / count, 1)
                stats['avg_duration'] = round(stats['avg_duration'] / count, 1)
                stats['avg_accuracy'] = round(stats['avg_accuracy'] / count, 3)
                stats['completion_rate'] = round((stats['completion_rate'] / count) * 100, 1)
        
        return game_stats
    
    def _analyze_behavioral_patterns(self, analyses):
        """Analyze behavioral patterns across all sessions"""
        if not analyses:
            return {}
        
        patterns = {
            'consistency': self._assess_consistency(analyses),
            'volatility': self._assess_emotional_volatility(analyses),
            'improvement_areas': self._identify_improvement_areas(analyses),
            'strengths': self._identify_behavioral_strengths(analyses)
        }
        
        return patterns
    
    def _assess_consistency(self, analyses):
        """Assess behavioral consistency across sessions"""
        anxiety_scores = [a.anxiety_score for a in analyses]
        depression_scores = [a.depression_score for a in analyses]
        attention_scores = [a.attention_score for a in analyses]
        
        consistency_scores = {
            'anxiety_consistency': 100 - (np.std(anxiety_scores) * 2),
            'depression_consistency': 100 - (np.std(depression_scores) * 2),
            'attention_consistency': 100 - (np.std(attention_scores) * 2)
        }
        
        # Overall consistency score
        overall_consistency = np.mean(list(consistency_scores.values()))
        
        return {
            'overall_score': max(0, round(overall_consistency, 1)),
            'individual_scores': {k: max(0, round(v, 1)) for k, v in consistency_scores.items()},
            'interpretation': 'high' if overall_consistency > 70 else 'moderate' if overall_consistency > 40 else 'low'
        }
    
    def _comprehensive_risk_assessment(self, analyses):
        """Perform comprehensive risk assessment"""
        if not analyses:
            return {'level': 'unknown', 'factors': []}
        
        latest = analyses[0]
        risk_factors = []
        risk_score = 0
        
        # Individual score assessment
        if latest.anxiety_score > 75:
            risk_factors.append("High anxiety indicators")
            risk_score += 3
        elif latest.anxiety_score > 50:
            risk_factors.append("Moderate anxiety indicators")
            risk_score += 2
        
        if latest.depression_score > 75:
            risk_factors.append("High depression indicators")
            risk_score += 3
        elif latest.depression_score > 50:
            risk_factors.append("Moderate depression indicators")
            risk_score += 2
        
        if latest.attention_score < 25:
            risk_factors.append("Significant attention difficulties")
            risk_score += 3
        elif latest.attention_score < 50:
            risk_factors.append("Moderate attention challenges")
            risk_score += 2
        
        # Trend analysis
        if len(analyses) >= 3:
            recent_anxiety_trend = self._calculate_simple_trend([a.anxiety_score for a in analyses[:3]])
            if recent_anxiety_trend == 'increasing':
                risk_factors.append("Worsening anxiety trend")
                risk_score += 2
        
        # Determine overall risk level
        if risk_score >= 6:
            level = 'high'
        elif risk_score >= 3:
            level = 'moderate'
        else:
            level = 'low'
        
        return {
            'level': level,
            'score': risk_score,
            'factors': risk_factors,
            'requires_professional_attention': level in ['high', 'moderate'] and risk_score >= 4
        }
    
    def _analyze_trends(self, analyses):
        """Analyze trends in behavioral indicators over time"""
        if len(analyses) < 3:
            return {'status': 'insufficient_data'}
        
        # Sort analyses by date
        sorted_analyses = sorted(analyses, key=lambda x: x.created_at)
        
        dates = [a.created_at for a in sorted_analyses]
        anxiety_scores = [a.anxiety_score for a in sorted_analyses]
        depression_scores = [a.depression_score for a in sorted_analyses]
        attention_scores = [a.attention_score for a in sorted_analyses]
        
        trends = {
            'anxiety': self._detailed_trend_analysis(dates, anxiety_scores),
            'depression': self._detailed_trend_analysis(dates, depression_scores),
            'attention': self._detailed_trend_analysis(dates, attention_scores),
            'overall_trajectory': self._calculate_overall_trajectory(anxiety_scores, depression_scores, attention_scores)
        }
        
        return trends
    
    def _detailed_trend_analysis(self, dates, scores):
        """Perform detailed trend analysis for a specific metric"""
        if len(scores) < 3:
            return {'trend': 'insufficient_data'}
        
        # Calculate linear trend
        x = np.arange(len(scores))
        slope, intercept = np.polyfit(x, scores, 1)
        
        # Calculate correlation coefficient
        correlation = np.corrcoef(x, scores)[0, 1]
        
        # Determine trend direction
        if slope > 2 and correlation > 0.3:
            direction = 'increasing'
        elif slope < -2 and correlation < -0.3:
            direction = 'decreasing'
        else:
            direction = 'stable'
        
        # Calculate recent change (last 3 sessions vs previous)
        if len(scores) >= 6:
            recent_avg = np.mean(scores[-3:])
            previous_avg = np.mean(scores[-6:-3])
            recent_change = recent_avg - previous_avg
        else:
            recent_change = scores[-1] - scores[0]
        
        return {
            'direction': direction,
            'slope': round(slope, 2),
            'correlation': round(correlation, 2),
            'recent_change': round(recent_change, 1),
            'statistical_significance': 'significant' if abs(correlation) > 0.5 else 'not_significant'
        }
    
    def _generate_visualizations(self, analyses, sessions):
        """Generate data visualizations for the report"""
        if not analyses:
            return {}
        
        visualizations = {}
        
        try:
            # Score trends over time
            visualizations['score_trends'] = self._create_score_trends_chart(analyses)
            
            # Game performance radar chart
            visualizations['performance_radar'] = self._create_performance_radar(analyses)
            
            # Session frequency heatmap
            visualizations['session_heatmap'] = self._create_session_heatmap(sessions)
            
        except Exception as e:
            print(f"Error generating visualizations: {e}")
            visualizations['error'] = 'Unable to generate visualizations'
        
        return visualizations
    
    def _create_score_trends_chart(self, analyses):
        """Create a trends chart for mental health scores"""
        # Sort analyses by date
        sorted_analyses = sorted(analyses, key=lambda x: x.created_at)
        
        dates = [a.created_at.strftime('%m/%d') for a in sorted_analyses]
        anxiety_scores = [a.anxiety_score for a in sorted_analyses]
        depression_scores = [a.depression_score for a in sorted_analyses]
        attention_scores = [a.attention_score for a in sorted_analyses]
        
        plt.figure(figsize=(10, 6))
        plt.plot(dates, anxiety_scores, marker='o', label='Anxiety', linewidth=2)
        plt.plot(dates, depression_scores, marker='s', label='Depression', linewidth=2)
        plt.plot(dates, attention_scores, marker='^', label='Attention', linewidth=2)
        
        plt.title('Mental Health Indicators Over Time', fontsize=14, fontweight='bold')
        plt.xlabel('Date')
        plt.ylabel('Score (0-100)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Convert to base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return image_base64
    
    def _create_performance_radar(self, analyses):
        """Create a radar chart showing current performance across all metrics"""
        if not analyses:
            return None
        
        latest_analysis = analyses[0]
        
        # Prepare data for radar chart
        categories = ['Anxiety\n(Lower=Better)', 'Depression\n(Lower=Better)', 
                     'Attention\n(Higher=Better)', 'Impulsivity\n(Lower=Better)', 
                     'Emotional\nRegulation\n(Higher=Better)']
        
        # Invert scores where appropriate for consistent interpretation (higher = better)
        values = [
            100 - latest_analysis.anxiety_score,  # Invert: lower anxiety is better
            100 - latest_analysis.depression_score,  # Invert: lower depression is better
            latest_analysis.attention_score,  # Keep: higher attention is better
            100 - latest_analysis.impulsivity_score,  # Invert: lower impulsivity is better
            latest_analysis.emotional_regulation_score  # Keep: higher regulation is better
        ]
        
        # Number of variables
        N = len(categories)
        
        # What will be the angle of each axis in the plot? (we divide the plot / number of variable)
        angles = [n / float(N) * 2 * np.pi for n in range(N)]
        angles += angles[:1]  # Complete the circle
        
        # Initialize the plot
        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))
        
        # Add values
        values += values[:1]  # Complete the circle
        ax.plot(angles, values, 'o-', linewidth=2, label='Current Performance')
        ax.fill(angles, values, alpha=0.25)
        
        # Add category labels
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, fontsize=10)
        
        # Set y-axis limits
        ax.set_ylim(0, 100)
        ax.set_yticks([20, 40, 60, 80, 100])
        ax.set_yticklabels(['20', '40', '60', '80', '100'], fontsize=8)
        ax.grid(True)
        
        plt.title('Current Mental Health Performance Profile', size=14, fontweight='bold', pad=20)
        
        # Convert to base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return image_base64
    
    def _create_session_heatmap(self, sessions):
        """Create a heatmap showing session frequency over time"""
        if len(sessions) < 5:
            return None
        
        # Create DataFrame with session data
        session_data = []
        for session in sessions:
            session_data.append({
                'date': session.created_at.date(),
                'hour': session.created_at.hour,
                'day_of_week': session.created_at.strftime('%A'),
                'completed': 1 if session.completed else 0
            })
        
        df = pd.DataFrame(session_data)
        
        # Create pivot table for heatmap
        pivot_table = df.groupby(['day_of_week', 'hour']).size().unstack(fill_value=0)
        
        # Reorder days of week
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        pivot_table = pivot_table.reindex([day for day in day_order if day in pivot_table.index])
        
        plt.figure(figsize=(12, 6))
        sns.heatmap(pivot_table, annot=True, fmt='d', cmap='YlOrRd', 
                   cbar_kws={'label': 'Number of Sessions'})
        plt.title('Session Activity Heatmap (Day vs Hour)', fontsize=14, fontweight='bold')
        plt.xlabel('Hour of Day')
        plt.ylabel('Day of Week')
        plt.tight_layout()
        
        # Convert to base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return image_base64
    
    def _generate_insights_recommendations(self, analyses):
        """Generate insights and recommendations section"""
        if not analyses:
            return self._empty_insights_recommendations()
        
        latest_analysis = analyses[0]
        
        # Extract insights from latest analysis
        insights = []
        if hasattr(latest_analysis, 'insights') and latest_analysis.insights:
            try:
                insights_data = json.loads(latest_analysis.insights) if isinstance(latest_analysis.insights, str) else latest_analysis.insights
                if isinstance(insights_data, list):
                    insights = insights_data
            except:
                pass
        
        # Generate recommendations based on analysis
        recommendations = self._generate_personalized_recommendations(analyses)
        
        # Generate actionable steps
        actionable_steps = self._generate_actionable_steps(latest_analysis, analyses)
        
        return {
            'key_insights': insights[:5],  # Top 5 insights
            'recommendations': recommendations,
            'actionable_steps': actionable_steps,
            'monitoring_suggestions': self._generate_monitoring_suggestions(analyses)
        }
    
    def _generate_personalized_recommendations(self, analyses):
        """Generate personalized recommendations based on user's pattern"""
        recommendations = []
        latest = analyses[0]
        
        # High-level recommendations based on scores
        if latest.anxiety_score > 70:
            recommendations.append({
                'category': 'Anxiety Management',
                'priority': 'High',
                'recommendation': 'Consider learning and practicing anxiety management techniques',
                'specific_actions': [
                    'Practice deep breathing exercises (4-7-8 technique)',
                    'Try progressive muscle relaxation',
                    'Consider mindfulness or meditation apps',
                    'Maintain a regular sleep schedule'
                ]
            })
        
        if latest.depression_score > 70:
            recommendations.append({
                'category': 'Mood Support',
                'priority': 'High',
                'recommendation': 'Focus on activities that support positive mood',
                'specific_actions': [
                    'Engage in regular physical activity',
                    'Maintain social connections',
                    'Practice gratitude journaling',
                    'Consider talking to a counselor or therapist'
                ]
            })
        
        if latest.attention_score < 40:
            recommendations.append({
                'category': 'Attention Enhancement',
                'priority': 'Medium',
                'recommendation': 'Work on improving focus and attention skills',
                'specific_actions': [
                    'Break tasks into smaller, manageable chunks',
                    'Use timer-based work sessions (Pomodoro technique)',
                    'Minimize distractions in study/work environment',
                    'Consider evaluation for attention-related concerns'
                ]
            })
        
        if latest.impulsivity_score > 70:
            recommendations.append({
                'category': 'Impulse Control',
                'priority': 'Medium',
                'recommendation': 'Develop strategies for better impulse control',
                'specific_actions': [
                    'Practice the "pause and think" strategy',
                    'Use the 10-second rule before making decisions',
                    'Identify triggers for impulsive behavior',
                    'Develop healthy coping strategies'
                ]
            })
        
        # Trend-based recommendations
        if len(analyses) >= 3:
            anxiety_trend = self._calculate_simple_trend([a.anxiety_score for a in analyses[:3]])
            if anxiety_trend == 'increasing':
                recommendations.append({
                    'category': 'Trend Alert',
                    'priority': 'High',
                    'recommendation': 'Address increasing anxiety patterns',
                    'specific_actions': [
                        'Review recent stressors and triggers',
                        'Increase self-care activities',
                        'Consider professional support if trend continues'
                    ]
                })
        
        return recommendations[:4]  # Return top 4 recommendations
    
    def _generate_actionable_steps(self, latest_analysis, all_analyses):
        """Generate specific actionable steps for the user"""
        steps = []
        
        # Immediate steps (next 1-2 weeks)
        immediate_steps = []
        if latest_analysis.requires_attention:
            immediate_steps.extend([
                "Schedule time for daily relaxation or mindfulness practice",
                "Track mood and stress levels for the next week",
                "Ensure adequate sleep (7-9 hours per night)"
            ])
        
        immediate_steps.append("Continue regular FeelSync game sessions for monitoring")
        
        # Short-term steps (next 1-2 months)
        short_term_steps = [
            "Review progress in FeelSync dashboard weekly",
            "Implement consistent stress management routines",
            "Consider joining support groups or activities of interest"
        ]
        
        # Long-term steps (next 3-6 months)
        long_term_steps = [
            "Develop a comprehensive self-care plan",
            "Build a strong support network",
            "Consider professional consultation if concerns persist"
        ]
        
        return {
            'immediate': immediate_steps[:3],
            'short_term': short_term_steps[:3],
            'long_term': long_term_steps[:3]
        }
    
    def _generate_monitoring_suggestions(self, analyses):
        """Generate suggestions for ongoing monitoring"""
        suggestions = [
            "Continue playing FeelSync games 2-3 times per week",
            "Pay attention to patterns in your behavioral responses",
            "Note any significant life changes that might affect results",
            "Review your progress reports monthly"
        ]
        
        if len(analyses) >= 3:
            suggestions.append("Track trends over time rather than focusing on individual sessions")
        
        return suggestions
    
    def _generate_disclaimer(self):
        """Generate important disclaimer text"""
        return {
            'title': 'Important Disclaimer',
            'content': [
                "This report is based on behavioral patterns observed during gameplay and is intended for self-awareness and educational purposes only.",
                "The FeelSync platform is NOT a diagnostic tool and should not be used to diagnose any mental health condition.",
                "The insights and recommendations provided are suggestions based on behavioral analysis and should not replace professional medical or psychological advice.",
                "If you are experiencing significant distress, persistent symptoms, or thoughts of self-harm, please contact a mental health professional immediately.",
                "The analysis is based on limited behavioral data and may not fully represent your overall mental health status.",
                "Consider this information as one input among many in understanding your wellbeing."
            ],
            'emergency_contacts': {
                'crisis_hotline': '988 (US Suicide & Crisis Lifeline)',
                'emergency': '911 (US Emergency Services)',
                'text_support': 'Text HOME to 741741 (Crisis Text Line)'
            }
        }
    
    # Helper methods for empty states
    def _empty_summary(self):
        return {
            'overall_status': 'no_data',
            'current_scores': {'anxiety': 0, 'depression': 0, 'attention': 50},
            'key_findings': ['No gaming sessions completed yet']
        }
    
    def _empty_detailed_analysis(self):
        return {
            'game_performance': {},
            'behavioral_patterns': {'consistency': {'overall_score': 0}},
            'risk_assessment': {'level': 'unknown'},
            'session_details': []
        }
    
    def _empty_insights_recommendations(self):
        return {
            'key_insights': ['Complete some game sessions to generate insights'],
            'recommendations': [],
            'actionable_steps': {
                'immediate': ['Start with a FeelSync game session'],
                'short_term': ['Play regularly for better analysis'],
                'long_term': ['Build consistent self-monitoring habits']
            }
        }
    
    def _generate_session_details(self, sessions, analyses):
        """Generate detailed information about individual sessions"""
        session_details = []
        
        # Create a mapping of sessions to analyses
        analysis_by_session = {a.session_id: a for a in analyses if a.session_id}
        
        for session in sessions[-10:]:  # Last 10 sessions
            analysis = analysis_by_session.get(session.id)
            
            detail = {
                'date': session.created_at.strftime('%Y-%m-%d %H:%M'),
                'game_type': session.game_type,
                'duration_minutes': round(session.duration / 60, 1) if session.duration else 0,
                'score': session.score,
                'accuracy': round(session.accuracy * 100, 1) if session.accuracy else 0,
                'completed': session.completed
            }
            
            if analysis:
                detail.update({
                    'anxiety_score': analysis.anxiety_score,
                    'depression_score': analysis.depression_score,
                    'attention_score': analysis.attention_score,
                    'predicted_cluster': analysis.predicted_cluster
                })
            
            session_details.append(detail)
        
        return session_details
    
    def _calculate_simple_trend(self, scores):
        """Simple trend calculation helper"""
        if len(scores) < 2:
            return 'stable'
        
        recent = np.mean(scores[-2:])
        earlier = np.mean(scores[:-2]) if len(scores) > 2 else scores[0]
        
        if recent > earlier + 5:
            return 'increasing'
        elif recent < earlier - 5:
            return 'decreasing'
        else:
            return 'stable'
    
    def _calculate_overall_trajectory(self, anxiety_scores, depression_scores, attention_scores):
        """Calculate overall trajectory across all metrics"""
        if len(anxiety_scores) < 3:
            return 'insufficient_data'
        
        # Calculate improvement score (lower anxiety/depression, higher attention = better)
        recent_half = len(anxiety_scores) // 2
        
        early_anxiety = np.mean(anxiety_scores[:recent_half])
        recent_anxiety = np.mean(anxiety_scores[recent_half:])
        
        early_depression = np.mean(depression_scores[:recent_half])
        recent_depression = np.mean(depression_scores[recent_half:])
        
        early_attention = np.mean(attention_scores[:recent_half])
        recent_attention = np.mean(attention_scores[recent_half:])
        
        improvement_score = (
            (early_anxiety - recent_anxiety) +  # Lower anxiety = improvement
            (early_depression - recent_depression) +  # Lower depression = improvement
            (recent_attention - early_attention)  # Higher attention = improvement
        ) / 3
        
        if improvement_score > 10:
            return 'improving'
        elif improvement_score < -10:
            return 'declining'
        else:
            return 'stable'
    
    def _identify_improvement_areas(self, analyses):
        """Identify areas that need improvement"""
        if not analyses:
            return []
        
        latest = analyses[0]
        areas = []
        
        if latest.anxiety_score > 60:
            areas.append('anxiety_management')
        if latest.depression_score > 60:
            areas.append('mood_support')
        if latest.attention_score < 40:
            areas.append('attention_focus')
        if latest.impulsivity_score > 60:
            areas.append('impulse_control')
        if latest.emotional_regulation_score < 40:
            areas.append('emotional_regulation')
        
        return areas
    
    def _identify_behavioral_strengths(self, analyses):
        """Identify behavioral strengths from the analysis"""
        if not analyses:
            return []
        
        latest = analyses[0]
        strengths = []
        
        if latest.anxiety_score < 40:
            strengths.append('low_anxiety_indicators')
        if latest.depression_score < 40:
            strengths.append('positive_mood_indicators')
        if latest.attention_score > 70:
            strengths.append('strong_attention_skills')
        if latest.impulsivity_score < 40:
            strengths.append('good_impulse_control')
        if latest.emotional_regulation_score > 70:
            strengths.append('effective_emotional_regulation')
        
        return strengths
    
    def _assess_emotional_volatility(self, analyses):
        """Assess emotional volatility across sessions"""
        if len(analyses) < 3:
            return {'level': 'unknown', 'score': 0}
        
        # Calculate volatility based on score variations
        anxiety_var = np.var([a.anxiety_score for a in analyses])
        depression_var = np.var([a.depression_score for a in analyses])
        
        volatility_score = (anxiety_var + depression_var) / 2
        
        if volatility_score > 400:
            level = 'high'
        elif volatility_score > 200:
            level = 'moderate'
        else:
            level = 'low'
        
        return {'level': level, 'score': round(volatility_score, 1)}
    
    def export_report_to_pdf(self, report_data):
        """Export the report to PDF format (placeholder for future implementation)"""
        # This would require additional libraries like reportlab or weasyprint
        # For now, return a structured format that could be converted to PDF
        return {
            'status': 'feature_planned',
            'message': 'PDF export functionality will be available in future versions'
        }
