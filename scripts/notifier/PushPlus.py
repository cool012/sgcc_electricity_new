from abc import ABC

import requests

from scripts.notifier.base_notifier import BaseNotifier


class PushPlusNotifier(BaseNotifier, ABC):

    def __init__(self, token: list, user_id, balance):
        super().__init__(user_id, balance)
        self.token = token

    def send(self):
        for t in self.token:
            title = '电费余额不足提醒'
            content = f'您用户号{self.user_id}的当前电费余额为：{self.balance}元，请及时充值。'
            url = 'http://www.pushplus.plus/send?token=' + t + '&title=' + title + '&content=' + content
            response = requests.get(url)
            response.raise_for_status()
