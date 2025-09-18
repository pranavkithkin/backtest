#!/usr/bin/env python3
"""
Advanced Trade Visualizer - TradingView Style Charts
Creates detailed charts for each trade showing entry, SL, TP, and actual price movement
"""
import sys
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from datetime import datetime, timedelta
import os

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from crypto_analyzer import BinanceClient, TradingSignal
import logging

logger = logging.getLogger(__name__)

class TradeVisualizer:
    """Creates TradingView-style charts for trade analysis"""
    
    def __init__(self):
        self.binance_client = BinanceClient()
        
    def create_trade_chart(self, signal: TradingSignal, stop_loss_pct: float = 10.0, 
                          risk_reward_ratio: float = 1.5, days_ahead: int = 30) -> go.Figure:
        """Create a detailed chart for a single trade"""
        
        # Calculate SL and TP levels
        entry_price = signal.entry_price
        stop_loss_price = entry_price * (1 - stop_loss_pct / 100)
        take_profit_price = entry_price * (1 + (stop_loss_pct * risk_reward_ratio) / 100)
        
        # Get historical data
        start_time = signal.timestamp - timedelta(days=5)  # 5 days before signal
        end_time = signal.timestamp + timedelta(days=days_ahead)  # Days after signal
        
        # Fetch price data using multiple timeframes
        price_data = self._get_comprehensive_price_data(signal.symbol, start_time, end_time)
        
        if price_data is None or price_data.empty:
            logger.error(f"No price data available for {signal.symbol}")
            return None
        
        # Create main chart
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.1,
            subplot_titles=(f'{signal.coin_name} Trade Analysis', 'Volume'),
            row_width=[0.7, 0.3]
        )
        
        # Candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=price_data.index,
                open=price_data['open'],
                high=price_data['high'],
                low=price_data['low'],
                close=price_data['close'],
                name=f'{signal.coin_name} Price',
                increasing_line_color='#00ff88',
                decreasing_line_color='#ff4444'
            ),
            row=1, col=1
        )
        
        # Volume bars
        colors = ['green' if close >= open else 'red' 
                 for close, open in zip(price_data['close'], price_data['open'])]
        
        fig.add_trace(
            go.Bar(
                x=price_data.index,
                y=price_data.get('volume', [0] * len(price_data)),
                name='Volume',
                marker_color=colors,
                opacity=0.6
            ),
            row=2, col=1
        )
        
        # Add signal entry point
        fig.add_hline(
            y=entry_price,
            line_dash="solid",
            line_color="blue",
            line_width=3,
            annotation_text=f"Entry: ${entry_price:.4f}",
            annotation_position="top right",
            row=1, col=1
        )
        
        # Add stop loss line
        fig.add_hline(
            y=stop_loss_price,
            line_dash="dash",
            line_color="red",
            line_width=2,
            annotation_text=f"Stop Loss: ${stop_loss_price:.4f} (-{stop_loss_pct}%)",
            annotation_position="bottom right",
            row=1, col=1
        )
        
        # Add take profit line
        fig.add_hline(
            y=take_profit_price,
            line_dash="dash",
            line_color="green",
            line_width=2,
            annotation_text=f"Take Profit: ${take_profit_price:.4f} (+{stop_loss_pct * risk_reward_ratio:.1f}%)",
            annotation_position="top right",
            row=1, col=1
        )
        
        # Add signal timestamp vertical line
        fig.add_vline(
            x=signal.timestamp,
            line_dash="dot",
            line_color="yellow",
            line_width=2,
            annotation_text=f"Signal Time: {signal.timestamp.strftime('%Y-%m-%d %H:%M')}",
            annotation_position="top",
            row=1, col=1
        )
        
        # Analyze what actually happened
        trade_result = self._analyze_trade_outcome(price_data, signal.timestamp, 
                                                 entry_price, stop_loss_price, take_profit_price)
        
        # Add outcome markers
        if trade_result['outcome'] == 'PROFIT':
            fig.add_scatter(
                x=[trade_result['hit_time']],
                y=[take_profit_price],
                mode='markers',
                marker=dict(color='green', size=15, symbol='triangle-up'),
                name='Take Profit Hit',
                row=1, col=1
            )
        elif trade_result['outcome'] == 'LOSS':
            fig.add_scatter(
                x=[trade_result['hit_time']],
                y=[stop_loss_price],
                mode='markers',
                marker=dict(color='red', size=15, symbol='triangle-down'),
                name='Stop Loss Hit',
                row=1, col=1
            )
        
        # Styling
        fig.update_layout(
            title=f'{signal.coin_name} Trade Analysis - {signal.timestamp.strftime("%Y-%m-%d %H:%M")}',
            xaxis_title='Time',
            yaxis_title='Price (USDT)',
            template='plotly_dark',
            height=800,
            showlegend=True,
            annotations=[
                dict(
                    x=0.02, y=0.98,
                    xref="paper", yref="paper",
                    text=f"<b>Trade Details:</b><br>"
                         f"Entry: ${entry_price:.4f}<br>"
                         f"Stop Loss: ${stop_loss_price:.4f} (-{stop_loss_pct}%)<br>"
                         f"Take Profit: ${take_profit_price:.4f} (+{stop_loss_pct * risk_reward_ratio:.1f}%)<br>"
                         f"Risk:Reward = 1:{risk_reward_ratio}<br>"
                         f"<b>Outcome: {trade_result['outcome']}</b><br>"
                         f"Hours to hit: {trade_result['hours_to_hit']:.1f}",
                    showarrow=False,
                    bgcolor="rgba(0,0,0,0.8)",
                    bordercolor="white",
                    borderwidth=1,
                    font=dict(color="white", size=12)
                )
            ]
        )
        
        # Update axes
        fig.update_xaxes(rangeslider_visible=False)
        fig.update_yaxes(title_text="Price (USDT)", row=1, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1)
        
        return fig
    
    def _get_comprehensive_price_data(self, symbol: str, start_time: datetime, end_time: datetime) -> pd.DataFrame:
        """Get comprehensive price data using multiple timeframes"""
        try:
            # Try different intervals based on time range
            time_diff = (end_time - start_time).total_seconds() / 3600  # hours
            
            if time_diff <= 24:  # Less than 1 day
                interval = '5m'
                limit = 288  # 24 hours * 12 (5-min intervals)
            elif time_diff <= 168:  # Less than 1 week  
                interval = '1h'
                limit = 168
            else:  # More than 1 week
                interval = '4h'
                limit = 180
            
            # Get klines data
            df = self.binance_client.get_klines_for_timeframe(
                symbol=symbol,
                start_dt=start_time,
                interval=interval,
                limit=limit
            )
            
            if df is None or df.empty:
                # Try with daily data as fallback
                df = self.binance_client.get_klines_for_timeframe(
                    symbol=symbol,
                    start_dt=start_time,
                    interval='1d',
                    limit=60
                )
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting price data for {symbol}: {e}")
            return None
    
    def _analyze_trade_outcome(self, price_data: pd.DataFrame, signal_time: datetime,
                             entry_price: float, stop_loss_price: float, 
                             take_profit_price: float) -> dict:
        """Analyze what actually happened with the trade"""
        
        # Filter data after signal time
        future_data = price_data[price_data.index >= signal_time]
        
        if future_data.empty:
            return {
                'outcome': 'NO_DATA',
                'hit_time': None,
                'hours_to_hit': 0
            }
        
        # Check each candle for SL/TP hits
        for timestamp, row in future_data.iterrows():
            high = row['high']
            low = row['low']
            
            hours_elapsed = (timestamp - signal_time).total_seconds() / 3600
            
            # Check for take profit first (more conservative)
            if high >= take_profit_price:
                return {
                    'outcome': 'PROFIT',
                    'hit_time': timestamp,
                    'hours_to_hit': hours_elapsed
                }
            
            # Check for stop loss
            if low <= stop_loss_price:
                return {
                    'outcome': 'LOSS',
                    'hit_time': timestamp,
                    'hours_to_hit': hours_elapsed
                }
        
        # Neither hit within available data
        last_time = future_data.index[-1]
        hours_elapsed = (last_time - signal_time).total_seconds() / 3600
        
        return {
            'outcome': 'NEITHER',
            'hit_time': last_time,
            'hours_to_hit': hours_elapsed
        }
    
    def create_portfolio_summary_chart(self, trades_df: pd.DataFrame) -> go.Figure:
        """Create a summary chart showing all trades performance"""
        
        # Calculate cumulative P&L
        trades_df['Cumulative_PnL'] = trades_df['PnL'].cumsum()
        trades_df['Trade_Number'] = range(1, len(trades_df) + 1)
        
        # Create summary chart
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            subplot_titles=('Cumulative P&L', 'Individual Trade P&L', 'Risk Amount per Trade'),
            vertical_spacing=0.08
        )
        
        # Cumulative P&L
        fig.add_trace(
            go.Scatter(
                x=trades_df['Trade_Number'],
                y=trades_df['Cumulative_PnL'],
                mode='lines+markers',
                name='Cumulative P&L',
                line=dict(color='blue', width=3)
            ),
            row=1, col=1
        )
        
        # Individual trade P&L
        colors = ['green' if pnl > 0 else 'red' for pnl in trades_df['PnL']]
        fig.add_trace(
            go.Bar(
                x=trades_df['Trade_Number'],
                y=trades_df['PnL'],
                name='Trade P&L',
                marker_color=colors
            ),
            row=2, col=1
        )
        
        # Risk amount per trade
        fig.add_trace(
            go.Scatter(
                x=trades_df['Trade_Number'],
                y=trades_df['Risk_Amount'],
                mode='lines+markers',
                name='Risk Amount',
                line=dict(color='orange', width=2)
            ),
            row=3, col=1
        )
        
        fig.update_layout(
            title='Portfolio Performance Summary',
            template='plotly_dark',
            height=900,
            showlegend=True
        )
        
        return fig

def main():
    """Main function to create trade visualizations"""
    print("🎯 ADVANCED TRADE VISUALIZER")
    print("="*60)
    print("Creates TradingView-style charts for trade analysis")
    print("="*60)
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Load your signals
        print("\n📊 Loading signals from CSV...")
        df = pd.read_csv('signals_last12months.csv')
        
        # Convert to TradingSignal objects
        signals = []
        for _, row in df.iterrows():
            try:
                signal = TradingSignal.from_csv_row(row)
                signals.append(signal)
            except Exception as e:
                continue
        
        print(f"✅ Loaded {len(signals)} signals")
        
        # Initialize visualizer
        visualizer = TradeVisualizer()
        
        # Get user preferences
        print("\n⚙️ VISUALIZATION SETTINGS:")
        num_charts = int(input("How many charts to create (1-20): ") or "5")
        stop_loss_pct = float(input("Stop Loss percentage (default 10%): ") or "10")
        risk_reward_ratio = float(input("Risk:Reward ratio (default 1.5): ") or "1.5")
        days_ahead = int(input("Days to analyze after signal (default 30): ") or "30")
        
        print(f"\n🔄 Creating {num_charts} detailed trade charts...")
        
        # Create charts for first N signals
        created_charts = 0
        for i, signal in enumerate(signals[:num_charts * 2]):  # Try more in case some fail
            if created_charts >= num_charts:
                break
                
            try:
                print(f"Creating chart {created_charts + 1}/{num_charts}: {signal.coin_name}")
                
                fig = visualizer.create_trade_chart(
                    signal=signal,
                    stop_loss_pct=stop_loss_pct,
                    risk_reward_ratio=risk_reward_ratio,
                    days_ahead=days_ahead
                )
                
                if fig is not None:
                    # Save chart
                    filename = f"trade_chart_{signal.symbol}_{signal.timestamp.strftime('%Y%m%d_%H%M%S')}.html"
                    fig.write_html(filename)
                    print(f"✅ Saved: {filename}")
                    created_charts += 1
                else:
                    print(f"⚠️ Skipped {signal.coin_name} (no data)")
                    
            except Exception as e:
                print(f"❌ Error creating chart for {signal.coin_name}: {e}")
                continue
        
        # Load trade results if available
        csv_files = [f for f in os.listdir('.') if f.startswith('concurrent_portfolio_analysis_') and f.endswith('.csv')]
        if csv_files:
            latest_csv = max(csv_files)
            print(f"\n📈 Creating portfolio summary from {latest_csv}...")
            
            trades_df = pd.read_csv(latest_csv)
            summary_fig = visualizer.create_portfolio_summary_chart(trades_df)
            summary_filename = f"portfolio_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            summary_fig.write_html(summary_filename)
            print(f"✅ Portfolio summary saved: {summary_filename}")
        
        print(f"\n🎉 Created {created_charts} trade visualization charts!")
        print("📂 Open the .html files in your browser to view the interactive charts")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error(f"Visualization error: {e}")

if __name__ == "__main__":
    main()