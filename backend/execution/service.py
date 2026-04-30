"""
MT5 Execution Service - Main orchestrator for automated trading

This is the core service that:
1. Connects to MT5 terminal
2. Fetches signals from the backend API
3. Validates signals
4. Executes trades with risk management
5. Monitors open positions
6. Logs all activities
"""

import logging
import threading
import time
from typing import Optional, Dict
from datetime import datetime, timedelta
from pathlib import Path

from execution.mt5.connection import get_mt5_connection, SymbolMapper
from execution.engines.position_sizer import PositionSizer
from execution.engines.validator import TradeValidator
from execution.engines.executor import create_order_executor
from execution.engines.signal_listener import create_signal_listener
from execution.engines.logger import get_execution_logger
from pathlib import Path

# Get the script's directory for log paths
script_dir = Path(__file__).parent.parent
log_dir = script_dir / 'execution' / 'logs'
log_dir.mkdir(parents=True, exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'execution_service.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class ExecutionService:
    """
    Main execution service for automated trading.
    """
    
    def __init__(
        self,
        mt5_account: int,
        mt5_password: str,
        mt5_server: str = "ICMarkets-Demo",
        api_base_url: str = "http://localhost:5000",
        user_id: int = None,
        polling_interval: int = 30
    ):
        """
        Initialize execution service.
        
        Args:
            mt5_account: MT5 account number
            mt5_password: MT5 password
            mt5_server: MT5 server name
            api_base_url: Backend API base URL
            user_id: User ID for signal fetching
            polling_interval: Signal polling interval in seconds
        """
        self.mt5_account = mt5_account
        self.mt5_password = mt5_password
        self.mt5_server = mt5_server
        self.api_base_url = api_base_url
        self.user_id = user_id
        self.polling_interval = polling_interval
        
        # Components
        self.mt5 = None
        self.signal_listener = None
        self.executor = None
        self.sizer = None
        self.validator = None
        self.logger = get_execution_logger()
        
        # Service state
        self.is_running = False
        self.bot_enabled = True  # Kill switch
        self.listener_thread = None
        self.monitor_thread = None
        
        # Statistics
        self.total_signals_processed = 0
        self.total_trades_executed = 0
        self.total_trades_closed = 0
        self.today_pnl = 0.0
        
        logger.info("=" * 70)
        logger.info("MT5 EXECUTION SERVICE INITIALIZED")
        logger.info("=" * 70)
    
    def start(self) -> bool:
        """
        Start the execution service.
        
        Returns:
            bool: True if successfully started
        """
        try:
            logger.info("Starting MT5 Execution Service...")
            
            # Step 1: Connect to MT5
            logger.info("Step 1: Connecting to MT5...")
            self.mt5 = get_mt5_connection(self.mt5_account, self.mt5_password, self.mt5_server)
            if not self.mt5:
                logger.error("Failed to connect to MT5 - check terminal is running and credentials are correct")
                return False
            
            # Step 2: Initialize components
            logger.info("Step 2: Initializing components...")
            account_info = self.mt5.get_account_info()
            self.sizer = PositionSizer(account_info['balance'], account_info['leverage'])
            self.validator = TradeValidator()
            self.executor = create_order_executor(self.mt5)
            self.signal_listener = create_signal_listener(self.api_base_url, self.user_id, self.polling_interval)
            
            # Initialize symbol mapper for auto-detecting broker symbols
            logger.info("Step 2b: Fetching broker symbols...")
            self.symbol_mapper = SymbolMapper(self.mt5)
            broker_symbols = self.symbol_mapper.get_symbol_map()
            logger.info(f"Loaded {len(broker_symbols)} broker symbols")
            
            # Step 3: Start listener thread
            logger.info("Step 3: Starting signal listener...")
            self.listener_thread = threading.Thread(
                target=self.signal_listener.poll_signals,
                kwargs={'callback': self._on_signal_received},
                daemon=True
            )
            self.listener_thread.start()
            
            # Step 4: Start monitor thread
            logger.info("Step 4: Starting position monitor...")
            self.monitor_thread = threading.Thread(
                target=self._monitor_positions,
                daemon=True
            )
            self.monitor_thread.start()
            
            # Step 5: Start main processing loop
            logger.info("Step 5: Starting main processing loop...")
            self.is_running = True
            
            self.logger.log_event(
                event_type="SERVICE_STARTED",
                status="SUCCESS",
                message=f"MT5 Execution Service started successfully",
                user_id=self.user_id,
                details={
                    'account': self.mt5_account,
                    'server': self.mt5_server,
                    'balance': account_info['balance'],
                    'equity': account_info['equity']
                }
            )
            
            logger.info("=" * 70)
            logger.info("[OK] MT5 EXECUTION SERVICE RUNNING")
            logger.info("=" * 70)
            logger.info(f"Account: {account_info['login']}")
            logger.info(f"Balance: {account_info['balance']} {account_info['currency']}")
            logger.info(f"Equity: {account_info['equity']} {account_info['currency']}")
            logger.info(f"Leverage: {account_info['leverage']}:1")
            logger.info(f"Mode: {account_info['trade_mode']}")
            logger.info("=" * 70)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start execution service: {e}", exc_info=True)
            self.logger.log_error(
                error_message=f"Failed to start execution service: {e}",
                error_type="SERVICE_START_ERROR",
                user_id=self.user_id
            )
            return False
    
    def stop(self) -> None:
        """Stop the execution service."""
        try:
            logger.info("Stopping MT5 Execution Service...")
            
            self.is_running = False
            
            # Stop signal listener
            if self.signal_listener:
                self.signal_listener.stop()
            
            # Close any open positions (optional - disable if you want to keep positions)
            # self._close_all_positions()
            
            # Disconnect from MT5
            if self.mt5:
                self.mt5.disconnect()
            
            self.logger.log_event(
                event_type="SERVICE_STOPPED",
                status="SUCCESS",
                message="MT5 Execution Service stopped",
                user_id=self.user_id,
                details={
                    'total_signals_processed': self.total_signals_processed,
                    'total_trades_executed': self.total_trades_executed,
                    'today_pnl': self.today_pnl
                }
            )
            
            logger.info("=" * 70)
            logger.info("[OK] MT5 EXECUTION SERVICE STOPPED")
            logger.info("=" * 70)
            logger.info(f"Total signals processed: {self.total_signals_processed}")
            logger.info(f"Total trades executed: {self.total_trades_executed}")
            logger.info(f"Total trades closed: {self.total_trades_closed}")
            logger.info(f"Today's P&L: ${self.today_pnl:.2f}")
            logger.info("=" * 70)
            
        except Exception as e:
            logger.error(f"Error stopping service: {e}", exc_info=True)
    
    def run(self) -> None:
        """
        Run the main execution loop (blocking).
        """
        try:
            if not self.start():
                logger.error("Failed to start service")
                return
            
            # Main loop
            while self.is_running:
                try:
                    # Process pending signals
                    signal = self.signal_listener.get_next_signal()
                    if signal:
                        self._process_signal(signal)
                    
                    # Brief sleep to prevent CPU spinning
                    time.sleep(1)
                    
                except KeyboardInterrupt:
                    logger.info("Keyboard interrupt - stopping service")
                    break
                except Exception as e:
                    logger.error(f"Error in main loop: {e}", exc_info=True)
                    time.sleep(5)
            
            self.stop()
            
        except Exception as e:
            logger.error(f"Fatal error in run loop: {e}", exc_info=True)
            self.stop()
    
    def _on_signal_received(self, signals: list) -> None:
        """
        Callback when signals are received.
        
        Args:
            signals: List of signals
        """
        logger.info(f"Received {len(signals)} signal(s)")
        for signal in signals:
            logger.info(
                f"  - {signal.get('symbol')} {signal.get('signal_type')} "
                f"@ {signal.get('price')} (confidence: {signal.get('confidence', 0):.2%})"
            )
    
    def _process_signal(self, signal: Dict) -> None:
        """
        Process a single signal.
        
        Args:
            signal: Signal dictionary
        """
        try:
            symbol = signal.get('symbol', 'UNKNOWN')
            
            # Normalize symbol to ensure .m suffix for MT5
            if not symbol.endswith('.m'):
                symbol = symbol + '.m'
            
            logger.info(f"\n{'=' * 70}")
            logger.info(f"PROCESSING SIGNAL: {symbol}")
            logger.info(f"{'=' * 70}")
            
            self.total_signals_processed += 1
            
            # Log signal receipt
            self.logger.log_event(
                event_type="SIGNAL_RECEIVED",
                status="SUCCESS",
                message=f"Signal received: {symbol} {signal.get('signal_type')}",
                symbol=symbol,
                user_id=self.user_id,
                details=signal
            )
            
            # Check bot enabled
            if not self.bot_enabled:
                self.logger.log_event(
                    event_type="SIGNAL_REJECTED",
                    status="FAILED",
                    message="Bot disabled (kill switch)",
                    symbol=symbol,
                    user_id=self.user_id
                )
                logger.warning("Bot is disabled - skipping signal")
                return
            
            # Resolve symbol to broker format using auto-detect mapper
            resolved_symbol = self.symbol_mapper.resolve_symbol(symbol)
            if not resolved_symbol:
                self.logger.log_event(
                    event_type="SYMBOL_LOOKUP_FAILED",
                    status="FAILED",
                    message=f"Symbol {symbol} not found in broker symbols",
                    symbol=symbol,
                    user_id=self.user_id
                )
                logger.error(f"Symbol {symbol} not available in broker - skipping execution")
                return
            
            # Use resolved broker symbol for MT5 operations
            logger.info(f"Symbol resolved: {symbol} -> {resolved_symbol}")
            symbol = resolved_symbol
            
            # Get symbol info from MT5
            symbol_info = self.mt5.get_symbol_info(symbol)
            if not symbol_info:
                self.logger.log_event(
                    event_type="SYMBOL_LOOKUP_FAILED",
                    status="FAILED",
                    message=f"Symbol {symbol} not found in MT5",
                    symbol=symbol,
                    user_id=self.user_id
                )
                return
            
            # Get account and position info
            account_info = self.mt5.get_account_info()
            open_positions = self.mt5.get_open_positions()
            
            # Validate signal
            is_valid, validation_reason = self.validator.validate_signal(
                signal=signal,
                symbol_info=symbol_info,
                open_positions=open_positions,
                account_info=account_info,
                today_pnl=self.today_pnl,
                bot_enabled=self.bot_enabled
            )
            
            if not is_valid:
                self.logger.log_event(
                    event_type="SIGNAL_VALIDATION_FAILED",
                    status="FAILED",
                    message=f"Signal validation failed: {validation_reason}",
                    symbol=symbol,
                    user_id=self.user_id
                )
                logger.warning(f"Signal validation failed: {validation_reason}")
                return
            
            self.logger.log_event(
                event_type="SIGNAL_VALIDATION_PASSED",
                status="SUCCESS",
                message="Signal passed all validations",
                symbol=symbol,
                user_id=self.user_id
            )
            
            # Calculate position size
            try:
                # Get entry and exit prices from signal or use current market price
                entry_price = signal.get('price') or symbol_info.get('ask')
                sl_price = signal.get('stop_loss')
                tp_price = signal.get('take_profit')
                signal_type = signal.get('signal_type', 'HOLD')
                
                # If SL/TP missing, calculate them automatically
                if not sl_price or not tp_price:
                    logger.info(f"SL/TP missing in signal, calculating automatically...")
                    sl_price, tp_price = self._calculate_sl_tp_auto(entry_price, signal_type)
                    if not sl_price or not tp_price:
                        logger.warning(f"Failed to calculate SL/TP - cannot execute")
                        self.logger.log_event(
                            event_type="SIGNAL_INCOMPLETE",
                            status="FAILED",
                            message="Failed to calculate SL/TP prices",
                            symbol=symbol,
                            user_id=self.user_id
                        )
                        return
                
                # Get user preferences for risk
                user_risk_percent = signal.get('risk_percent', 1.0)
                
                lot_size = self.sizer.calculate_lot_size(
                    symbol=symbol,
                    entry_price=entry_price,
                    stop_loss_price=sl_price,
                    risk_percent=user_risk_percent
                )
                
                # Validate margin
                if not self.sizer.validate_margin(symbol, lot_size, entry_price, account_info.get('free_margin', 0)):
                    self.logger.log_event(
                        event_type="MARGIN_INSUFFICIENT",
                        status="FAILED",
                        message=f"Insufficient margin for {lot_size:.2f} lots",
                        symbol=symbol,
                        user_id=self.user_id
                    )
                    logger.warning("Insufficient margin - rejecting trade")
                    return
                
                # Place order
                order_type = signal.get('signal_type')  # BUY or SELL
                success, order_info = self.executor.place_market_order(
                    symbol=symbol,
                    order_type=order_type,
                    volume=lot_size,
                    entry_price=entry_price,
                    stop_loss=sl_price,
                    take_profit=tp_price,
                    comment=f"Signal: {signal.get('reason', 'Auto-generated')}"
                )
                
                if success:
                    self.total_trades_executed += 1
                    
                    self.logger.log_event(
                        event_type="ORDER_PLACED",
                        status="SUCCESS",
                        message=f"Order placed: {order_type} {lot_size:.2f} lots",
                        symbol=symbol,
                        user_id=self.user_id,
                        details=order_info
                    )
                    
                    logger.info(f"[OK] Trade executed successfully!")
                    logger.info(f"  Type: {order_type} | Volume: {lot_size:.2f}")
                    logger.info(f"  Entry: {entry_price:.5f} | SL: {sl_price:.5f} | TP: {tp_price:.5f}")
                    logger.info(f"  Risk: ${(account_info['balance'] * user_risk_percent / 100):.2f}")
                    
                else:
                    self.logger.log_event(
                        event_type="ORDER_FAILED",
                        status="FAILED",
                        message=f"Failed to place order: {order_info.get('error', 'Unknown error')}",
                        symbol=symbol,
                        user_id=self.user_id,
                        details=order_info
                    )
                    logger.error(f"✗ Order placement failed: {order_info.get('error')}")
                
            except Exception as e:
                logger.error(f"Error processing signal: {e}", exc_info=True)
                self.logger.log_error(
                    error_message=f"Error processing signal for {symbol}: {e}",
                    error_type="SIGNAL_PROCESSING_ERROR",
                    user_id=self.user_id
                )
            
        except Exception as e:
            logger.error(f"Critical error processing signal: {e}", exc_info=True)
            self.logger.log_error(
                error_message=f"Critical error processing signal: {e}",
                error_type="CRITICAL_ERROR",
                user_id=self.user_id
            )
    
    def _monitor_positions(self) -> None:
        """
        Monitor open positions and update stats.
        """
        logger.info("Position monitor started")
        
        while self.is_running:
            try:
                # Get current account info
                account_info = self.mt5.get_account_info()
                if account_info:
                    self.today_pnl = account_info.get('equity', 0) - account_info.get('balance', 0)
                
                # Get open positions
                open_positions = self.mt5.get_open_positions()
                
                if open_positions:
                    logger.debug(f"Monitoring {len(open_positions)} open position(s)")
                    total_pnl = sum(p['pnl'] for p in open_positions)
                    logger.debug(f"  Total P&L: ${total_pnl:.2f}")
                
                # Sleep before next check
                time.sleep(10)
                
            except Exception as e:
                logger.error(f"Error in position monitor: {e}", exc_info=True)
                time.sleep(10)
    
    def _close_all_positions(self) -> None:
        """Close all open positions (use cautiously)."""
        try:
            positions = self.mt5.get_open_positions()
            logger.warning(f"Closing {len(positions)} open position(s)...")
            
            for position in positions:
                self.executor.close_position(position['symbol'])
                time.sleep(0.5)
            
            logger.info("All positions closed")
        except Exception as e:
            logger.error(f"Error closing positions: {e}")
    
    def _calculate_sl_tp_auto(self, entry_price: float, signal_type: str):
        """
        Automatically calculate Stop Loss and Take Profit if missing.
        Uses 1:2 risk-reward ratio.
        
        Args:
            entry_price: Entry price
            signal_type: Signal type (BUY, SELL, HOLD)
        
        Returns:
            tuple: (stop_loss, take_profit)
        """
        try:
            if not entry_price or signal_type == 'HOLD':
                return None, None
            
            # Risk-reward ratio
            rr_ratio = 2.0
            
            # For forex, use pips. 20 pips distance for standard risk
            pip_distance = 0.0020  # 20 pips for most pairs (0.0001 * 20)
            
            if signal_type == 'BUY':
                # Stop loss below entry
                stop_loss = entry_price - pip_distance
                # Take profit above entry (1:2 ratio)
                take_profit = entry_price + (pip_distance * rr_ratio)
            elif signal_type == 'SELL':
                # Stop loss above entry
                stop_loss = entry_price + pip_distance
                # Take profit below entry (1:2 ratio)
                take_profit = entry_price - (pip_distance * rr_ratio)
            else:
                return None, None
            
            return round(stop_loss, 5), round(take_profit, 5)
        except Exception as e:
            logger.error(f"Error calculating SL/TP: {e}")
            return None, None
    
    def toggle_bot(self, enabled: bool) -> None:
        """
        Toggle bot on/off (kill switch).
        
        Args:
            enabled: True to enable, False to disable
        """
        self.bot_enabled = enabled
        status = "ENABLED" if enabled else "DISABLED"
        logger.warning(f"Bot {status} (kill switch)")
        
        self.logger.log_event(
            event_type="BOT_TOGGLED",
            status="SUCCESS",
            message=f"Bot {status}",
            user_id=self.user_id
        )


def main():
    """
    Main entry point for the execution service.
    
    Configure MT5 credentials and API details below.
    """
    
    # ===== CONFIGURATION =====
    MT5_ACCOUNT = 1234567  # Your MT5 account number
    MT5_PASSWORD = "your_password"  # Your MT5 password
    MT5_SERVER = "ICMarkets-Demo"  # Server name (use Demo for testing)
    
    API_BASE_URL = "http://localhost:5000"  # Backend API URL
    USER_ID = 1  # Your user ID
    
    # ===== START SERVICE =====
    service = ExecutionService(
        mt5_account=MT5_ACCOUNT,
        mt5_password=MT5_PASSWORD,
        mt5_server=MT5_SERVER,
        api_base_url=API_BASE_URL,
        user_id=USER_ID,
        polling_interval=30  # Poll signals every 30 seconds
    )
    
    try:
        service.run()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        service.stop()


if __name__ == '__main__':
    main()
