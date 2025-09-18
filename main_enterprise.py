"""
Enterprise Main Entry Point
==========================

Production-ready main script for enterprise trading signal analysis.
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.enterprise_analyzer import EnterpriseSignalAnalyzer

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Enterprise Trading Signal Analyzer',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python main_enterprise.py --file signals.csv --timezone Dubai
  python main_enterprise.py --file signals.csv --timezone New_York --confidence 0.99
  python main_enterprise.py --file signals.csv --export csv,json,html --user "analyst@company.com"
        '''
    )
    
    parser.add_argument(
        '--file', '-f',
        required=True,
        help='Path to CSV file containing trading signals'
    )
    
    parser.add_argument(
        '--timezone', '-t',
        default='Dubai',
        help='Analysis timezone (default: Dubai)'
    )
    
    parser.add_argument(
        '--confidence', '-c',
        type=float,
        default=0.95,
        choices=[0.90, 0.95, 0.99],
        help='Statistical confidence level (default: 0.95)'
    )
    
    parser.add_argument(
        '--export', '-e',
        default='csv,json,txt,html',
        help='Export formats: csv,json,txt,html (default: all)'
    )
    
    parser.add_argument(
        '--output-dir', '-o',
        default='output',
        help='Output directory for results (default: output)'
    )
    
    parser.add_argument(
        '--user', '-u',
        default='enterprise_user',
        help='User identifier for audit logging (default: enterprise_user)'
    )
    
    parser.add_argument(
        '--config', '-cfg',
        default='config/default.yaml',
        help='Configuration file path (default: config/default.yaml)'
    )
    
    parser.add_argument(
        '--no-ml',
        action='store_true',
        help='Disable machine learning predictions'
    )
    
    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Only validate data quality, do not run full analysis'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    return parser.parse_args()

def print_banner():
    """Print enterprise banner"""
    banner = """
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║    🏢 ENTERPRISE TRADING SIGNAL ANALYZER v2.0.0                 ║
║                                                                  ║
║    Professional-grade analysis with enterprise architecture      ║
║    Statistical validation • ML predictions • Audit trails       ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""
    print(banner)

def main():
    """Main enterprise application entry point"""
    
    args = parse_arguments()
    
    # Print banner
    print_banner()
    
    # Validate input file
    input_file = Path(args.file)
    if not input_file.exists():
        print(f"❌ Error: Signal file not found: {args.file}")
        sys.exit(1)
    
    # Parse export formats
    export_formats = [fmt.strip() for fmt in args.export.split(',')]
    
    print(f"📊 Starting enterprise analysis...")
    print(f"📁 Input file: {args.file}")
    print(f"🌍 Timezone: {args.timezone}")
    print(f"📈 Confidence level: {args.confidence*100:.0f}%")
    print(f"👤 User: {args.user}")
    print(f"📤 Export formats: {', '.join(export_formats)}")
    print("─" * 70)
    
    try:
        # Initialize enterprise analyzer
        analyzer = EnterpriseSignalAnalyzer(
            config_path=args.config,
            user=args.user
        )
        
        print("✅ Enterprise analyzer initialized")
        
        # Load signals
        print(f"📥 Loading signals from {args.file}...")
        data = analyzer.load_signals(args.file, args.timezone)
        print(f"✅ Loaded {len(data):,} signals successfully")
        
        # Validate data quality
        print("🔍 Validating data quality...")
        validation_results = analyzer.validate_data_quality()
        
        if validation_results['valid']:
            print("✅ Data quality validation passed")
            for warning in validation_results.get('warnings', []):
                print(f"⚠️  Warning: {warning}")
        else:
            print(f"❌ Data quality validation failed: {validation_results.get('reason', 'Unknown')}")
            if not args.validate_only:
                response = input("Continue with analysis anyway? (y/N): ")
                if response.lower() != 'y':
                    sys.exit(1)
        
        # Print data statistics
        stats = validation_results['statistics']
        print(f"📊 Data Statistics:")
        print(f"   • Total signals: {stats['total_signals']:,}")
        print(f"   • Unique assets: {stats['unique_assets']}")
        print(f"   • Date span: {stats['date_span_days']} days")
        print(f"   • Data completeness: {stats['completeness_pct']:.1f}%")
        
        if args.validate_only:
            print("✅ Data validation complete. Exiting as requested.")
            return
        
        # Run comprehensive analysis
        print("\n🔬 Running comprehensive enterprise analysis...")
        analysis_results = analyzer.run_comprehensive_analysis(
            timezone=args.timezone,
            confidence_level=args.confidence,
            enable_ml=not args.no_ml
        )
        
        duration = analysis_results['metadata']['analysis_duration']
        print(f"✅ Analysis completed in {duration:.2f} seconds")
        
        # Generate report
        print("📋 Generating enterprise report...")
        report = analyzer.generate_enterprise_report(analysis_results)
        
        if args.verbose:
            print("\n" + "="*70)
            print("ANALYSIS REPORT PREVIEW:")
            print("="*70)
            # Show first 20 lines of report
            lines = report.split('\n')[:20]
            for line in lines:
                print(line)
            print("... (full report will be exported)")
            print("="*70)
        
        # Export results
        print(f"📤 Exporting results in {len(export_formats)} formats...")
        exported_files = analyzer.export_results(
            analysis_results,
            export_formats,
            args.output_dir
        )
        
        # Display export summary
        print("\n📁 EXPORT SUMMARY:")
        print("─" * 50)
        for file_type, file_path in exported_files.items():
            file_size = Path(file_path).stat().st_size if Path(file_path).exists() else 0
            print(f"   {file_type:20}: {file_path} ({file_size:,} bytes)")
        
        # Display key recommendations
        recommendations = analysis_results.get('parameter_optimization', {}).get('recommendations', {})
        if recommendations:
            print("\n🎯 KEY RECOMMENDATIONS:")
            print("─" * 50)
            print(f"   Optimal Risk Range: {recommendations.get('optimal_risk_range', 'N/A')}")
            print(f"   Best Trading Hour:  {recommendations.get('optimal_hour', 'N/A')}:00 {args.timezone}")
            print(f"   Top Market Session: {recommendations.get('optimal_session', 'N/A')}")
        
        # Summary statistics
        metadata = analysis_results['metadata']
        print(f"\n📈 ANALYSIS SUMMARY:")
        print("─" * 50)
        print(f"   Signals Analyzed: {metadata['signal_count']:,}")
        print(f"   Unique Assets: {metadata['unique_assets']}")
        print(f"   Analysis Duration: {metadata['analysis_duration']:.2f}s")
        print(f"   ML Predictions: {'✅ Enabled' if not args.no_ml else '❌ Disabled'}")
        print(f"   Files Exported: {len(exported_files)}")
        
        print(f"\n🎉 Enterprise analysis completed successfully!")
        print(f"📁 Results saved to: {args.output_dir}/")
        
    except KeyboardInterrupt:
        print("\n⚠️  Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Analysis failed with error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()