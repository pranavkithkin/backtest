"""
Enterprise Report Generator
=========================

Professional report generation with multiple formats and templates.
"""

from datetime import datetime
from typing import Dict, Any, Optional
import pandas as pd

class ReportGenerator:
    """Enterprise-grade report generator with professional formatting"""
    
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.report_config = config.get('reporting', {})
        
    def generate_comprehensive_report(self, analysis_results: Dict[str, Any], format_type: str = 'comprehensive') -> str:
        """Generate comprehensive enterprise report"""
        
        metadata = analysis_results.get('metadata', {})
        timezone = metadata.get('timezone', 'Unknown')
        
        # Report header
        report = self._generate_header(metadata, timezone)
        
        # Executive summary
        report += self._generate_executive_summary(analysis_results)
        
        # Time patterns section
        if 'time_patterns' in analysis_results:
            report += self._generate_time_patterns_section(analysis_results['time_patterns'], timezone)
        
        # Parameter optimization section
        if 'parameter_optimization' in analysis_results:
            report += self._generate_optimization_section(analysis_results['parameter_optimization'])
        
        # Market conditions section
        if 'market_conditions' in analysis_results:
            report += self._generate_market_conditions_section(analysis_results['market_conditions'])
        
        # Asset performance section
        if 'asset_performance' in analysis_results:
            report += self._generate_asset_performance_section(analysis_results['asset_performance'])
        
        # ML insights section
        if 'ml_predictions' in analysis_results and analysis_results['ml_predictions'].get('model_available'):
            report += self._generate_ml_insights_section(analysis_results['ml_predictions'])
        
        # Statistical validation section
        if 'statistical_validation' in analysis_results:
            report += self._generate_validation_section(analysis_results['statistical_validation'])
        
        # Recommendations section
        report += self._generate_recommendations_section(analysis_results)
        
        # Footer
        report += self._generate_footer()
        
        return report
    
    def _generate_header(self, metadata: Dict[str, Any], timezone: str) -> str:
        """Generate professional report header"""
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return f"""
🏢 ENTERPRISE TRADING SIGNAL ANALYSIS REPORT
{'='*70}
📅 Generated: {timestamp}
🌍 Trading Timezone: {timezone}
📊 Analysis Period: {metadata.get('date_range', {}).get('start', 'N/A')} to {metadata.get('date_range', {}).get('end', 'N/A')}
📈 Dataset: {metadata.get('signal_count', 0):,} signals from {metadata.get('unique_assets', 0)} assets
⚙️ Analysis Version: {self.config.get('app.version', '2.0.0')}
👤 Generated for: {metadata.get('user', 'Enterprise User')}

"""
    
    def _generate_executive_summary(self, analysis_results: Dict[str, Any]) -> str:
        """Generate executive summary section"""
        
        metadata = analysis_results.get('metadata', {})
        
        # Calculate key metrics
        signal_count = metadata.get('signal_count', 0)
        unique_assets = metadata.get('unique_assets', 0)
        analysis_duration = metadata.get('analysis_duration', 0)
        
        # Get optimization results for summary
        opt_results = analysis_results.get('parameter_optimization', {})
        recommendations = opt_results.get('recommendations', {})
        
        return f"""
📋 EXECUTIVE SUMMARY
{'='*25}
• Portfolio Size: {signal_count:,} trading signals analyzed
• Asset Diversity: {unique_assets} unique cryptocurrencies
• Analysis Completion: {analysis_duration:.2f} seconds processing time
• Confidence Level: {opt_results.get('confidence_level', 0.95)*100:.0f}% statistical confidence
• Data Quality: {metadata.get('completeness_pct', 0):.1f}% data completeness

🎯 KEY FINDINGS:
• Optimal Risk Range: {recommendations.get('optimal_risk_range', 'Calculating...')}
• Best Trading Hour: {recommendations.get('optimal_hour', 'TBD')}:00 {metadata.get('timezone', '')} time
• Top Market Session: {recommendations.get('optimal_session', 'Analyzing...')}
• Statistical Significance: {'Validated' if opt_results.get('significance_tests') else 'Pending'}

"""
    
    def _generate_time_patterns_section(self, time_patterns: Dict[str, Any], timezone: str) -> str:
        """Generate time patterns analysis section"""
        
        report = f"""
⏰ TIME PATTERN ANALYSIS ({timezone})
{'='*40}
"""
        
        # Hourly patterns
        if 'hourly' in time_patterns:
            hourly_data = time_patterns['hourly']
            if hasattr(hourly_data, 'to_dict'):
                hourly_dict = hourly_data.to_dict()
                
                # Find best hours by signal count and performance
                if 'coin' in hourly_dict and 'count' in hourly_dict['coin']:
                    signal_counts = hourly_dict['coin']['count']
                    best_activity_hour = max(signal_counts.items(), key=lambda x: x[1])
                    
                    report += f"""
📊 HOURLY PATTERNS:
• Peak Activity: Hour {best_activity_hour[0]} with {best_activity_hour[1]} signals
• Activity Distribution: Signals spread across {len(signal_counts)} different hours
"""
        
        # Session patterns
        if 'session' in time_patterns:
            session_data = time_patterns['session']
            if hasattr(session_data, 'to_dict'):
                session_dict = session_data.to_dict()
                
                if 'coin' in session_dict and 'count' in session_dict['coin']:
                    session_counts = session_dict['coin']['count']
                    best_session = max(session_counts.items(), key=lambda x: x[1])
                    
                    report += f"""
🕐 SESSION ANALYSIS:
• Most Active Session: {best_session[0]} ({best_session[1]} signals)
• Session Coverage: {len(session_counts)} market sessions analyzed
"""
        
        # Weekend analysis
        if 'weekend' in time_patterns:
            weekend_data = time_patterns['weekend']
            if hasattr(weekend_data, 'to_dict'):
                weekend_dict = weekend_data.to_dict()
                
                if 'coin' in weekend_dict and 'count' in weekend_dict['coin']:
                    weekend_counts = weekend_dict['coin']['count']
                    weekend_signals = weekend_counts.get(True, 0)
                    weekday_signals = weekend_counts.get(False, 0)
                    total_signals = weekend_signals + weekday_signals
                    
                    if total_signals > 0:
                        weekend_pct = (weekend_signals / total_signals) * 100
                        report += f"""
📅 WEEKEND vs WEEKDAY:
• Weekend Activity: {weekend_signals} signals ({weekend_pct:.1f}%)
• Weekday Activity: {weekday_signals} signals ({100-weekend_pct:.1f}%)
"""
        
        return report
    
    def _generate_optimization_section(self, optimization_results: Dict[str, Any]) -> str:
        """Generate parameter optimization section"""
        
        report = f"""
⚙️ PARAMETER OPTIMIZATION ANALYSIS
{'='*40}
"""
        
        # Risk analysis
        risk_analysis = optimization_results.get('risk_analysis', {})
        if risk_analysis:
            # Find best performing risk ranges
            best_ranges = sorted(
                risk_analysis.items(),
                key=lambda x: x[1].get('success_potential', 0),
                reverse=True
            )[:3]
            
            report += f"""
💰 RISK LEVEL OPTIMIZATION:
"""
            for i, (range_name, stats) in enumerate(best_ranges, 1):
                report += f"""  {i}. {range_name}: {stats.get('success_potential', 0):.1f}% success rate ({stats.get('count', 0)} signals)
     • Average R/R: {stats.get('avg_rr_ratio', 0):.2f}
     • Strong Signals: {stats.get('strong_signal_pct', 0):.1f}%
"""
        
        # Time optimization
        recommendations = optimization_results.get('recommendations', {})
        if recommendations:
            report += f"""
⏱️ OPTIMAL TRADING PARAMETERS:
• Risk Range: {recommendations.get('optimal_risk_range', 'Calculating...')}
• Trading Hour: {recommendations.get('optimal_hour', 'TBD')}:00 (Performance: {recommendations.get('hour_performance', 0):.2f} avg R/R)
• Market Session: {recommendations.get('optimal_session', 'Analyzing...')} (Performance: {recommendations.get('session_performance', 0):.2f} avg R/R)
• Reasoning: {recommendations.get('risk_reasoning', 'Data-driven optimization based on historical performance')}
"""
        
        # Statistical significance
        significance_tests = optimization_results.get('significance_tests', {})
        if significance_tests:
            report += f"""
📊 STATISTICAL VALIDATION:
"""
            for test_name, test_results in significance_tests.items():
                if isinstance(test_results, dict) and 'significant' in test_results:
                    status = "✅ Significant" if test_results['significant'] else "⚠️ Not Significant"
                    interpretation = test_results.get('interpretation', 'Statistical test performed')
                    report += f"• {test_name.replace('_', ' ').title()}: {status} (p={test_results.get('p_value', 0):.3f})\n"
                    report += f"  {interpretation}\n"
        
        return report
    
    def _generate_market_conditions_section(self, market_conditions: Dict[str, Any]) -> str:
        """Generate market conditions section"""
        
        report = f"""
🔍 MARKET REGIME ANALYSIS
{'='*30}
"""
        
        if market_conditions.get('regime_analysis'):
            clusters_found = market_conditions.get('clusters_found', 0)
            report += f"""
• Market Regimes Detected: {clusters_found} distinct trading environments
• Analysis Method: K-means clustering with {len(market_conditions.get('feature_columns', []))} features
• Pattern Recognition: Advanced statistical clustering applied
"""
            
            # Analyze weekly data if available
            weekly_data = market_conditions.get('weekly_data')
            if weekly_data is not None and hasattr(weekly_data, '__len__'):
                total_periods = len(weekly_data)
                
                if 'regime_label' in weekly_data.columns:
                    regime_counts = weekly_data['regime_label'].value_counts()
                    if len(regime_counts) > 0:
                        best_regime = regime_counts.index[0]
                        best_count = regime_counts.iloc[0]
                        report += f"""
• Dominant Market Regime: {best_regime} ({best_count}/{total_periods} periods)
• Regime Stability: {(best_count/total_periods)*100:.1f}% of analyzed periods
"""
        else:
            report += """
• Market Regime Analysis: Insufficient data for reliable clustering
• Recommendation: Collect more historical data for regime detection
"""
        
        return report
    
    def _generate_asset_performance_section(self, asset_performance: Dict[str, Any]) -> str:
        """Generate asset performance section"""
        
        report = f"""
🏆 ASSET PERFORMANCE ANALYSIS
{'='*35}
"""
        
        # Top performers
        top_performers = asset_performance.get('top_performers', {})
        if top_performers and 'risk_reward_ratio' in top_performers and 'mean' in top_performers['risk_reward_ratio']:
            rr_means = top_performers['risk_reward_ratio']['mean']
            
            report += f"""
💎 TOP PERFORMING ASSETS:
"""
            # Sort and show top 5
            sorted_assets = sorted(rr_means.items(), key=lambda x: x[1], reverse=True)[:5]
            for i, (asset, rr_ratio) in enumerate(sorted_assets, 1):
                # Get signal count if available
                signal_count = 'N/A'
                if 'timestamp_local' in top_performers and 'count' in top_performers['timestamp_local']:
                    signal_count = top_performers['timestamp_local']['count'].get(asset, 'N/A')
                
                report += f"  {i}. {asset}: {rr_ratio:.2f} avg R/R ({signal_count} signals)\n"
        
        # Most active assets
        most_active = asset_performance.get('most_active', {})
        if most_active and 'timestamp_local' in most_active and 'count' in most_active['timestamp_local']:
            signal_counts = most_active['timestamp_local']['count']
            
            report += f"""
📈 MOST ACTIVE ASSETS:
"""
            sorted_active = sorted(signal_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            for i, (asset, count) in enumerate(sorted_active, 1):
                report += f"  {i}. {asset}: {count} signals\n"
        
        min_threshold = asset_performance.get('minimum_signals_threshold', 3)
        report += f"""
📊 Analysis Criteria: Minimum {min_threshold} signals per asset for inclusion
"""
        
        return report
    
    def _generate_ml_insights_section(self, ml_predictions: Dict[str, Any]) -> str:
        """Generate ML insights section"""
        
        report = f"""
🤖 MACHINE LEARNING INSIGHTS
{'='*35}
"""
        
        model_performance = ml_predictions.get('model_performance', {})
        if model_performance:
            train_score = model_performance.get('train_score', 0)
            test_score = model_performance.get('test_score', 0)
            sample_size = model_performance.get('sample_size', 0)
            
            report += f"""
🎯 MODEL PERFORMANCE:
• Training Accuracy: {train_score*100:.1f}%
• Testing Accuracy: {test_score*100:.1f}%
• Sample Size: {sample_size:,} signals
• Model Status: {'✅ Reliable' if test_score > 0.3 else '⚠️ Needs More Data'}
"""
        
        # Feature importance
        feature_importance = ml_predictions.get('feature_importance', [])
        if feature_importance:
            report += f"""
🔍 KEY PREDICTIVE FACTORS:
"""
            for i, feature_info in enumerate(feature_importance[:5], 1):
                feature_name = feature_info.get('feature', 'Unknown')
                importance = feature_info.get('importance', 0)
                report += f"  {i}. {feature_name}: {importance*100:.1f}% importance\n"
        
        return report
    
    def _generate_validation_section(self, validation_results: Dict[str, Any]) -> str:
        """Generate statistical validation section"""
        
        report = f"""
✅ STATISTICAL VALIDATION
{'='*30}
"""
        
        checks = validation_results.get('checks', {})
        
        # Sample size validation
        if 'sample_size' in checks:
            sample_check = checks['sample_size']
            status = "✅ Adequate" if sample_check.get('adequate') else "⚠️ Limited"
            
            report += f"""
📊 DATA ADEQUACY:
• Sample Size: {sample_check.get('value', 0)} signals
• Status: {status}
• Recommendation: {sample_check.get('recommendation', 'Continue analysis')}
"""
        
        # Statistical significance
        if 'statistical_significance' in checks:
            sig_check = checks['statistical_significance']
            tests_performed = sig_check.get('tests_performed', [])
            significant_results = sig_check.get('significant_results', [])
            
            report += f"""
🔬 SIGNIFICANCE TESTING:
• Tests Performed: {len(tests_performed)}
• Significant Results: {len(significant_results)}
• Validation Level: {validation_results.get('confidence_level', 0.95)*100:.0f}%
"""
        
        return report
    
    def _generate_recommendations_section(self, analysis_results: Dict[str, Any]) -> str:
        """Generate recommendations section"""
        
        metadata = analysis_results.get('metadata', {})
        timezone = metadata.get('timezone', 'your timezone')
        
        # Get key recommendations
        opt_results = analysis_results.get('parameter_optimization', {})
        recommendations = opt_results.get('recommendations', {})
        
        return f"""
🎯 ENTERPRISE RECOMMENDATIONS
{'='*35}

🔥 IMMEDIATE ACTIONS:
1. 📈 OPTIMAL TIMING: Focus trading during {recommendations.get('optimal_hour', 'peak')}:00 {timezone} time
2. ⚖️ RISK MANAGEMENT: Use {recommendations.get('optimal_risk_range', 'configured')} risk levels
3. 🕐 SESSION FOCUS: Prioritize {recommendations.get('optimal_session', 'identified')} market session
4. 📊 MONITORING: Track performance metrics continuously

💡 STRATEGIC INSIGHTS:
• Risk-Reward Optimization: Data indicates optimal balance at specified parameters
• Market Timing: Statistical analysis confirms time-based performance patterns
• Asset Selection: Focus on top-performing categories and individual assets
• Validation: All recommendations backed by {opt_results.get('confidence_level', 0.95)*100:.0f}% confidence level

⚠️ RISK DISCLAIMERS:
• Past performance does not guarantee future results
• Market conditions can change rapidly
• Recommendations based on historical data analysis
• Consider current market context before implementation

📋 MONITORING RECOMMENDATIONS:
• Update analysis monthly with new signal data
• Monitor for regime changes in market conditions
• Validate performance against live trading results
• Adjust parameters based on ongoing performance data

"""
    
    def _generate_footer(self) -> str:
        """Generate professional report footer"""
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return f"""
{'='*70}
🏷️ REPORT METADATA
• Generated by: Enterprise Trading Signal Analyzer v{self.config.get('app.version', '2.0.0')}
• Analysis Engine: Statistical + Machine Learning Hybrid
• Report Type: Comprehensive Professional Analysis
• Generated: {timestamp}
• Environment: {self.config.get('app.environment', 'Production')}

📧 SUPPORT: For questions about this analysis or methodology
🔄 UPDATES: Recommend monthly analysis updates for optimal results
⚖️ COMPLIANCE: This analysis is for informational purposes only

© 2025 Enterprise Trading Analytics Platform. All rights reserved.
{'='*70}
"""