"""Position management for concurrent trading"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging

from ..models import TradingSignal, AnalysisResult

logger = logging.getLogger(__name__)


@dataclass
class OpenPosition:
    """Represents an open trading position"""
    signal: TradingSignal
    entry_fill_time: datetime
    entry_fill_price: float
    position_size: float
    risk_amount: float
    stop_loss_price: float
    take_profit_price: float
    position_id: str
    sl_moved_to_entry: bool = False  # Track if SL has been moved to entry
    
    def __post_init__(self):
        """Generate unique position ID"""
        if not self.position_id:
            self.position_id = f"{self.signal.coin_name}_{self.entry_fill_time.strftime('%Y%m%d_%H%M%S')}"


@dataclass
class ClosedPosition:
    """Represents a closed trading position"""
    position: OpenPosition
    close_time: datetime
    close_reason: str  # 'PROFIT', 'LOSS', 'TIMEOUT'
    pnl: float
    hours_held: float


class PositionManager:
    """Manages concurrent trading positions"""
    
    def __init__(self, initial_capital: float, risk_per_trade_pct: float, move_sl_to_entry_pct: float = 3.0):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.risk_per_trade_pct = risk_per_trade_pct
        self.move_sl_to_entry_pct = move_sl_to_entry_pct  # Percentage move required to move SL to entry
        
        # Track positions
        self.open_positions: Dict[str, OpenPosition] = {}
        self.closed_positions: List[ClosedPosition] = []
        self.pending_signals: List[TradingSignal] = []
        
        # Track capital allocation
        self.allocated_capital = 0.0  # Capital tied up in open positions
        self.available_capital = initial_capital
        
    def add_signal(self, signal: TradingSignal) -> None:
        """Add a new trading signal to pending list"""
        self.pending_signals.append(signal)
        logger.debug(f"Added signal: {signal.coin_name} at {signal.timestamp}")
    
    def check_limit_fills(self, current_time: datetime, price_data: Dict[str, float]) -> List[OpenPosition]:
        """Check if any pending signals can fill their limit orders"""
        filled_positions = []
        signals_to_remove = []
        
        for signal in self.pending_signals:
            # Skip if signal timestamp is in the future
            if signal.timestamp > current_time:
                continue
                
            # Check if we have price data for this symbol
            symbol = signal.symbol
            if symbol not in price_data:
                continue
                
            current_price = price_data[symbol]
            
            # For long positions: limit fills when current price <= limit price
            if current_price <= signal.entry_price:
                # Calculate position size based on current available capital
                risk_amount = self.available_capital * (self.risk_per_trade_pct / 100)
                
                # Skip if not enough capital
                if risk_amount <= 0:
                    logger.warning(f"Insufficient capital for {signal.coin_name}: Available={self.available_capital:.2f}")
                    continue
                
                position_size = risk_amount / (signal.entry_price * 0.10)  # Assuming 10% stop loss for position sizing
                
                # Create open position
                position = OpenPosition(
                    signal=signal,
                    entry_fill_time=current_time,
                    entry_fill_price=signal.entry_price,
                    position_size=position_size,
                    risk_amount=risk_amount,
                    stop_loss_price=signal.entry_price * 0.90,  # 10% stop loss
                    take_profit_price=signal.entry_price * 1.15,  # 15% take profit (1:1.5 risk/reward)
                    position_id=""
                )
                
                # Update capital allocation
                self.allocated_capital += risk_amount
                self.available_capital -= risk_amount
                
                # Add to open positions
                self.open_positions[position.position_id] = position
                filled_positions.append(position)
                signals_to_remove.append(signal)
                
                logger.info(f"Limit filled: {signal.coin_name} at ${signal.entry_price:.4f}, Risk: ${risk_amount:.2f}")
        
        # Remove filled signals from pending
        for signal in signals_to_remove:
            self.pending_signals.remove(signal)
            
        return filled_positions
    
    def check_position_exits(self, current_time: datetime, price_data: Dict[str, float]) -> List[ClosedPosition]:
        """Check if any open positions should be closed"""
        closed_positions = []
        positions_to_remove = []
        
        for position_id, position in self.open_positions.items():
            symbol = position.signal.symbol
            
            if symbol not in price_data:
                continue
                
            current_price = price_data[symbol]
            
            # Check if we should move SL to entry (trailing stop)
            if not position.sl_moved_to_entry:
                price_increase_pct = ((current_price - position.entry_fill_price) / position.entry_fill_price) * 100
                if price_increase_pct >= self.move_sl_to_entry_pct:
                    position.stop_loss_price = position.entry_fill_price
                    position.sl_moved_to_entry = True
                    logger.info(f"SL moved to entry for {position.signal.coin_name}: Price up {price_increase_pct:.2f}% (>= {self.move_sl_to_entry_pct}%)")
            
            # Check for take profit
            if current_price >= position.take_profit_price:
                pnl = position.risk_amount * 1.5  # 1:1.5 risk/reward
                hours_held = (current_time - position.entry_fill_time).total_seconds() / 3600
                
                closed_pos = ClosedPosition(
                    position=position,
                    close_time=current_time,
                    close_reason='PROFIT',
                    pnl=pnl,
                    hours_held=hours_held
                )
                
                closed_positions.append(closed_pos)
                positions_to_remove.append(position_id)
                
                # Update capital
                self.current_capital += pnl
                self.available_capital += position.risk_amount + pnl
                self.allocated_capital -= position.risk_amount
                
                logger.info(f"Take profit hit: {position.signal.coin_name} +${pnl:.2f}")
                
            # Check for stop loss
            elif current_price <= position.stop_loss_price:
                # Calculate PnL based on whether SL was moved to entry or not
                if position.sl_moved_to_entry and position.stop_loss_price == position.entry_fill_price:
                    pnl = 0  # Breakeven if SL was moved to entry
                    logger.info(f"Breakeven exit: {position.signal.coin_name} (SL at entry)")
                else:
                    pnl = -position.risk_amount  # Full risk amount lost
                    logger.info(f"Stop loss hit: {position.signal.coin_name} -${abs(pnl):.2f}")
                
                hours_held = (current_time - position.entry_fill_time).total_seconds() / 3600
                
                closed_pos = ClosedPosition(
                    position=position,
                    close_time=current_time,
                    close_reason='LOSS' if pnl < 0 else 'BREAKEVEN',
                    pnl=pnl,
                    hours_held=hours_held
                )
                
                closed_positions.append(closed_pos)
                positions_to_remove.append(position_id)
                
                # Update capital
                self.current_capital += pnl
                self.available_capital += position.risk_amount + pnl
                self.allocated_capital -= position.risk_amount
        
        # Remove closed positions from open positions
        for position_id in positions_to_remove:
            del self.open_positions[position_id]
            
        return closed_positions
    
    def get_portfolio_summary(self) -> Dict:
        """Get current portfolio summary"""
        total_pnl = sum([pos.pnl for pos in self.closed_positions])
        
        winning_trades = len([pos for pos in self.closed_positions if pos.pnl > 0])
        losing_trades = len([pos for pos in self.closed_positions if pos.pnl < 0])
        total_trades = len(self.closed_positions)
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        return {
            'initial_capital': self.initial_capital,
            'current_capital': self.current_capital,
            'available_capital': self.available_capital,
            'allocated_capital': self.allocated_capital,
            'total_pnl': total_pnl,
            'total_return_pct': (total_pnl / self.initial_capital) * 100,
            'open_positions_count': len(self.open_positions),
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'closed_positions': self.closed_positions
        }