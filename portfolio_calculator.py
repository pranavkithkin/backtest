#!/usr/bin/env python3
"""
Interactive Portfolio Calculator for Crypto Trading Signals
"""
import sys
from pathlib import Path
from datetime import datetime
import os

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, skip

from crypto_analyzer import ProfitLossAnalyzer, PortfolioCalculator
from crypto_analyzer.utils import setup_logging, find_csv_files
import logging

logger = logging.getLogger(__name__)


def get_date_input(prompt: str) -> datetime:
    """Get date input from user in dd-mm-yyyy format"""
    while True:
        try:
            date_str = input(f"{prompt} (dd-mm-yyyy): ").strip()
            return datetime.strptime(date_str, "%d-%m-%Y")
        except ValueError:
            print("❌ Invalid date format! Please use dd-mm-yyyy (e.g., 15-01-2023)")


def get_float_input(prompt: str, min_val: float = None, max_val: float = None) -> float:
    """Get float input from user with validation"""
    while True:
        try:
            value = float(input(f"{prompt}: ").strip())
            if min_val is not None and value < min_val:
                print(f"❌ Value must be at least {min_val}")
                continue
            if max_val is not None and value > max_val:
                print(f"❌ Value must be at most {max_val}")
                continue
            return value
        except ValueError:
            print("❌ Invalid number! Please enter a valid number.")


def get_csv_file_choice() -> str:
    """Let user choose a CSV file"""
    print("\n📁 Available CSV files:")
    
    # Look for CSV files in current directory and common folders
    search_paths = [
        ".",
        "data",
        "signals",
        "input"
    ]
    
    csv_files = []
    for path in search_paths:
        if os.path.exists(path):
            csv_files.extend(find_csv_files(path))
    
    if not csv_files:
        print("❌ No CSV files found! Please ensure you have CSV files with trading signals.")
        return None
    
    # Remove duplicates and sort
    csv_files = list(set(csv_files))
    csv_files.sort()
    
    for i, file in enumerate(csv_files, 1):
        print(f"  {i}. {os.path.basename(file)}")
    
    while True:
        try:
            choice = int(input(f"\nChoose file (1-{len(csv_files)}): ")) - 1
            if 0 <= choice < len(csv_files):
                return csv_files[choice]
            else:
                print(f"❌ Please enter a number between 1 and {len(csv_files)}")
        except ValueError:
            print("❌ Please enter a valid number")


def display_results(performance: dict):
    """Display portfolio performance results"""
    print("\n" + "="*70)
    print("📊 PORTFOLIO PERFORMANCE RESULTS")
    print("="*70)
    
    settings = performance['settings']
    print(f"📋 STRATEGY SETTINGS:")
    print(f"   Stop Loss: {settings['stop_loss_pct']}%")
    print(f"   Target Profit: {settings['target_profit_pct']}% (Risk:Reward = 1:{settings['risk_reward_ratio']})")
    print(f"   Risk per trade: {settings['risk_per_trade_pct']}% of capital")
    print()
    
    print(f"📄 DATA SUMMARY:")
    print(f"   Total signals in CSV: {performance['total_signals']}")
    print(f"   Valid tradeable signals: {performance['total_trades']}")
    print(f"   Invalid/skipped symbols: {performance['invalid_symbols_count']}")
    print(f"   Success rate: {(performance['total_trades']/performance['total_signals']*100):.1f}%")
    print()
    
    print(f"💰 CAPITAL SUMMARY:")
    print(f"   Initial Capital: ${performance['initial_capital']:,.2f}")
    print(f"   Final Capital: ${performance['final_capital']:,.2f}")
    print(f"   Total P&L: ${performance['total_pnl']:,.2f}")
    print(f"   Total Return: {performance['total_return_pct']:.2f}%")
    print()
    
    print(f"📈 TRADE STATISTICS:")
    print(f"   Total Trades: {performance['total_trades']}")
    print(f"   Winning Trades: {performance['winning_trades']}")
    print(f"   Losing Trades: {performance['losing_trades']}")
    print(f"   No Outcome: {performance['neither_trades']}")
    print(f"   Win Rate: {performance['win_rate']:.1f}%")
    print()
    
    print(f"💡 PERFORMANCE METRICS:")
    print(f"   Average Win: ${performance['avg_win']:,.2f}")
    print(f"   Average Loss: ${performance['avg_loss']:,.2f}")
    if performance['profit_factor'] != float('inf'):
        print(f"   Profit Factor: {performance['profit_factor']:.2f}")
    else:
        print(f"   Profit Factor: ∞ (no losses)")
    
    # Performance interpretation
    print(f"\n🎯 INTERPRETATION:")
    if performance['total_return_pct'] > 0:
        print(f"   ✅ Strategy would have been PROFITABLE with {performance['total_return_pct']:.2f}% return")
    else:
        print(f"   ❌ Strategy would have resulted in a LOSS of {abs(performance['total_return_pct']):.2f}%")
    
    if performance['win_rate'] >= 50:
        print(f"   ✅ Good win rate of {performance['win_rate']:.1f}%")
    else:
        print(f"   ⚠️  Win rate of {performance['win_rate']:.1f}% is below 50%")
    
    if performance['invalid_symbols_count'] > 0:
        print(f"   ℹ️  {performance['invalid_symbols_count']} symbols were skipped (not available on Binance)")


def main():
    """Main interactive function"""
    print("🚀 CRYPTO TRADING SIGNAL PORTFOLIO CALCULATOR")
    print("="*70)
    print("This tool calculates your overall portfolio performance based on:")
    print("• Date range for analysis")
    print("• Stop loss percentage")
    print("• Risk-to-reward ratio")
    print("• Risk per trade percentage")
    print("="*70)
    
    # Setup logging (quiet mode for interactive use)
    setup_logging("WARNING")
    
    try:
        # Step 1: Choose CSV file
        csv_file = get_csv_file_choice()
        if not csv_file:
            return
        
        print(f"\n✅ Selected file: {os.path.basename(csv_file)}")
        
        # Step 2: Get date range
        print(f"\n📅 DATE RANGE SELECTION:")
        from_date = get_date_input("From date")
        to_date = get_date_input("To date")
        
        if from_date >= to_date:
            print("❌ From date must be before to date!")
            return
        
        # Step 3: Get trading parameters
        print(f"\n⚙️  TRADING PARAMETERS:")
        stop_loss_pct = get_float_input("Stop Loss percentage (e.g., 2 for 2%)", 0.1, 50)
        risk_reward_ratio = get_float_input("Risk to Reward ratio (e.g., 2 for 1:2)", 0.5, 10)
        risk_per_trade_pct = get_float_input("Risk per trade percentage (e.g., 2 for 2% of capital)", 0.1, 10)
        
        # Optional: Initial capital
        print(f"\n💵 CAPITAL SETTINGS:")
        initial_capital = get_float_input("Initial capital (default: $100,000)", 1000, 10000000)
        
        print(f"\n🔄 PROCESSING...")
        print(f"   Loading signals from {os.path.basename(csv_file)}...")
        
        # Initialize analyzer and calculator
        analyzer = ProfitLossAnalyzer()
        calculator = PortfolioCalculator(analyzer)
        
        # Load signals
        all_signals = calculator.load_signals_from_csv(csv_file)
        if not all_signals:
            print("❌ No valid signals found in the CSV file!")
            return
        
        print(f"   Found {len(all_signals)} total signals")
        
        # Filter by date range
        filtered_signals = calculator.filter_signals_by_date(
            all_signals, 
            from_date.replace(tzinfo=datetime.now().astimezone().tzinfo), 
            to_date.replace(tzinfo=datetime.now().astimezone().tzinfo)
        )
        
        if not filtered_signals:
            print(f"❌ No signals found in the date range {from_date.strftime('%d-%m-%Y')} to {to_date.strftime('%d-%m-%Y')}")
            return
        
        print(f"   {len(filtered_signals)} signals in date range")
        print(f"   Analyzing with Stop Loss: {stop_loss_pct}%, Risk:Reward: 1:{risk_reward_ratio}")
        
        # Calculate portfolio performance
        performance = calculator.calculate_portfolio_performance(
            signals=filtered_signals,
            stop_loss_pct=stop_loss_pct,
            risk_reward_ratio=risk_reward_ratio,
            risk_per_trade_pct=risk_per_trade_pct,
            initial_capital=initial_capital
        )
        
        # Display results
        display_results(performance)
        
        # Ask if user wants to save detailed results
        save_details = input(f"\n💾 Save detailed trade-by-trade results to CSV? (y/n): ").lower().strip()
        if save_details == 'y':
            from datetime import datetime as dt
            timestamp = dt.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"portfolio_analysis_{timestamp}.csv"
            
            # Prepare detailed results
            detailed_results = []
            for trade in performance['trade_results']:
                detailed_results.append({
                    'Date': trade['signal'].date,
                    'Time': trade['signal'].time,
                    'Coin': trade['signal'].coin_name,
                    'Entry_Price': trade['signal'].entry_price,
                    'Outcome': trade['outcome'],
                    'PnL': trade['pnl'],
                    'Position_Size': trade['position_size'],
                    'Capital_After': trade['capital_after'],
                    'Hours_to_Hit': trade['result'].hours_to_hit
                })
            
            import pandas as pd
            pd.DataFrame(detailed_results).to_csv(output_file, index=False)
            print(f"✅ Detailed results saved to: {output_file}")
    
    except KeyboardInterrupt:
        print(f"\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        logger.error(f"Error in interactive calculator: {e}")


if __name__ == "__main__":
    main()