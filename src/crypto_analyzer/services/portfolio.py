"""Portfolio calculator for interactive analysis"""
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
import logging

from ..models import TradingSignal, AnalysisResult
from ..services import ProfitLossAnalyzer

logger = logging.getLogger(__name__)


class PortfolioCalculator:
    """Calculate portfolio performance based on user parameters"""
    
    def __init__(self, analyzer: ProfitLossAnalyzer):
        self.analyzer = analyzer
    
    def calculate_portfolio_performance(
        self, 
        signals: List[TradingSignal],
        stop_loss_pct: float,
        risk_reward_ratio: float,
        risk_per_trade_pct: float,
        initial_capital: float = 100000
    ) -> Dict:
        """
        Calculate overall portfolio performance
        
        Args:
            signals: List of trading signals to analyze
            stop_loss_pct: Stop loss percentage (e.g., 2 = 2%)
            risk_reward_ratio: Risk to reward ratio (e.g., 2 = 1:2)
            risk_per_trade_pct: Risk per trade as % of capital (e.g., 2 = 2%)
            initial_capital: Starting capital amount
        
        Returns:
            Dictionary with portfolio performance metrics
        """
        # Calculate target profit based on risk-reward ratio
        target_profit_pct = stop_loss_pct * risk_reward_ratio
        target_loss_pct = -stop_loss_pct  # Make it negative
        
        logger.info(f"Analyzing {len(signals)} signals with:")
        logger.info(f"  Stop Loss: {stop_loss_pct}%")
        logger.info(f"  Target Profit: {target_profit_pct}% (Risk:Reward = 1:{risk_reward_ratio})")
        logger.info(f"  Risk per trade: {risk_per_trade_pct}% of capital")
        
        # Update analyzer settings
        self.analyzer.settings.update_analysis_config(
            target_profit_pct=target_profit_pct,
            target_loss_pct=target_loss_pct
        )
        
        # Track portfolio metrics
        current_capital = initial_capital
        total_trades = 0
        winning_trades = 0
        losing_trades = 0
        neither_trades = 0
        total_pnl = 0
        trade_results = []
        
        for signal in signals:
            result = self.analyzer.analyze_signal(signal)
            
            if result.first_hit in ['ERROR', 'SKIP', 'NO_FILL']:
                logger.debug(f"Skipping {signal.symbol}: {result.first_hit}")
                continue
                
            total_trades += 1
            
            # Calculate position size based on risk per trade
            risk_amount = current_capital * (risk_per_trade_pct / 100)
            position_size = risk_amount / (stop_loss_pct / 100)  # Position size in USD
            
            # Calculate P&L for this trade
            if result.first_hit == 'PROFIT':
                pnl = risk_amount * risk_reward_ratio  # Gain = risk * reward ratio
                winning_trades += 1
                trade_outcome = "WIN"
            elif result.first_hit == 'LOSS':
                pnl = -risk_amount  # Loss = risk amount
                losing_trades += 1
                trade_outcome = "LOSS"
            else:
                pnl = 0  # No outcome within timeframe
                neither_trades += 1
                trade_outcome = "NEITHER"
            
            # Update capital
            current_capital += pnl
            total_pnl += pnl
            
            trade_results.append({
                'signal': signal,
                'result': result,
                'position_size': position_size,
                'pnl': pnl,
                'outcome': trade_outcome,
                'capital_after': current_capital
            })
        
        # Calculate performance metrics
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        total_return_pct = ((current_capital - initial_capital) / initial_capital) * 100
        
        # Calculate additional metrics
        winning_pnl = sum([t['pnl'] for t in trade_results if t['outcome'] == 'WIN'])
        losing_pnl = sum([t['pnl'] for t in trade_results if t['outcome'] == 'LOSS'])
        
        avg_win = winning_pnl / winning_trades if winning_trades > 0 else 0
        avg_loss = abs(losing_pnl) / losing_trades if losing_trades > 0 else 0
        
        # Add information about invalid symbols
        invalid_symbols_count = len(signals) - total_trades
        
        return {
            'initial_capital': initial_capital,
            'final_capital': current_capital,
            'total_pnl': total_pnl,
            'total_return_pct': total_return_pct,
            'total_trades': total_trades,
            'invalid_symbols_count': invalid_symbols_count,
            'total_signals': len(signals),
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'neither_trades': neither_trades,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': winning_pnl / abs(losing_pnl) if losing_pnl != 0 else float('inf'),
            'trade_results': trade_results,
            'settings': {
                'stop_loss_pct': stop_loss_pct,
                'target_profit_pct': target_profit_pct,
                'risk_reward_ratio': risk_reward_ratio,
                'risk_per_trade_pct': risk_per_trade_pct
            }
        }
    
    def filter_signals_by_date(
        self, 
        signals: List[TradingSignal], 
        from_date: datetime, 
        to_date: datetime
    ) -> List[TradingSignal]:
        """Filter signals by date range"""
        filtered = []
        for signal in signals:
            if from_date <= signal.timestamp <= to_date:
                filtered.append(signal)
        return filtered
    
    def load_signals_from_csv(self, csv_file: str) -> List[TradingSignal]:
        """Load signals from CSV file"""
        try:
            df = pd.read_csv(csv_file)
            
            # Check for your specific CSV format first
            if 'timestamp_utc' in df.columns and 'coin' in df.columns and 'entry' in df.columns:
                required_cols = ['timestamp_utc', 'coin', 'entry']
                logger.info(f"Detected your CSV format with columns: {required_cols}")
            # Check for standard format
            elif 'Timestamp' in df.columns and 'Coin_Name' in df.columns and 'CMP' in df.columns:
                required_cols = ['Timestamp', 'Coin_Name', 'CMP']
                logger.info(f"Detected standard CSV format with columns: {required_cols}")
            else:
                logger.error(f"Unsupported CSV format. Found columns: {list(df.columns)}")
                return []
            
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                logger.error(f"Missing required columns: {missing_cols}")
                return []
            
            # Clean and prepare data based on format
            if 'timestamp_utc' in df.columns:
                # Your format
                df = df.dropna(subset=['timestamp_utc', 'coin'])
                df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'], utc=True)
                df = df.sort_values('timestamp_utc')
            else:
                # Standard format
                df = df.dropna(subset=required_cols)
                df['Timestamp'] = pd.to_datetime(df['Timestamp'], utc=True)
                df = df.sort_values('Timestamp')
            
            signals = []
            for _, row in df.iterrows():
                try:
                    signal = TradingSignal.from_csv_row(row)
                    signals.append(signal)
                except Exception as e:
                    logger.warning(f"Error processing row: {e}")
                    continue
            
            logger.info(f"Successfully loaded {len(signals)} valid signals from {len(df)} rows")
            return signals
            
        except Exception as e:
            logger.error(f"Error loading CSV file: {e}")
            return []