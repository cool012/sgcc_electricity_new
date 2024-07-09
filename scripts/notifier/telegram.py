from abc import ABC

import requests

from scripts.notifier.base_notifier import BaseNotifier


class TelegramNotifier(BaseNotifier, ABC):

    def __init__(self, token: str, chat_id: int, user_id, balance):
        super().__init__(user_id, balance)
        self.token = token
        self.chat_id = chat_id

    def send(self):
        url = 'https://api.telegram.org/bot{}/sendMessage'.format(self.token)
        text = f"[电费余额不足提醒] 当前电费余额为：{self.balance}元，请及时充值。"
        data = {
            'chat_id': self.chat_id,
            'text': text
        }
        response = requests.post(url=url, json=data)
        response.raise_for_status()
