"""Tests for utility functions"""
import pytest
import pandas as pd
from datetime import datetime, timezone
import tempfile
import os

from crypto_analyzer.utils import (
    floor_to_timeframe,
    validate_csv_file,
    load_and_validate_csv,
    generate_output_filename
)


class TestUtilityFunctions:
    """Test cases for utility functions"""
    
    def test_floor_to_timeframe(self):
        """Test datetime flooring to timeframe boundaries"""
        dt = datetime(2023, 1, 1, 12, 37, 45, tzinfo=timezone.utc)
        
        # Test 1 minute - should keep same
        result = floor_to_timeframe(dt, 1)
        assert result.minute == 37
        
        # Test 5 minute - should floor to 35
        result = floor_to_timeframe(dt, 5)
        assert result.minute == 35
        
        # Test 15 minute - should floor to 30
        result = floor_to_timeframe(dt, 15)
        assert result.minute == 30
        
        # Test 1 hour - should floor to 0 minutes
        result = floor_to_timeframe(dt, 60)
        assert result.minute == 0
    
    def test_validate_csv_file(self):
        """Test CSV file validation"""
        # Valid CSV
        df = pd.DataFrame({
            'Timestamp': ['2023-01-01'],
            'Coin_Name': ['BTC'],
            'CMP': [50000]
        })
        is_valid, missing = validate_csv_file(df, ['Timestamp', 'Coin_Name', 'CMP'])
        assert is_valid
        assert len(missing) == 0
        
        # Invalid CSV
        df_invalid = pd.DataFrame({'Other': ['data']})
        is_valid, missing = validate_csv_file(df_invalid, ['Timestamp', 'Coin_Name', 'CMP'])
        assert not is_valid
        assert len(missing) == 3
    
    def test_generate_output_filename(self):
        """Test output filename generation"""
        result = generate_output_filename("signals_jan2023.csv", "analysis_")
        assert result == "analysis_jan2023.csv"
        
        result = generate_output_filename("data.csv", "result_")
        assert result == "result_data.csv"