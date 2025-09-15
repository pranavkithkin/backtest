#!/usr/bin/env python3
"""
Concurrent Portfolio Calculator - Final Version
Handles limit entries with concurrent position management
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
    pass

from crypto_analyzer import ProfitLossAnalyzer, ConcurrentPortfolioCalculator
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
    
    search_paths = [".", "data", "signals", "input"]
    csv_files = []
    for path in search_paths:
        if os.path.exists(path):
            csv_files.extend(find_csv_files(path))
    
    if not csv_files:
        print("❌ No CSV files found! Please ensure you have CSV files with trading signals.")
        return None
    
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


def display_concurrent_results(performance: dict):
    """Display concurrent portfolio performance results"""
    print("\n" + "="*80)
    print("📊 CONCURRENT PORTFOLIO PERFORMANCE RESULTS")
    print("="*80)
    
    settings = performance['settings']
    print(f"📋 STRATEGY SETTINGS:")
    print(f"   Stop Loss: {settings['stop_loss_pct']}%")
    print(f"   Target Profit: {settings['target_profit_pct']}% (Risk:Reward = 1:{settings['risk_reward_ratio']})")
    print(f"   Risk per trade: {settings['risk_per_trade_pct']}% of available capital")
    print()
    
    print(f"📄 SIMULATION SUMMARY:")
    print(f"   Total signals processed: {performance['total_signals']}")
    print(f"   Simulation period: {performance['simulation_start'].strftime('%Y-%m-%d')} to {performance['simulation_end'].strftime('%Y-%m-%d')}")
    print(f"   Final open positions: {performance['open_positions_count']}")
    print()
    
    print(f"💰 CAPITAL SUMMARY:")
    print(f"   Initial Capital: ${performance['initial_capital']:,.2f}")
    print(f"   Final Capital: ${performance['current_capital']:,.2f}")
    print(f"   Available Capital: ${performance['available_capital']:,.2f}")
    print(f"   Allocated Capital: ${performance['allocated_capital']:,.2f}")
    print(f"   Total P&L: ${performance['total_pnl']:,.2f}")
    print(f"   Total Return: {performance['total_return_pct']:.2f}%")
    print()
    
    print(f"📈 TRADE STATISTICS:")
    print(f"   Total Completed Trades: {performance['total_trades']}")
    print(f"   Winning Trades: {performance['winning_trades']}")
    print(f"   Losing Trades: {performance['losing_trades']}")
    print(f"   Win Rate: {performance['win_rate']:.1f}%")
    print()
    
    # Show recent events
    if 'simulation_events' in performance and performance['simulation_events']:
        print(f"📅 RECENT TRADING EVENTS:")
        events = performance['simulation_events'][-10:]  # Last 10 events
        for event in events:
            if event['type'] == 'ENTRY':
                print(f"   🟢 ENTRY: {event['symbol']} at ${event['price']:.4f} (Risk: ${event['risk_amount']:.2f})")
            elif event['type'] == 'EXIT':
                pnl_sign = "+" if event['pnl'] > 0 else ""
                print(f"   🔴 EXIT:  {event['symbol']} - {event['reason']} ({pnl_sign}${event['pnl']:.2f}) after {event['hours_held']:.1f}h")
        print()
    
    # Performance interpretation
    print(f"🎯 INTERPRETATION:")
    if performance['total_return_pct'] > 0:
        print(f"   ✅ Concurrent strategy would have been PROFITABLE with {performance['total_return_pct']:.2f}% return")
    else:
        print(f"   ❌ Concurrent strategy would have resulted in a LOSS of {abs(performance['total_return_pct']):.2f}%")
    
    if performance['win_rate'] >= 50:
        print(f"   ✅ Good win rate of {performance['win_rate']:.1f}%")
    else:
        print(f"   ⚠️  Win rate of {performance['win_rate']:.1f}% is below 50%")
    
    if performance['open_positions_count'] > 0:
        print(f"   ℹ️  {performance['open_positions_count']} positions still open at simulation end")


def main():
    """Main interactive function"""
    print("🚀 CONCURRENT CRYPTO TRADING PORTFOLIO CALCULATOR")
    print("="*80)
    print("This advanced tool simulates concurrent position management with:")
    print("• Limit order entries (wait for price to hit limit)")
    print("• Multiple positions open simultaneously")
    print("• Risk calculated when limit orders actually fill")
    print("• Capital updates only when positions close")
    print("• Real-time position tracking and management")
    print("="*80)
    
    # Setup logging
    setup_logging("INFO")
    
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
        print(f"\n⚙️  CONCURRENT TRADING PARAMETERS:")
        stop_loss_pct = get_float_input("Stop Loss percentage (e.g., 10 for 10%)", 1, 50)
        risk_reward_ratio = get_float_input("Risk to Reward ratio (e.g., 1.5 for 1:1.5)", 0.5, 10)
        risk_per_trade_pct = get_float_input("Risk per trade percentage (e.g., 5 for 5% of available capital)", 0.5, 20)
        
        # Optional: Initial capital
        print(f"\n💵 CAPITAL SETTINGS:")
        initial_capital = get_float_input("Initial capital (default: $100,000)", 1000, 10000000)
        
        print(f"\n🔄 STARTING CONCURRENT SIMULATION...")
        print(f"   Loading signals from {os.path.basename(csv_file)}...")
        
        # Initialize analyzer and concurrent calculator
        analyzer = ProfitLossAnalyzer()
        calculator = ConcurrentPortfolioCalculator(analyzer)
        
        # Load signals
        all_signals = calculator.load_signals_from_csv(csv_file)
        if not all_signals:
            print("❌ No valid signals found in the CSV file!")
            return
        
        print(f"   Found {len(all_signals)} total signals")
        
        # Filter by date range
        from_date_utc = from_date.replace(tzinfo=datetime.now().astimezone().tzinfo)
        to_date_utc = to_date.replace(tzinfo=datetime.now().astimezone().tzinfo)
        
        filtered_signals = calculator.filter_signals_by_date(all_signals, from_date_utc, to_date_utc)
        
        if not filtered_signals:
            print(f"❌ No signals found in the date range {from_date.strftime('%d-%m-%Y')} to {to_date.strftime('%d-%m-%Y')}")
            return
        
        print(f"   {len(filtered_signals)} signals in date range")
        print(f"   Running concurrent simulation with:")
        print(f"     • Stop Loss: {stop_loss_pct}%")
        print(f"     • Risk:Reward: 1:{risk_reward_ratio}")
        print(f"     • Risk per trade: {risk_per_trade_pct}% of available capital")
        print(f"   ⏳ This may take a few minutes...")
        
        # Calculate concurrent portfolio performance
        performance = calculator.calculate_concurrent_portfolio_performance(
            signals=filtered_signals,
            stop_loss_pct=stop_loss_pct,
            risk_reward_ratio=risk_reward_ratio,
            risk_per_trade_pct=risk_per_trade_pct,
            initial_capital=initial_capital
        )
        
        # Display results
        display_concurrent_results(performance)
        
        # Ask if user wants to save detailed results
        save_details = input(f"\n💾 Save detailed simulation results to CSV? (y/n): ").lower().strip()
        if save_details == 'y':
            from datetime import datetime as dt
            timestamp = dt.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"concurrent_portfolio_analysis_{timestamp}.csv"
            
            # Prepare detailed results
            detailed_results = []
            for pos in performance['closed_positions']:
                detailed_results.append({
                    'Signal_Date': pos.position.signal.date,
                    'Signal_Time': pos.position.signal.time,
                    'Coin': pos.position.signal.coin_name,
                    'Limit_Price': pos.position.signal.entry_price,
                    'Entry_Fill_Time': pos.position.entry_fill_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'Entry_Fill_Price': pos.position.entry_fill_price,
                    'Close_Time': pos.close_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'Close_Reason': pos.close_reason,
                    'PnL': pos.pnl,
                    'Hours_Held': pos.hours_held,
                    'Risk_Amount': pos.position.risk_amount,
                    'Position_Size': pos.position.position_size
                })
            
            import pandas as pd
            pd.DataFrame(detailed_results).to_csv(output_file, index=False)
            print(f"✅ Detailed concurrent results saved to: {output_file}")
    
    except KeyboardInterrupt:
        print(f"\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        logger.error(f"Error in concurrent calculator: {e}")


if __name__ == "__main__":
    main()