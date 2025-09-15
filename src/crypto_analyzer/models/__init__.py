"""Data models for the crypto analyzer"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import pandas as pd


@dataclass
class TradingSignal:
    """Represents a trading signal"""
    timestamp: datetime
    coin_name: str
    entry_price: float
    date: Optional[str] = None
    time: Optional[str] = None
    
    @classmethod
    def from_csv_row(cls, row: pd.Series) -> 'TradingSignal':
        """Create TradingSignal from CSV row - handles multiple CSV formats"""
        # Handle your specific CSV format
        if 'timestamp_utc' in row and 'coin' in row and 'entry' in row:
            timestamp = pd.to_datetime(row['timestamp_utc'], utc=True)
            coin_name = str(row['coin']).strip().upper()
            
            # Handle empty entry values
            entry_price = row['entry']
            if pd.isna(entry_price) or entry_price == '':
                # Use sl (stop loss) as fallback if entry is empty
                if 'sl' in row and not pd.isna(row['sl']) and row['sl'] != '':
                    entry_price = float(row['sl'])
                else:
                    raise ValueError(f"No valid entry price found for {coin_name}")
            else:
                entry_price = float(entry_price)
            
            return cls(
                timestamp=timestamp,
                coin_name=coin_name,
                entry_price=entry_price,
                date=timestamp.strftime('%Y-%m-%d'),
                time=timestamp.strftime('%H:%M:%S')
            )
        
        # Handle standard CSV format
        elif 'Timestamp' in row and 'Coin_Name' in row and 'CMP' in row:
            timestamp = pd.to_datetime(row['Timestamp'], utc=True)
            return cls(
                timestamp=timestamp,
                coin_name=row['Coin_Name'].strip().upper(),
                entry_price=float(row['CMP']),
                date=row.get('Date', timestamp.strftime('%Y-%m-%d')),
                time=row.get('Time', timestamp.strftime('%H:%M:%S'))
            )
        
        else:
            raise ValueError(f"Unsupported CSV format. Expected columns: timestamp_utc, coin, entry OR Timestamp, Coin_Name, CMP")
    
    @property
    def symbol(self) -> str:
        """Get Binance symbol for this coin"""
        coin = self.coin_name.strip().upper()
        
        # Comprehensive symbol mappings for problematic coins
        symbol_mappings = {
            # Keep 1000 prefix coins as-is
            '1000CHEEMS': '1000CHEEMSUSDT',
            '1000WHY': '1000WHYUSDT', 
            '1000X': '1000XUSDT',
            '1000000BOB': '1000000BOBUSDT',
            
            # Remove numeric suffixes but keep the base name
            'BROCCOLI714': 'BROCCOLIUSDT',  # Will be marked invalid
            'BANANAS31': 'BANANASUSDT',     # Will be marked invalid
            
            # Special mappings for coins that exist with different symbols
            'PUMPBTC': 'PUMPUSDT',
            
            # Common alternative mappings (these might not exist)
            'BROCCOLI': 'BROCCOLIUSDT',  # Likely invalid
            'BANANAS': 'BANANASUSDT',    # Likely invalid
            'FART': 'FARTUSDT',          # Likely invalid
            'MUBARAK': 'MUBARAKUSDT',    # Likely invalid
            'PIPPIN': 'PIPPINUSDT',      # Likely invalid
            'ZEREBRO': 'ZEREBROUSDT',    # Likely invalid
            'SWARMS': 'SWARMSUSDT',      # Likely invalid
            'KAITO': 'KAITOUSDT',        # Likely invalid
            'SHELL': 'SHELLUSDT',        # Likely invalid
            'RESOLV': 'RESOLVUSDT',      # Likely invalid
            'IDOL': 'IDOLUSDT',          # Likely invalid
            'CROSS': 'CROSSUSDT',        # Likely invalid
            'BULLA': 'BULLAUSDT',        # Likely invalid
            'VELVET': 'VELVETUSDT',      # Likely invalid
            'SOPH': 'SOPHUSDT',          # Likely invalid
            'EPIC': 'EPICUSDT',          # Likely invalid
            'TREE': 'TREEUSDT',          # Likely invalid
            'SKATE': 'SKATEUSDT',        # Likely invalid
            'TANSSI': 'TANSSIUSDT',      # Likely invalid
            'ICNT': 'ICNTUSDT',          # Likely invalid
            'TAC': 'TACUSDT',            # Likely invalid
            'CUDIS': 'CUDISUSDT',        # Likely invalid
            'DAM': 'DAMUSDT',            # Likely invalid
            'XPL': 'XPLUSDT',            # Likely invalid
            'GPS': 'GPSUSDT',            # Likely invalid
            'IP': 'IPUSDT',              # Likely invalid
            'BMT': 'BMTUSDT',            # Likely invalid
            'TUT': 'TUTUSDT',            # Likely invalid
            'BR': 'BRUSDT',              # Likely invalid
            'BERA': 'BERAUSDT',          # Likely invalid
            'H': 'HUSDT',                # Likely invalid
            'VIC': 'VICUSDT',            # Likely invalid
            'KERNEL': 'KERNELUSDT',      # Likely invalid
            'SIGN': 'SIGNUSDT',          # Likely invalid
            'DOLO': 'DOLOUSDT',          # Likely invalid
            'ATH': 'ATHUSDT',            # Likely invalid
            'AIOT': 'AIOTUSDT',          # Likely invalid
            'MAVIA': 'MAVIAUSDT',        # Likely invalid
            'VINE': 'VINEUSDT',          # Likely invalid
            'EPT': 'EPTUSDT',            # Likely invalid
            'SWELL': 'SWELLUSDT',        # Likely invalid
            'AGT': 'AGTUSDT',            # Likely invalid
            'PORT3': 'PORT3USDT',        # Likely invalid
            'NEWT': 'NEWTUSDT',          # Likely invalid
            'MYX': 'MYXUSDT',            # Likely invalid
            'BID': 'BIDUSDT',            # Likely invalid
            'OBOL': 'OBOLUSDT',          # Likely invalid
            'BDXN': 'BDXNUSDT',          # Likely invalid
            'PENGU': 'PENGUUSDT',        # Likely invalid
            'VVV': 'VVVUSDT',            # Likely invalid
            'BAN': 'BANUSDT',            # Likely invalid
            'ALPACA': 'ALPACAUSDT',      # Likely invalid
            'ALCH': 'ALCHUSDT',          # Likely invalid
            'TST': 'TSTUSDT',            # Likely invalid
            'LAYER': 'LAYERUSDT',        # Likely invalid
            'LUMIA': 'LUMIAUSDT',        # Likely invalid
            'HEI': 'HEIUSDT',            # Likely invalid
            'TROY': 'TROYUSDT',          # This one might be valid
            'REZ': 'REZUSDT',            # This one might be valid
            'BANANA': 'BANANAUSDT',      # This one might be valid
            'CAKE': 'CAKEUSDT',          # This one is likely valid
            'VIDT': 'VIDTUSDT',          # This one might be valid
            'ACH': 'ACHUSDT',            # This one might be valid
            'ORCA': 'ORCAUSDT',          # This one might be valid
            'MLN': 'MLNUSDT',            # This one is likely valid
            'FUN': 'FUNUSDT',            # This one might be valid
            'PUMP': 'PUMPUSDT',          # This one might be valid
            'FHE': 'FHEUSDT',            # Likely invalid
            'GUN': 'GUNUSDT',            # Likely invalid
            'INIT': 'INITUSDT',          # Likely invalid
            'BANK': 'BANKUSDT',          # Likely invalid
            'FLM': 'FLMUSDT',            # This one might be valid
            'RDNT': 'RDNTUSDT',          # This one might be valid
            'NKN': 'NKNUSDT',            # This one is likely valid
            'VOXEL': 'VOXELUSDT',        # This one might be valid
            'TRUMP': 'TRUMPUSDT',        # Likely invalid
            'MEMEFI': 'MEMEFIUSDT',      # Likely invalid
            'VIRTUAL': 'VIRTUALUSDT',    # Likely invalid
            'TURBO': 'TURBOUSDT',        # This one might be valid
            'VANA': 'VANAUSDT',          # This one might be valid
            'PEPE': 'PEPEUSDT',          # This one is definitely valid
            'ENA': 'ENAUSDT',            # This one might be valid
            'HYPE': 'HYPEUSDT',          # Likely invalid
            'A2Z': 'A2ZUSDT',            # Likely invalid
            'FORTH': 'FORTHUSDT',        # This one might be valid
            'IN': 'INUSDT',              # Likely invalid
            'MEME': 'MEMEUSDT',          # This one might be valid
            'BAND': 'BANDUSDT',          # This one is likely valid
            'UMA': 'UMAUSDT',            # This one is likely valid
            'RED': 'REDUSDT',            # Likely invalid
            'DOGS': 'DOGSUSDT',          # This one might be valid
            'ONG': 'ONGUSDT',            # This one might be valid
        }
        
        # Check if we have a specific mapping
        if coin in symbol_mappings:
            return symbol_mappings[coin]
        
        # Remove numeric suffixes (but keep 1000 prefix)
        if not coin.startswith('1000') and any(char.isdigit() for char in coin):
            # Remove trailing numbers
            import re
            coin = re.sub(r'\d+$', '', coin)
        
        return f"{coin}USDT"


@dataclass 
class AnalysisResult:
    """Represents the result of profit/loss analysis"""
    signal: TradingSignal
    first_hit: str  # 'PROFIT', 'LOSS', 'NEITHER', 'NO_FILL', 'SKIP', 'ERROR'
    hit_time: Optional[datetime]
    hours_to_hit: float
    loss_profit: float
    hit_date: Optional[str] = None
    entry_fill_time: Optional[datetime] = None
    entry_fill_price: Optional[float] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for CSV export"""
        return {
            'Date': self.signal.date,
            'Time': self.signal.time,
            'Coin_Name': self.signal.coin_name,
            'Entry_Price': self.signal.entry_price,
            'Entry_Fill_Time': self.entry_fill_time.strftime('%Y-%m-%d %H:%M:%S') if self.entry_fill_time else None,
            'Entry_Fill_Price': self.entry_fill_price,
            'Hit_Date': self.hit_date,
            'Loss_Profit': self.loss_profit,
            'Hours_to_Hit': self.hours_to_hit,
            'Result_Type': self.first_hit
        }


@dataclass
class PriceData:
    """Represents price data for a specific timeframe"""
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    timestamp: datetime