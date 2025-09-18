#!/usr/bin/env python3
"""
TradingView Screenshot Analyzer
Automatically captures TradingView screenshots for each signal with entry, SL, and TP levels
Adjusts timeframe based on how long it took to hit TP or SL
"""
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta
import os
import json
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import requests
from typing import Dict, List, Tuple, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from crypto_analyzer import TradingSignal

logger = logging.getLogger(__name__)

class TradingViewScreenshotAnalyzer:
    """Automated TradingView screenshot capture with dynamic timeframes"""
    
    def __init__(self, binance_api_key: str = None, binance_secret: str = None):
        self.binance_api_key = binance_api_key or os.getenv('BINANCE_API_KEY')
        self.binance_secret = binance_secret or os.getenv('BINANCE_SECRET')
        self.driver = None
        self.screenshots_dir = "tradingview_screenshots"
        self.setup_directories()
        
    def setup_directories(self):
        """Create necessary directories"""
        os.makedirs(self.screenshots_dir, exist_ok=True)
        os.makedirs(f"{self.screenshots_dir}/signals", exist_ok=True)
        
    def setup_webdriver(self):
        """Setup Chrome WebDriver for TradingView"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run headless Chrome
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-gpu")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            print("✅ Chrome WebDriver initialized successfully")
        except Exception as e:
            print(f"❌ Error initializing WebDriver: {e}")
            print("Please install ChromeDriver: brew install chromedriver")
            return False
        return True
    
    def get_historical_data(self, symbol: str, start_time: datetime, end_time: datetime) -> pd.DataFrame:
        """Get historical price data from Binance API"""
        try:
            base_url = "https://api.binance.com/api/v3/klines"
            
            # Convert to milliseconds
            start_ms = int(start_time.timestamp() * 1000)
            end_ms = int(end_time.timestamp() * 1000)
            
            params = {
                'symbol': symbol,
                'interval': '1m',  # 1-minute intervals for precise analysis
                'startTime': start_ms,
                'endTime': end_ms,
                'limit': 1000
            }
            
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Convert to DataFrame
            df = pd.DataFrame(data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
                
            return df
            
        except Exception as e:
            print(f"❌ Error getting historical data for {symbol}: {e}")
            return pd.DataFrame()
    
    def analyze_trade_outcome(self, signal: TradingSignal, stop_loss_pct: float = 10.0, 
                            risk_reward_ratio: float = 1.5) -> Dict:
        """Analyze when a trade hit SL or TP and determine optimal timeframe"""
        
        entry_price = signal.entry_price
        stop_loss_price = entry_price * (1 - stop_loss_pct / 100)
        take_profit_price = entry_price * (1 + (stop_loss_pct * risk_reward_ratio) / 100)
        
        # Get historical data for analysis (up to 30 days)
        end_time = signal.timestamp + timedelta(days=30)
        if end_time > datetime.now():
            end_time = datetime.now()
            
        df = self.get_historical_data(signal.symbol, signal.timestamp, end_time)
        
        if df.empty:
            return {
                'outcome': 'no_data',
                'hit_time': None,
                'duration_minutes': 0,
                'recommended_timeframe': '1D',
                'final_price': entry_price,
                'max_profit_pct': 0,
                'max_loss_pct': 0
            }
        
        # Find when SL or TP was hit
        hit_sl_time = None
        hit_tp_time = None
        
        for _, row in df.iterrows():
            current_time = row['timestamp']
            low_price = row['low']
            high_price = row['high']
            
            # Check if stop loss was hit
            if low_price <= stop_loss_price and hit_sl_time is None:
                hit_sl_time = current_time
                
            # Check if take profit was hit
            if high_price >= take_profit_price and hit_tp_time is None:
                hit_tp_time = current_time
        
        # Determine outcome and timing
        outcome = 'ongoing'
        hit_time = None
        
        if hit_sl_time is not None and hit_tp_time is not None:
            # Both hit, use the first one
            if hit_sl_time < hit_tp_time:
                outcome = 'stop_loss'
                hit_time = hit_sl_time
            else:
                outcome = 'take_profit'
                hit_time = hit_tp_time
        elif hit_sl_time is not None:
            outcome = 'stop_loss'
            hit_time = hit_sl_time
        elif hit_tp_time is not None:
            outcome = 'take_profit'
            hit_time = hit_tp_time
        
        # Calculate duration and determine timeframe
        if hit_time:
            duration_minutes = (hit_time - signal.timestamp).total_seconds() / 60
        else:
            duration_minutes = (df['timestamp'].iloc[-1] - signal.timestamp).total_seconds() / 60
        
        # Determine optimal timeframe based on duration
        if duration_minutes <= 60:  # Less than 1 hour
            timeframe = '5'
        elif duration_minutes <= 240:  # Less than 4 hours
            timeframe = '15'
        elif duration_minutes <= 1440:  # Less than 1 day
            timeframe = '60'
        elif duration_minutes <= 4320:  # Less than 3 days
            timeframe = '240'
        else:
            timeframe = '1D'
        
        # Calculate max profit/loss percentages
        max_price = df['high'].max()
        min_price = df['low'].min()
        max_profit_pct = ((max_price - entry_price) / entry_price) * 100
        max_loss_pct = ((min_price - entry_price) / entry_price) * 100
        
        final_price = df['close'].iloc[-1] if not df.empty else entry_price
        
        return {
            'outcome': outcome,
            'hit_time': hit_time,
            'duration_minutes': duration_minutes,
            'recommended_timeframe': timeframe,
            'final_price': final_price,
            'max_profit_pct': max_profit_pct,
            'max_loss_pct': max_loss_pct,
            'stop_loss_price': stop_loss_price,
            'take_profit_price': take_profit_price
        }
    
    def capture_tradingview_screenshot(self, signal: TradingSignal, analysis: Dict, 
                                     filename: str) -> bool:
        """Capture TradingView screenshot with annotations"""
        try:
            symbol_clean = signal.symbol.replace('USDT', '')
            
            # Build TradingView URL
            tv_url = f"https://www.tradingview.com/chart/?symbol=BINANCE:{symbol_clean}USDT"
            
            # Add timeframe parameter
            timeframe = analysis['recommended_timeframe']
            tv_url += f"&interval={timeframe}"
            
            print(f"📸 Capturing screenshot for {signal.symbol} with {timeframe} timeframe...")
            
            # Navigate to TradingView
            self.driver.get(tv_url)
            
            # Wait for chart to load
            try:
                WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "chart-container"))
                )
                time.sleep(5)  # Additional wait for chart data
            except TimeoutException:
                print(f"❌ Timeout waiting for chart to load for {signal.symbol}")
                return False
            
            # Try to close any popups/notifications
            try:
                close_buttons = self.driver.find_elements(By.XPATH, "//button[contains(@class, 'close') or contains(text(), 'Close') or contains(@aria-label, 'Close')]")
                for button in close_buttons:
                    try:
                        button.click()
                        time.sleep(1)
                    except:
                        pass
            except:
                pass
            
            # Set the chart to the signal date
            try:
                # This is complex with TradingView's interface, so we'll capture the current view
                # In a production environment, you might want to use TradingView's Pine Script or API
                pass
            except:
                pass
            
            # Take screenshot
            screenshot_path = os.path.join(self.screenshots_dir, "signals", filename)
            self.driver.save_screenshot(screenshot_path)
            
            print(f"✅ Screenshot saved: {screenshot_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error capturing screenshot for {signal.symbol}: {e}")
            return False
    
    def add_trade_annotations(self, signal: TradingSignal, analysis: Dict) -> str:
        """Generate annotation text for the trade"""
        outcome_emoji = {
            'take_profit': '🎯',
            'stop_loss': '🛑',
            'ongoing': '⏳',
            'no_data': '❓'
        }
        
        duration_str = ""
        if analysis['hit_time']:
            duration_minutes = analysis['duration_minutes']
            if duration_minutes < 60:
                duration_str = f"{duration_minutes:.0f}m"
            elif duration_minutes < 1440:
                duration_str = f"{duration_minutes/60:.1f}h"
            else:
                duration_str = f"{duration_minutes/1440:.1f}d"
        
        annotation = f"""
{outcome_emoji.get(analysis['outcome'], '❓')} {signal.symbol}
📈 Entry: ${signal.entry_price:.4f}
🛑 SL: ${analysis.get('stop_loss_price', 0):.4f}
🎯 TP: ${analysis.get('take_profit_price', 0):.4f}
⏱️ Timeframe: {analysis['recommended_timeframe']}
🔄 Outcome: {analysis['outcome'].replace('_', ' ').title()}
"""
        if duration_str:
            annotation += f"⏳ Duration: {duration_str}\n"
        
        annotation += f"📊 Max Profit: {analysis['max_profit_pct']:.2f}%\n"
        annotation += f"📉 Max Loss: {analysis['max_loss_pct']:.2f}%"
        
        return annotation
    
    def process_signals_file(self, csv_file: str, max_signals: int = 50) -> Dict:
        """Process signals from CSV file and capture screenshots"""
        if not os.path.exists(csv_file):
            print(f"❌ Signals file not found: {csv_file}")
            return {}
        
        print(f"📊 Loading signals from {csv_file}")
        df = pd.read_csv(csv_file)
        
        # Convert timestamp column
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        elif 'Timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['Timestamp'])
        else:
            print("❌ No timestamp column found in CSV")
            return {}
        
        # Setup WebDriver
        if not self.setup_webdriver():
            return {}
        
        results = {}
        processed = 0
        
        try:
            for index, row in df.iterrows():
                if processed >= max_signals:
                    break
                
                try:
                    # Create TradingSignal object
                    signal = TradingSignal(
                        symbol=row.get('symbol', row.get('Symbol', '')),
                        timestamp=row['timestamp'],
                        entry_price=float(row.get('entry_price', row.get('Entry_Price', row.get('price', 0)))),
                        signal_type=row.get('signal_type', row.get('Signal_Type', 'BUY')),
                        confidence=row.get('confidence', row.get('Confidence', 0.8))
                    )
                    
                    if not signal.symbol or signal.entry_price <= 0:
                        print(f"⚠️ Skipping invalid signal: {signal.symbol}")
                        continue
                    
                    print(f"\n🔍 Analyzing signal {processed + 1}/{min(len(df), max_signals)}: {signal.symbol}")
                    
                    # Analyze trade outcome
                    analysis = self.analyze_trade_outcome(signal)
                    
                    # Generate filename
                    timestamp_str = signal.timestamp.strftime("%Y%m%d_%H%M%S")
                    filename = f"{signal.symbol}_{timestamp_str}_{analysis['outcome']}.png"
                    
                    # Capture screenshot
                    success = self.capture_tradingview_screenshot(signal, analysis, filename)
                    
                    if success:
                        # Generate annotation
                        annotation = self.add_trade_annotations(signal, analysis)
                        
                        results[signal.symbol] = {
                            'signal': signal,
                            'analysis': analysis,
                            'annotation': annotation,
                            'screenshot_file': filename,
                            'success': True
                        }
                        
                        print(f"✅ Processed {signal.symbol}: {analysis['outcome']}")
                        print(f"📊 Duration: {analysis['duration_minutes']:.0f}m, Timeframe: {analysis['recommended_timeframe']}")
                    else:
                        results[signal.symbol] = {
                            'signal': signal,
                            'analysis': analysis,
                            'success': False,
                            'error': 'Screenshot capture failed'
                        }
                    
                    processed += 1
                    time.sleep(2)  # Rate limiting
                    
                except Exception as e:
                    print(f"❌ Error processing signal {index}: {e}")
                    continue
        
        finally:
            if self.driver:
                self.driver.quit()
                print("🔒 WebDriver closed")
        
        return results
    
    def generate_summary_report(self, results: Dict) -> str:
        """Generate a summary report of all processed signals"""
        successful = sum(1 for r in results.values() if r.get('success', False))
        total = len(results)
        
        outcomes = {}
        timeframes = {}
        
        for result in results.values():
            if result.get('success', False):
                analysis = result['analysis']
                outcome = analysis['outcome']
                timeframe = analysis['recommended_timeframe']
                
                outcomes[outcome] = outcomes.get(outcome, 0) + 1
                timeframes[timeframe] = timeframes.get(timeframe, 0) + 1
        
        report = f"""
📊 TRADINGVIEW SCREENSHOT ANALYSIS SUMMARY
{'='*50}

📈 Total Signals Processed: {total}
✅ Successful Screenshots: {successful}
❌ Failed Screenshots: {total - successful}
📈 Success Rate: {(successful/total*100):.1f}%

🎯 OUTCOMES:
"""
        for outcome, count in outcomes.items():
            emoji = {'take_profit': '🎯', 'stop_loss': '🛑', 'ongoing': '⏳', 'no_data': '❓'}.get(outcome, '❓')
            report += f"{emoji} {outcome.replace('_', ' ').title()}: {count}\n"
        
        report += "\n⏱️ TIMEFRAMES USED:\n"
        for timeframe, count in timeframes.items():
            report += f"📊 {timeframe}: {count}\n"
        
        report += f"\n📁 Screenshots saved in: {self.screenshots_dir}/signals/\n"
        
        return report
    
    def create_enhanced_analyzer(self, signals_file: str = "signals_last12months.csv"):
        """Main method to run the enhanced screenshot analyzer"""
        print("🚀 Starting Enhanced TradingView Screenshot Analyzer")
        print("="*60)
        
        # Check if signals file exists
        if not os.path.exists(signals_file):
            print(f"❌ Signals file not found: {signals_file}")
            print("📝 Looking for alternative signal files...")
            
            # Look for CSV files in the directory
            csv_files = [f for f in os.listdir('.') if f.endswith('.csv') and 'signal' in f.lower()]
            if csv_files:
                signals_file = csv_files[0]
                print(f"✅ Found signals file: {signals_file}")
            else:
                print("❌ No signals CSV files found in current directory")
                return
        
        # Process signals
        results = self.process_signals_file(signals_file, max_signals=20)  # Limit for demo
        
        if not results:
            print("❌ No signals were processed successfully")
            return
        
        # Generate and display summary
        summary = self.generate_summary_report(results)
        print(summary)
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"screenshot_analysis_{timestamp}.json"
        
        # Convert results to JSON-serializable format
        json_results = {}
        for symbol, result in results.items():
            if result.get('success', False):
                json_results[symbol] = {
                    'symbol': result['signal'].symbol,
                    'timestamp': result['signal'].timestamp.isoformat(),
                    'entry_price': result['signal'].entry_price,
                    'outcome': result['analysis']['outcome'],
                    'duration_minutes': result['analysis']['duration_minutes'],
                    'timeframe': result['analysis']['recommended_timeframe'],
                    'max_profit_pct': result['analysis']['max_profit_pct'],
                    'max_loss_pct': result['analysis']['max_loss_pct'],
                    'screenshot_file': result['screenshot_file'],
                    'annotation': result['annotation']
                }
        
        with open(results_file, 'w') as f:
            json.dump(json_results, f, indent=2)
        
        print(f"💾 Detailed results saved to: {results_file}")
        print("🎉 Screenshot analysis complete!")


def main():
    """Main execution function"""
    analyzer = TradingViewScreenshotAnalyzer()
    
    # You can customize the signals file here
    signals_file = "signals_last12months.csv"
    
    analyzer.create_enhanced_analyzer(signals_file)


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('screenshot_analyzer.log'),
            logging.StreamHandler()
        ]
    )
    
    main()