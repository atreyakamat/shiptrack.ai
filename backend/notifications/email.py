import logging
import smtplib
from email.message import EmailMessage
import os
from typing import Dict, Any
from .base import BaseNotificationProvider

logger = logging.getLogger(__name__)

class EmailNotificationProvider(BaseNotificationProvider):
    def send(self, event_type: str, shipment_id: int, message: str, context: Dict[str, Any] = None) -> bool:
        try:
            tracking_num = context.get('tracking_number', 'UNKNOWN') if context else 'UNKNOWN'
            
            subject = f"Shipment Update - {tracking_num}"
            body = f"Hello,\n\nThere is an update for your shipment {tracking_num}:\n\n{message}\n\n"
            
            if context and 'location' in context:
                body += f"Location: {context['location']}\n"
                
            body += "\nThank you for using ShipTrack AI."
            
            smtp_host = os.getenv('SMTP_HOST')
            smtp_port = os.getenv('SMTP_PORT', '587')
            smtp_user = os.getenv('SMTP_USER')
            smtp_pass = os.getenv('SMTP_PASS')
            recipient = os.getenv('EMAIL_RECIPIENT')
            
            if smtp_host and smtp_user and smtp_pass and recipient:
                msg = EmailMessage()
                msg.set_content(body)
                msg['Subject'] = subject
                msg['From'] = smtp_user
                msg['To'] = recipient
                
                with smtplib.SMTP(smtp_host, int(smtp_port)) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_pass)
                    server.send_message(msg)
                logger.info("Real Email message sent successfully.")
                return True
            else:
                # MOCK IMPLEMENTATION
                logger.info("=" * 40)
                logger.info("MOCK EMAIL DISPATCHED")
                logger.info("-" * 40)
                logger.info(f"Subject: {subject}\n\n{body}")
                logger.info("=" * 40)
                return True
        except Exception as e:
            logger.error(f"Failed to dispatch Email notification: {e}")
            return False
