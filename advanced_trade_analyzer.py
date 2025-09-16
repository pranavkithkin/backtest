#!/usr/bin/env python3
"""
Advanced Trade Analysis and Heatmap Generator
Creates various visualizations for trade analysis
"""
import sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime, timedelta
import os

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import logging

logger = logging.getLogger(__name__)


class TradeAnalyzer:
    """Advanced trade analysis and visualization"""
    
    def __init__(self):
        # Set style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
    def analyze_trade_patterns(self, csv_file: str):
        """
        Create comprehensive analysis of trade patterns
        """
        try:
            df = pd.read_csv(csv_file)
            print(f"📊 Analyzing {len(df)} trades from {csv_file}")
            print(f"📋 Columns found: {list(df.columns)}")
            
            # Handle different CSV formats
            if 'Signal_Date' in df.columns and 'Signal_Time' in df.columns:
                # Concurrent portfolio format
                df['Date'] = pd.to_datetime(df['Signal_Date'])
                df['Time'] = df['Signal_Time']
                df['Entry_Price'] = df['Entry_Fill_Price']
                
                # Map close reasons to outcomes
                df['Outcome'] = df['Close_Reason'].map({
                    'PROFIT': 'WIN',
                    'LOSS': 'LOSS', 
                    'BREAKEVEN': 'BREAKEVEN'
                }).fillna('UNKNOWN')
                
                # Calculate hours to hit from Hours_Held
                if 'Hours_Held' in df.columns:
                    df['Hours_to_Hit'] = df['Hours_Held']
                    
            elif 'Date' not in df.columns:
                print("❌ Unsupported CSV format. Expected Date or Signal_Date column.")
                return
            
            # Prepare data
            df['Date'] = pd.to_datetime(df['Date'])
            
            # Handle time parsing
            if df['Time'].dtype == 'object':
                try:
                    df['Hour'] = pd.to_datetime(df['Time'], format='%H:%M:%S').dt.hour
                except:
                    try:
                        df['Hour'] = pd.to_datetime(df['Time']).dt.hour
                    except:
                        df['Hour'] = 12  # Default if parsing fails
            else:
                df['Hour'] = pd.to_datetime(df['Time']).dt.hour
                
            df['DayOfWeek'] = df['Date'].dt.day_name()
            df['Month'] = df['Date'].dt.month_name()
            
            # Ensure we have valid outcomes for analysis
            if 'Outcome' not in df.columns:
                # Try to infer from PnL
                if 'PnL' in df.columns:
                    df['Outcome'] = df['PnL'].apply(lambda x: 'WIN' if x > 0 else 'LOSS' if x < 0 else 'BREAKEVEN')
                else:
                    print("❌ Cannot determine trade outcomes. Need 'Outcome' column or 'PnL' column.")
                    return
            
            # Create figure with subplots
            fig = plt.figure(figsize=(20, 15))
            
            # 1. Win Rate by Hour
            plt.subplot(3, 3, 1)
            hourly_stats = df.groupby('Hour').agg({
                'Outcome': lambda x: (x == 'WIN').sum() / len(x) * 100 if len(x) > 0 else 0
            }).round(2)
            if len(hourly_stats) > 0:
                hourly_stats.plot(kind='bar', color='skyblue')
                plt.title('Win Rate by Hour of Day', fontweight='bold')
                plt.ylabel('Win Rate (%)')
                plt.xlabel('Hour')
                plt.xticks(rotation=45)
            
            # 2. Win Rate by Day of Week
            plt.subplot(3, 3, 2)
            daily_stats = df.groupby('DayOfWeek').agg({
                'Outcome': lambda x: (x == 'WIN').sum() / len(x) * 100 if len(x) > 0 else 0
            }).round(2)
            if len(daily_stats) > 0:
                daily_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                daily_stats = daily_stats.reindex([d for d in daily_order if d in daily_stats.index])
                daily_stats.plot(kind='bar', color='lightgreen')
                plt.title('Win Rate by Day of Week', fontweight='bold')
                plt.ylabel('Win Rate (%)')
                plt.xlabel('Day')
                plt.xticks(rotation=45)
            
            # 3. PnL Distribution
            plt.subplot(3, 3, 3)
            if 'PnL' in df.columns:
                pnl_data = df['PnL'].dropna()
                if len(pnl_data) > 0:
                    plt.hist(pnl_data, bins=min(30, len(pnl_data)), alpha=0.7, color='purple')
                    plt.axvline(pnl_data.mean(), color='red', linestyle='--', label=f'Mean: ${pnl_data.mean():.2f}')
                    plt.title('PnL Distribution', fontweight='bold')
                    plt.xlabel('PnL ($)')
                    plt.ylabel('Frequency')
                    plt.legend()
            
            # 4. Trade Count Heatmap (Hour vs Day)
            plt.subplot(3, 3, 4)
            try:
                heatmap_data = df.pivot_table(values='Coin', index='Hour', columns='DayOfWeek', aggfunc='count', fill_value=0)
                daily_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                available_days = [d for d in daily_order if d in heatmap_data.columns]
                if available_days:
                    heatmap_data = heatmap_data.reindex(columns=available_days)
                    sns.heatmap(heatmap_data, annot=True, fmt='d', cmap='YlOrRd')
                    plt.title('Trade Count Heatmap', fontweight='bold')
                    plt.ylabel('Hour of Day')
                    plt.xlabel('Day of Week')
            except Exception as e:
                plt.text(0.5, 0.5, f'Heatmap error:\n{str(e)[:50]}...', ha='center', va='center', transform=plt.gca().transAxes)
            
            # 5. Win Rate Heatmap
            plt.subplot(3, 3, 5)
            try:
                win_heatmap = df.pivot_table(values='Outcome', index='Hour', columns='DayOfWeek', 
                                           aggfunc=lambda x: (x == 'WIN').sum() / len(x) * 100 if len(x) > 0 else 0)
                available_days = [d for d in daily_order if d in win_heatmap.columns]
                if available_days:
                    win_heatmap = win_heatmap.reindex(columns=available_days)
                    sns.heatmap(win_heatmap, annot=True, fmt='.1f', cmap='RdYlGn', center=50)
                    plt.title('Win Rate Heatmap (%)', fontweight='bold')
                    plt.ylabel('Hour of Day')
                    plt.xlabel('Day of Week')
            except Exception as e:
                plt.text(0.5, 0.5, f'Win Rate Heatmap error:\n{str(e)[:50]}...', ha='center', va='center', transform=plt.gca().transAxes)
            
            # 6. Time to Hit Distribution
            plt.subplot(3, 3, 6)
            if 'Hours_to_Hit' in df.columns:
                valid_hours = df[df['Hours_to_Hit'].notna()]['Hours_to_Hit']
                if len(valid_hours) > 0:
                    plt.hist(valid_hours, bins=min(30, len(valid_hours)), alpha=0.7, color='orange')
                    plt.axvline(valid_hours.mean(), color='red', linestyle='--', label=f'Mean: {valid_hours.mean():.2f}h')
                    plt.title('Time to Hit Distribution', fontweight='bold')
                    plt.xlabel('Hours to Hit Target')
                    plt.ylabel('Frequency')
                    plt.legend()
            elif 'Hours_Held' in df.columns:
                valid_hours = df[df['Hours_Held'].notna()]['Hours_Held']
                if len(valid_hours) > 0:
                    plt.hist(valid_hours, bins=min(30, len(valid_hours)), alpha=0.7, color='orange')
                    plt.axvline(valid_hours.mean(), color='red', linestyle='--', label=f'Mean: {valid_hours.mean():.2f}h')
                    plt.title('Hours Held Distribution', fontweight='bold')
                    plt.xlabel('Hours Held')
                    plt.ylabel('Frequency')
                    plt.legend()
            
            # 7. Top Performing Coins
            plt.subplot(3, 3, 7)
            if len(df) > 0:
                coin_performance = df.groupby('Coin').agg({
                    'Outcome': lambda x: (x == 'WIN').sum() / len(x) * 100 if len(x) > 0 else 0,
                    'Coin': 'count'
                }).rename(columns={'Coin': 'Count', 'Outcome': 'Win_Rate'})
                
                # Filter coins with at least 2 trades (reduced from 3 for smaller datasets)
                coin_performance = coin_performance[coin_performance['Count'] >= 2]
                
                if len(coin_performance) > 0:
                    top_coins = coin_performance.nlargest(min(10, len(coin_performance)), 'Win_Rate')
                    if len(top_coins) > 0:
                        top_coins['Win_Rate'].plot(kind='barh', color='gold')
                        plt.title(f'Top Coins by Win Rate (≥2 trades)', fontweight='bold')
                        plt.xlabel('Win Rate (%)')
            
            # 8. Monthly Performance
            plt.subplot(3, 3, 8)
            monthly_stats = df.groupby('Month').agg({
                'Outcome': lambda x: (x == 'WIN').sum() / len(x) * 100 if len(x) > 0 else 0,
                'Month': 'count'
            }).rename(columns={'Month': 'Count', 'Outcome': 'Win_Rate'})
            if len(monthly_stats) > 0:
                monthly_stats['Win_Rate'].plot(kind='bar', color='coral')
                plt.title('Win Rate by Month', fontweight='bold')
                plt.ylabel('Win Rate (%)')
                plt.xlabel('Month')
                plt.xticks(rotation=45)
            
            # 9. Entry Price vs Success Rate
            plt.subplot(3, 3, 9)
            if 'Entry_Price' in df.columns and len(df) >= 5:
                try:
                    # Create price bins
                    df['Price_Bin'] = pd.qcut(df['Entry_Price'], q=min(5, len(df)), labels=False, duplicates='drop')
                    bin_labels = ['Very Low', 'Low', 'Medium', 'High', 'Very High']
                    df['Price_Bin_Label'] = df['Price_Bin'].map(lambda x: bin_labels[int(x)] if pd.notna(x) and int(x) < len(bin_labels) else 'Unknown')
                    
                    price_bin_stats = df.groupby('Price_Bin_Label').agg({
                        'Outcome': lambda x: (x == 'WIN').sum() / len(x) * 100 if len(x) > 0 else 0
                    }).round(2)
                    
                    if len(price_bin_stats) > 0:
                        price_bin_stats.plot(kind='bar', color='lightblue')
                        plt.title('Win Rate by Entry Price Range', fontweight='bold')
                        plt.ylabel('Win Rate (%)')
                        plt.xlabel('Price Range')
                        plt.xticks(rotation=45)
                except Exception as e:
                    plt.text(0.5, 0.5, f'Price analysis error:\n{str(e)[:50]}...', ha='center', va='center', transform=plt.gca().transAxes)
            
            plt.tight_layout()
            
            # Save the analysis
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"trade_analysis_{timestamp}.png"
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            print(f"✅ Analysis saved as: {filename}")
            
            plt.show()
            
            # Print summary statistics
            self.print_summary_stats(df)
            
        except Exception as e:
            logger.error(f"Error creating trade analysis: {e}")
            print(f"❌ Error creating trade analysis: {e}")
            
    def print_summary_stats(self, df):
        """Print summary statistics"""
        print("\n" + "="*50)
        print("📈 TRADE ANALYSIS SUMMARY")
        print("="*50)
        
        total_trades = len(df)
        wins = len(df[df['Outcome'] == 'WIN'])
        losses = len(df[df['Outcome'] == 'LOSS'])
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
        
        print(f"Total Trades: {total_trades}")
        print(f"Wins: {wins}")
        print(f"Losses: {losses}")
        print(f"Win Rate: {win_rate:.2f}%")
        
        if 'PnL' in df.columns:
            total_pnl = df['PnL'].sum()
            avg_win = df[df['PnL'] > 0]['PnL'].mean() if len(df[df['PnL'] > 0]) > 0 else 0
            avg_loss = df[df['PnL'] < 0]['PnL'].mean() if len(df[df['PnL'] < 0]) > 0 else 0
            
            print(f"Total PnL: ${total_pnl:.2f}")
            print(f"Average Win: ${avg_win:.2f}")
            print(f"Average Loss: ${avg_loss:.2f}")
            print(f"Profit Factor: {abs(avg_win / avg_loss):.2f}" if avg_loss != 0 else "N/A")
        
        if 'Hours_to_Hit' in df.columns:
            valid_hours = df[df['Hours_to_Hit'].notna()]['Hours_to_Hit']
            if len(valid_hours) > 0:
                print(f"Average Time to Hit: {valid_hours.mean():.2f} hours")
                print(f"Median Time to Hit: {valid_hours.median():.2f} hours")
        
        # Best and worst performing hours
        hourly_win_rate = df.groupby(df['Date'].dt.hour)['Outcome'].apply(
            lambda x: (x == 'WIN').sum() / len(x) * 100
        )
        
        if len(hourly_win_rate) > 0:
            best_hour = hourly_win_rate.idxmax()
            worst_hour = hourly_win_rate.idxmin()
            print(f"Best Trading Hour: {best_hour}:00 ({hourly_win_rate[best_hour]:.1f}% win rate)")
            print(f"Worst Trading Hour: {worst_hour}:00 ({hourly_win_rate[worst_hour]:.1f}% win rate)")
    
    def create_stop_loss_optimization_chart(self, csv_file: str):
        """
        Create a chart showing optimal stop loss percentages
        """
        try:
            df = pd.read_csv(csv_file)
            
            # Simulate different stop loss percentages
            sl_percentages = np.arange(2, 21, 1)  # 2% to 20%
            results = []
            
            for sl_pct in sl_percentages:
                # Calculate what would happen with this SL
                # This is a simplified simulation
                wins = len(df[df['Outcome'] == 'WIN'])
                total = len(df)
                win_rate = wins / total * 100 if total > 0 else 0
                
                # Estimate profit factor (this would need more sophisticated calculation)
                estimated_profit_factor = 1.5 * (win_rate / 100) / (1 - win_rate / 100) if win_rate < 100 else float('inf')
                
                results.append({
                    'SL_Percentage': sl_pct,
                    'Estimated_Win_Rate': win_rate,
                    'Estimated_Profit_Factor': min(estimated_profit_factor, 5)  # Cap at 5 for visualization
                })
            
            results_df = pd.DataFrame(results)
            
            # Create the chart
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
            
            # Win Rate vs SL
            ax1.plot(results_df['SL_Percentage'], results_df['Estimated_Win_Rate'], 'bo-', linewidth=2)
            ax1.set_xlabel('Stop Loss Percentage (%)')
            ax1.set_ylabel('Estimated Win Rate (%)')
            ax1.set_title('Win Rate vs Stop Loss Percentage', fontweight='bold')
            ax1.grid(True, alpha=0.3)
            
            # Profit Factor vs SL
            ax2.plot(results_df['SL_Percentage'], results_df['Estimated_Profit_Factor'], 'ro-', linewidth=2)
            ax2.axhline(y=1, color='black', linestyle='--', alpha=0.5, label='Breakeven')
            ax2.set_xlabel('Stop Loss Percentage (%)')
            ax2.set_ylabel('Estimated Profit Factor')
            ax2.set_title('Profit Factor vs Stop Loss Percentage', fontweight='bold')
            ax2.grid(True, alpha=0.3)
            ax2.legend()
            
            plt.tight_layout()
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"stop_loss_optimization_{timestamp}.png"
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            print(f"✅ Stop loss optimization chart saved as: {filename}")
            
            plt.show()
            
        except Exception as e:
            logger.error(f"Error creating stop loss optimization chart: {e}")


def main():
    """Main function"""
    print("📊 ADVANCED TRADE ANALYZER")
    print("=" * 50)
    
    analyzer = TradeAnalyzer()
    
    # Find CSV files
    csv_files = [f for f in os.listdir('.') if f.endswith('.csv') and ('analysis' in f.lower() or 'portfolio' in f.lower())]
    
    if not csv_files:
        print("❌ No CSV analysis files found in current directory")
        return
        
    print(f"\nFound CSV files:")
    for i, file in enumerate(csv_files, 1):
        print(f"{i}. {file}")
        
    try:
        file_idx = int(input(f"\nSelect CSV file (1-{len(csv_files)}): ")) - 1
        selected_file = csv_files[file_idx]
        
        print("\nAnalysis Options:")
        print("1. Complete Trade Pattern Analysis")
        print("2. Stop Loss Optimization Chart")
        print("3. Both")
        
        choice = input("\nSelect option (1, 2, or 3): ").strip()
        
        if choice in ['1', '3']:
            analyzer.analyze_trade_patterns(selected_file)
            
        if choice in ['2', '3']:
            analyzer.create_stop_loss_optimization_chart(selected_file)
            
    except (ValueError, IndexError):
        print("❌ Invalid selection")


if __name__ == "__main__":
    main()
