import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from src.config import config
from src.utils.logger import logger

class EmailNotifier:
    """Send trading signals via Email"""
    
    def __init__(self, smtp_server=None, smtp_port=None, sender_email=None, sender_password=None):
        self.smtp_server = smtp_server or config.SMTP_SERVER
        self.smtp_port = smtp_port or config.SMTP_PORT
        self.sender_email = sender_email or config.SENDER_EMAIL
        self.sender_password = sender_password or config.SENDER_PASSWORD
    
    def is_configured(self):
        """Check if Email is properly configured"""
        return bool(self.sender_email and self.sender_password)
    
    def send_signal(self, signal, recipient_email=None):
        """
        Send a trading signal via email
        
        Args:
            signal: CombinedSignal object
            recipient_email: Email address to send to
        """
        if not self.is_configured():
            logger.warning('Email not configured. Skipping notification.')
            return False
        
        if not recipient_email:
            recipient_email = self.sender_email
        
        try:
            subject = f"🚀 SofAi FX Signal: {signal.signal.value} {signal.symbol}"
            body = self._format_signal_email(signal)
            
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = self.sender_email
            message['To'] = recipient_email
            
            # Create HTML email
            html_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif; background-color: #f5f5f5;">
                    <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px;">
                        <h2 style="color: #2c3e50;">📊 SofAi FX Trading Signal</h2>
                        <hr style="border: none; border-top: 2px solid #ecf0f1;">
                        
                        <p><strong>Pair:</strong> {signal.symbol}</p>
                        <p><strong>Signal:</strong> <span style="color: {'green' if signal.signal.value == 'BUY' else 'red' if signal.signal.value == 'SELL' else 'orange'}; font-size: 18px;"><b>{signal.signal.value}</b></span></p>
                        <p><strong>Price:</strong> {signal.price:.4f}</p>
                        <p><strong>Confidence:</strong> {signal.confidence:.0%}</p>
                        
                        <h3 style="color: #34495e;">Analysis Details</h3>
                        <p><strong>Reason:</strong><br/>{signal.reason}</p>
                        
                        <p><strong>Strategy Signals:</strong></p>
                        <ul>
                            <li>RSI: {signal.rsi_signal.signal.value if signal.rsi_signal else 'N/A'}</li>
                            <li>Moving Average: {signal.ma_signal.signal.value if signal.ma_signal else 'N/A'}</li>
                        </ul>
                        
                        <hr style="border: none; border-top: 1px solid #ecf0f1;">
                        <p style="color: #7f8c8d; font-size: 12px;">
                            Sent: {signal.timestamp.strftime('%Y-%m-%d %H:%M:%S')}<br/>
                            Disclaimer: This signal is for educational purposes only. Always do your own research.
                        </p>
                    </div>
                </body>
            </html>
            """
            
            message.attach(MIMEText(html_body, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)
            
            logger.info(f'Email sent to {recipient_email} for {signal.symbol}')
            return True
        
        except smtplib.SMTPException as e:
            logger.error(f'SMTP error: {e}')
            return False
        except Exception as e:
            logger.error(f'Error sending email: {e}')
            return False
    
    def _format_signal_email(self, signal):
        """Format signal for email body"""
        return f"""
Trading Signal Alert

Pair: {signal.symbol}
Signal: {signal.signal.value}
Price: {signal.price:.4f}
Confidence: {signal.confidence:.0%}

Reason: {signal.reason}

Strategy Signals:
- RSI: {signal.rsi_signal.signal.value if signal.rsi_signal else 'N/A'}
- Moving Average: {signal.ma_signal.signal.value if signal.ma_signal else 'N/A'}

Time: {signal.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
        """
