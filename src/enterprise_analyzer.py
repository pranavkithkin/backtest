"""
Enterprise Trading Signal Analyzer
=================================

Main enterprise-level analyzer with configuration management, professional logging,
and structured output following enterprise architecture patterns.
"""

import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np
import pytz

# Enterprise imports
from src.utils.config_manager import ConfigManager
from src.utils.logger import setup_enterprise_logging, audit_logger, performance_logger, log_timing
from src.data.processor import DataProcessor
from src.analysis.engine import AnalysisEngine
from src.reports.generator import ReportGenerator
from src.export.manager import ExportManager

class EnterpriseSignalAnalyzer:
    """
    Enterprise-grade signal analyzer with professional architecture:
    - Configuration-driven operation
    - Comprehensive logging and audit trails  
    - Modular component design
    - Performance monitoring
    - Scalable data processing
    """
    
    def __init__(self, config_path: Optional[str] = None, user: str = "system"):
        """Initialize enterprise analyzer with configuration and logging"""
        
        # Initialize configuration
        self.config = ConfigManager(config_path)
        if not self.config.validate_config():
            raise ValueError("Invalid configuration detected")
        
        # Setup enterprise logging
        self.loggers = setup_enterprise_logging(self.config.get('logging', {}))
        self.logger = self.loggers['analyzer']
        
        # User context for audit trails
        self.user = user
        
        # Initialize components
        self.data_processor = DataProcessor(self.config, self.loggers['data_processor'])
        self.analysis_engine = AnalysisEngine(self.config, self.loggers['ml_engine'])
        self.report_generator = ReportGenerator(self.config, self.loggers['analyzer'])
        self.export_manager = ExportManager(self.config, self.loggers['exporter'])
        
        # Analysis state
        self.current_analysis = None
        self.analysis_metadata = {}
        
        self.logger.info(f"Enterprise Signal Analyzer initialized for user: {user}")
        audit_logger.log_analysis_start(self.user, "initialization", "system")
    
    @log_timing
    def load_signals(self, csv_file: str, timezone: str = None) -> pd.DataFrame:
        """Load and process signals with enterprise data validation"""
        
        start_time = time.time()
        timezone = timezone or self.config.get('timezones.default', 'Dubai')
        
        self.logger.info(f"Loading signals from {csv_file} for timezone {timezone}")
        audit_logger.log_analysis_start(self.user, timezone, csv_file)
        
        try:
            # Validate file exists and is accessible
            if not Path(csv_file).exists():
                raise FileNotFoundError(f"Signal file not found: {csv_file}")
            
            # Process data through enterprise processor
            processed_data = self.data_processor.load_and_process(csv_file, timezone)
            
            # Store analysis metadata
            self.analysis_metadata = {
                'data_file': csv_file,
                'timezone': timezone,
                'load_time': datetime.now(),
                'signal_count': len(processed_data),
                'unique_assets': processed_data['coin'].nunique(),
                'date_range': {
                    'start': processed_data['timestamp_local'].min(),
                    'end': processed_data['timestamp_local'].max()
                }
            }
            
            self.current_analysis = processed_data
            
            duration = time.time() - start_time
            performance_logger.log_data_stats(
                "signal_loading", 
                len(processed_data), 
                len(processed_data) / duration
            )
            
            self.logger.info(f"Successfully loaded {len(processed_data)} signals in {duration:.2f}s")
            return processed_data
            
        except Exception as e:
            self.logger.error(f"Failed to load signals: {e}")
            raise
    
    @log_timing
    def run_comprehensive_analysis(self, 
                                 timezone: str = None,
                                 confidence_level: float = 0.95,
                                 enable_ml: bool = True) -> Dict[str, Any]:
        """Run comprehensive enterprise analysis with all modules"""
        
        if self.current_analysis is None:
            raise ValueError("No data loaded. Call load_signals() first.")
        
        timezone = timezone or self.analysis_metadata.get('timezone', 'Dubai')
        start_time = time.time()
        
        self.logger.info("Starting comprehensive enterprise analysis")
        
        try:
            results = {}
            
            # Time Pattern Analysis
            self.logger.info("Running time pattern analysis...")
            results['time_patterns'] = self.analysis_engine.analyze_time_patterns(
                self.current_analysis, timezone
            )
            
            # Market Condition Detection
            self.logger.info("Detecting market conditions...")
            results['market_conditions'] = self.analysis_engine.detect_market_conditions(
                self.current_analysis
            )
            
            # Parameter Optimization
            self.logger.info("Optimizing trading parameters...")
            results['parameter_optimization'] = self.analysis_engine.optimize_parameters(
                self.current_analysis, confidence_level
            )
            
            # Risk Analysis
            self.logger.info("Performing risk analysis...")
            results['risk_analysis'] = self.analysis_engine.analyze_risk_distribution(
                self.current_analysis
            )
            
            # Asset Performance Analysis
            self.logger.info("Analyzing asset performance...")
            results['asset_performance'] = self.analysis_engine.analyze_asset_performance(
                self.current_analysis
            )
            
            # Machine Learning Predictions (if enabled)
            if enable_ml:
                self.logger.info("Generating ML predictions...")
                results['ml_predictions'] = self.analysis_engine.generate_predictions(
                    self.current_analysis
                )
            
            # Statistical Validation
            self.logger.info("Performing statistical validation...")
            results['statistical_validation'] = self.analysis_engine.validate_results(
                results, confidence_level
            )
            
            # Add metadata
            results['metadata'] = {
                **self.analysis_metadata,
                'analysis_time': datetime.now(),
                'analysis_duration': time.time() - start_time,
                'confidence_level': confidence_level,
                'ml_enabled': enable_ml,
                'user': self.user
            }
            
            duration = time.time() - start_time
            audit_logger.log_analysis_complete(
                self.user, 
                duration, 
                self.analysis_metadata['signal_count']
            )
            
            self.logger.info(f"Comprehensive analysis completed in {duration:.2f}s")
            return results
            
        except Exception as e:
            self.logger.error(f"Analysis failed: {e}")
            raise
    
    @log_timing
    def generate_enterprise_report(self, 
                                 analysis_results: Dict[str, Any],
                                 format_type: str = 'comprehensive') -> str:
        """Generate enterprise-grade report with professional formatting"""
        
        self.logger.info(f"Generating {format_type} enterprise report")
        
        try:
            report = self.report_generator.generate_comprehensive_report(
                analysis_results, 
                format_type
            )
            
            self.logger.info("Enterprise report generated successfully")
            return report
            
        except Exception as e:
            self.logger.error(f"Report generation failed: {e}")
            raise
    
    @log_timing
    def export_results(self, 
                      analysis_results: Dict[str, Any],
                      export_formats: List[str] = None,
                      output_dir: str = None) -> Dict[str, str]:
        """Export analysis results in multiple enterprise formats"""
        
        export_formats = export_formats or ['csv', 'json', 'html']
        output_dir = output_dir or self.config.get('export.output_dir', 'output')
        
        self.logger.info(f"Exporting results in formats: {export_formats}")
        
        try:
            exported_files = self.export_manager.export_analysis_results(
                analysis_results,
                export_formats,
                output_dir,
                self.user
            )
            
            # Log exports for audit
            for format_type, file_path in exported_files.items():
                audit_logger.log_export(self.user, format_type, file_path)
            
            self.logger.info(f"Successfully exported {len(exported_files)} files")
            return exported_files
            
        except Exception as e:
            self.logger.error(f"Export failed: {e}")
            raise
    
    def get_supported_timezones(self) -> Dict[str, str]:
        """Get all supported timezones with descriptions"""
        timezones = self.config.get_timezones()
        return {tz.name: f"{tz.description} ({tz.code})" for tz in timezones.values()}
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """Get current analysis summary and metadata"""
        if not self.analysis_metadata:
            return {"status": "No analysis loaded"}
        
        return {
            "status": "Analysis loaded",
            "metadata": self.analysis_metadata,
            "config_version": self.config.get('app.version'),
            "user": self.user
        }
    
    def validate_data_quality(self, min_signals: int = 10) -> Dict[str, Any]:
        """Validate data quality for reliable analysis"""
        if self.current_analysis is None:
            return {"valid": False, "reason": "No data loaded"}
        
        data = self.current_analysis
        validation_results = {
            "valid": True,
            "warnings": [],
            "statistics": {}
        }
        
        # Check minimum signal count
        if len(data) < min_signals:
            validation_results["valid"] = False
            validation_results["warnings"].append(f"Insufficient signals: {len(data)} < {min_signals}")
        
        # Check data completeness
        required_columns = ['coin', 'entry', 'sl', 'tp', 'timestamp_local']
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            validation_results["warnings"].append(f"Missing columns: {missing_columns}")
        
        # Check for extreme outliers
        if 'risk_reward_ratio' in data.columns:
            extreme_rr = data[data['risk_reward_ratio'] > 100]
            if len(extreme_rr) > 0:
                validation_results["warnings"].append(f"Extreme R/R ratios detected: {len(extreme_rr)} signals")
        
        # Calculate statistics
        validation_results["statistics"] = {
            "total_signals": len(data),
            "unique_assets": data['coin'].nunique(),
            "date_span_days": (data['timestamp_local'].max() - data['timestamp_local'].min()).days,
            "completeness_pct": (1 - data.isnull().sum().sum() / (len(data) * len(data.columns))) * 100
        }
        
        return validation_results
    
    def __str__(self) -> str:
        return f"EnterpriseSignalAnalyzer(user={self.user}, config={self.config.get('app.name')})"
    
    def __repr__(self) -> str:
        return self.__str__()