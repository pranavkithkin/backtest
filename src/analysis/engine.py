"""
Enterprise Analysis Engine
=========================

Core analysis engine with statistical methods, ML predictions, and validation.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from scipy import stats
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
import logging

class AnalysisEngine:
    """Enterprise analysis engine with comprehensive statistical methods"""
    
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.analysis_config = config.get_analysis_config()
        self.ml_config = config.get('ml', {})
        
    def analyze_time_patterns(self, data: pd.DataFrame, timezone: str) -> Dict[str, Any]:
        """Comprehensive time-based pattern analysis"""
        
        self.logger.debug("Analyzing time patterns")
        results = {}
        
        # Hourly analysis with comprehensive metrics
        hourly_stats = data.groupby('hour').agg({
            'coin': 'count',
            'potential_risk': ['mean', 'std', 'median'],
            'potential_reward': ['mean', 'std', 'median'],
            'risk_reward_ratio': ['mean', 'std', 'median', lambda x: (x >= 2).sum()],
            'time_volatility': 'mean',
            'signal_strength': lambda x: (x == 'Strong').sum()
        }).round(3)
        
        # Daily patterns
        daily_stats = data.groupby('day_name').agg({
            'coin': 'count',
            'potential_risk': ['mean', 'std'],
            'potential_reward': ['mean', 'std'],
            'risk_reward_ratio': ['mean', 'std'],
            'signal_strength': lambda x: (x == 'Strong').sum()
        }).round(3)
        
        # Market session analysis
        session_stats = data.groupby('market_session').agg({
            'coin': 'count',
            'potential_risk': ['mean', 'std'],
            'potential_reward': ['mean', 'std'],
            'risk_reward_ratio': ['mean', 'std'],
            'signal_strength': lambda x: (x == 'Strong').sum()
        }).round(3)
        
        # Weekend vs weekday
        weekend_stats = data.groupby('is_weekend').agg({
            'coin': 'count',
            'potential_risk': 'mean',
            'potential_reward': 'mean',
            'risk_reward_ratio': 'mean',
            'signal_strength': lambda x: (x == 'Strong').sum()
        }).round(3)
        
        # Monthly seasonality
        monthly_stats = data.groupby('month').agg({
            'coin': 'count',
            'risk_reward_ratio': ['mean', 'std'],
            'signal_strength': lambda x: (x == 'Strong').sum()
        }).round(3)
        
        results = {
            'hourly': hourly_stats,
            'daily': daily_stats,
            'session': session_stats,
            'weekend': weekend_stats,
            'monthly': monthly_stats,
            'timezone': timezone,
            'analysis_timestamp': pd.Timestamp.now()
        }
        
        return results
    
    def detect_market_conditions(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Advanced market condition detection with clustering"""
        
        self.logger.debug("Detecting market conditions")
        
        # Group by weekly periods for regime analysis
        weekly_data = data.groupby([
            data['timestamp_local'].dt.to_period('W')
        ]).agg({
            'coin': 'count',
            'potential_risk': ['mean', 'std'],
            'potential_reward': ['mean', 'std'],
            'risk_reward_ratio': ['mean', 'std'],
            'time_volatility': 'mean',
            'signal_strength': lambda x: (x == 'Strong').sum() / len(x) if len(x) > 0 else 0
        }).reset_index()
        
        # Flatten column names
        weekly_data.columns = ['_'.join(col).strip() if isinstance(col, tuple) else col 
                              for col in weekly_data.columns]
        
        # Features for clustering
        feature_cols = [
            'potential_risk_mean', 'potential_reward_mean', 'risk_reward_ratio_mean',
            'potential_risk_std', 'time_volatility_mean'
        ]
        
        # Add signal strength if available
        strength_col = 'signal_strength_<lambda>'
        if strength_col in weekly_data.columns:
            feature_cols.append(strength_col)
        
        # Clean data for clustering
        available_cols = [col for col in feature_cols if col in weekly_data.columns]
        clean_data = weekly_data[available_cols].dropna()
        
        if len(clean_data) > 5:
            # Normalize features
            scaler = StandardScaler()
            scaled_features = scaler.fit_transform(clean_data)
            
            # Determine optimal clusters
            optimal_clusters = min(4, max(2, len(clean_data) // 3))
            
            # K-means clustering
            kmeans = KMeans(n_clusters=optimal_clusters, random_state=42)
            clusters = kmeans.fit_predict(scaled_features)
            
            weekly_data.loc[clean_data.index, 'market_regime'] = clusters
            
            # Label regimes based on characteristics
            regime_stats = clean_data.groupby(clusters).mean()
            regime_labels = self._label_market_regimes(regime_stats)
            
            weekly_data['regime_label'] = weekly_data['market_regime'].map(regime_labels)
        
        return {
            'weekly_data': weekly_data,
            'regime_analysis': True if len(clean_data) > 5 else False,
            'feature_columns': available_cols,
            'clusters_found': optimal_clusters if len(clean_data) > 5 else 0
        }
    
    def _label_market_regimes(self, regime_stats: pd.DataFrame) -> Dict[int, str]:
        """Label market regimes based on statistical characteristics"""
        
        regime_labels = {}
        
        for cluster_id in regime_stats.index:
            stats_row = regime_stats.loc[cluster_id]
            
            # Get mean values for comparison
            mean_rr = regime_stats['risk_reward_ratio_mean'].mean()
            mean_risk = regime_stats['potential_risk_mean'].mean()
            
            if 'risk_reward_ratio_mean' in stats_row.index:
                if stats_row['risk_reward_ratio_mean'] > mean_rr:
                    if 'potential_risk_mean' in stats_row.index and stats_row['potential_risk_mean'] < mean_risk:
                        regime_labels[cluster_id] = 'Optimal'
                    else:
                        regime_labels[cluster_id] = 'High_Reward'
                elif 'potential_risk_mean' in stats_row.index and stats_row['potential_risk_mean'] > mean_risk:
                    regime_labels[cluster_id] = 'High_Risk'
                else:
                    regime_labels[cluster_id] = 'Conservative'
            else:
                regime_labels[cluster_id] = f'Regime_{cluster_id}'
        
        return regime_labels
    
    def optimize_parameters(self, data: pd.DataFrame, confidence_level: float = 0.95) -> Dict[str, Any]:
        """Advanced parameter optimization with statistical validation"""
        
        self.logger.debug("Optimizing trading parameters")
        
        valid_data = data.dropna(subset=['potential_risk', 'potential_reward', 'risk_reward_ratio'])
        
        if len(valid_data) == 0:
            return {'error': 'No valid data for optimization'}
        
        results = {}
        
        # Risk level optimization with configured ranges
        risk_ranges = self.analysis_config.risk_ranges
        risk_analysis = {}
        
        for risk_config in risk_ranges:
            min_risk, max_risk = risk_config['min'], risk_config['max']
            label = risk_config['label']
            
            subset = valid_data[
                (valid_data['potential_risk'] >= min_risk) & 
                (valid_data['potential_risk'] < max_risk)
            ]
            
            min_signals = self.analysis_config.minimum_signals.get('risk_analysis', 5)
            if len(subset) >= min_signals:
                strong_signals = len(subset[subset['signal_strength'] == 'Strong'])
                
                risk_analysis[f'{min_risk}-{max_risk}%'] = {
                    'label': label,
                    'count': len(subset),
                    'avg_risk': float(subset['potential_risk'].mean()),
                    'avg_reward': float(subset['potential_reward'].mean()),
                    'avg_rr_ratio': float(subset['risk_reward_ratio'].mean()),
                    'success_potential': float(len(subset[subset['risk_reward_ratio'] >= 2]) / len(subset) * 100),
                    'strong_signals': int(strong_signals),
                    'strong_signal_pct': float(strong_signals / len(subset) * 100),
                    'median_rr': float(subset['risk_reward_ratio'].median()),
                    'confidence_interval': self._calculate_confidence_interval(
                        subset['risk_reward_ratio'], confidence_level
                    )
                }
        
        # Time-based optimization
        time_optimization = self._optimize_time_parameters(valid_data)
        
        # Statistical significance testing
        significance_tests = self._perform_statistical_tests(valid_data)
        
        # Find optimal parameters
        recommendations = self._generate_parameter_recommendations(risk_analysis, time_optimization)
        
        results = {
            'risk_analysis': risk_analysis,
            'time_optimization': time_optimization,
            'significance_tests': significance_tests,
            'recommendations': recommendations,
            'confidence_level': confidence_level,
            'sample_size': len(valid_data)
        }
        
        return results
    
    def _optimize_time_parameters(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Optimize time-based parameters"""
        
        # Hourly performance analysis
        hourly_performance = data.groupby('hour').agg({
            'risk_reward_ratio': ['mean', 'count', 'std'],
            'signal_strength': lambda x: (x == 'Strong').sum(),
            'potential_risk': 'mean'
        }).round(3)
        
        # Session performance analysis
        session_performance = data.groupby('market_session').agg({
            'risk_reward_ratio': ['mean', 'count', 'std'],
            'potential_risk': 'mean',
            'signal_strength': lambda x: (x == 'Strong').sum()
        }).round(3)
        
        # Category performance analysis
        category_performance = data.groupby('coin_category').agg({
            'risk_reward_ratio': ['mean', 'count', 'std'],
            'potential_risk': 'mean',
            'potential_reward': 'mean'
        }).round(3)
        
        return {
            'hourly': hourly_performance.to_dict(),
            'session': session_performance.to_dict(),
            'category': category_performance.to_dict()
        }
    
    def _perform_statistical_tests(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Perform statistical significance tests"""
        
        tests = {}
        
        try:
            # Weekend vs weekday test
            weekend_rr = data[data['is_weekend'] == True]['risk_reward_ratio'].dropna()
            weekday_rr = data[data['is_weekend'] == False]['risk_reward_ratio'].dropna()
            
            if len(weekend_rr) > 5 and len(weekday_rr) > 5:
                weekend_test = stats.ttest_ind(weekend_rr, weekday_rr)
                tests['weekend_vs_weekday'] = {
                    'statistic': float(weekend_test.statistic),
                    'p_value': float(weekend_test.pvalue),
                    'significant': weekend_test.pvalue < 0.05,
                    'weekend_mean': float(weekend_rr.mean()),
                    'weekday_mean': float(weekday_rr.mean()),
                    'interpretation': 'Weekends perform differently' if weekend_test.pvalue < 0.05 else 'No significant difference'
                }
            
            # Session differences test
            sessions = data['market_session'].unique()
            if len(sessions) > 2:
                session_groups = [
                    data[data['market_session'] == session]['risk_reward_ratio'].dropna() 
                    for session in sessions 
                    if len(data[data['market_session'] == session]) > 5
                ]
                
                if len(session_groups) > 2:
                    session_test = stats.f_oneway(*session_groups)
                    tests['session_differences'] = {
                        'statistic': float(session_test.statistic),
                        'p_value': float(session_test.pvalue),
                        'significant': session_test.pvalue < 0.05,
                        'interpretation': 'Trading sessions show significant differences' if session_test.pvalue < 0.05 else 'No significant session differences'
                    }
                    
        except Exception as e:
            tests['error'] = str(e)
            self.logger.warning(f"Statistical tests failed: {e}")
        
        return tests
    
    def _calculate_confidence_interval(self, data: pd.Series, confidence_level: float) -> Dict[str, float]:
        """Calculate confidence interval for data series"""
        
        try:
            mean = data.mean()
            sem = stats.sem(data.dropna())
            margin = sem * stats.t.ppf((1 + confidence_level) / 2, len(data) - 1)
            
            return {
                'lower': float(mean - margin),
                'upper': float(mean + margin),
                'mean': float(mean)
            }
        except:
            return {'lower': 0, 'upper': 0, 'mean': 0}
    
    def _generate_parameter_recommendations(self, risk_analysis: Dict, time_optimization: Dict) -> Dict[str, Any]:
        """Generate optimal parameter recommendations"""
        
        recommendations = {}
        
        # Find optimal risk range
        if risk_analysis:
            best_risk = max(
                risk_analysis.items(),
                key=lambda x: x[1]['success_potential'] * (x[1]['count'] / 100),
                default=(None, {})
            )
            recommendations['optimal_risk_range'] = best_risk[0] if best_risk[0] else 'N/A'
            recommendations['risk_reasoning'] = f"Best success rate: {best_risk[1].get('success_potential', 0):.1f}%" if best_risk[1] else 'Insufficient data'
        
        # Find optimal trading times
        hourly_data = time_optimization.get('hourly', {})
        if hourly_data and 'risk_reward_ratio' in hourly_data and 'mean' in hourly_data['risk_reward_ratio']:
            best_hour = max(hourly_data['risk_reward_ratio']['mean'].items(), key=lambda x: x[1], default=(0, 0))
            recommendations['optimal_hour'] = int(best_hour[0])
            recommendations['hour_performance'] = float(best_hour[1])
        
        # Find optimal session
        session_data = time_optimization.get('session', {})
        if session_data and 'risk_reward_ratio' in session_data and 'mean' in session_data['risk_reward_ratio']:
            best_session = max(session_data['risk_reward_ratio']['mean'].items(), key=lambda x: x[1], default=('N/A', 0))
            recommendations['optimal_session'] = best_session[0]
            recommendations['session_performance'] = float(best_session[1])
        
        return recommendations
    
    def analyze_risk_distribution(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze risk distribution patterns"""
        
        valid_data = data.dropna(subset=['potential_risk'])
        
        return {
            'risk_statistics': {
                'mean': float(valid_data['potential_risk'].mean()),
                'median': float(valid_data['potential_risk'].median()),
                'std': float(valid_data['potential_risk'].std()),
                'min': float(valid_data['potential_risk'].min()),
                'max': float(valid_data['potential_risk'].max()),
                'q25': float(valid_data['potential_risk'].quantile(0.25)),
                'q75': float(valid_data['potential_risk'].quantile(0.75))
            },
            'risk_distribution': valid_data['potential_risk'].value_counts().to_dict(),
            'sample_size': len(valid_data)
        }
    
    def analyze_asset_performance(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze individual asset performance"""
        
        min_signals = self.analysis_config.minimum_signals.get('coin_analysis', 3)
        
        asset_stats = data.groupby('coin').agg({
            'timestamp_local': 'count',
            'potential_risk': ['mean', 'std'],
            'potential_reward': ['mean', 'std'],
            'risk_reward_ratio': ['mean', 'std', 'median'],
            'signal_strength': lambda x: (x == 'Strong').sum()
        }).round(3)
        
        # Filter assets with sufficient signals
        asset_stats = asset_stats[asset_stats[('timestamp_local', 'count')] >= min_signals]
        
        return {
            'asset_statistics': asset_stats.to_dict(),
            'top_performers': asset_stats.nlargest(10, ('risk_reward_ratio', 'mean')).to_dict(),
            'most_active': asset_stats.nlargest(10, ('timestamp_local', 'count')).to_dict(),
            'minimum_signals_threshold': min_signals
        }
    
    def generate_predictions(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Generate ML predictions for risk-reward optimization"""
        
        valid_data = data.dropna(subset=['potential_risk', 'potential_reward', 'risk_reward_ratio'])
        min_samples = self.ml_config.get('prediction_threshold', 50)
        
        if len(valid_data) < min_samples:
            return {'error': f'Insufficient data for ML predictions: {len(valid_data)} < {min_samples}'}
        
        try:
            # Feature engineering for ML
            feature_columns = self.ml_config.get('features', {}).get('time_based', [])
            categorical_features = self.ml_config.get('features', {}).get('categorical', [])
            
            # Create feature matrix
            X_numeric = valid_data[feature_columns]
            X_categorical = pd.get_dummies(valid_data[categorical_features])
            X = pd.concat([X_numeric, X_categorical], axis=1)
            y = valid_data['risk_reward_ratio']
            
            # Split data
            rf_config = self.ml_config.get('models', {}).get('random_forest', {})
            test_size = rf_config.get('test_size', 0.2)
            random_state = rf_config.get('random_state', 42)
            
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state)
            
            # Train model
            n_estimators = rf_config.get('n_estimators', 100)
            rf_model = RandomForestRegressor(n_estimators=n_estimators, random_state=random_state)
            rf_model.fit(X_train, y_train)
            
            # Evaluate model
            train_score = rf_model.score(X_train, y_train)
            test_score = rf_model.score(X_test, y_test)
            
            # Feature importance
            feature_importance = pd.DataFrame({
                'feature': X.columns,
                'importance': rf_model.feature_importances_
            }).sort_values('importance', ascending=False)
            
            return {
                'model_performance': {
                    'train_score': float(train_score),
                    'test_score': float(test_score),
                    'feature_count': len(X.columns),
                    'sample_size': len(valid_data)
                },
                'feature_importance': feature_importance.to_dict('records'),
                'model_available': True,
                'prediction_threshold_met': True
            }
            
        except Exception as e:
            return {'error': f'ML prediction failed: {str(e)}'}
    
    def validate_results(self, results: Dict[str, Any], confidence_level: float) -> Dict[str, Any]:
        """Validate analysis results for statistical significance"""
        
        validation = {
            'confidence_level': confidence_level,
            'validation_timestamp': pd.Timestamp.now().isoformat(),
            'checks': {}
        }
        
        # Validate sample sizes
        if 'parameter_optimization' in results and 'sample_size' in results['parameter_optimization']:
            sample_size = results['parameter_optimization']['sample_size']
            validation['checks']['sample_size'] = {
                'value': sample_size,
                'adequate': sample_size >= 30,
                'recommendation': 'Adequate for analysis' if sample_size >= 30 else 'Consider more data for reliability'
            }
        
        # Validate statistical significance
        if 'parameter_optimization' in results and 'significance_tests' in results['parameter_optimization']:
            sig_tests = results['parameter_optimization']['significance_tests']
            validation['checks']['statistical_significance'] = {
                'tests_performed': list(sig_tests.keys()),
                'significant_results': [k for k, v in sig_tests.items() if isinstance(v, dict) and v.get('significant', False)]
            }
        
        return validation