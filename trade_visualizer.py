#!/usr/bin/env python3
"""
Trade Visualization Tool
Creates charts showing trade entries, exits, and price action
"""
import sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import numpy as np
import os

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from crypto_analyzer import BinanceClient
import logging

logger = logging.getLogger(__name__)


class TradeVisualizer:
    """Visualize individual trades with price action"""
    
    def __init__(self):
        self.client = BinanceClient()
        
    def visualize_trade(
        self, 
        symbol: str, 
        entry_time: datetime, 
        entry_price: float,
        stop_loss_price: float,
        take_profit_price: float,
        actual_exit_time: datetime = None,
        actual_exit_price: float = None,
        exit_reason: str = None,
        days_before: int = 2,
        days_after: int = 5
    ):
        """
        Create a chart showing the trade with entry, SL, TP, and actual exit
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            entry_time: When the trade was entered
            entry_price: Entry price
            stop_loss_price: Stop loss price
            take_profit_price: Take profit price
            actual_exit_time: When trade actually exited (if known)
            actual_exit_price: Actual exit price (if known)
            exit_reason: Reason for exit ('PROFIT', 'LOSS', 'BREAKEVEN', etc.)
            days_before: Days of price history before entry
            days_after: Days of price history after entry
        """
        try:
            # Calculate time range
            start_time = entry_time - timedelta(days=days_before)
            end_time = entry_time + timedelta(days=days_after)
            
            # Get price data using the correct method
            print(f"📊 Getting price data for {symbol}...")
            
            # Calculate how many hours of data we need
            total_hours = int((end_time - start_time).total_seconds() / 3600) + 24
            
            # Use the BinanceClient's method
            df = self.client.get_klines_for_timeframe(
                symbol=symbol,
                start_dt=start_time,
                interval=self.client.client.KLINE_INTERVAL_1HOUR,
                limit=min(total_hours, 1000)  # Binance API limit
            )
            
            if df is None or len(df) == 0:
                print(f"❌ No price data found for {symbol}")
                return
                
            # Create the chart
            fig, ax1 = plt.subplots(1, 1, figsize=(15, 10))
            
            # Price chart - df already has timestamp as index
            ax1.plot(df.index, df['close'], 'b-', linewidth=1, label='Price', alpha=0.8)
            
            # Entry point
            ax1.axvline(x=entry_time, color='green', linestyle='--', alpha=0.7, label='Entry Time')
            ax1.axhline(y=entry_price, color='green', linestyle='-', alpha=0.7, label=f'Entry: ${entry_price:.4f}')
            
            # Stop Loss and Take Profit levels
            ax1.axhline(y=stop_loss_price, color='red', linestyle='-', alpha=0.7, label=f'Stop Loss: ${stop_loss_price:.4f}')
            ax1.axhline(y=take_profit_price, color='blue', linestyle='-', alpha=0.7, label=f'Take Profit: ${take_profit_price:.4f}')
            
            # Actual exit (if provided)
            if actual_exit_time and actual_exit_price:
                color = 'green' if exit_reason == 'PROFIT' else 'red' if exit_reason == 'LOSS' else 'orange'
                ax1.axvline(x=actual_exit_time, color=color, linestyle=':', alpha=0.7, label=f'Exit Time ({exit_reason})')
                ax1.scatter([actual_exit_time], [actual_exit_price], color=color, s=100, zorder=5, label=f'Exit: ${actual_exit_price:.4f}')
            
            # Fill areas
            ax1.fill_between(df.index, stop_loss_price, take_profit_price, alpha=0.1, color='gray', label='Trade Range')
            
            # Formatting
            ax1.set_title(f'{symbol} Trade Analysis\nEntry: {entry_time.strftime("%Y-%m-%d %H:%M")} at ${entry_price:.4f}', fontsize=14, fontweight='bold')
            ax1.set_ylabel('Price (USDT)', fontweight='bold')
            ax1.set_xlabel('Time', fontweight='bold')
            ax1.legend(loc='upper left')
            ax1.grid(True, alpha=0.3)
            
            # Format x-axis
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
            ax1.xaxis.set_major_locator(mdates.HourLocator(interval=12))
            plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
            
            plt.tight_layout()
            
            # Save chart
            filename = f"trade_chart_{symbol}_{entry_time.strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            print(f"✅ Chart saved as: {filename}")
            
            # Show chart
            plt.show()
            
        except Exception as e:
            logger.error(f"Error creating chart for {symbol}: {e}")
            
    def visualize_from_csv(self, csv_file: str, max_charts: int = 10):
        """
        Create charts for trades from a CSV results file
        
        Args:
            csv_file: Path to CSV file with trade results
            max_charts: Maximum number of charts to create
        """
        try:
            df = pd.read_csv(csv_file)
            print(f"📊 Found {len(df)} trades in {csv_file}")
            
            # Check column names to handle different CSV formats
            print(f"📋 Columns found: {list(df.columns)}")
            
            if max_charts < len(df):
                print(f"📈 Creating charts for first {max_charts} trades...")
                df = df.head(max_charts)
            
            for idx, row in df.iterrows():
                print(f"\n🎯 Creating chart {idx + 1}/{len(df)}...")
                
                try:
                    # Handle different CSV formats
                    if 'Signal_Date' in df.columns and 'Signal_Time' in df.columns:
                        # Concurrent portfolio format
                        symbol = row['Coin'] + 'USDT' if not row['Coin'].endswith('USDT') else row['Coin']
                        entry_time = pd.to_datetime(f"{row['Signal_Date']} {row['Signal_Time']}")
                        entry_price = float(row['Entry_Fill_Price']) if 'Entry_Fill_Price' in row else float(row['Limit_Price'])
                        
                        # Extract exit information
                        exit_time = pd.to_datetime(row['Close_Time']) if pd.notna(row['Close_Time']) else None
                        exit_reason = row['Close_Reason'] if 'Close_Reason' in row else 'UNKNOWN'
                        pnl = float(row['PnL']) if 'PnL' in row and pd.notna(row['PnL']) else 0
                        
                    elif 'Date' in df.columns and 'Time' in df.columns:
                        # Regular portfolio format
                        symbol = row['Coin'] + 'USDT' if not row['Coin'].endswith('USDT') else row['Coin']
                        entry_time = pd.to_datetime(f"{row['Date']} {row['Time']}")
                        entry_price = float(row['Entry_Price'])
                        
                        # Determine exit info if available
                        exit_time = None
                        exit_reason = row.get('Outcome', 'UNKNOWN')
                        pnl = float(row['PnL']) if 'PnL' in row and pd.notna(row['PnL']) else 0
                        
                        if 'Hours_to_Hit' in row and pd.notna(row['Hours_to_Hit']):
                            exit_time = entry_time + timedelta(hours=float(row['Hours_to_Hit']))
                    else:
                        print(f"❌ Unsupported CSV format. Expected columns: Signal_Date/Date, Signal_Time/Time, Coin, etc.")
                        continue
                    
                    # Calculate SL and TP based on available data or defaults
                    if 'Risk_Amount' in row and pd.notna(row['Risk_Amount']):
                        # Calculate from risk amount (assuming 10% default SL)
                        risk_amount = float(row['Risk_Amount'])
                        stop_loss_pct = 10  # Default assumption
                        risk_reward = 1.5   # Default assumption
                        
                        stop_loss_price = entry_price * (1 - stop_loss_pct / 100)
                        take_profit_price = entry_price * (1 + (stop_loss_pct * risk_reward) / 100)
                    else:
                        # Use default calculations
                        stop_loss_pct = 10
                        risk_reward = 1.5
                        stop_loss_price = entry_price * (1 - stop_loss_pct / 100)
                        take_profit_price = entry_price * (1 + (stop_loss_pct * risk_reward) / 100)
                    
                    # Determine exit price if not available
                    exit_price = None
                    if exit_time and exit_reason:
                        if exit_reason in ['PROFIT', 'WIN']:
                            exit_price = take_profit_price
                        elif exit_reason in ['LOSS', 'STOP']:
                            exit_price = stop_loss_price
                        elif exit_reason == 'BREAKEVEN':
                            exit_price = entry_price
                        elif pnl != 0:
                            # Try to calculate exit price from PnL
                            # This is approximate
                            if pnl > 0:
                                exit_price = take_profit_price
                            else:
                                exit_price = stop_loss_price
                
                    print(f"   📍 {symbol}: Entry ${entry_price:.4f}, SL ${stop_loss_price:.4f}, TP ${take_profit_price:.4f}")
                    if exit_time:
                        exit_price_str = f"${exit_price:.4f}" if exit_price else "N/A"
                        print(f"   🎯 Exit: {exit_reason} at {exit_price_str}")
                
                    self.visualize_trade(
                        symbol=symbol,
                        entry_time=entry_time,
                        entry_price=entry_price,
                        stop_loss_price=stop_loss_price,
                        take_profit_price=take_profit_price,
                        actual_exit_time=exit_time,
                        actual_exit_price=exit_price,
                        exit_reason=exit_reason
                    )
                
                except Exception as e:
                    print(f"❌ Error processing trade {idx + 1}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error processing CSV file: {e}")
            print(f"❌ Error processing CSV file: {e}")


def main():
    """Main function for interactive use"""
    print("🎯 TRADE VISUALIZER")
    print("=" * 50)
    
    visualizer = TradeVisualizer()
    
    print("\nOptions:")
    print("1. Visualize from CSV results file")
    print("2. Visualize single trade manually")
    
    choice = input("\nSelect option (1 or 2): ").strip()
    
    if choice == "1":
        # Find CSV files
        csv_files = [f for f in os.listdir('.') if f.endswith('.csv') and 'analysis' in f.lower()]
        
        if not csv_files:
            print("❌ No CSV analysis files found in current directory")
            return
            
        print(f"\nFound CSV files:")
        for i, file in enumerate(csv_files, 1):
            print(f"{i}. {file}")
            
        try:
            file_idx = int(input(f"\nSelect CSV file (1-{len(csv_files)}): ")) - 1
            selected_file = csv_files[file_idx]
            
            max_charts = int(input("How many charts to create (default 5): ") or "5")
            
            visualizer.visualize_from_csv(selected_file, max_charts)
            
        except (ValueError, IndexError):
            print("❌ Invalid selection")
            
    elif choice == "2":
        # Manual trade entry
        symbol = input("Enter symbol (e.g., BTCUSDT): ").strip().upper()
        entry_date = input("Enter entry date (YYYY-MM-DD HH:MM): ").strip()
        entry_price = float(input("Enter entry price: "))
        stop_loss_price = float(input("Enter stop loss price: "))
        take_profit_price = float(input("Enter take profit price: "))
        
        entry_time = datetime.strptime(entry_date, "%Y-%m-%d %H:%M")
        
        visualizer.visualize_trade(
            symbol=symbol,
            entry_time=entry_time,
            entry_price=entry_price,
            stop_loss_price=stop_loss_price,
            take_profit_price=take_profit_price
        )
    
    else:
        print("❌ Invalid option")


if __name__ == "__main__":
    main()
