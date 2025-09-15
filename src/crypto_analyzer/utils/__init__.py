"""Utility functions for the crypto analyzer"""
from datetime import datetime, timezone, timedelta
from typing import Optional
import pandas as pd
import os
import glob
import logging

logger = logging.getLogger(__name__)


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


def validate_csv_file(df: pd.DataFrame, required_columns: list) -> tuple[bool, list]:
    """Validate CSV file has required columns"""
    missing_cols = [col for col in required_columns if col not in df.columns]
    return len(missing_cols) == 0, missing_cols


def load_and_validate_csv(file_path: str) -> Optional[pd.DataFrame]:
    """Load and validate CSV file - handles multiple CSV formats"""
    try:
        df = pd.read_csv(file_path)
        
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
            logger.error("Expected either: timestamp_utc, coin, entry OR Timestamp, Coin_Name, CMP")
            return None
        
        is_valid, missing_cols = validate_csv_file(df, required_cols)
        if not is_valid:
            logger.error(f"Missing required columns in {file_path}: {missing_cols}")
            return None
        
        # Clean and prepare data based on format
        if 'timestamp_utc' in df.columns:
            # Your format
            df = df.dropna(subset=['timestamp_utc', 'coin'])
            # Don't drop rows with empty 'entry' as we handle that in TradingSignal.from_csv_row
            df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'], utc=True)
            df = df.sort_values('timestamp_utc')
        else:
            # Standard format
            df = df.dropna(subset=required_cols)
            df['Timestamp'] = pd.to_datetime(df['Timestamp'], utc=True)
            df = df.sort_values('Timestamp')
        
        logger.info(f"Loaded {len(df)} rows from {file_path}")
        return df
        
    except Exception as e:
        logger.error(f"Error loading CSV file {file_path}: {e}")
        return None


def find_csv_files(folder_path: str) -> list:
    """Find all CSV files in a folder"""
    if not os.path.exists(folder_path):
        logger.error(f"Folder '{folder_path}' not found!")
        return []
    
    csv_pattern = os.path.join(folder_path, "*.csv")
    csv_files = glob.glob(csv_pattern)
    
    if not csv_files:
        logger.warning(f"No CSV files found in '{folder_path}' folder!")
    
    return csv_files


def ensure_directory_exists(directory_path: str) -> None:
    """Ensure directory exists, create if it doesn't"""
    os.makedirs(directory_path, exist_ok=True)


def generate_output_filename(input_filename: str, prefix: str) -> str:
    """Generate output filename from input filename"""
    base_name = os.path.basename(input_filename)
    
    if "_" in base_name:
        parts = base_name.replace('.csv', '').split('_')
        if len(parts) >= 2:
            month_year = parts[-1]
        else:
            month_year = base_name.replace('.csv', '')
    else:
        month_year = base_name.replace('.csv', '')
    
    return f"{prefix}{month_year}.csv"


def setup_logging(level: str = "INFO") -> None:
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('crypto_analyzer.log')
        ]
    )