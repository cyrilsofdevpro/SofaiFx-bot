import asyncio
from telegram import Bot
from telegram.error import TelegramError
from src.config import config
from src.utils.logger import logger

class TelegramNotifier:
    """Send trading signals via Telegram bot"""
    
    def __init__(self, bot_token=None, chat_id=None):
        self.bot_token = bot_token or config.TELEGRAM_BOT_TOKEN
        self.chat_id = chat_id or config.TELEGRAM_CHAT_ID
        self.bot = None
        
        if self.bot_token:
            self.bot = Bot(token=self.bot_token)
    
    def is_configured(self):
        """Check if Telegram is properly configured"""
        return bool(self.bot_token and self.chat_id)
    
    def send_signal(self, signal):
        """
        Send a trading signal to Telegram
        
        Args:
            signal: CombinedSignal object from signal_generator
        """
        if not self.is_configured():
            logger.warning('Telegram not configured. Skipping notification.')
            return False
        
        try:
            message = self._format_signal_message(signal)
            
            # Run async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.bot.send_message(chat_id=self.chat_id, text=message, parse_mode='HTML')
            )
            loop.close()
            
            logger.info(f'Telegram message sent for {signal.symbol}')
            return True
        
        except TelegramError as e:
            logger.error(f'Telegram error: {e}')
            return False
        except Exception as e:
            logger.error(f'Error sending Telegram message: {e}')
            return False
    
    def _format_signal_message(self, signal):
        """Format signal as Telegram message"""
        emoji = '📈' if signal.signal.value == 'BUY' else '📉' if signal.signal.value == 'SELL' else '⏸️'
        
        message = f"""
{emoji} <b>SofAi FX Trading Signal</b>

<b>Pair:</b> {signal.symbol}
<b>Signal:</b> <b>{signal.signal.value}</b>
<b>Price:</b> {signal.price:.4f}
<b>Confidence:</b> {signal.confidence:.0%}

<b>Reason:</b>
{signal.reason}

<b>Analysis:</b>
• RSI: {signal.rsi_signal.signal.value if signal.rsi_signal else 'N/A'}
• MA: {signal.ma_signal.signal.value if signal.ma_signal else 'N/A'}

⏰ <i>{signal.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</i>
        """.strip()
        
        return message
