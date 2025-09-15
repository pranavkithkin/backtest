#!/usr/bin/env python3
"""
Quick API test to check if Binance connection is working
"""
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from crypto_analyzer import BinanceClient
from crypto_analyzer.models import TradingSignal
from datetime import datetime, timezone
import pandas as pd

def test_api_connection():
    """Test basic API connection"""
    print("🔍 Testing Binance API Connection...")
    
    try:
        client = BinanceClient()
        
        # Test basic connection
        if client.test_connection():
            print("✅ API connection successful!")
        else:
            print("❌ API connection failed!")
            return False
        
        # Test a simple symbol lookup
        print("\n📊 Testing symbol data retrieval...")
        
        test_symbols = [
            'BTCUSDT',
            'ETHUSDT', 
            '1000CHEEMSUSDT',  # This might fail
            'CHEEMSUSDT',      # This will likely fail
            'DOGEUSDT'
        ]
        
        for symbol in test_symbols:
            print(f"   Testing {symbol}...")
            try:
                # Try to get just 1 candle for the last day
                start_time = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
                df = client.get_klines_for_timeframe(
                    symbol=symbol,
                    start_dt=start_time,
                    interval='1d',
                    limit=1
                )
                
                if df is not None and not df.empty:
                    price = df.iloc[0]['close']
                    print(f"     ✅ {symbol}: ${price}")
                else:
                    print(f"     ❌ {symbol}: No data returned")
                    
            except Exception as e:
                print(f"     ❌ {symbol}: {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def test_csv_symbol_mapping():
    """Test how our CSV symbols are being mapped"""
    print("\n🔄 Testing CSV symbol mapping...")
    
    # Sample data from your CSV
    test_data = [
        {'coin': 'BTC', 'entry': 94.346},
        {'coin': '1000CHEEMS', 'entry': 0.0008587},
        {'coin': '1000WHY', 'entry': 0.0001531},
        {'coin': 'DOGE', 'entry': 0.30777},
        {'coin': 'BROCCOLI714', 'entry': 0.03355},
    ]
    
    for data in test_data:
        try:
            # Create a mock signal to test symbol mapping
            signal = TradingSignal(
                timestamp=datetime.now(timezone.utc),
                coin_name=data['coin'],
                entry_price=data['entry']
            )
            print(f"   {data['coin']} → {signal.symbol}")
        except Exception as e:
            print(f"   ❌ {data['coin']}: {e}")

def test_portfolio_calculator_load():
    """Test if portfolio calculator can load your CSV"""
    print("\n📄 Testing CSV file loading...")
    
    try:
        from crypto_analyzer import PortfolioCalculator, ProfitLossAnalyzer
        
        analyzer = ProfitLossAnalyzer()
        calculator = PortfolioCalculator(analyzer)
        
        csv_file = "signals_last12months.csv"
        signals = calculator.load_signals_from_csv(csv_file)
        
        print(f"   ✅ Loaded {len(signals)} signals from CSV")
        
        if signals:
            print(f"   First signal: {signals[0].coin_name} → {signals[0].symbol}")
            print(f"   Last signal: {signals[-1].coin_name} → {signals[-1].symbol}")
            
            # Count unique symbols
            unique_symbols = set(s.symbol for s in signals)
            print(f"   Unique symbols: {len(unique_symbols)}")
            
            # Show some symbol mappings
            print("\n   Sample symbol mappings:")
            for i, signal in enumerate(signals[:10]):
                print(f"     {signal.coin_name} → {signal.symbol}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ CSV loading failed: {e}")
        return False

def main():
    print("🚀 BINANCE API TEST SUITE")
    print("=" * 50)
    
    # Test 1: Basic API connection
    api_works = test_api_connection()
    
    # Test 2: Symbol mapping
    test_csv_symbol_mapping()
    
    # Test 3: CSV loading
    csv_works = test_portfolio_calculator_load()
    
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY:")
    print(f"   API Connection: {'✅ PASS' if api_works else '❌ FAIL'}")
    print(f"   CSV Loading: {'✅ PASS' if csv_works else '❌ FAIL'}")
    
    if api_works and csv_works:
        print("\n🎉 All tests passed! Your system is ready to use.")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main()