"""Concurrent portfolio calculator using position manager"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
import logging

from ..models import TradingSignal
from ..services import ProfitLossAnalyzer
from .position_manager import PositionManager, OpenPosition, ClosedPosition

logger = logging.getLogger(__name__)


class ConcurrentPortfolioCalculator:
    """Calculate portfolio performance with concurrent position management"""
    
    def __init__(self, analyzer: ProfitLossAnalyzer):
        self.analyzer = analyzer
    
    def calculate_concurrent_portfolio_performance(
        self, 
        signals: List[TradingSignal],
        stop_loss_pct: float,
        risk_reward_ratio: float,
        risk_per_trade_pct: float,
        initial_capital: float = 100000,
        move_sl_to_entry_pct: float = 3.0
    ) -> Dict:
        """
        Calculate portfolio performance with concurrent position management
        Uses the same efficient API calls as the original system
        """
        logger.info(f"Starting concurrent portfolio analysis with {len(signals)} signals")
        logger.info(f"Parameters: SL={stop_loss_pct}%, RR=1:{risk_reward_ratio}, Risk={risk_per_trade_pct}%, Move SL to entry at {move_sl_to_entry_pct}%")
        
        # Calculate target profit based on risk-reward ratio
        target_profit_pct = stop_loss_pct * risk_reward_ratio
        target_loss_pct = -stop_loss_pct
        
        # Update analyzer settings
        self.analyzer.settings.update_analysis_config(
            target_profit_pct=target_profit_pct,
            target_loss_pct=target_loss_pct
        )
        
        # Initialize position manager with trailing stop parameter
        position_manager = PositionManager(initial_capital, risk_per_trade_pct, move_sl_to_entry_pct)
        
        # Sort signals by timestamp
        sorted_signals = sorted(signals, key=lambda x: x.timestamp)
        
        # Process each signal individually using the original efficient method
        all_events = []
        processed_count = 0
        
        for i, signal in enumerate(sorted_signals):
            processed_count += 1
            logger.info(f"Processing signal {processed_count}/{len(sorted_signals)}: {signal.coin_name}")
            
            try:
                # Use the original analyzer to get limit fill and exit data efficiently
                result = self.analyzer.analyze_signal(signal)
                
                if result.first_hit in ['ERROR', 'SKIP', 'NO_FILL']:
                    logger.debug(f"Skipping {signal.symbol}: {result.first_hit}")
                    continue
                
                # Calculate risk amount based on current available capital
                risk_amount = position_manager.available_capital * (risk_per_trade_pct / 100)
                
                if risk_amount <= 0:
                    logger.warning(f"Insufficient capital for {signal.coin_name}")
                    continue
                
                # Simulate position opening
                entry_time = result.entry_fill_time if hasattr(result, 'entry_fill_time') and result.entry_fill_time else signal.timestamp
                entry_price = result.entry_fill_price if hasattr(result, 'entry_fill_price') and result.entry_fill_price else signal.entry_price
                
                # Create position
                position = OpenPosition(
                    signal=signal,
                    entry_fill_time=entry_time,
                    entry_fill_price=entry_price,
                    position_size=risk_amount / (entry_price * (stop_loss_pct / 100)),
                    risk_amount=risk_amount,
                    stop_loss_price=entry_price * (1 - stop_loss_pct / 100),
                    take_profit_price=entry_price * (1 + target_profit_pct / 100),
                    position_id=f"{signal.coin_name}_{entry_time.strftime('%Y%m%d_%H%M%S')}"
                )
                
                # Calculate P&L based on result
                if result.first_hit == 'PROFIT':
                    pnl = risk_amount * risk_reward_ratio
                    close_reason = 'PROFIT'
                elif result.first_hit == 'LOSS':
                    pnl = -risk_amount
                    close_reason = 'LOSS'
                else:
                    pnl = 0
                    close_reason = 'NEITHER'
                
                # Update position manager capital
                position_manager.available_capital -= risk_amount  # Allocate capital
                position_manager.current_capital += pnl  # Apply P&L
                position_manager.available_capital += risk_amount + pnl  # Return capital + P&L
                
                # Create closed position
                if result.hit_time:
                    close_time = result.hit_time
                else:
                    close_time = entry_time + timedelta(hours=result.hours_to_hit)
                
                closed_pos = ClosedPosition(
                    position=position,
                    close_time=close_time,
                    close_reason=close_reason,
                    pnl=pnl,
                    hours_held=result.hours_to_hit
                )
                
                position_manager.closed_positions.append(closed_pos)
                
                # Log events
                all_events.append({
                    'time': entry_time,
                    'type': 'ENTRY',
                    'symbol': signal.coin_name,
                    'price': entry_price,
                    'risk_amount': risk_amount,
                    'available_capital': position_manager.available_capital
                })
                
                if close_reason in ['PROFIT', 'LOSS']:
                    all_events.append({
                        'time': close_time,
                        'type': 'EXIT',
                        'symbol': signal.coin_name,
                        'reason': close_reason,
                        'pnl': pnl,
                        'hours_held': result.hours_to_hit,
                        'current_capital': position_manager.current_capital
                    })
                
                # Progress update
                if processed_count % 10 == 0:
                    logger.info(f"Processed {processed_count}/{len(sorted_signals)} signals. Current capital: ${position_manager.current_capital:.2f}")
                    
            except Exception as e:
                logger.error(f"Error processing signal {signal.coin_name}: {e}")
                continue
        
        # Get final summary
        final_summary = position_manager.get_portfolio_summary()
        
        # Add simulation details
        final_summary.update({
            'simulation_events': all_events,
            'settings': {
                'stop_loss_pct': stop_loss_pct,
                'target_profit_pct': target_profit_pct,
                'risk_reward_ratio': risk_reward_ratio,
                'risk_per_trade_pct': risk_per_trade_pct
            },
            'total_signals': len(signals),
            'simulation_start': sorted_signals[0].timestamp if sorted_signals else None,
            'simulation_end': sorted_signals[-1].timestamp if sorted_signals else None
        })
        
        logger.info(f"Analysis completed. Final capital: ${final_summary['current_capital']:.2f}")
        logger.info(f"Total return: {final_summary['total_return_pct']:.2f}%")
        
        return final_summary
    
    def _get_market_prices(self, current_time: datetime, signals: List[TradingSignal]) -> Dict[str, float]:
        """Get current market prices for all symbols - REMOVED FOR EFFICIENCY"""
        # This method was causing too many API calls
        # Instead, we'll use the progressive timeframe analysis like the original system
        return {}
    
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
                logger.info(f"Detected CSV format with columns: {required_cols}")
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
            
            # Clean and prepare data
            if 'timestamp_utc' in df.columns:
                df = df.dropna(subset=['timestamp_utc', 'coin'])
                df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'], utc=True)
                df = df.sort_values('timestamp_utc')
            else:
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