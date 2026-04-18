import requests
import json
import pprint
from loguru import logger
from typing import Optional


class TelegramClient:
    def __init__(self, chat_id: str, token: str):
        self.chat_id = chat_id
        self.token = token

    def send_message_with_image(self, text: str, image_url: str, keyboard: Optional[list] = None):
        logger.debug("Sending telegram notification")
        data = {
            'chat_id': self.chat_id,
            'photo': image_url,
            'caption': text,
            'parse_mode': 'HTML',
        }

        if keyboard is not None:
            data.update({
                'reply_markup': json.dumps({
                    'inline_keyboard': keyboard
                })
            })
        response = requests.post(
            url=self.send_photo_endpoint,
            data=data,
        )
        logger.success(
            f"[TELEGRAM_NOTIFIER] {response.status_code} {pprint.pformat(response.json())}"
        )

    def send_message(self, text: str):
        logger.debug("Sending telegram text message")
        response = requests.post(
            url=self.send_message_endpoint,
            json={
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': 'HTML',
            },
        )
        logger.success(
            f"[TELEGRAM_NOTIFIER] {response.status_code} {pprint.pformat(response.json())}"
        )

    def answer_callback_query(
            self, callback_query_id: str, text: Optional[str] = None, show_alert: bool = False):
        response = requests.post(
            url=self.answer_callback_query,
            json={
                'callback_query_id': callback_query_id,
                'text': text,
                'show_alert': show_alert,
            },
        )
        logger.debug(f"answerCallbackQuery: {response.status_code} {response.text}")

    @property
    def send_photo_endpoint(self):
        return f'https://api.telegram.org/bot{self.token}/sendPhoto'

    @property
    def send_message_endpoint(self):
        return f'https://api.telegram.org/bot{self.token}/sendMessage'

    @property
    def answer_callback_query_endpoint(self):
        return f'https://api.telegram.org/bot{self.token}/answerCallbackQuery'

    @staticmethod
    def compose_keyboard(*buttons):
        return [[button] for button in buttons]
