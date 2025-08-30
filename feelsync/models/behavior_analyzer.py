import json
import numpy as np
from datetime import datetime, timedelta
from .ml_models import BehaviorPredictor

class BehaviorAnalyzer:
    """Main behavioral analysis engine for processing game session data"""
    
    def __init__(self):
        self.predictor = BehaviorPredictor()
        self.analysis_rules = self._load_analysis_rules()
    
    def analyze_session(self, behavioral_data):
        """Analyze a single game session and return comprehensive results"""
        
        if isinstance(behavioral_data, str):
            behavioral_data = json.loads(behavioral_data)
        
        # Basic ML predictions
        anxiety_score = self.predictor.predict_anxiety(behavioral_data)
        depression_score = self.predictor.predict_depression(behavioral_data)
        attention_score = self.predictor.predict_attention(behavioral_data)
        cluster = self.predictor.predict_cluster(behavioral_data)
        
        # Detailed behavioral metrics
        detailed_metrics = self._calculate_detailed_metrics(behavioral_data)
        
        # Generate insights
        insights = self._generate_insights(
            anxiety_score, depression_score, attention_score, 
            cluster, detailed_metrics, behavioral_data
        )
        
        # Risk assessment
        risk_assessment = self._assess_risk_level(
            anxiety_score, depression_score, attention_score, detailed_metrics
        )
        
        return {
            'anxiety_score': round(anxiety_score, 2),
            'depression_score': round(depression_score, 2),
            'attention_score': round(attention_score, 2),
            'impulsivity_score': round(detailed_metrics.get('impulsivity_score', 0), 2),
            'emotional_regulation_score': round(detailed_metrics.get('emotional_regulation_score', 50), 2),
            'predicted_cluster': cluster,
            'confidence_score': detailed_metrics.get('confidence_score', 0.7),
            'detailed_metrics': detailed_metrics,
            'insights': insights,
            'risk_level': risk_assessment['level'],
            'requires_attention': risk_assessment['requires_attention'],
            'recommendations': self._generate_recommendations(risk_assessment, insights),
            'analysis_timestamp': datetime.utcnow().isoformat()
        }
    
    def _calculate_detailed_metrics(self, behavioral_data):
        """Calculate detailed behavioral metrics from game data"""
        metrics = {}
        
        # Reaction time analysis
        reaction_times = behavioral_data.get('reactionTimes', [])
        if reaction_times:
            metrics['reaction_time_mean'] = np.mean(reaction_times)
            metrics['reaction_time_std'] = np.std(reaction_times)
            metrics['reaction_time_median'] = np.median(reaction_times)
            metrics['reaction_time_range'] = max(reaction_times) - min(reaction_times)
            
            # Percentile analysis
            metrics['reaction_time_p25'] = np.percentile(reaction_times, 25)
            metrics['reaction_time_p75'] = np.percentile(reaction_times, 75)
            
            # Consistency measure
            metrics['reaction_consistency'] = 1 - (metrics['reaction_time_std'] / metrics['reaction_time_mean'])
        else:
            metrics.update({
                'reaction_time_mean': 0, 'reaction_time_std': 0,
                'reaction_time_median': 0, 'reaction_time_range': 0,
                'reaction_time_p25': 0, 'reaction_time_p75': 0,
                'reaction_consistency': 0
            })
        
        # Error pattern analysis
        total_clicks = behavioral_data.get('totalClicks', 0)
        mistakes = behavioral_data.get('mistakes', 0)
        
        metrics['error_rate'] = mistakes / max(total_clicks, 1)
        metrics['accuracy'] = 1 - metrics['error_rate']
        
        # Hesitation analysis
        hesitation_times = behavioral_data.get('hesitationTimes', [])
        metrics['hesitation_frequency'] = len(hesitation_times) / max(total_clicks, 1)
        
        if hesitation_times:
            metrics['avg_hesitation_duration'] = np.mean(hesitation_times)
            metrics['hesitation_severity'] = np.mean([h for h in hesitation_times if h > 1000])
        else:
            metrics['avg_hesitation_duration'] = 0
            metrics['hesitation_severity'] = 0
        
        # Emotional choice analysis
        emotional_choices = behavioral_data.get('emotionalChoices', {})
        total_emotional = sum(emotional_choices.values())
        
        if total_emotional > 0:
            metrics['positive_choice_ratio'] = emotional_choices.get('positive', 0) / total_emotional
            metrics['negative_choice_ratio'] = emotional_choices.get('negative', 0) / total_emotional
            metrics['neutral_choice_ratio'] = emotional_choices.get('neutral', 0) / total_emotional
            
            # Emotional bias score (-1 to 1, negative values indicate negative bias)
            metrics['emotional_bias_score'] = (
                metrics['positive_choice_ratio'] - metrics['negative_choice_ratio']
            )
        else:
            metrics.update({
                'positive_choice_ratio': 0.33, 'negative_choice_ratio': 0.33,
                'neutral_choice_ratio': 0.33, 'emotional_bias_score': 0
            })
        
        # Impulsivity indicators
        if reaction_times:
            fast_reactions = [rt for rt in reaction_times if rt < 300]  # Very fast reactions
            metrics['impulsivity_frequency'] = len(fast_reactions) / len(reaction_times)
            
            # Impulsivity score based on fast reactions with high error correlation
            fast_reaction_errors = sum(1 for rt in reaction_times[:mistakes] if rt < 500)
            metrics['impulsivity_score'] = min(
                (metrics['impulsivity_frequency'] * 50) + 
                (fast_reaction_errors / max(mistakes, 1) * 50), 
                100
            )
        else:
            metrics['impulsivity_frequency'] = 0
            metrics['impulsivity_score'] = 0
        
        # Attention pattern analysis
        if reaction_times and len(reaction_times) > 5:
            # Look for attention lapses (unusually slow reactions)
            attention_threshold = metrics['reaction_time_mean'] + (2 * metrics['reaction_time_std'])
            attention_lapses = [rt for rt in reaction_times if rt > attention_threshold]
            metrics['attention_lapse_frequency'] = len(attention_lapses) / len(reaction_times)
            
            # Sustained attention measure (consistency over time)
            chunks = [reaction_times[i:i+5] for i in range(0, len(reaction_times)-4, 5)]
            chunk_means = [np.mean(chunk) for chunk in chunks if len(chunk) == 5]
            
            if len(chunk_means) > 1:
                metrics['sustained_attention_consistency'] = 1 - (np.std(chunk_means) / np.mean(chunk_means))
            else:
                metrics['sustained_attention_consistency'] = 1
        else:
            metrics['attention_lapse_frequency'] = 0
            metrics['sustained_attention_consistency'] = 1
        
        # Emotional regulation assessment
        if 'emotionalStateChanges' in behavioral_data:
            state_changes = behavioral_data['emotionalStateChanges']
            metrics['emotional_volatility'] = len(state_changes) / max(total_clicks, 1)
            metrics['emotional_regulation_score'] = max(0, 100 - (metrics['emotional_volatility'] * 100))
        else:
            # Infer from emotional choices and reaction time patterns
            emotion_variance = np.var(list(emotional_choices.values())) if emotional_choices else 0
            rt_volatility = metrics['reaction_time_std'] / max(metrics['reaction_time_mean'], 1)
            
            regulation_score = 100 - min((emotion_variance * 10) + (rt_volatility * 30), 100)
            metrics['emotional_regulation_score'] = max(regulation_score, 0)
        
        # Stress indicators
        stress_score = 0
        if metrics['reaction_time_std'] > 800:  # High variance
            stress_score += 25
        if metrics['error_rate'] > 0.3:  # High error rate
            stress_score += 25
        if metrics['hesitation_frequency'] > 0.4:  # Frequent hesitation
            stress_score += 25
        if metrics['emotional_bias_score'] < -0.3:  # Strong negative bias
            stress_score += 25
        
        metrics['stress_indicators'] = min(stress_score, 100)
        
        # Confidence score for the analysis
        data_quality_score = min(
            len(reaction_times) / 20,  # More data = higher confidence
            1.0
        )
        consistency_score = metrics['reaction_consistency'] if metrics['reaction_consistency'] > 0 else 0
        metrics['confidence_score'] = (data_quality_score + consistency_score) / 2
        
        return metrics
    
    def _generate_insights(self, anxiety_score, depression_score, attention_score, 
                          cluster, detailed_metrics, behavioral_data):
        """Generate human-readable insights from the analysis"""
        insights = []
        
        # Anxiety-related insights
        if anxiety_score > 70:
            insights.append("High anxiety patterns detected in gameplay behavior")
            if detailed_metrics['hesitation_frequency'] > 0.3:
                insights.append("Frequent hesitation suggests decision-making anxiety")
        elif anxiety_score > 40:
            insights.append("Moderate anxiety indicators present")
        
        # Depression-related insights
        if depression_score > 70:
            insights.append("Behavioral patterns consistent with depressive tendencies")
            if detailed_metrics['reaction_time_mean'] > 1200:
                insights.append("Slower reaction times may indicate reduced engagement")
        elif depression_score > 40:
            insights.append("Some indicators of low mood or motivation")
        
        # Attention-related insights
        if attention_score < 30:
            insights.append("Significant attention difficulties observed")
            if detailed_metrics['attention_lapse_frequency'] > 0.2:
                insights.append("Frequent attention lapses detected during gameplay")
        elif attention_score < 60:
            insights.append("Moderate attention challenges present")
        
        # Cluster-specific insights
        if cluster == 'fast_accurate':
            insights.append("Shows quick decision-making with high accuracy")
            insights.append("Demonstrates good cognitive processing speed")
        elif cluster == 'slow_consistent':
            insights.append("Thoughtful, deliberate approach to decision-making")
            insights.append("Prioritizes accuracy over speed")
        elif cluster == 'erratic':
            insights.append("Variable performance patterns observed")
            insights.append("May benefit from strategies to improve consistency")
        
        # Behavioral pattern insights
        if detailed_metrics['impulsivity_score'] > 70:
            insights.append("High impulsivity indicators in gameplay")
            insights.append("Tendency toward quick decisions without full consideration")
        
        if detailed_metrics['emotional_bias_score'] < -0.4:
            insights.append("Strong bias toward negative emotional choices")
            insights.append("May indicate current negative mood state")
        elif detailed_metrics['emotional_bias_score'] > 0.4:
            insights.append("Positive emotional choice bias observed")
            insights.append("Generally optimistic response patterns")
        
        if detailed_metrics['emotional_regulation_score'] < 40:
            insights.append("Challenges with emotional regulation detected")
            insights.append("Emotional responses show high variability")
        
        # Performance insights
        if detailed_metrics['accuracy'] > 0.8:
            insights.append("Excellent accuracy demonstrates good focus")
        elif detailed_metrics['accuracy'] < 0.5:
            insights.append("Low accuracy may indicate attention or processing difficulties")
        
        if detailed_metrics['reaction_consistency'] > 0.7:
            insights.append("Consistent reaction times indicate stable attention")
        elif detailed_metrics['reaction_consistency'] < 0.3:
            insights.append("Highly variable reaction times suggest attention fluctuations")
        
        # Stress-related insights
        if detailed_metrics['stress_indicators'] > 60:
            insights.append("Multiple stress indicators present in behavior")
            insights.append("Consider stress management techniques")
        
        # Positive insights
        if anxiety_score < 30 and depression_score < 30:
            insights.append("Overall positive mental health indicators")
        
        if detailed_metrics['sustained_attention_consistency'] > 0.8:
            insights.append("Strong sustained attention capabilities")
        
        return insights
    
    def _assess_risk_level(self, anxiety_score, depression_score, attention_score, detailed_metrics):
        """Assess overall risk level and need for professional attention"""
        
        risk_factors = 0
        
        # High individual scores
        if anxiety_score > 80:
            risk_factors += 3
        elif anxiety_score > 60:
            risk_factors += 2
        elif anxiety_score > 40:
            risk_factors += 1
        
        if depression_score > 80:
            risk_factors += 3
        elif depression_score > 60:
            risk_factors += 2
        elif depression_score > 40:
            risk_factors += 1
        
        if attention_score < 20:
            risk_factors += 3
        elif attention_score < 40:
            risk_factors += 2
        elif attention_score < 60:
            risk_factors += 1
        
        # Additional behavioral risk factors
        if detailed_metrics['impulsivity_score'] > 80:
            risk_factors += 2
        
        if detailed_metrics['emotional_regulation_score'] < 30:
            risk_factors += 2
        
        if detailed_metrics['stress_indicators'] > 80:
            risk_factors += 2
        
        if detailed_metrics['emotional_bias_score'] < -0.6:  # Very negative bias
            risk_factors += 1
        
        # Determine risk level
        if risk_factors >= 6:
            level = 'high'
            requires_attention = True
        elif risk_factors >= 3:
            level = 'medium'
            requires_attention = True
        else:
            level = 'low'
            requires_attention = False
        
        return {
            'level': level,
            'requires_attention': requires_attention,
            'risk_factors': risk_factors,
            'primary_concerns': self._identify_primary_concerns(
                anxiety_score, depression_score, attention_score, detailed_metrics
            )
        }
    
    def _identify_primary_concerns(self, anxiety_score, depression_score, attention_score, detailed_metrics):
        """Identify primary areas of concern"""
        concerns = []
        
        scores = {
            'anxiety': anxiety_score,
            'depression': depression_score,
            'attention_deficit': 100 - attention_score,  # Invert for concern level
            'impulsivity': detailed_metrics['impulsivity_score'],
            'emotional_dysregulation': 100 - detailed_metrics['emotional_regulation_score']
        }
        
        # Sort by severity
        sorted_concerns = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        for concern, score in sorted_concerns:
            if score > 60:
                concerns.append(concern)
        
        return concerns[:3]  # Return top 3 concerns
    
    def _generate_recommendations(self, risk_assessment, insights):
        """Generate personalized recommendations based on analysis"""
        recommendations = []
        
        if risk_assessment['level'] == 'high':
            recommendations.append({
                'category': 'professional_help',
                'priority': 'high',
                'text': 'Consider speaking with a mental health professional for comprehensive assessment',
                'type': 'urgent'
            })
        elif risk_assessment['level'] == 'medium':
            recommendations.append({
                'category': 'monitoring',
                'priority': 'medium',
                'text': 'Continue monitoring symptoms and consider professional consultation if patterns persist',
                'type': 'advisory'
            })
        
        # Specific recommendations based on primary concerns
        for concern in risk_assessment['primary_concerns']:
            if concern == 'anxiety':
                recommendations.extend([
                    {
                        'category': 'self_care',
                        'priority': 'medium',
                        'text': 'Practice relaxation techniques like deep breathing or mindfulness',
                        'type': 'self_help'
                    },
                    {
                        'category': 'lifestyle',
                        'priority': 'medium',
                        'text': 'Consider regular exercise and consistent sleep schedule',
                        'type': 'lifestyle'
                    }
                ])
            
            elif concern == 'depression':
                recommendations.extend([
                    {
                        'category': 'social',
                        'priority': 'medium',
                        'text': 'Maintain social connections and engage in enjoyable activities',
                        'type': 'lifestyle'
                    },
                    {
                        'category': 'professional_help',
                        'priority': 'medium',
                        'text': 'Consider counseling or therapy for mood support',
                        'type': 'advisory'
                    }
                ])
            
            elif concern == 'attention_deficit':
                recommendations.extend([
                    {
                        'category': 'cognitive',
                        'priority': 'medium',
                        'text': 'Break tasks into smaller chunks and minimize distractions',
                        'type': 'self_help'
                    },
                    {
                        'category': 'evaluation',
                        'priority': 'medium',
                        'text': 'Consider evaluation for attention-related disorders if difficulties persist',
                        'type': 'advisory'
                    }
                ])
            
            elif concern == 'impulsivity':
                recommendations.append({
                    'category': 'behavioral',
                    'priority': 'medium',
                    'text': 'Practice pause-and-think strategies before making decisions',
                    'type': 'self_help'
                })
            
            elif concern == 'emotional_dysregulation':
                recommendations.append({
                    'category': 'emotional',
                    'priority': 'medium',
                    'text': 'Learn emotion regulation techniques like cognitive reframing',
                    'type': 'self_help'
                })
        
        # General wellness recommendations
        recommendations.extend([
            {
                'category': 'wellness',
                'priority': 'low',
                'text': 'Maintain regular sleep, exercise, and healthy eating habits',
                'type': 'lifestyle'
            },
            {
                'category': 'monitoring',
                'priority': 'low',
                'text': 'Continue periodic self-assessment through FeelSync games',
                'type': 'platform'
            }
        ])
        
        return recommendations
    
    def _load_analysis_rules(self):
        """Load rule-based analysis guidelines"""
        return {
            'anxiety_thresholds': {'low': 30, 'medium': 60, 'high': 80},
            'depression_thresholds': {'low': 30, 'medium': 60, 'high': 80},
            'attention_thresholds': {'high': 80, 'medium': 60, 'low': 30},
            'reaction_time_norms': {'fast': 500, 'normal': 1000, 'slow': 1500},
            'accuracy_norms': {'high': 0.8, 'medium': 0.6, 'low': 0.4},
            'hesitation_thresholds': {'low': 0.1, 'medium': 0.3, 'high': 0.5}
        }
    
    def compare_with_normative_data(self, user_metrics, age_group='adolescent'):
        """Compare user metrics with normative data for their age group"""
        
        # Simplified normative data (in a real system, this would come from research)
        norms = {
            'adolescent': {
                'reaction_time_mean': (600, 1200),  # (min, max) normal range
                'accuracy': (0.6, 0.9),
                'hesitation_frequency': (0.1, 0.4),
                'emotional_bias_score': (-0.2, 0.3)
            }
        }
        
        comparison = {}
        age_norms = norms.get(age_group, norms['adolescent'])
        
        for metric, (min_norm, max_norm) in age_norms.items():
            user_value = user_metrics.get(metric, 0)
            
            if user_value < min_norm:
                comparison[metric] = 'below_average'
            elif user_value > max_norm:
                comparison[metric] = 'above_average'
            else:
                comparison[metric] = 'average'
        
        return comparison
    
    def generate_longitudinal_analysis(self, user_analyses_history):
        """Analyze trends across multiple sessions for a user"""
        
        if len(user_analyses_history) < 2:
            return {'status': 'insufficient_data', 'message': 'Need at least 2 sessions for trend analysis'}
        
        # Extract time series data
        dates = [analysis.created_at for analysis in user_analyses_history]
        anxiety_scores = [analysis.anxiety_score for analysis in user_analyses_history]
        depression_scores = [analysis.depression_score for analysis in user_analyses_history]
        attention_scores = [analysis.attention_score for analysis in user_analyses_history]
        
        # Calculate trends
        trends = {
            'anxiety_trend': self._calculate_trend(anxiety_scores),
            'depression_trend': self._calculate_trend(depression_scores),
            'attention_trend': self._calculate_trend(attention_scores),
            'timespan_days': (dates[-1] - dates[0]).days,
            'session_frequency': len(user_analyses_history) / max((dates[-1] - dates[0]).days, 1),
            'overall_trajectory': self._assess_overall_trajectory(anxiety_scores, depression_scores, attention_scores)
        }
        
        return trends
    
    def _calculate_trend(self, scores):
        """Calculate trend direction for a series of scores"""
        if len(scores) < 3:
            return 'insufficient_data'
        
        # Simple linear trend calculation
        x = range(len(scores))
        slope = np.polyfit(x, scores, 1)[0]
        
        if slope > 2:
            return 'increasing'
        elif slope < -2:
            return 'decreasing'
        else:
            return 'stable'
    
    def _assess_overall_trajectory(self, anxiety_scores, depression_scores, attention_scores):
        """Assess overall mental health trajectory"""
        
        # Calculate recent vs. early averages
        n = len(anxiety_scores)
        split = max(2, n // 2)
        
        early_anxiety = np.mean(anxiety_scores[:split])
        recent_anxiety = np.mean(anxiety_scores[split:])
        
        early_depression = np.mean(depression_scores[:split])
        recent_depression = np.mean(depression_scores[split:])
        
        early_attention = np.mean(attention_scores[:split])
        recent_attention = np.mean(attention_scores[split:])
        
        # Improvement = lower anxiety/depression, higher attention
        improvement_score = (
            (early_anxiety - recent_anxiety) +
            (early_depression - recent_depression) +
            (recent_attention - early_attention)
        ) / 3
        
        if improvement_score > 10:
            return 'improving'
        elif improvement_score < -10:
            return 'declining'
        else:
            return 'stable'
