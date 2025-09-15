"""Configuration settings for the crypto analyzer"""
from dataclasses import dataclass
from typing import Dict, List
from binance.client import Client


@dataclass
class TimeframeConfig:
    """Configuration for a single timeframe"""
    interval: str
    minutes: int
    max_candles: int


@dataclass
class AnalysisConfig:
    """Configuration for analysis parameters"""
    target_profit_pct: float = 100.0
    target_loss_pct: float = -30.0
    max_days_ahead: int = 365


@dataclass
class APIConfig:
    """Configuration for API settings"""
    request_sleep: float = 0.2
    max_retries: int = 3
    retry_sleep: float = 1.5


class Settings:
    """Main settings class"""
    
    # Default timeframes for progressive analysis
    TIMEFRAMES = [
        TimeframeConfig(Client.KLINE_INTERVAL_1MINUTE, 1, 5),
        TimeframeConfig(Client.KLINE_INTERVAL_5MINUTE, 5, 3),
        TimeframeConfig(Client.KLINE_INTERVAL_15MINUTE, 15, 4),
        TimeframeConfig(Client.KLINE_INTERVAL_1HOUR, 60, 24),
        TimeframeConfig(Client.KLINE_INTERVAL_4HOUR, 240, 18),
        TimeframeConfig(Client.KLINE_INTERVAL_1DAY, 1440, 30),
    ]
    
    # Default analysis parameters
    ANALYSIS = AnalysisConfig()
    
    # Default API settings
    API = APIConfig()
    
    # Default folders
    INPUT_FOLDER = "rose_long_signals_with_prices"
    OUTPUT_FOLDER = "profit_loss_analysis_30_100"
    OUTPUT_PREFIX = "profit_loss_analysis_"
    
    @classmethod
    def update_analysis_config(cls, **kwargs):
        """Update analysis configuration"""
        for key, value in kwargs.items():
            if hasattr(cls.ANALYSIS, key):
                setattr(cls.ANALYSIS, key, value)
    
    @classmethod
    def update_folders(cls, input_folder: str = None, output_folder: str = None, output_prefix: str = None):
        """Update folder configurations"""
        if input_folder:
            cls.INPUT_FOLDER = input_folder
        if output_folder:
            cls.OUTPUT_FOLDER = output_folder
        if output_prefix:
            cls.OUTPUT_PREFIX = output_prefix