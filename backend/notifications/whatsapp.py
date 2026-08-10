import logging
import os
import requests
from typing import Dict, Any
from .base import BaseNotificationProvider
from backend.config import Config

logger = logging.getLogger(__name__)

class WhatsAppNotificationProvider(BaseNotificationProvider):
    def send(self, event_type: str, shipment_id: int, message: str, context: Dict[str, Any] = None) -> bool:
        try:
            tracking_num = context.get('tracking_number', 'UNKNOWN') if context else 'UNKNOWN'
            
            # Format a nice message template for WhatsApp
            template = f"📦 *ShipTrack AI Update*\n\n"
            template += f"ID: {tracking_num}\n"
            template += f"{message}\n\n"
            
            if context and 'location' in context:
                template += f"📍 Location: {context['location']}\n"
                
            token = Config.WHATSAPP_ACCESS_TOKEN
            phone_id = Config.WHATSAPP_PHONE_NUMBER_ID
            recipient = Config.WHATSAPP_RECIPIENT_NUMBER
            
            if token and phone_id and recipient:
                url = f"https://graph.facebook.com/v17.0/{phone_id}/messages"
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
                data = {
                    "messaging_product": "whatsapp",
                    "to": recipient,
                    "type": "text",
                    "text": {"body": template}
                }
                res = requests.post(url, headers=headers, json=data)
                if res.status_code not in (200, 201):
                    logger.error(f"WhatsApp API Error: {res.text}")
                    return False
                logger.info("Real WhatsApp message sent successfully.")
                return True
            else:
                # MOCK IMPLEMENTATION
                logger.info("=" * 40)
                logger.info("MOCK WHATSAPP MESSAGE DISPATCHED")
                logger.info("-" * 40)
                logger.info(template)
                logger.info("=" * 40)
                return True
        except Exception as e:
            logger.error(f"Failed to dispatch WhatsApp notification: {e}")
            return False
