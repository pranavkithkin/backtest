#!/usr/bin/env python3
"""
TradingView Premium Trade Analyzer
Uses advanced TradingView Premium features for precise signal analysis
"""
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta
import os
import json
from flask import Flask, render_template, request, jsonify
import webbrowser
import threading
import time

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from crypto_analyzer import TradingSignal
import logging

logger = logging.getLogger(__name__)

class PremiumTradingViewAnalyzer:
    """Premium TradingView trade analyzer with advanced features"""
    
    def __init__(self):
        self.app = Flask(__name__)
        self.signals_data = []
        self.trades_data = []
        self.setup_routes()
    
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            """Main dashboard"""
            return render_template('premium_dashboard.html', 
                                 signals=self.signals_data[:50],
                                 total_signals=len(self.signals_data))
        
        @self.app.route('/premium_trade/<int:trade_index>')
        def premium_trade_detail(trade_index):
            """Premium trade detail page"""
            if trade_index >= len(self.signals_data):
                return "Trade not found", 404
            
            signal = self.signals_data[trade_index]
            return render_template('premium_trade_detail.html', 
                                 signal=signal, 
                                 trade_index=trade_index)
        
        @self.app.route('/api/trade_data/<int:trade_index>')
        def get_trade_data(trade_index):
            """API endpoint for trade data"""
            if trade_index >= len(self.signals_data):
                return jsonify({"error": "Trade not found"}), 404
            
            signal = self.signals_data[trade_index]
            
            # Get trading parameters from query
            stop_loss_pct = float(request.args.get('stop_loss', 10))
            risk_reward_ratio = float(request.args.get('risk_reward', 1.5))
            
            # Calculate precise timestamps
            signal_time = datetime.strptime(signal['timestamp'], '%Y-%m-%d %H:%M:%S')
            signal_unix = int(signal_time.timestamp())
            
            trade_data = {
                'symbol': signal['symbol'].replace('USDT', ''),
                'exchange': 'BINANCE',
                'entry_price': signal['entry_price'],
                'stop_loss_price': signal['entry_price'] * (1 - stop_loss_pct / 100),
                'take_profit_price': signal['entry_price'] * (1 + (stop_loss_pct * risk_reward_ratio) / 100),
                'signal_time': signal['timestamp'],
                'signal_unix': signal_unix,
                'stop_loss_pct': stop_loss_pct,
                'risk_reward_ratio': risk_reward_ratio,
                'coin_name': signal['coin_name'],
                'start_time': signal_unix - (7 * 24 * 3600),  # 7 days before
                'end_time': signal_unix + (30 * 24 * 3600)    # 30 days after
            }
            
            return jsonify(trade_data)
    
    def load_data(self):
        """Load signals and trades data"""
        try:
            # Load signals
            print("📊 Loading signals from CSV...")
            df = pd.read_csv('signals_last12months.csv')
            
            for _, row in df.iterrows():
                try:
                    signal = TradingSignal.from_csv_row(row)
                    self.signals_data.append({
                        'coin_name': signal.coin_name,
                        'symbol': signal.symbol,
                        'entry_price': signal.entry_price,
                        'timestamp': signal.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                        'date': signal.timestamp.strftime('%Y-%m-%d'),
                        'time': signal.timestamp.strftime('%H:%M:%S')
                    })
                except Exception as e:
                    continue
            
            print(f"✅ Loaded {len(self.signals_data)} signals")
            
            # Load trade results if available
            csv_files = [f for f in os.listdir('.') if f.startswith('concurrent_portfolio_analysis_') and f.endswith('.csv')]
            if csv_files:
                latest_csv = max(csv_files)
                trades_df = pd.read_csv(latest_csv)
                self.trades_data = trades_df.to_dict('records')
                print(f"✅ Loaded {len(self.trades_data)} trade results from {latest_csv}")
            
        except Exception as e:
            print(f"❌ Error loading data: {e}")
    
    def create_templates(self):
        """Create Premium HTML templates"""
        os.makedirs('templates', exist_ok=True)
        
        # Premium dashboard template
        premium_dashboard_html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Premium TradingView Trade Analyzer</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .trade-card { margin-bottom: 15px; cursor: pointer; transition: all 0.3s; border-left: 4px solid #007bff; }
        .trade-card:hover { transform: translateY(-2px); box-shadow: 0 8px 16px rgba(0,0,0,0.15); border-left-color: #28a745; }
        body { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
        .navbar { background: rgba(0,0,0,0.8); backdrop-filter: blur(10px); }
        .container-content { background: rgba(255,255,255,0.95); border-radius: 15px; padding: 30px; margin-top: 20px; }
        .premium-badge { background: linear-gradient(45deg, #f093fb 0%, #f5576c 100%); color: white; padding: 5px 15px; border-radius: 20px; font-size: 12px; }
    </style>
</head>
<body>
    <nav class="navbar navbar-dark">
        <div class="container-fluid">
            <span class="navbar-brand mb-0 h1">📊 Premium TradingView Trade Analyzer <span class="premium-badge">PREMIUM</span></span>
            <span class="navbar-text">{{total_signals}} Total Signals</span>
        </div>
    </nav>
    
    <div class="container-fluid">
        <div class="container-content">
            <div class="row">
                <div class="col-12 text-center mb-4">
                    <h2>🚀 Advanced Signal Analysis Dashboard</h2>
                    <p class="text-muted">Premium TradingView integration with precise signal timing and advanced chart features</p>
                    <div class="alert alert-info">
                        <strong>Premium Features:</strong> Precise time navigation • Advanced chart markers • Real-time calculations • Professional indicators
                    </div>
                </div>
            </div>
            
            <div class="row">
                {% for signal in signals %}
                <div class="col-xl-2 col-lg-3 col-md-4 col-sm-6">
                    <div class="card trade-card" onclick="openPremiumTrade({{loop.index0}})">
                        <div class="card-body">
                            <h6 class="card-title">{{signal.coin_name}}</h6>
                            <p class="card-text" style="font-size: 0.85rem;">
                                <strong>Entry:</strong> ${{signal.entry_price}}<br>
                                <strong>Date:</strong> {{signal.date}}<br>
                                <strong>Time:</strong> {{signal.time}}
                            </p>
                            <div class="d-flex justify-content-between">
                                <span class="badge bg-primary">{{signal.symbol}}</span>
                                <span class="premium-badge" style="font-size: 10px;">PREMIUM</span>
                            </div>
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>
    
    <script>
        function openPremiumTrade(index) {
            window.open('/premium_trade/' + index, '_blank');
        }
    </script>
</body>
</html>
        '''
        
        # Premium trade detail template with advanced TradingView features
        premium_trade_detail_html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Premium Trade Analysis - {{signal.coin_name}}</title>
    <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
        .navbar { background: rgba(0,0,0,0.8); backdrop-filter: blur(10px); }
        .content-panel { background: rgba(255,255,255,0.95); border-radius: 15px; padding: 20px; margin-bottom: 20px; backdrop-filter: blur(10px); }
        .chart-container { border-radius: 15px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.3); }
        .btn-timeframe { margin: 2px; border-radius: 20px; }
        .btn-timeframe.active { background: linear-gradient(45deg, #f093fb 0%, #f5576c 100%); border: none; }
        .trade-info { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white; border-radius: 15px; padding: 20px; }
        .premium-badge { background: linear-gradient(45deg, #f093fb 0%, #f5576c 100%); color: white; padding: 3px 10px; border-radius: 15px; font-size: 11px; }
        .control-section { background: rgba(255,255,255,0.9); border-radius: 10px; padding: 15px; margin-bottom: 15px; }
    </style>
</head>
<body>
    <nav class="navbar navbar-dark">
        <div class="container-fluid">
            <a class="navbar-brand" href="/">📊 Premium TradingView Analyzer</a>
            <span class="navbar-text">{{signal.coin_name}} <span class="premium-badge">PREMIUM</span></span>
        </div>
    </nav>
    
    <div class="container-fluid mt-3">
        <!-- Premium Control Panel -->
        <div class="content-panel">
            <div class="row">
                <div class="col-md-8">
                    <div class="control-section">
                        <h6>⚙️ Premium Trading Parameters</h6>
                        <div class="row">
                            <div class="col-md-3">
                                <label class="form-label">Stop Loss %</label>
                                <input type="number" class="form-control" id="stopLoss" value="10" step="0.5" min="1" max="50">
                            </div>
                            <div class="col-md-3">
                                <label class="form-label">Risk:Reward</label>
                                <input type="number" class="form-control" id="riskReward" value="1.5" step="0.1" min="0.5" max="10">
                            </div>
                            <div class="col-md-3">
                                <label class="form-label">Analysis Days</label>
                                <input type="number" class="form-control" id="analysisDays" value="30" min="7" max="90">
                            </div>
                            <div class="col-md-3">
                                <label class="form-label">&nbsp;</label>
                                <button class="btn btn-success form-control" onclick="updatePremiumChart()">🚀 Update</button>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="control-section">
                        <h6>⏰ Premium Timeframes</h6>
                        <div>
                            <button class="btn btn-outline-primary btn-timeframe" onclick="changePremiumTimeframe('1')">1m</button>
                            <button class="btn btn-outline-primary btn-timeframe" onclick="changePremiumTimeframe('5')">5m</button>
                            <button class="btn btn-outline-primary btn-timeframe" onclick="changePremiumTimeframe('15')">15m</button>
                            <button class="btn btn-outline-primary btn-timeframe" onclick="changePremiumTimeframe('60')">1h</button>
                            <button class="btn btn-outline-primary btn-timeframe" onclick="changePremiumTimeframe('240')">4h</button>
                            <button class="btn btn-outline-primary btn-timeframe" onclick="changePremiumTimeframe('1D')">1D</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Premium Trade Info -->
        <div class="trade-info mb-3">
            <div class="row align-items-center">
                <div class="col-md-2">
                    <strong>💰 Entry Price:</strong><br>
                    $<span id="entryPrice">{{signal.entry_price}}</span>
                </div>
                <div class="col-md-2">
                    <strong>🛑 Stop Loss:</strong><br>
                    $<span id="stopLossPrice">-</span> (<span id="stopLossPct">-</span>%)
                </div>
                <div class="col-md-2">
                    <strong>🎯 Take Profit:</strong><br>
                    $<span id="takeProfitPrice">-</span> (<span id="takeProfitPct">-</span>%)
                </div>
                <div class="col-md-3">
                    <strong>📅 Signal Time:</strong><br>
                    {{signal.timestamp}}
                </div>
                <div class="col-md-3">
                    <strong>📊 Symbol:</strong><br>
                    {{signal.symbol}} ({{signal.coin_name}})
                </div>
            </div>
        </div>
        
        <!-- Premium Chart Container -->
        <div class="chart-container">
            <div id="premium_tradingview_chart" style="height: 750px; width: 100%;"></div>
        </div>
        
        <!-- Premium Controls -->
        <div class="content-panel mt-3">
            <div class="row">
                <div class="col-md-8">
                    <h6>🎛️ Premium Chart Controls</h6>
                    <button class="btn btn-primary me-2" onclick="jumpToSignalTimePrecise()">📍 Jump to Signal Time</button>
                    <button class="btn btn-warning me-2" onclick="addPremiumLevels()">📏 Add SL/TP Levels</button>
                    <button class="btn btn-info me-2" onclick="addSignalMarkers()">🎯 Add Signal Markers</button>
                    <button class="btn btn-success me-2" onclick="analyzePremiumTrade()">📊 Analyze Trade</button>
                </div>
                <div class="col-md-4">
                    <div id="chartStatus">
                        <p><strong>Chart Status:</strong> <span id="statusText">Initializing...</span></p>
                        <p><strong>Current Time:</strong> <span id="currentTimeframe">1h</span></p>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Trade Analysis Results -->
        <div id="tradeAnalysisResults" class="content-panel" style="display: none;">
            <h6>📈 Premium Trade Analysis Results</h6>
            <div id="analysisContent"></div>
        </div>
    </div>
    
    <script>
        let premiumWidget;
        let currentSymbol = '{{signal.symbol}}'.replace('USDT', '');
        let currentTimeframe = '60';
        let tradeIndex = {{trade_index}};
        let signalTimestamp = new Date('{{signal.timestamp}}').getTime() / 1000;
        let entryPrice = {{signal.entry_price}};
        let tradeData = null;
        
        // Initialize Premium TradingView widget with advanced features
        function initPremiumChart() {
            const container = document.getElementById('premium_tradingview_chart');
            container.innerHTML = '';
            
            premiumWidget = new TradingView.widget({
                "width": "100%",
                "height": 750,
                "symbol": "BINANCE:" + currentSymbol + "USDT",
                "interval": currentTimeframe,
                "timezone": "Etc/UTC",
                "theme": "light",
                "style": "1",
                "locale": "en",
                "toolbar_bg": "#f1f3f6",
                "enable_publishing": false,
                "allow_symbol_change": true,
                "container_id": "premium_tradingview_chart",
                "studies": [
                    "Volume@tv-basicstudies",
                    "RSI@tv-basicstudies",
                    "MACD@tv-basicstudies"
                ],
                "show_popup_button": true,
                "popup_width": "1400",
                "popup_height": "900",
                "hide_side_toolbar": false,
                "details": true,
                "hotlist": true,
                "calendar": true,
                "news": ["headlines"],
                // Premium features
                "studies_overrides": {
                    "volume.volume.color.0": "#FF6B6B",
                    "volume.volume.color.1": "#4ECDC4",
                    "RSI.plot.color": "#9C27B0",
                    "MACD.histogram.color": "#2196F3"
                },
                "overrides": {
                    "mainSeriesProperties.candleStyle.upColor": "#4ECDC4",
                    "mainSeriesProperties.candleStyle.downColor": "#FF6B6B",
                    "mainSeriesProperties.candleStyle.borderUpColor": "#4ECDC4",
                    "mainSeriesProperties.candleStyle.borderDownColor": "#FF6B6B",
                    "mainSeriesProperties.candleStyle.wickUpColor": "#4ECDC4",
                    "mainSeriesProperties.candleStyle.wickDownColor": "#FF6B6B"
                },
                "disabled_features": [
                    "use_localstorage_for_settings"
                ],
                "enabled_features": [
                    "side_toolbar_in_fullscreen_mode",
                    "header_in_fullscreen_mode",
                    "timeframes_toolbar",
                    "volume_force_overlay",
                    "create_volume_indicator_by_default",
                    "moving_average_pine_id",
                    "hide_last_na_study_output"
                ],
                // Advanced Premium settings
                "loading_screen": { "backgroundColor": "#ffffff" },
                "custom_css_url": "",
                "saved_data": null,
                "auto_save_delay": 5,
                // Time range settings for precise navigation
                "time_frames": [
                    { "text": "1d", "resolution": "5" },
                    { "text": "5d", "resolution": "15" },
                    { "text": "1m", "resolution": "60" },
                    { "text": "3m", "resolution": "240" },
                    { "text": "6m", "resolution": "1D" },
                    { "text": "1y", "resolution": "1W" }
                ]
            });
            
            // Enhanced ready callback with Premium features
            premiumWidget.onChartReady(function() {
                console.log('Premium chart is ready');
                document.getElementById('statusText').textContent = 'Premium Ready';
                
                // Load trade data and setup
                loadTradeDataAndSetup();
            });
        }
        
        // Load trade data and setup premium features
        function loadTradeDataAndSetup() {
            fetch(`/api/trade_data/${tradeIndex}?stop_loss=${document.getElementById('stopLoss').value}&risk_reward=${document.getElementById('riskReward').value}`)
                .then(response => response.json())
                .then(data => {
                    tradeData = data;
                    console.log('Trade data loaded:', data);
                    
                    // Setup premium visualization
                    setTimeout(() => {
                        jumpToSignalTimePrecise();
                        updatePremiumLevels();
                    }, 1500);
                })
                .catch(error => {
                    console.error('Error loading trade data:', error);
                    document.getElementById('statusText').textContent = 'Error loading data';
                });
        }
        
        // Precise signal time navigation (Premium feature)
        function jumpToSignalTimePrecise() {
            if (!premiumWidget || !tradeData) return;
            
            try {
                const chart = premiumWidget.chart();
                
                // Calculate precise time range
                const analysisDays = parseInt(document.getElementById('analysisDays').value) || 30;
                const startTime = tradeData.signal_unix - (7 * 24 * 3600); // 7 days before
                const endTime = tradeData.signal_unix + (analysisDays * 24 * 3600); // Analysis days after
                
                // Set visible range with premium precision
                chart.setVisibleRange({
                    from: startTime,
                    to: endTime
                });
                
                document.getElementById('statusText').textContent = 'Jumped to signal time (Premium)';
                console.log(`Jumped to signal time: ${new Date(tradeData.signal_unix * 1000)}`);
                
            } catch (error) {
                console.error('Error jumping to signal time:', error);
                document.getElementById('statusText').textContent = 'Error navigating to signal time';
            }
        }
        
        // Add premium trading levels with enhanced visualization
        function addPremiumLevels() {
            if (!premiumWidget || !tradeData) return;
            
            try {
                const chart = premiumWidget.chart();
                
                // Clear existing shapes
                chart.removeAllShapes();
                
                // Add Entry Level (Blue solid line)
                chart.createShape(
                    { time: tradeData.signal_unix, price: tradeData.entry_price },
                    {
                        shape: 'horizontal_line',
                        text: `ENTRY: $${tradeData.entry_price.toFixed(4)}`,
                        overrides: {
                            linecolor: '#2196F3',
                            linewidth: 3,
                            linestyle: 0, // solid
                            showLabel: true,
                            textcolor: '#FFFFFF',
                            horzLabelsAlign: 'right'
                        }
                    }
                );
                
                // Add Stop Loss Level (Red dashed line)
                chart.createShape(
                    { time: tradeData.signal_unix, price: tradeData.stop_loss_price },
                    {
                        shape: 'horizontal_line',
                        text: `STOP LOSS: $${tradeData.stop_loss_price.toFixed(4)} (-${tradeData.stop_loss_pct}%)`,
                        overrides: {
                            linecolor: '#F44336',
                            linewidth: 2,
                            linestyle: 2, // dashed
                            showLabel: true,
                            textcolor: '#FFFFFF',
                            horzLabelsAlign: 'right'
                        }
                    }
                );
                
                // Add Take Profit Level (Green dashed line)
                chart.createShape(
                    { time: tradeData.signal_unix, price: tradeData.take_profit_price },
                    {
                        shape: 'horizontal_line',
                        text: `TAKE PROFIT: $${tradeData.take_profit_price.toFixed(4)} (+${(tradeData.stop_loss_pct * tradeData.risk_reward_ratio).toFixed(1)}%)`,
                        overrides: {
                            linecolor: '#4CAF50',
                            linewidth: 2,
                            linestyle: 2, // dashed
                            showLabel: true,
                            textcolor: '#FFFFFF',
                            horzLabelsAlign: 'right'
                        }
                    }
                );
                
                document.getElementById('statusText').textContent = 'Premium levels added';
                
            } catch (error) {
                console.error('Error adding premium levels:', error);
                document.getElementById('statusText').textContent = 'Error adding levels';
            }
        }
        
        // Add premium signal markers
        function addSignalMarkers() {
            if (!premiumWidget || !tradeData) return;
            
            try {
                const chart = premiumWidget.chart();
                
                // Add BUY signal marker
                chart.createShape(
                    { time: tradeData.signal_unix, price: tradeData.entry_price },
                    {
                        shape: 'arrow_up',
                        text: `BUY SIGNAL\\n${tradeData.signal_time}\\nEntry: $${tradeData.entry_price.toFixed(4)}\\nRisk:Reward 1:${tradeData.risk_reward_ratio}`,
                        overrides: {
                            color: '#4CAF50',
                            textcolor: '#FFFFFF',
                            fontsize: 14,
                            transparency: 20
                        }
                    }
                );
                
                // Add vertical line at signal time
                chart.createShape(
                    { time: tradeData.signal_unix, price: tradeData.entry_price },
                    {
                        shape: 'vertical_line',
                        text: `Signal Time: ${tradeData.signal_time}`,
                        overrides: {
                            linecolor: '#FF9800',
                            linewidth: 1,
                            linestyle: 1, // dotted
                            showLabel: true,
                            textcolor: '#FF9800'
                        }
                    }
                );
                
                document.getElementById('statusText').textContent = 'Signal markers added';
                
            } catch (error) {
                console.error('Error adding signal markers:', error);
                document.getElementById('statusText').textContent = 'Error adding markers';
            }
        }
        
        // Change timeframe with premium features
        function changePremiumTimeframe(timeframe) {
            currentTimeframe = timeframe;
            
            // Update timeframe display
            const timeframeText = 
                timeframe === '1' ? '1m' : 
                timeframe === '5' ? '5m' : 
                timeframe === '15' ? '15m' : 
                timeframe === '60' ? '1h' : 
                timeframe === '240' ? '4h' : '1D';
            
            document.getElementById('currentTimeframe').textContent = timeframeText;
            
            // Update active button
            document.querySelectorAll('.btn-timeframe').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            
            // Recreate widget with new timeframe
            initPremiumChart();
        }
        
        // Update premium chart
        function updatePremiumChart() {
            updatePremiumLevels();
            loadTradeDataAndSetup();
        }
        
        // Update premium levels display
        function updatePremiumLevels() {
            const stopLoss = parseFloat(document.getElementById('stopLoss').value);
            const riskReward = parseFloat(document.getElementById('riskReward').value);
            
            const stopLossPrice = entryPrice * (1 - stopLoss / 100);
            const takeProfitPrice = entryPrice * (1 + (stopLoss * riskReward) / 100);
            const takeProfitPct = stopLoss * riskReward;
            
            // Update display
            document.getElementById('stopLossPrice').textContent = stopLossPrice.toFixed(4);
            document.getElementById('stopLossPct').textContent = stopLoss.toFixed(1);
            document.getElementById('takeProfitPrice').textContent = takeProfitPrice.toFixed(4);
            document.getElementById('takeProfitPct').textContent = takeProfitPct.toFixed(1);
        }
        
        // Premium trade analysis
        function analyzePremiumTrade() {
            document.getElementById('tradeAnalysisResults').style.display = 'block';
            document.getElementById('analysisContent').innerHTML = `
                <div class="row">
                    <div class="col-md-4">
                        <h6>📊 Premium Analysis</h6>
                        <p><strong>Symbol:</strong> ${currentSymbol}USDT</p>
                        <p><strong>Entry Price:</strong> $${entryPrice.toFixed(4)}</p>
                        <p><strong>Risk:Reward:</strong> 1:${document.getElementById('riskReward').value}</p>
                        <p><strong>Stop Loss:</strong> ${document.getElementById('stopLoss').value}%</p>
                    </div>
                    <div class="col-md-4">
                        <h6>⏰ Timing Analysis</h6>
                        <p><strong>Signal Time:</strong> ${tradeData.signal_time}</p>
                        <p><strong>Timeframe:</strong> ${document.getElementById('currentTimeframe').textContent}</p>
                        <p><strong>Analysis Period:</strong> ${document.getElementById('analysisDays').value} days</p>
                    </div>
                    <div class="col-md-4">
                        <h6>💰 Risk Management</h6>
                        <p><strong>Max Loss:</strong> ${document.getElementById('stopLoss').value}% of capital</p>
                        <p><strong>Target Profit:</strong> ${(parseFloat(document.getElementById('stopLoss').value) * parseFloat(document.getElementById('riskReward').value)).toFixed(1)}% of capital</p>
                        <p><strong>Position Sizing:</strong> Based on risk amount</p>
                    </div>
                </div>
            `;
        }
        
        // Initialize on page load
        document.addEventListener('DOMContentLoaded', function() {
            updatePremiumLevels();
            initPremiumChart();
            
            // Set initial active timeframe
            document.querySelector('[onclick="changePremiumTimeframe(\\'60\\')"]').classList.add('active');
        });
    </script>
</body>
</html>
        '''
        
        # Save templates
        with open('templates/premium_dashboard.html', 'w') as f:
            f.write(premium_dashboard_html)
        with open('templates/premium_trade_detail.html', 'w') as f:
            f.write(premium_trade_detail_html)
        
        print("✅ Created Premium HTML templates")
    
    def run(self, host='127.0.0.1', port=5001, debug=False):
        """Run the premium application"""
        self.load_data()
        self.create_templates()
        
        print(f"\n🚀 Starting Premium TradingView Trade Analyzer...")
        print(f"🎯 Premium Dashboard: http://{host}:{port}")
        print(f"⭐ Premium Features Enabled:")
        print(f"   • Precise signal time navigation")
        print(f"   • Advanced chart markers and levels")
        print(f"   • Enhanced timeframe controls (1m, 5m, 15m, 1h, 4h, 1D)")
        print(f"   • Professional indicators (Volume, RSI, MACD)")
        print(f"   • Real-time trade analysis")
        
        # Auto-open browser
        def open_browser():
            time.sleep(1.5)
            webbrowser.open(f'http://{host}:{port}')
        
        threading.Timer(1, open_browser).start()
        
        # Run Flask app
        self.app.run(host=host, port=port, debug=debug)

def main():
    """Main function"""
    print("🌟 PREMIUM TRADINGVIEW TRADE ANALYZER")
    print("="*70)
    print("Premium Features:")
    print("• 🎯 Precise signal time navigation")
    print("• 📊 Advanced TradingView chart integration")  
    print("• ⏰ Professional timeframe controls")
    print("• 📈 Enhanced indicators (RSI, MACD, Volume)")
    print("• 🎛️ Real-time parameter adjustment")
    print("• 💰 Professional risk management tools")
    print("="*70)
    
    try:
        analyzer = PremiumTradingViewAnalyzer()
        analyzer.run(port=5001, debug=False)
        
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error(f"Premium application error: {e}")

if __name__ == "__main__":
    main()