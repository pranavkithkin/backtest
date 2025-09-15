"""API client for interacting with Binance"""
import time
import pandas as pd
import os
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Set
from binance.client import Client
import logging

from ..config import Settings
from ..models import PriceData

logger = logging.getLogger(__name__)


class BinanceClient:
    """Wrapper for Binance API client with retry logic and rate limiting"""
    
    def __init__(self, api_key: str = None, api_secret: str = None):
        """Initialize Binance client"""
        # Use provided credentials or try to load from environment
        if api_key and api_secret:
            self.client = Client(api_key, api_secret)
        else:
            # Try to load from environment variables
            env_api_key = os.getenv('BINANCE_API_KEY')
            env_api_secret = os.getenv('BINANCE_API_SECRET')
            
            if env_api_key and env_api_secret:
                self.client = Client(env_api_key, env_api_secret)
                logger.info("Using Binance API credentials from environment variables")
            else:
                # Initialize without credentials (public endpoints only)
                self.client = Client()
                logger.warning("No API credentials provided - using public endpoints only")
        
        self.settings = Settings()
        
        # Cache for invalid symbols to avoid retrying them
        self.invalid_symbols: Set[str] = set()
        self.valid_symbols: Set[str] = set()
    
    def get_klines_for_timeframe(self, symbol: str, start_dt: datetime, 
                                interval: str, limit: int) -> Optional[pd.DataFrame]:
        """Fetch klines for a specific timeframe with retry logic"""
        # Check if symbol is known to be invalid
        if symbol in self.invalid_symbols:
            logger.debug(f"Skipping known invalid symbol: {symbol}")
            return None
        
        for attempt in range(self.settings.API.max_retries):
            try:
                klines = self.client.futures_klines(
                    symbol=symbol,
                    interval=interval,
                    startTime=self._to_ms(start_dt),
                    limit=limit
                )
                
                time.sleep(self.settings.API.request_sleep)
                
                if not klines:
                    return None
                
                # Cache as valid symbol
                self.valid_symbols.add(symbol)
                return self._process_klines(klines)
                
            except Exception as e:
                error_message = str(e)
                
                # Check if this is an invalid symbol error
                if "Invalid symbol" in error_message or "code=-1121" in error_message:
                    logger.warning(f"Invalid symbol detected: {symbol}")
                    self.invalid_symbols.add(symbol)
                    return None
                
                # For other errors, continue with retry logic
                logger.warning(f"Attempt {attempt + 1} failed for {symbol}: {e}")
                if attempt < self.settings.API.max_retries - 1:
                    time.sleep(self.settings.API.retry_sleep)
                else:
                    logger.error(f"All attempts failed for {symbol}")
                    return None
    
    def _process_klines(self, klines: List) -> pd.DataFrame:
        """Process raw klines data into DataFrame"""
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
    
    def _to_ms(self, dt: datetime) -> int:
        """Convert datetime to milliseconds timestamp"""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return int(dt.timestamp() * 1000)
    
    def test_connection(self) -> bool:
        """Test if the API connection is working"""
        try:
            self.client.ping()
            return True
        except Exception as e:
            logger.error(f"API connection test failed: {e}")
            return False