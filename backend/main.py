#!/usr/bin/env python3
"""
SofAi FX Bot - Main Entry Point

This script runs the trading bot that monitors forex pairs
and generates trading signals based on technical analysis
"""

import schedule
import time
from src.data.alpha_vantage import alpha_vantage
from src.signals.signal_generator import SignalGenerator
from src.notifications.telegram_notifier import TelegramNotifier
from src.notifications.email_notifier import EmailNotifier
from src.config import config
from src.utils.logger import logger

class ForexBot:
    def __init__(self):
        self.signal_generator = SignalGenerator()
        self.telegram = TelegramNotifier()
        self.email = EmailNotifier()
        self.is_running = False
    
    def analyze_pair(self, pair):
        """Analyze a single currency pair"""
        try:
            if '/' in pair:
                from_sym, to_sym = pair.split('/')
            else:
                from_sym = pair[:3]
                to_sym = pair[3:]
            
            logger.info(f'Analyzing {pair}...')
            
            # Fetch market data
            df = alpha_vantage.get_forex_data(from_sym, to_sym, interval='60min')
            
            if df is None or df.empty:
                logger.warning(f'Failed to fetch data for {pair}')
                return
            
            # Generate signal
            signal = self.signal_generator.generate_signal(df, pair)
            
            if signal and signal.signal.value != 'HOLD':
                logger.info(f'Signal generated: {signal}')
                
                # Send notifications
                self.telegram.send_signal(signal)
                self.email.send_signal(signal)
            
        except Exception as e:
            logger.error(f'Error analyzing {pair}: {e}')
    
    def analyze_all_pairs(self):
        """Analyze all configured currency pairs"""
        logger.info('Starting analysis of all pairs...')
        for pair in config.CURRENCY_PAIRS:
            self.analyze_pair(pair)
        logger.info('Analysis complete')
    
    def schedule_jobs(self):
        """Schedule periodic analysis"""
        # Run analysis every UPDATE_INTERVAL seconds
        schedule.every(config.UPDATE_INTERVAL).seconds.do(self.analyze_all_pairs)
        
        logger.info(f'Scheduled analysis every {config.UPDATE_INTERVAL} seconds')
        logger.info(f'Monitoring pairs: {", ".join(config.CURRENCY_PAIRS)}')
    
    def run(self):
        """Run the bot in continuous mode"""
        self.is_running = True
        logger.info('SofAi FX Bot started')
        logger.info(f'Telegram enabled: {self.telegram.is_configured()}')
        logger.info(f'Email enabled: {self.email.is_configured()}')
        
        self.schedule_jobs()
        
        # Run scheduled tasks
        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(10)  # Check every 10 seconds
        except KeyboardInterrupt:
            logger.info('Bot stopped by user')
            self.is_running = False

def main():
    bot = ForexBot()
    bot.run()

if __name__ == '__main__':
    main()
