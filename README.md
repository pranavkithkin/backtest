# Crypto Profit/Loss Analyzer

A professional cryptocurrency trading signal analysis tool that evaluates the historical performance of trading signals against defined profit and loss targets using Binance market data.

## Features

- 📊 **Automated Analysis**: Process CSV files containing trading signals
- 🔄 **Progressive Timeframes**: Uses multiple timeframes (1m to 1d) for comprehensive analysis
- 🎯 **Customizable Targets**: Set your own profit/loss percentages
- 📈 **Binance Integration**: Real-time and historical price data via Binance API
- 🚀 **Enterprise-Ready**: Modular, scalable, and well-tested codebase
- 📝 **Detailed Logging**: Comprehensive logging for debugging and monitoring
- 🔧 **CLI Interface**: Easy-to-use command-line interface

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd FINAL_BACKTEST

# Install dependencies
pip install -r requirements.txt

# Or install in development mode
pip install -e .
```

### Basic Usage

```bash
# Analyze all CSV files in a folder
python main.py --input-folder signals --output-folder results

# Customize profit/loss targets
python main.py --input-folder signals --profit 50 --loss -20

# Process a single file
python main.py --single-file signals/my_signals.csv --output-folder results

# Set custom timeframe
python main.py --input-folder signals --max-days 180
```

## Configuration

The analyzer uses progressive timeframes by default:
- 1 minute (5 candles)
- 5 minutes (3 candles)  
- 15 minutes (4 candles)
- 1 hour (24 candles)
- 4 hours (18 candles)
- 1 day (30 candles)

## Input Format

CSV files should contain these columns:
- `Timestamp`: Entry timestamp (UTC)
- `Coin_Name`: Cryptocurrency symbol (e.g., BTC)
- `CMP`: Current Market Price (entry price)

Optional columns:
- `Date`: Date string
- `Time`: Time string

## Output Format

Results include:
- `Date`: Entry date
- `Time`: Entry time
- `Coin_Name`: Cryptocurrency symbol
- `Entry_Price`: Entry price
- `Hit_Date`: Date when target was hit (if any)
- `Loss_Profit`: Percentage hit (+100%, -30%, or 0)
- `Hours_to_Hit`: Time taken to hit target

## API Configuration

For Binance API access (optional):

```bash
python main.py --api-key YOUR_API_KEY --api-secret YOUR_API_SECRET
```

## Development

### Project Structure

```
src/crypto_analyzer/
├── __init__.py           # Package exports
├── api/                  # Binance API client
├── config/              # Configuration settings
├── models/              # Data models
├── services/            # Business logic
└── utils/               # Utility functions
```

### Running Tests

```bash
pip install pytest
pytest tests/
```

### Code Quality

```bash
# Install development dependencies
pip install -e .[dev]

# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.