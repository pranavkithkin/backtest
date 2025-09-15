import time
import pandas as pd
import os
import glob
from datetime import datetime, timezone, timedelta
from binance.client import Client
import logging

# Configuration
INPUT_FOLDER = "rose_long_signals_with_prices"  # Folder containing signals with entry prices
OUTPUT_FOLDER = "profit_loss_analysis_30_100"  # Output folder for analyzed files
OUTPUT_PREFIX = "profit_loss_analysis_"  # Prefix for output files

# Analysis parameters
TARGET_PROFIT_PCT = 100   # Target profit percentage
TARGET_LOSS_PCT = -30     # Target loss percentage (negative)
MAX_DAYS_AHEAD = 365       # Maximum days to look ahead from entry

# Progressive timeframe strategy
TIMEFRAMES = [
    {'interval': Client.KLINE_INTERVAL_1MINUTE, 'minutes': 1, 'max_candles': 5},
    {'interval': Client.KLINE_INTERVAL_5MINUTE, 'minutes': 5, 'max_candles': 3},
    {'interval': Client.KLINE_INTERVAL_15MINUTE, 'minutes': 15, 'max_candles': 4},
    {'interval': Client.KLINE_INTERVAL_1HOUR, 'minutes': 60, 'max_candles': 24},
    {'interval': Client.KLINE_INTERVAL_4HOUR, 'minutes': 240, 'max_candles': 18},
    {'interval': Client.KLINE_INTERVAL_1DAY, 'minutes': 1440, 'max_candles': 30},
]

# API settings
REQUEST_SLEEP = 0.2
MAX_RETRIES = 3
RETRY_SLEEP = 1.5

# Initialize Binance client
client = Client()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_symbol(coin: str) -> str:
    """Map coin to Binance USDT futures symbol"""
    return f"{coin.upper()}USDT"

def to_ms(dt: datetime) -> int:
    """Convert datetime to milliseconds timestamp"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return int(dt.timestamp() * 1000)

def floor_to_timeframe(dt: datetime, minutes: int) -> datetime:
    """Floor datetime to the start of timeframe boundary"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    
    dt = dt.replace(second=0, microsecond=0)
    
    if minutes == 1:
        return dt
    elif minutes == 5:
        return dt.replace(minute=(dt.minute // 5) * 5)
    elif minutes == 15:
        return dt.replace(minute=(dt.minute // 15) * 15)
    elif minutes == 60:
        return dt.replace(minute=0)
    elif minutes == 240:
        return dt.replace(minute=0, hour=(dt.hour // 4) * 4)
    elif minutes == 1440:
        return dt.replace(minute=0, hour=0)
    else:
        return dt

def get_klines_for_timeframe(symbol: str, start_dt: datetime, interval: str, limit: int) -> pd.DataFrame:
    """Fetch klines for a specific timeframe"""
    for attempt in range(MAX_RETRIES):
        try:
            klines = client.futures_klines(
                symbol=symbol,
                interval=interval,
                startTime=to_ms(start_dt),
                limit=limit
            )
            
            time.sleep(REQUEST_SLEEP)
            
            if not klines:
                return None
            
            columns = [
                'open_time', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_volume', 'taker_buy_quote_volume', 'ignore'
            ]
            
            df = pd.DataFrame(klines, columns=columns)
            df['timestamp'] = pd.to_datetime(df['open_time'], unit='ms', utc=True)
            df = df.set_index('timestamp')
            
            for col in ['open', 'high', 'low', 'close']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            return df[['open', 'high', 'low', 'close']]
            
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_SLEEP)
            else:
                return None

def analyze_progressive_timeframes(symbol: str, entry_dt: datetime, entry_price: float, 
                                 profit_pct: float, loss_pct: float) -> dict:
    """Analyze targets using progressive timeframes"""
    profit_target = entry_price * (1 + profit_pct / 100)
    loss_target = entry_price * (1 + loss_pct / 100)
    
    current_time = entry_dt
    max_end_time = min(
        entry_dt + timedelta(days=MAX_DAYS_AHEAD),
        datetime.now(timezone.utc)
    )
    
    for tf_idx, timeframe in enumerate(TIMEFRAMES):
        if current_time >= max_end_time:
            break
            
        interval = timeframe['interval']
        minutes = timeframe['minutes']
        max_candles = timeframe['max_candles']
        
        aligned_start = floor_to_timeframe(current_time, minutes)
        
        if tf_idx == 0 and aligned_start > current_time:
            aligned_start = aligned_start - timedelta(minutes=minutes)
        
        df = get_klines_for_timeframe(symbol, aligned_start, interval, max_candles + 5)
        
        if df is None or df.empty:
            continue
        
        future_df = df[df.index >= current_time].copy()
        if future_df.empty:
            current_time = aligned_start + timedelta(minutes=minutes * max_candles)
            continue
        
        if len(future_df) > max_candles:
            future_df = future_df.iloc[:max_candles]
        
        for timestamp, row in future_df.iterrows():
            high = row['high']
            low = row['low']
            
            hours_elapsed = (timestamp - entry_dt).total_seconds() / 3600
            
            if high >= profit_target:
                return {
                    'first_hit': 'PROFIT',
                    'hit_time': timestamp,
                    'hours_to_hit': round(hours_elapsed, 2)
                }
            
            if low <= loss_target:
                return {
                    'first_hit': 'LOSS',
                    'hit_time': timestamp,
                    'hours_to_hit': round(hours_elapsed, 2)
                }
        
        last_candle_time = future_df.index[-1]
        current_time = last_candle_time + timedelta(minutes=minutes)
    
    total_hours = (current_time - entry_dt).total_seconds() / 3600
    return {
        'first_hit': 'NEITHER',
        'hit_time': None,
        'hours_to_hit': round(total_hours, 2)
    }

def process_csv_file(input_file: str, output_file: str) -> bool:
    """Process a single CSV file and analyze profit/loss"""
    try:
        df = pd.read_csv(input_file)
        logger.info(f"Loaded {len(df)} signals from {os.path.basename(input_file)}")
        
        required_cols = ['Timestamp', 'Coin_Name', 'CMP']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            logger.error(f"Missing required columns in {input_file}: {missing_cols}")
            return False
        
        df = df.dropna(subset=required_cols)
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], utc=True)
        df = df.sort_values('Timestamp')
        
        logger.info(f"Processing {len(df)} valid signals from {os.path.basename(input_file)}...")
        
        results = []
        
        for index, row in df.iterrows():
            try:
                timestamp = row['Timestamp']
                coin = row['Coin_Name'].strip().upper()
                entry_price = float(row['CMP'])
                symbol = get_symbol(coin)
                
                logger.info(f"  [{index + 1}/{len(df)}] Analyzing {symbol} | Entry: ${entry_price:.4f}")
                
                analysis = analyze_progressive_timeframes(
                    symbol, timestamp, entry_price, TARGET_PROFIT_PCT, TARGET_LOSS_PCT
                )
                
                if analysis['first_hit'] == 'PROFIT':
                    loss_profit = TARGET_PROFIT_PCT
                    hit_date = analysis['hit_time'].strftime('%Y-%m-%d') if analysis['hit_time'] else None
                elif analysis['first_hit'] == 'LOSS':
                    loss_profit = TARGET_LOSS_PCT
                    hit_date = analysis['hit_time'].strftime('%Y-%m-%d') if analysis['hit_time'] else None
                else:
                    loss_profit = 0
                    hit_date = None
                
                result = {
                    'Date': row.get('Date', timestamp.strftime('%Y-%m-%d')),
                    'Time': row.get('Time', timestamp.strftime('%H:%M:%S')),
                    'Coin_Name': coin,
                    'Entry_Price': entry_price,
                    'Hit_Date': hit_date,
                    'Loss_Profit': loss_profit,
                    'Hours_to_Hit': analysis['hours_to_hit']
                }
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"  Error processing row {index}: {e}")
                continue
        
        output_df = pd.DataFrame(results)
        
        if not output_df.empty:
            output_df.to_csv(output_file, index=False)
            logger.info(f"✅ Successfully analyzed {len(output_df)} signals to {os.path.basename(output_file)}")
            return True
        else:
            logger.error(f"No valid results to save from {input_file}!")
            return False
    
    except Exception as e:
        logger.error(f"Error processing {input_file}: {e}")
        return False

def main():
    logger.info("Starting profit/loss analysis for files in folder...")
    logger.info(f"Target: +{TARGET_PROFIT_PCT}% vs {TARGET_LOSS_PCT}%")
    
    try:
        if not os.path.exists(INPUT_FOLDER):
            logger.error(f"Input folder '{INPUT_FOLDER}' not found!")
            return
        
        os.makedirs(OUTPUT_FOLDER, exist_ok=True)
        
        csv_pattern = os.path.join(INPUT_FOLDER, "*.csv")
        csv_files = glob.glob(csv_pattern)
        
        if not csv_files:
            logger.error(f"No CSV files found in '{INPUT_FOLDER}' folder!")
            return
        
        logger.info(f"Found {len(csv_files)} CSV files to process:")
        for file in csv_files:
            logger.info(f"  - {os.path.basename(file)}")
        
        print("="*70)
        
        successful_files = 0
        
        for i, input_file in enumerate(csv_files, 1):
            base_name = os.path.basename(input_file)
            
            if "_" in base_name:
                parts = base_name.replace('.csv', '').split('_')
                if len(parts) >= 2:
                    month_year = parts[-1]
                else:
                    month_year = base_name.replace('.csv', '')
            else:
                month_year = base_name.replace('.csv', '')
            
            output_name = f"{OUTPUT_PREFIX}{month_year}.csv"
            output_file = os.path.join(OUTPUT_FOLDER, output_name)
            
            logger.info(f"\n[{i}/{len(csv_files)}] Processing: {base_name}")
            logger.info(f"Output: {output_name}")
            
            if process_csv_file(input_file, output_file):
                successful_files += 1
        
        print("\n" + "="*70)
        logger.info(f"📊 SUMMARY:")
        logger.info(f"Files processed successfully: {successful_files}/{len(csv_files)}")
        logger.info(f"Output folder: {OUTPUT_FOLDER}/")
        
        if successful_files > 0:
            logger.info(f"🎉 Processing completed! Check '{OUTPUT_FOLDER}/' folder for results.")
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()