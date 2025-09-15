"""Main service for profit and loss analysis"""
import pandas as pd
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict
import logging
import os

from ..api import BinanceClient
from ..models import TradingSignal, AnalysisResult
from ..config import Settings
from ..utils import floor_to_timeframe, load_and_validate_csv, ensure_directory_exists, generate_output_filename

logger = logging.getLogger(__name__)


class ProfitLossAnalyzer:
    """Main service for analyzing profit and loss of trading signals"""
    
    def __init__(self, api_key: str = None, api_secret: str = None):
        """Initialize the analyzer with Binance client"""
        self.binance_client = BinanceClient(api_key, api_secret)
        self.settings = Settings()
    
    def analyze_signal(self, signal: TradingSignal) -> AnalysisResult:
        """Analyze a single trading signal for profit/loss outcomes"""
        try:
            logger.info(f"Analyzing {signal.symbol} | Entry: ${signal.entry_price:.4f}")
            
            analysis = self._analyze_progressive_timeframes(
                signal.symbol, 
                signal.timestamp, 
                signal.entry_price, 
                self.settings.ANALYSIS.target_profit_pct, 
                self.settings.ANALYSIS.target_loss_pct
            )
            
            # Determine loss_profit and hit_date based on analysis
            if analysis['first_hit'] == 'PROFIT':
                loss_profit = self.settings.ANALYSIS.target_profit_pct
                hit_date = analysis['hit_time'].strftime('%Y-%m-%d') if analysis['hit_time'] else None
            elif analysis['first_hit'] == 'LOSS':
                loss_profit = self.settings.ANALYSIS.target_loss_pct
                hit_date = analysis['hit_time'].strftime('%Y-%m-%d') if analysis['hit_time'] else None
            else:
                loss_profit = 0
                hit_date = None
            
            return AnalysisResult(
                signal=signal,
                first_hit=analysis['first_hit'],
                hit_time=analysis['hit_time'],
                hours_to_hit=analysis['hours_to_hit'],
                loss_profit=loss_profit,
                hit_date=hit_date
            )
            
        except Exception as e:
            logger.warning(f"Error analyzing signal {signal.symbol}: {e}")
            # Return a result indicating this symbol should be skipped
            return AnalysisResult(
                signal=signal,
                first_hit='SKIP',
                hit_time=None,
                hours_to_hit=0,
                loss_profit=0
            )
    
    def _analyze_progressive_timeframes(self, symbol: str, entry_dt: datetime, 
                                      limit_price: float, profit_pct: float, 
                                      loss_pct: float) -> Dict:
        """Analyze limit entry fill, then targets using progressive timeframes"""
        
        current_time = entry_dt
        max_end_time = min(
            entry_dt + timedelta(days=self.settings.ANALYSIS.max_days_ahead),
            datetime.now(timezone.utc)
        )
        
        entry_filled = False
        actual_entry_time = None
        actual_entry_price = limit_price  # Use limit price for SL/TP calculation
        
        # Calculate SL/TP targets based on limit price
        profit_target = limit_price * (1 + profit_pct / 100)
        loss_target = limit_price * (1 + loss_pct / 100)
        
        for tf_idx, timeframe in enumerate(self.settings.TIMEFRAMES):
            if current_time >= max_end_time:
                break
                
            interval = timeframe.interval
            minutes = timeframe.minutes
            max_candles = timeframe.max_candles
            
            aligned_start = floor_to_timeframe(current_time, minutes)
            
            if tf_idx == 0 and aligned_start > current_time:
                aligned_start = aligned_start - timedelta(minutes=minutes)
            
            df = self.binance_client.get_klines_for_timeframe(
                symbol, aligned_start, interval, max_candles + 5
            )
            
            if df is None or df.empty:
                continue
            
            future_df = df[df.index >= current_time].copy()
            if future_df.empty:
                current_time = aligned_start + timedelta(minutes=minutes * max_candles)
                continue
            
            if len(future_df) > max_candles:
                future_df = future_df.iloc[:max_candles]
            
            # Check each candle
            for timestamp, row in future_df.iterrows():
                high = row['high']
                low = row['low']
                
                # Step 1: Check for limit entry fill (if not already filled)
                if not entry_filled:
                    # For long positions: entry fills when market goes at or below limit price
                    if low <= limit_price:
                        entry_filled = True
                        actual_entry_time = timestamp
                        actual_entry_price = limit_price  # Assume filled at limit price
                        logger.info(f"  Limit entry filled at {timestamp} for {symbol} at ${limit_price}")
                        continue  # Move to next candle to start checking SL/TP
                
                # Step 2: Check for SL/TP (only after entry is filled)
                if entry_filled:
                    hours_elapsed = (timestamp - actual_entry_time).total_seconds() / 3600
                    
                    # Check profit target first (more conservative)
                    if high >= profit_target:
                        total_hours = (actual_entry_time - entry_dt).total_seconds() / 3600 + hours_elapsed
                        return {
                            'first_hit': 'PROFIT',
                            'hit_time': timestamp,
                            'hours_to_hit': round(total_hours, 2),
                            'entry_fill_time': actual_entry_time,
                            'entry_fill_price': actual_entry_price
                        }
                    
                    # Check stop loss
                    if low <= loss_target:
                        total_hours = (actual_entry_time - entry_dt).total_seconds() / 3600 + hours_elapsed
                        return {
                            'first_hit': 'LOSS',
                            'hit_time': timestamp,
                            'hours_to_hit': round(total_hours, 2),
                            'entry_fill_time': actual_entry_time,
                            'entry_fill_price': actual_entry_price
                        }
            
            last_candle_time = future_df.index[-1]
            current_time = last_candle_time + timedelta(minutes=minutes)
        
        # If we reach here, either entry never filled or SL/TP never hit
        total_hours = (current_time - entry_dt).total_seconds() / 3600
        
        if not entry_filled:
            return {
                'first_hit': 'NO_FILL',
                'hit_time': None,
                'hours_to_hit': round(total_hours, 2),
                'entry_fill_time': None,
                'entry_fill_price': None
            }
        else:
            return {
                'first_hit': 'NEITHER',
                'hit_time': None,
                'hours_to_hit': round(total_hours, 2),
                'entry_fill_time': actual_entry_time,
                'entry_fill_price': actual_entry_price
            }
    
    def process_csv_file(self, input_file: str, output_file: str) -> bool:
        """Process a single CSV file and analyze all signals"""
        try:
            df = load_and_validate_csv(input_file)
            if df is None:
                return False
            
            logger.info(f"Processing {len(df)} valid signals from {input_file}")
            
            results = []
            for index, row in df.iterrows():
                try:
                    signal = TradingSignal.from_csv_row(row)
                    result = self.analyze_signal(signal)
                    
                    if result.first_hit != 'ERROR':
                        results.append(result.to_dict())
                    
                except Exception as e:
                    logger.error(f"Error processing row {index}: {e}")
                    continue
            
            if results:
                output_df = pd.DataFrame(results)
                output_df.to_csv(output_file, index=False)
                logger.info(f"✅ Successfully analyzed {len(output_df)} signals to {output_file}")
                return True
            else:
                logger.error(f"No valid results to save from {input_file}!")
                return False
        
        except Exception as e:
            logger.error(f"Error processing {input_file}: {e}")
            return False
    
    def batch_process(self, input_folder: str, output_folder: str, output_prefix: str) -> Dict:
        """Process all CSV files in a folder"""
        from ..utils import find_csv_files
        
        csv_files = find_csv_files(input_folder)
        if not csv_files:
            return {'success': False, 'message': 'No CSV files found'}
        
        ensure_directory_exists(output_folder)
        
        logger.info(f"Found {len(csv_files)} CSV files to process")
        successful_files = 0
        
        for i, input_file in enumerate(csv_files, 1):
            output_filename = generate_output_filename(input_file, output_prefix)
            output_file = os.path.join(output_folder, output_filename)
            
            logger.info(f"[{i}/{len(csv_files)}] Processing: {os.path.basename(input_file)}")
            
            if self.process_csv_file(input_file, output_file):
                successful_files += 1
        
        return {
            'success': True,
            'total_files': len(csv_files),
            'successful_files': successful_files,
            'output_folder': output_folder
        }


# Import PortfolioCalculator here to avoid circular imports
from .portfolio import PortfolioCalculator