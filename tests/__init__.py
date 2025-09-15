"""Test configuration and fixtures"""
import pytest
import pandas as pd
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from crypto_analyzer.models import TradingSignal, AnalysisResult
from crypto_analyzer.config import Settings


@pytest.fixture
def sample_trading_signal():
    """Create a sample trading signal for testing"""
    return TradingSignal(
        timestamp=datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        coin_name="BTC",
        entry_price=50000.0,
        date="2023-01-01",
        time="12:00:00"
    )


@pytest.fixture
def sample_csv_data():
    """Create sample CSV data for testing"""
    return pd.DataFrame({
        'Timestamp': ['2023-01-01 12:00:00+00:00', '2023-01-02 13:00:00+00:00'],
        'Coin_Name': ['BTC', 'ETH'],
        'CMP': [50000.0, 2000.0],
        'Date': ['2023-01-01', '2023-01-02'],
        'Time': ['12:00:00', '13:00:00']
    })


@pytest.fixture
def mock_binance_client():
    """Create a mock Binance client for testing"""
    client = Mock()
    client.test_connection.return_value = True
    client.get_klines_for_timeframe.return_value = pd.DataFrame({
        'open': [50000, 51000, 52000],
        'high': [51000, 52000, 53000],
        'low': [49000, 50000, 51000],
        'close': [50500, 51500, 52500]
    })
    return client