"""Tests for data models"""
import pytest
import pandas as pd
from datetime import datetime, timezone

from crypto_analyzer.models import TradingSignal, AnalysisResult


class TestTradingSignal:
    """Test cases for TradingSignal model"""
    
    def test_trading_signal_creation(self):
        """Test basic TradingSignal creation"""
        signal = TradingSignal(
            timestamp=datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            coin_name="BTC",
            entry_price=50000.0
        )
        assert signal.coin_name == "BTC"
        assert signal.entry_price == 50000.0
        assert signal.symbol == "BTCUSDT"
    
    def test_from_csv_row(self):
        """Test creating TradingSignal from CSV row"""
        row = pd.Series({
            'Timestamp': '2023-01-01 12:00:00+00:00',
            'Coin_Name': 'btc',
            'CMP': 50000.0,
            'Date': '2023-01-01',
            'Time': '12:00:00'
        })
        
        signal = TradingSignal.from_csv_row(row)
        assert signal.coin_name == "BTC"
        assert signal.entry_price == 50000.0
        assert signal.date == "2023-01-01"
        assert signal.time == "12:00:00"


class TestAnalysisResult:
    """Test cases for AnalysisResult model"""
    
    def test_analysis_result_to_dict(self):
        """Test converting AnalysisResult to dictionary"""
        signal = TradingSignal(
            timestamp=datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            coin_name="BTC",
            entry_price=50000.0,
            date="2023-01-01",
            time="12:00:00"
        )
        
        result = AnalysisResult(
            signal=signal,
            first_hit="PROFIT",
            hit_time=datetime(2023, 1, 2, 12, 0, 0, tzinfo=timezone.utc),
            hours_to_hit=24.0,
            loss_profit=100.0,
            hit_date="2023-01-02"
        )
        
        result_dict = result.to_dict()
        assert result_dict['Coin_Name'] == "BTC"
        assert result_dict['Entry_Price'] == 50000.0
        assert result_dict['Loss_Profit'] == 100.0
        assert result_dict['Hours_to_Hit'] == 24.0