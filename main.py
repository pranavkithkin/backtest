#!/usr/bin/env python3
"""
Main entry point for the Crypto Profit/Loss Analyzer
"""
import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from crypto_analyzer import ProfitLossAnalyzer, Settings
from crypto_analyzer.utils import setup_logging
import logging

logger = logging.getLogger(__name__)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Cryptocurrency Profit/Loss Analysis Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --input-folder signals --output-folder results
  python main.py --input-folder signals --profit 50 --loss -20
  python main.py --interactive  # Interactive portfolio calculator
        """
    )
    
    parser.add_argument(
        "--interactive", 
        action="store_true",
        help="Run interactive portfolio calculator"
    )
    
    parser.add_argument(
        "--input-folder", 
        default=Settings.INPUT_FOLDER,
        help=f"Input folder containing CSV files (default: {Settings.INPUT_FOLDER})"
    )
    
    parser.add_argument(
        "--output-folder", 
        default=Settings.OUTPUT_FOLDER,
        help=f"Output folder for results (default: {Settings.OUTPUT_FOLDER})"
    )
    
    parser.add_argument(
        "--output-prefix", 
        default=Settings.OUTPUT_PREFIX,
        help=f"Prefix for output files (default: {Settings.OUTPUT_PREFIX})"
    )
    
    parser.add_argument(
        "--profit", 
        type=float, 
        default=Settings.ANALYSIS.target_profit_pct,
        help=f"Target profit percentage (default: {Settings.ANALYSIS.target_profit_pct})"
    )
    
    parser.add_argument(
        "--loss", 
        type=float, 
        default=Settings.ANALYSIS.target_loss_pct,
        help=f"Target loss percentage (default: {Settings.ANALYSIS.target_loss_pct})"
    )
    
    parser.add_argument(
        "--max-days", 
        type=int, 
        default=Settings.ANALYSIS.max_days_ahead,
        help=f"Maximum days to look ahead (default: {Settings.ANALYSIS.max_days_ahead})"
    )
    
    parser.add_argument(
        "--api-key", 
        help="Binance API key (optional)"
    )
    
    parser.add_argument(
        "--api-secret", 
        help="Binance API secret (optional)"
    )
    
    parser.add_argument(
        "--log-level", 
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
        default='INFO',
        help="Logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--single-file", 
        help="Process a single CSV file instead of a folder"
    )
    
    args = parser.parse_args()
    
    # If interactive mode, run the portfolio calculator
    if args.interactive:
        import subprocess
        subprocess.run([sys.executable, "portfolio_calculator.py"])
        return 0
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Update settings
    Settings.update_analysis_config(
        target_profit_pct=args.profit,
        target_loss_pct=args.loss,
        max_days_ahead=args.max_days
    )
    
    Settings.update_folders(
        input_folder=args.input_folder,
        output_folder=args.output_folder,
        output_prefix=args.output_prefix
    )
    
    logger.info("Starting Crypto Profit/Loss Analyzer")
    logger.info(f"Target: +{args.profit}% vs {args.loss}%")
    logger.info(f"Max lookahead: {args.max_days} days")
    
    try:
        # Initialize analyzer
        analyzer = ProfitLossAnalyzer(api_key=args.api_key, api_secret=args.api_secret)
        
        # Test API connection
        if not analyzer.binance_client.test_connection():
            logger.warning("API connection test failed. Continuing anyway...")
        
        if args.single_file:
            # Process single file
            output_file = Path(args.output_folder) / f"{args.output_prefix}{Path(args.single_file).stem}.csv"
            success = analyzer.process_csv_file(args.single_file, str(output_file))
            
            if success:
                logger.info("✅ Single file processing completed successfully!")
            else:
                logger.error("❌ Single file processing failed!")
                return 1
        else:
            # Batch process folder
            result = analyzer.batch_process(
                args.input_folder, 
                args.output_folder, 
                args.output_prefix
            )
            
            if result['success']:
                logger.info("📊 BATCH PROCESSING SUMMARY:")
                logger.info(f"Files processed successfully: {result['successful_files']}/{result['total_files']}")
                logger.info(f"Output folder: {result['output_folder']}")
                logger.info("🎉 Processing completed!")
            else:
                logger.error(f"❌ Batch processing failed: {result.get('message', 'Unknown error')}")
                return 1
    
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())