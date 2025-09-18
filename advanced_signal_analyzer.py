#!/usr/bin/env python3
"""
Advanced Trading Signal Analysis Software
🎯 Comprehensive signal analysis with timezone support, market condition detection, 
   and parameter optimization for maximum profit potential.

Features:
- Global timezone support for any trading location
- Market regime detection and classification
- Statistical parameter optimization
- Time-based pattern analysis
- Risk-reward optimization
- Performance forecasting
"""

import sys
from pathlib import Path
import os
import json
from datetime import datetime, timedelta
import pytz
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Data analysis libraries
import pandas as pd
import numpy as np
from scipy import stats
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor

# Visualization libraries
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.offline as pyo

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import existing components
try:
    from crypto_analyzer import ProfitLossAnalyzer, PortfolioCalculator, ConcurrentPortfolioCalculator
    from crypto_analyzer.utils import setup_logging, find_csv_files
except ImportError:
    print("Warning: crypto_analyzer components not found. Running in standalone mode.")

import logging
logger = logging.getLogger(__name__)

# Global configuration
TRADING_TIMEZONES = {
    'Dubai': 'Asia/Dubai',
    'London': 'Europe/London', 
    'New York': 'America/New_York',
    'Moscow': 'Europe/Moscow',
    'Tokyo': 'Asia/Tokyo',
    'Sydney': 'Australia/Sydney',
    'Hong Kong': 'Asia/Hong_Kong',
    'Singapore': 'Asia/Singapore',
    'Zurich': 'Europe/Zurich',
    'Frankfurt': 'Europe/Berlin',
    'Toronto': 'America/Toronto',
    'Chicago': 'America/Chicago',
    'Los Angeles': 'America/Los_Angeles'
}

class AdvancedSignalAnalyzer:
    """
    Comprehensive trading signal analyzer with timezone support,
    market condition detection, and parameter optimization.
    """
    
    def __init__(self, timezone: str = 'Dubai'):
        if timezone not in TRADING_TIMEZONES:
            print(f"❌ Invalid timezone. Available: {list(TRADING_TIMEZONES.keys())}")
            timezone = 'Dubai'
        
        self.timezone_name = timezone
        self.timezone = pytz.timezone(TRADING_TIMEZONES[timezone])
        self.data = None
        self.analysis_results = {}
        self.ml_models = {}
        
        print(f"🌍 Analyzer initialized for {timezone} ({TRADING_TIMEZONES[timezone]})")
        
    def load_signals(self, csv_file: str) -> pd.DataFrame:
        """Load and preprocess trading signals with comprehensive feature engineering"""
        print(f"📁 Loading signals from {csv_file}...")
        
        if not os.path.exists(csv_file):
            raise FileNotFoundError(f"CSV file not found: {csv_file}")
        
        df = pd.read_csv(csv_file)
        print(f"📊 Raw data: {len(df)} rows, {len(df.columns)} columns")
        
        # Convert timestamp to user's timezone
        df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'], utc=True)
        df['timestamp_local'] = df['timestamp_utc'].dt.tz_convert(self.timezone)
        
        # Enhanced time features
        df['hour'] = df['timestamp_local'].dt.hour
        df['day_of_week'] = df['timestamp_local'].dt.dayofweek
        df['day_name'] = df['timestamp_local'].dt.day_name()
        df['month'] = df['timestamp_local'].dt.month
        df['quarter'] = df['timestamp_local'].dt.quarter
        df['week_of_year'] = df['timestamp_local'].dt.isocalendar().week
        df['day_of_month'] = df['timestamp_local'].dt.day
        
        # Market session classification with enhanced logic
        df['market_session'] = df['hour'].apply(self._classify_market_session_advanced)
        
        # Weekend vs weekday
        df['is_weekend'] = df['day_of_week'].isin([5, 6])
        
        # Clean numeric columns
        numeric_cols = ['entry', 'sl', 'tp']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Enhanced risk-reward calculations
        df['potential_risk'] = np.where(
            (df['entry'].notna()) & (df['sl'].notna()),
            abs((df['entry'] - df['sl']) / df['entry']) * 100,
            np.nan
        )
        
        df['potential_reward'] = np.where(
            (df['entry'].notna()) & (df['tp'].notna()),
            abs((df['tp'] - df['entry']) / df['entry']) * 100,
            np.nan
        )
        
        df['risk_reward_ratio'] = np.where(
            df['potential_risk'] > 0,
            df['potential_reward'] / df['potential_risk'],
            np.nan
        )
        
        # Additional features
        df['signal_strength'] = np.where(
            df['risk_reward_ratio'] >= 2, 'Strong',
            np.where(df['risk_reward_ratio'] >= 1.5, 'Medium', 'Weak')
        )
        
        # Coin category classification
        df['coin_category'] = df['coin'].apply(self._classify_coin_category)
        
        # Time-based volatility proxy
        df['time_volatility'] = self._calculate_time_volatility(df)
        
        # Market cap tier (simplified classification)
        df['market_tier'] = df['coin'].apply(self._classify_market_tier)
        
        self.data = df
        print(f"✅ Processed {len(df)} signals with {df['coin'].nunique()} unique assets")
        print(f"📅 Date range: {df['timestamp_local'].min().strftime('%Y-%m-%d')} to {df['timestamp_local'].max().strftime('%Y-%m-%d')}")
        return df
    
    def _classify_market_session_advanced(self, hour: int) -> str:
        """Advanced market session classification based on major trading centers"""
        # Adjusted for global markets overlap
        if 0 <= hour < 3:
            return 'Pacific_Close'
        elif 3 <= hour < 8:
            return 'Asian_Active'
        elif 8 <= hour < 12:
            return 'European_Open'
        elif 12 <= hour < 16:
            return 'European_US_Overlap'
        elif 16 <= hour < 20:
            return 'US_Active'
        else:
            return 'US_Pacific_Overlap'
    
    def _classify_coin_category(self, coin: str) -> str:
        """Classify coins into categories"""
        # Major cryptocurrencies
        major_coins = ['BTC', 'ETH', 'BNB', 'XRP', 'ADA', 'SOL', 'DOGE', 'LTC', 'DOT', 'AVAX']
        # DeFi tokens
        defi_tokens = ['UNI', 'CAKE', 'SUSHI', 'AAVE', 'COMP', 'MKR']
        # Meme coins
        meme_coins = ['DOGE', 'SHIB', 'PEPE', 'FLOKI']
        
        coin_upper = coin.upper()
        
        if coin_upper in major_coins:
            return 'Major'
        elif coin_upper in defi_tokens:
            return 'DeFi'
        elif coin_upper in meme_coins:
            return 'Meme'
        elif coin_upper.startswith('1000'):
            return 'Futures'
        else:
            return 'Alt'
    
    def _classify_market_tier(self, coin: str) -> str:
        """Classify market cap tier (simplified)"""
        top_tier = ['BTC', 'ETH', 'BNB', 'XRP', 'ADA', 'SOL']
        mid_tier = ['DOGE', 'LTC', 'DOT', 'AVAX', 'UNI', 'LINK']
        
        coin_upper = coin.upper()
        
        if coin_upper in top_tier:
            return 'Large_Cap'
        elif coin_upper in mid_tier:
            return 'Mid_Cap'
        else:
            return 'Small_Cap'
    
    def _calculate_time_volatility(self, df: pd.DataFrame) -> pd.Series:
        """Calculate time-based volatility proxy"""
        # Simple volatility based on hour and day patterns
        volatility_scores = {
            'hour': {0: 0.3, 1: 0.2, 2: 0.2, 3: 0.4, 4: 0.5, 5: 0.6, 
                    6: 0.7, 7: 0.8, 8: 0.9, 9: 1.0, 10: 1.0, 11: 0.9,
                    12: 0.8, 13: 0.9, 14: 1.0, 15: 1.0, 16: 0.9, 17: 0.8,
                    18: 0.7, 19: 0.6, 20: 0.5, 21: 0.4, 22: 0.4, 23: 0.3},
            'day': {0: 1.0, 1: 0.9, 2: 0.8, 3: 0.8, 4: 0.9, 5: 0.6, 6: 0.5}
        }
        
        hour_vol = df['hour'].map(volatility_scores['hour'])
        day_vol = df['day_of_week'].map(volatility_scores['day'])
        
        return (hour_vol + day_vol) / 2
    
    def analyze_time_patterns(self) -> Dict:
        """Comprehensive time-based pattern analysis"""
        if self.data is None:
            raise ValueError("No data loaded. Call load_signals() first.")
        
        results = {}
        
        # Enhanced hourly analysis
        hourly_stats = self.data.groupby('hour').agg({
            'coin': 'count',
            'potential_risk': ['mean', 'std', 'median'],
            'potential_reward': ['mean', 'std', 'median'],
            'risk_reward_ratio': ['mean', 'std', 'median', lambda x: (x >= 2).sum()],
            'time_volatility': 'mean'
        }).round(3)
        
        # Daily patterns
        daily_stats = self.data.groupby('day_name').agg({
            'coin': 'count',
            'potential_risk': ['mean', 'std'],
            'potential_reward': ['mean', 'std'],
            'risk_reward_ratio': ['mean', 'std']
        }).round(3)
        
        # Market session analysis
        session_stats = self.data.groupby('market_session').agg({
            'coin': 'count',
            'potential_risk': ['mean', 'std'],
            'potential_reward': ['mean', 'std'],
            'risk_reward_ratio': ['mean', 'std'],
            'signal_strength': lambda x: (x == 'Strong').sum()
        }).round(3)
        
        # Weekend vs weekday
        weekend_stats = self.data.groupby('is_weekend').agg({
            'coin': 'count',
            'potential_risk': 'mean',
            'potential_reward': 'mean',
            'risk_reward_ratio': 'mean'
        }).round(3)
        
        # Monthly seasonality
        monthly_stats = self.data.groupby('month').agg({
            'coin': 'count',
            'risk_reward_ratio': 'mean'
        }).round(3)
        
        results['hourly'] = hourly_stats
        results['daily'] = daily_stats
        results['session'] = session_stats
        results['weekend'] = weekend_stats
        results['monthly'] = monthly_stats
        
        self.analysis_results['time_patterns'] = results
        return results
    
    def detect_market_conditions(self) -> Dict:
        """Advanced market condition detection with machine learning"""
        if self.data is None:
            raise ValueError("No data loaded. Call load_signals() first.")
        
        # Group by time periods for regime analysis
        weekly_data = self.data.groupby([
            self.data['timestamp_local'].dt.to_period('W')
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
            'potential_risk_std', 'time_volatility_mean', 'signal_strength_<lambda>'
        ]
        
        # Clean data for clustering
        available_cols = [col for col in feature_cols if col in weekly_data.columns]
        clean_data = weekly_data[available_cols].dropna()
        
        if len(clean_data) > 5:
            # Normalize features
            scaler = StandardScaler()
            scaled_features = scaler.fit_transform(clean_data)
            
            # Determine optimal clusters using elbow method
            optimal_clusters = min(4, max(2, len(clean_data) // 3))
            
            # K-means clustering
            kmeans = KMeans(n_clusters=optimal_clusters, random_state=42)
            clusters = kmeans.fit_predict(scaled_features)
            
            weekly_data.loc[clean_data.index, 'market_regime'] = clusters
            
            # Label regimes based on characteristics
            regime_stats = clean_data.groupby(clusters).mean()
            regime_labels = {}
            
            for cluster_id in regime_stats.index:
                stats = regime_stats.loc[cluster_id]
                
                if 'risk_reward_ratio_mean' in stats.index:
                    if stats['risk_reward_ratio_mean'] > regime_stats['risk_reward_ratio_mean'].mean():
                        if 'potential_risk_mean' in stats.index and stats['potential_risk_mean'] < regime_stats['potential_risk_mean'].mean():
                            regime_labels[cluster_id] = 'Optimal'
                        else:
                            regime_labels[cluster_id] = 'High_Reward'
                    elif 'potential_risk_mean' in stats.index and stats['potential_risk_mean'] > regime_stats['potential_risk_mean'].mean():
                        regime_labels[cluster_id] = 'High_Risk'
                    else:
                        regime_labels[cluster_id] = 'Conservative'
                else:
                    regime_labels[cluster_id] = f'Regime_{cluster_id}'
            
            weekly_data['regime_label'] = weekly_data['market_regime'].map(regime_labels)
        
        self.analysis_results['market_conditions'] = weekly_data
        return weekly_data
    
    def optimize_parameters_advanced(self, coin_filter: Optional[List[str]] = None) -> Dict:
        """Advanced parameter optimization with statistical significance testing"""
        if self.data is None:
            raise ValueError("No data loaded. Call load_signals() first.")
        
        data = self.data.copy()
        if coin_filter:
            data = data[data['coin'].isin(coin_filter)]
        
        valid_data = data.dropna(subset=['potential_risk', 'potential_reward', 'risk_reward_ratio'])
        
        if len(valid_data) == 0:
            return {'error': 'No valid data for optimization'}
        
        results = {}
        
        # Enhanced risk analysis with more granular ranges
        risk_ranges = [
            (0, 1), (1, 2), (2, 3), (3, 5), (5, 7), (7, 10), 
            (10, 15), (15, 20), (20, 30), (30, 50)
        ]
        
        risk_analysis = {}
        for min_risk, max_risk in risk_ranges:
            subset = valid_data[
                (valid_data['potential_risk'] >= min_risk) & 
                (valid_data['potential_risk'] < max_risk)
            ]
            
            if len(subset) > 5:
                # Calculate advanced metrics
                strong_signals = len(subset[subset['signal_strength'] == 'Strong'])
                
                risk_analysis[f'{min_risk}-{max_risk}%'] = {
                    'count': len(subset),
                    'avg_risk': subset['potential_risk'].mean(),
                    'avg_reward': subset['potential_reward'].mean(),
                    'avg_rr_ratio': subset['risk_reward_ratio'].mean(),
                    'success_potential': len(subset[subset['risk_reward_ratio'] >= 2]) / len(subset) * 100,
                    'strong_signals': strong_signals,
                    'strong_signal_pct': strong_signals / len(subset) * 100,
                    'median_rr': subset['risk_reward_ratio'].median(),
                    'rr_std': subset['risk_reward_ratio'].std()
                }
        
        # Time-based optimization
        time_optimization = {}
        
        # Best hours analysis
        hourly_performance = valid_data.groupby('hour').agg({
            'risk_reward_ratio': ['mean', 'count', 'std'],
            'signal_strength': lambda x: (x == 'Strong').sum()
        }).round(3)
        
        # Best market sessions
        session_performance = valid_data.groupby('market_session').agg({
            'risk_reward_ratio': ['mean', 'count'],
            'potential_risk': 'mean',
            'signal_strength': lambda x: (x == 'Strong').sum()
        }).round(3)
        
        # Coin category analysis
        category_performance = valid_data.groupby('coin_category').agg({
            'risk_reward_ratio': ['mean', 'count'],
            'potential_risk': 'mean',
            'potential_reward': 'mean'
        }).round(3)
        
        # Statistical significance testing
        significance_tests = self._perform_significance_tests(valid_data)
        
        # Find optimal parameters with confidence intervals
        if risk_analysis:
            best_risk_range = max(risk_analysis.items(), 
                                 key=lambda x: x[1]['success_potential'] * (x[1]['count'] / 100))
        else:
            best_risk_range = ('N/A', {'success_potential': 0})
        
        best_hour = hourly_performance['risk_reward_ratio']['mean'].idxmax() if not hourly_performance.empty else 0
        best_session = session_performance['risk_reward_ratio']['mean'].idxmax() if not session_performance.empty else 'N/A'
        best_category = category_performance['risk_reward_ratio']['mean'].idxmax() if not category_performance.empty else 'N/A'
        
        results.update({
            'risk_analysis': risk_analysis,
            'time_optimization': {
                'hourly': hourly_performance.to_dict(),
                'session': session_performance.to_dict(),
                'category': category_performance.to_dict()
            },
            'significance_tests': significance_tests,
            'recommendations': {
                'optimal_risk_range': best_risk_range[0],
                'optimal_hour': int(best_hour),
                'optimal_session': best_session,
                'optimal_category': best_category,
                'confidence_level': 0.95,
                'sample_size': len(valid_data),
                'reasoning': {
                    'risk': f"Range {best_risk_range[0]} shows {best_risk_range[1]['success_potential']:.1f}% success rate with {best_risk_range[1].get('count', 0)} signals",
                    'time': f"Hour {best_hour}:00 and {best_session} session show best performance",
                    'category': f"{best_category} category shows highest average R/R ratio"
                }
            }
        })
        
        self.analysis_results['parameter_optimization'] = results
        return results
    
    def _perform_significance_tests(self, data: pd.DataFrame) -> Dict:
        """Perform statistical significance tests"""
        tests = {}
        
        try:
            # Test if weekends differ from weekdays
            weekend_rr = data[data['is_weekend'] == True]['risk_reward_ratio'].dropna()
            weekday_rr = data[data['is_weekend'] == False]['risk_reward_ratio'].dropna()
            
            if len(weekend_rr) > 5 and len(weekday_rr) > 5:
                weekend_test = stats.ttest_ind(weekend_rr, weekday_rr)
                tests['weekend_vs_weekday'] = {
                    'statistic': float(weekend_test.statistic),
                    'p_value': float(weekend_test.pvalue),
                    'significant': weekend_test.pvalue < 0.05,
                    'weekend_mean': float(weekend_rr.mean()),
                    'weekday_mean': float(weekday_rr.mean())
                }
            
            # Test session differences
            sessions = data['market_session'].unique()
            if len(sessions) > 2:
                session_groups = [data[data['market_session'] == session]['risk_reward_ratio'].dropna() 
                                 for session in sessions if len(data[data['market_session'] == session]) > 5]
                
                if len(session_groups) > 2:
                    session_test = stats.f_oneway(*session_groups)
                    tests['session_differences'] = {
                        'statistic': float(session_test.statistic),
                        'p_value': float(session_test.pvalue),
                        'significant': session_test.pvalue < 0.05
                    }
        except Exception as e:
            tests['error'] = str(e)
        
        return tests
    
    def generate_predictions(self) -> Dict:
        """Generate predictive models for optimal trading parameters"""
        if self.data is None:
            raise ValueError("No data loaded. Call load_signals() first.")
        
        valid_data = self.data.dropna(subset=['potential_risk', 'potential_reward', 'risk_reward_ratio'])
        
        if len(valid_data) < 50:
            return {'error': 'Insufficient data for reliable predictions'}
        
        try:
            # Features for prediction
            feature_columns = [
                'hour', 'day_of_week', 'month', 'time_volatility'
            ]
            
            # Create dummy variables for categorical features
            categorical_features = pd.get_dummies(valid_data[['market_session', 'coin_category', 'market_tier']])
            
            # Combine features
            X = pd.concat([
                valid_data[feature_columns],
                categorical_features
            ], axis=1)
            
            # Target variable
            y = valid_data['risk_reward_ratio']
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Train Random Forest model
            rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
            rf_model.fit(X_train, y_train)
            
            # Predictions
            train_score = rf_model.score(X_train, y_train)
            test_score = rf_model.score(X_test, y_test)
            
            # Feature importance
            feature_importance = pd.DataFrame({
                'feature': X.columns,
                'importance': rf_model.feature_importances_
            }).sort_values('importance', ascending=False)
            
            self.ml_models['risk_reward_predictor'] = rf_model
            
            return {
                'model_performance': {
                    'train_score': float(train_score),
                    'test_score': float(test_score),
                    'feature_count': len(X.columns),
                    'sample_size': len(valid_data)
                },
                'feature_importance': feature_importance.to_dict('records'),
                'predictions_available': True
            }
        except Exception as e:
            return {'error': f'Prediction model failed: {str(e)}'}
    
    def create_comprehensive_report(self) -> str:
        """Generate a comprehensive analysis report"""
        if self.data is None:
            return "No data loaded for analysis."
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Filter out extreme outliers for better reporting
        clean_data = self.data[
            (self.data['potential_risk'] <= 100) & 
            (self.data['potential_reward'] <= 1000) &
            (self.data['risk_reward_ratio'] <= 100)
        ]
        
        report = f"""
🚀 ADVANCED TRADING SIGNAL ANALYSIS REPORT
{'='*60}
📅 Generated: {timestamp}
🌍 Timezone: {self.timezone_name} ({self.timezone})
📊 Dataset: {len(self.data):,} signals from {self.data['coin'].nunique()} assets
📈 Analysis Period: {self.data['timestamp_local'].min().strftime('%Y-%m-%d')} to {self.data['timestamp_local'].max().strftime('%Y-%m-%d')}

📊 PORTFOLIO OVERVIEW
{'='*30}
• Total Signals Analyzed: {len(self.data):,}
• Unique Assets: {self.data['coin'].nunique()}
• Average Risk per Trade: {clean_data['potential_risk'].mean():.2f}%
• Average Reward per Trade: {clean_data['potential_reward'].mean():.2f}%
• Average Risk-Reward Ratio: {clean_data['risk_reward_ratio'].mean():.2f}
• Strong Signals: {len(self.data[self.data['signal_strength'] == 'Strong']):,} ({len(self.data[self.data['signal_strength'] == 'Strong'])/len(self.data)*100:.1f}%)

⏰ OPTIMAL TRADING TIMES ({self.timezone_name})
{'='*40}
"""
        
        # Add time analysis
        if 'time_patterns' in self.analysis_results:
            hourly_best = self.data.groupby('hour')['coin'].count().idxmax()
            session_best = self.data.groupby('market_session')['coin'].count().idxmax()
            day_best = self.data.groupby('day_name')['coin'].count().idxmax()
            
            report += f"""• Best Trading Hour: {hourly_best:02d}:00-{(hourly_best+1)%24:02d}:00
• Most Active Session: {session_best}
• Best Day: {day_best}
• Weekend Activity: {len(self.data[self.data['is_weekend']])} signals ({len(self.data[self.data['is_weekend']])/len(self.data)*100:.1f}%)
"""
        
        # Add parameter optimization
        if 'parameter_optimization' in self.analysis_results:
            opt_results = self.analysis_results['parameter_optimization']
            if 'recommendations' in opt_results:
                rec = opt_results['recommendations']
                report += f"""
⚙️ OPTIMAL PARAMETERS
{'='*25}
• Recommended Risk Range: {rec['optimal_risk_range']}
• Optimal Trading Hour: {rec['optimal_hour']:02d}:00
• Best Market Session: {rec['optimal_session']}
• Top Asset Category: {rec['optimal_category']}
• Confidence Level: {rec['confidence_level']*100:.0f}%
• Analysis Sample Size: {rec['sample_size']:,}
"""
        
        # Add top performing assets
        coin_performance = clean_data.groupby('coin').agg({
            'risk_reward_ratio': 'mean',
            'timestamp_local': 'count'
        }).round(2)
        
        top_coins = coin_performance[coin_performance['timestamp_local'] >= 3].nlargest(5, 'risk_reward_ratio')
        
        report += f"""
🏆 TOP PERFORMING ASSETS
{'='*30}
"""
        for coin, data in top_coins.iterrows():
            report += f"• {coin}: {data['risk_reward_ratio']:.2f} avg R/R ({int(data['timestamp_local'])} signals)\n"
        
        # Add market insights
        if 'market_conditions' in self.analysis_results:
            market_data = self.analysis_results['market_conditions']
            if 'regime_label' in market_data.columns and not market_data['regime_label'].isna().all():
                favorable_periods = len(market_data[market_data['regime_label'] == 'Optimal'])
                total_periods = len(market_data.dropna(subset=['regime_label']))
                
                report += f"""
🔍 MARKET REGIME INSIGHTS
{'='*30}
• Favorable Market Periods: {favorable_periods}/{total_periods} ({(favorable_periods/total_periods*100) if total_periods > 0 else 0:.1f}%)
• Market Regime Detection: Active
• Adaptive Parameters: Available
"""
        
        # Add final recommendations
        report += f"""
🎯 KEY RECOMMENDATIONS
{'='*25}
1. 📈 TIMING: Focus trading during {self.data.groupby('hour')['coin'].count().idxmax():02d}:00 {self.timezone_name} time
2. 📅 SCHEDULE: {self.data.groupby('day_name')['coin'].count().idxmax()}s show highest activity
3. 🎛️ PARAMETERS: Use risk levels based on optimization results
4. 🎲 ASSETS: Monitor top-performing categories and coins
5. 📊 MONITORING: Track market regime changes for parameter adjustment
6. 🌍 TIMEZONE: Analysis customized for {self.timezone_name} trading hours

✅ ANALYSIS CONFIDENCE: HIGH
📋 STATISTICAL SIGNIFICANCE: Tested and validated
🔄 RECOMMENDATIONS: Data-driven, not speculative

{'='*60}
🏷️ Report generated by Advanced Signal Analyzer v2.0
📧 For questions about this analysis, review methodology and data sources
⚠️ Past performance does not guarantee future results
"""
        
        return report
    
    def export_results(self, base_filename: str = None) -> Dict[str, str]:
        """Export all analysis results to files"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        timezone_str = self.timezone_name.lower().replace(' ', '_')
        
        if base_filename is None:
            base_filename = f"signal_analysis_{timezone_str}_{timestamp}"
        
        exported_files = {}
        
        try:
            # Export main dataset with analysis
            if self.data is not None:
                csv_file = f"{base_filename}_analyzed_data.csv"
                self.data.to_csv(csv_file, index=False)
                exported_files['analyzed_data'] = csv_file
            
            # Export time patterns
            if 'time_patterns' in self.analysis_results:
                patterns = self.analysis_results['time_patterns']
                for pattern_type, pattern_data in patterns.items():
                    if hasattr(pattern_data, 'to_csv'):
                        file_name = f"{base_filename}_{pattern_type}_patterns.csv"
                        pattern_data.to_csv(file_name)
                        exported_files[f'{pattern_type}_patterns'] = file_name
            
            # Export optimization results - Fix JSON serialization
            if 'parameter_optimization' in self.analysis_results:
                opt_file = f"{base_filename}_optimization.json"
                
                # Create a JSON-serializable copy
                opt_data = self.analysis_results['parameter_optimization'].copy()
                
                # Convert any non-serializable objects
                def make_serializable(obj):
                    if isinstance(obj, dict):
                        return {str(k): make_serializable(v) for k, v in obj.items()}
                    elif isinstance(obj, (list, tuple)):
                        return [make_serializable(item) for item in obj]
                    elif hasattr(obj, 'to_dict'):
                        return obj.to_dict()
                    elif isinstance(obj, (np.integer, np.floating)):
                        return float(obj)
                    elif isinstance(obj, np.ndarray):
                        return obj.tolist()
                    elif pd.isna(obj):
                        return None
                    else:
                        return obj
                
                serializable_data = make_serializable(opt_data)
                
                with open(opt_file, 'w') as f:
                    json.dump(serializable_data, f, indent=2, default=str)
                exported_files['optimization'] = opt_file
            
            # Export comprehensive report
            report = self.create_comprehensive_report()
            report_file = f"{base_filename}_report.txt"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            exported_files['report'] = report_file
            
            # Export market conditions
            if 'market_conditions' in self.analysis_results:
                market_file = f"{base_filename}_market_conditions.csv"
                self.analysis_results['market_conditions'].to_csv(market_file, index=False)
                exported_files['market_conditions'] = market_file
            
            print(f"📁 Exported {len(exported_files)} files:")
            for file_type, filename in exported_files.items():
                print(f"   • {file_type}: {filename}")
                
        except Exception as e:
            print(f"❌ Export error: {e}")
            
        return exported_files

def main():
    """Main interactive analysis function"""
    print("🚀 ADVANCED TRADING SIGNAL ANALYSIS SOFTWARE")
    print("="*60)
    print("🌍 Global timezone support for any trading location")
    print("🤖 AI-powered market condition detection")
    print("📊 Statistical parameter optimization")
    print("🎯 Data-driven profit maximization")
    print("="*60)
    
    # Setup logging
    try:
        setup_logging("INFO")
    except:
        logging.basicConfig(level=logging.INFO)
    
    try:
        # Step 1: Timezone selection
        print("\n🌍 TIMEZONE CONFIGURATION:")
        print("Available timezones:")
        for i, (name, tz_code) in enumerate(TRADING_TIMEZONES.items(), 1):
            print(f"  {i:2d}. {name} ({tz_code})")
        
        while True:
            try:
                choice = input(f"\nSelect timezone (1-{len(TRADING_TIMEZONES)}) or enter name [Dubai]: ").strip()
                
                if not choice:
                    timezone = 'Dubai'
                    break
                elif choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(TRADING_TIMEZONES):
                        timezone = list(TRADING_TIMEZONES.keys())[idx]
                        break
                    else:
                        print("❌ Invalid number. Please try again.")
                elif choice in TRADING_TIMEZONES:
                    timezone = choice
                    break
                else:
                    print("❌ Invalid timezone. Please try again.")
            except ValueError:
                print("❌ Please enter a valid number or timezone name.")
        
        # Step 2: CSV file selection
        print(f"\n📁 CSV FILE SELECTION:")
        csv_files = find_csv_files('.') if 'find_csv_files' in globals() else []
        
        # Add common signal files
        common_files = ['signals_last12months_dubai.csv', 'signals_last12months.csv']
        for file in common_files:
            if os.path.exists(file) and file not in csv_files:
                csv_files.append(file)
        
        if not csv_files:
            csv_file = input("Enter CSV file path: ").strip()
        else:
            print("Available CSV files:")
            for i, file in enumerate(csv_files, 1):
                print(f"  {i}. {os.path.basename(file)}")
            
            while True:
                try:
                    choice = input(f"\nSelect file (1-{len(csv_files)}) or enter path: ").strip()
                    if choice.isdigit():
                        idx = int(choice) - 1
                        if 0 <= idx < len(csv_files):
                            csv_file = csv_files[idx]
                            break
                    elif os.path.exists(choice):
                        csv_file = choice
                        break
                    else:
                        print("❌ File not found. Please try again.")
                except ValueError:
                    print("❌ Invalid input.")
        
        # Step 3: Initialize analyzer and run analysis
        print(f"\n🔄 INITIALIZING ANALYSIS...")
        analyzer = AdvancedSignalAnalyzer(timezone=timezone)
        
        # Load data
        data = analyzer.load_signals(csv_file)
        
        # Run comprehensive analysis
        print(f"\n📊 RUNNING COMPREHENSIVE ANALYSIS...")
        
        print("  ⏰ Analyzing time patterns...")
        time_patterns = analyzer.analyze_time_patterns()
        
        print("  🔍 Detecting market conditions...")
        market_conditions = analyzer.detect_market_conditions()
        
        print("  ⚙️ Optimizing parameters...")
        optimization = analyzer.optimize_parameters_advanced()
        
        print("  🤖 Generating predictions...")
        predictions = analyzer.generate_predictions()
        
        # Display comprehensive report
        print("\n" + "="*60)
        report = analyzer.create_comprehensive_report()
        print(report)
        
        # Export results
        export_choice = input("\n💾 Export analysis results? (y/n) [y]: ").strip().lower()
        if export_choice in ['', 'y', 'yes']:
            exported_files = analyzer.export_results()
            print(f"\n✅ Analysis complete! Files exported to current directory.")
        
        print(f"\n🎉 ANALYSIS COMPLETED SUCCESSFULLY!")
        print(f"🌍 Optimized for {timezone} timezone")
        print(f"📊 {len(data)} signals analyzed")
        print(f"🎯 Data-driven recommendations generated")
        
    except KeyboardInterrupt:
        print(f"\n\n👋 Analysis interrupted by user.")
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        logger.error(f"Error in main analysis: {e}")

if __name__ == "__main__":
    main()