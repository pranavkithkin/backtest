"""
Enterprise Export Manager
=======================

Professional data export with multiple formats and structured output.
"""

import json
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd

class ExportManager:
    """Enterprise-grade export manager with multiple format support"""
    
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.export_config = config.get('export', {})
        
    def export_analysis_results(self, 
                               analysis_results: Dict[str, Any],
                               export_formats: List[str],
                               output_dir: str,
                               user: str) -> Dict[str, str]:
        """Export analysis results in multiple enterprise formats"""
        
        # Ensure output directory exists
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Generate timestamp for file naming
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        metadata = analysis_results.get('metadata', {})
        timezone = metadata.get('timezone', 'unknown').lower()
        
        # Use configured filename template
        template = self.export_config.get('filename_template', '{analysis_type}_{timezone}_{timestamp}')
        
        exported_files = {}
        
        try:
            # Export main analysis data as CSV
            if 'csv' in export_formats:
                csv_files = self._export_csv_files(analysis_results, output_path, template, timezone, timestamp)
                exported_files.update(csv_files)
            
            # Export optimization results as JSON
            if 'json' in export_formats:
                json_file = self._export_json_file(analysis_results, output_path, template, timezone, timestamp)
                exported_files['optimization_json'] = json_file
            
            # Export comprehensive report as text
            if 'txt' in export_formats:
                txt_file = self._export_text_report(analysis_results, output_path, template, timezone, timestamp)
                exported_files['comprehensive_report'] = txt_file
            
            # Export HTML dashboard (if configured)
            if 'html' in export_formats:
                html_file = self._export_html_dashboard(analysis_results, output_path, template, timezone, timestamp)
                exported_files['html_dashboard'] = html_file
            
            self.logger.info(f"Successfully exported {len(exported_files)} files for user {user}")
            return exported_files
            
        except Exception as e:
            self.logger.error(f"Export failed: {e}")
            raise
    
    def _export_csv_files(self, analysis_results: Dict[str, Any], output_path: Path, 
                         template: str, timezone: str, timestamp: str) -> Dict[str, str]:
        """Export analysis data as CSV files"""
        
        csv_files = {}
        
        # Time patterns data
        if 'time_patterns' in analysis_results:
            time_patterns = analysis_results['time_patterns']
            
            # Hourly patterns
            if 'hourly' in time_patterns:
                filename = template.format(
                    analysis_type='hourly_patterns',
                    timezone=timezone,
                    timestamp=timestamp
                ) + '.csv'
                file_path = output_path / filename
                
                hourly_data = time_patterns['hourly']
                if hasattr(hourly_data, 'to_csv'):
                    hourly_data.to_csv(file_path)
                    csv_files['hourly_patterns'] = str(file_path)
            
            # Daily patterns
            if 'daily' in time_patterns:
                filename = template.format(
                    analysis_type='daily_patterns',
                    timezone=timezone,
                    timestamp=timestamp
                ) + '.csv'
                file_path = output_path / filename
                
                daily_data = time_patterns['daily']
                if hasattr(daily_data, 'to_csv'):
                    daily_data.to_csv(file_path)
                    csv_files['daily_patterns'] = str(file_path)
            
            # Session patterns
            if 'session' in time_patterns:
                filename = template.format(
                    analysis_type='session_patterns',
                    timezone=timezone,
                    timestamp=timestamp
                ) + '.csv'
                file_path = output_path / filename
                
                session_data = time_patterns['session']
                if hasattr(session_data, 'to_csv'):
                    session_data.to_csv(file_path)
                    csv_files['session_patterns'] = str(file_path)
            
            # Weekend patterns
            if 'weekend' in time_patterns:
                filename = template.format(
                    analysis_type='weekend_patterns',
                    timezone=timezone,
                    timestamp=timestamp
                ) + '.csv'
                file_path = output_path / filename
                
                weekend_data = time_patterns['weekend']
                if hasattr(weekend_data, 'to_csv'):
                    weekend_data.to_csv(file_path)
                    csv_files['weekend_patterns'] = str(file_path)
            
            # Monthly patterns
            if 'monthly' in time_patterns:
                filename = template.format(
                    analysis_type='monthly_patterns',
                    timezone=timezone,
                    timestamp=timestamp
                ) + '.csv'
                file_path = output_path / filename
                
                monthly_data = time_patterns['monthly']
                if hasattr(monthly_data, 'to_csv'):
                    monthly_data.to_csv(file_path)
                    csv_files['monthly_patterns'] = str(file_path)
        
        # Market conditions data
        if 'market_conditions' in analysis_results:
            market_conditions = analysis_results['market_conditions']
            if 'weekly_data' in market_conditions:
                filename = template.format(
                    analysis_type='market_conditions',
                    timezone=timezone,
                    timestamp=timestamp
                ) + '.csv'
                file_path = output_path / filename
                
                weekly_data = market_conditions['weekly_data']
                if hasattr(weekly_data, 'to_csv'):
                    weekly_data.to_csv(file_path, index=False)
                    csv_files['market_conditions'] = str(file_path)
        
        return csv_files
    
    def _export_json_file(self, analysis_results: Dict[str, Any], output_path: Path,
                         template: str, timezone: str, timestamp: str) -> str:
        """Export optimization results as JSON"""
        
        filename = template.format(
            analysis_type='optimization',
            timezone=timezone,
            timestamp=timestamp
        ) + '.json'
        file_path = output_path / filename
        
        # Prepare JSON-serializable data
        export_data = {}
        
        # Parameter optimization
        if 'parameter_optimization' in analysis_results:
            export_data['parameter_optimization'] = self._make_json_serializable(
                analysis_results['parameter_optimization']
            )
        
        # Asset performance
        if 'asset_performance' in analysis_results:
            export_data['asset_performance'] = self._make_json_serializable(
                analysis_results['asset_performance']
            )
        
        # ML predictions
        if 'ml_predictions' in analysis_results:
            export_data['ml_predictions'] = self._make_json_serializable(
                analysis_results['ml_predictions']
            )
        
        # Metadata
        if 'metadata' in analysis_results:
            export_data['metadata'] = self._make_json_serializable(
                analysis_results['metadata']
            )
        
        # Export with proper formatting
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
        
        return str(file_path)
    
    def _export_text_report(self, analysis_results: Dict[str, Any], output_path: Path,
                           template: str, timezone: str, timestamp: str) -> str:
        """Export comprehensive text report"""
        
        filename = template.format(
            analysis_type='report',
            timezone=timezone,
            timestamp=timestamp
        ) + '.txt'
        file_path = output_path / filename
        
        # Generate report using report generator
        from src.reports.generator import ReportGenerator
        report_generator = ReportGenerator(self.config, self.logger)
        
        report_content = report_generator.generate_comprehensive_report(
            analysis_results, 'comprehensive'
        )
        
        # Write to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return str(file_path)
    
    def _export_html_dashboard(self, analysis_results: Dict[str, Any], output_path: Path,
                              template: str, timezone: str, timestamp: str) -> str:
        """Export HTML dashboard (simplified version)"""
        
        filename = template.format(
            analysis_type='dashboard',
            timezone=timezone,
            timestamp=timestamp
        ) + '.html'
        file_path = output_path / filename
        
        # Generate HTML content
        html_content = self._generate_html_dashboard(analysis_results)
        
        # Write to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(file_path)
    
    def _generate_html_dashboard(self, analysis_results: Dict[str, Any]) -> str:
        """Generate HTML dashboard content"""
        
        metadata = analysis_results.get('metadata', {})
        timezone = metadata.get('timezone', 'Unknown')
        
        # Get key metrics
        signal_count = metadata.get('signal_count', 0)
        unique_assets = metadata.get('unique_assets', 0)
        
        # Get recommendations
        opt_results = analysis_results.get('parameter_optimization', {})
        recommendations = opt_results.get('recommendations', {})
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enterprise Trading Signal Analysis Dashboard</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            padding: 30px;
        }}
        .header {{
            text-align: center;
            border-bottom: 2px solid #007bff;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background: linear-gradient(135deg, #007bff, #0056b3);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
        }}
        .metric-label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
        .section {{
            margin-bottom: 30px;
            padding: 20px;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
        }}
        .section-title {{
            font-size: 1.5em;
            color: #333;
            border-bottom: 2px solid #007bff;
            padding-bottom: 10px;
            margin-bottom: 15px;
        }}
        .recommendation {{
            background: #e8f4fd;
            border-left: 4px solid #007bff;
            padding: 15px;
            margin: 10px 0;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏢 Enterprise Trading Signal Analysis</h1>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Timezone: {timezone}</p>
        </div>
        
        <div class="metrics">
            <div class="metric-card">
                <div class="metric-value">{signal_count:,}</div>
                <div class="metric-label">Total Signals</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{unique_assets}</div>
                <div class="metric-label">Unique Assets</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{recommendations.get('optimal_hour', 'TBD')}</div>
                <div class="metric-label">Optimal Hour</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{opt_results.get('confidence_level', 0.95)*100:.0f}%</div>
                <div class="metric-label">Confidence Level</div>
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">🎯 Key Recommendations</div>
            <div class="recommendation">
                <strong>Optimal Risk Range:</strong> {recommendations.get('optimal_risk_range', 'Calculating...')}
            </div>
            <div class="recommendation">
                <strong>Best Trading Hour:</strong> {recommendations.get('optimal_hour', 'TBD')}:00 {timezone} time
            </div>
            <div class="recommendation">
                <strong>Top Market Session:</strong> {recommendations.get('optimal_session', 'Analyzing...')}
            </div>
        </div>
        
        <div class="footer">
            <p>© 2025 Enterprise Trading Analytics Platform | Generated by Signal Analyzer v{self.config.get('app.version', '2.0.0')}</p>
            <p><strong>Disclaimer:</strong> This analysis is for informational purposes only. Past performance does not guarantee future results.</p>
        </div>
    </div>
</body>
</html>
"""
        
        return html_content
    
    def _make_json_serializable(self, obj: Any) -> Any:
        """Convert objects to JSON-serializable format"""
        
        if isinstance(obj, dict):
            return {key: self._make_json_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_serializable(item) for item in obj]
        elif isinstance(obj, (pd.Timestamp, datetime)):
            return obj.isoformat()
        elif isinstance(obj, pd.DataFrame):
            return obj.to_dict('records')
        elif isinstance(obj, (pd.Series, pd.Index)):
            return obj.to_list()
        elif hasattr(obj, 'item'):  # numpy scalars
            return obj.item()
        elif pd.isna(obj):
            return None
        else:
            try:
                json.dumps(obj)  # Test if already serializable
                return obj
            except (TypeError, ValueError):
                return str(obj)
    
    def create_analysis_archive(self, exported_files: Dict[str, str], 
                               output_dir: str, archive_name: str = None) -> str:
        """Create compressed archive of all exported files"""
        
        import zipfile
        
        if not archive_name:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            archive_name = f"signal_analysis_archive_{timestamp}.zip"
        
        archive_path = Path(output_dir) / archive_name
        
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_type, file_path in exported_files.items():
                if Path(file_path).exists():
                    # Add file with descriptive name
                    arcname = f"{file_type}_{Path(file_path).name}"
                    zipf.write(file_path, arcname)
        
        self.logger.info(f"Created analysis archive: {archive_path}")
        return str(archive_path)
    
    def generate_export_manifest(self, exported_files: Dict[str, str], 
                                output_dir: str) -> str:
        """Generate manifest file listing all exports"""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        manifest_path = Path(output_dir) / f"export_manifest_{timestamp}.json"
        
        manifest_data = {
            'export_timestamp': datetime.now().isoformat(),
            'total_files': len(exported_files),
            'files': {}
        }
        
        for file_type, file_path in exported_files.items():
            file_info = {
                'path': file_path,
                'exists': Path(file_path).exists(),
                'size_bytes': Path(file_path).stat().st_size if Path(file_path).exists() else 0,
                'type': file_type
            }
            manifest_data['files'][file_type] = file_info
        
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest_data, f, indent=2, ensure_ascii=False)
        
        return str(manifest_path)