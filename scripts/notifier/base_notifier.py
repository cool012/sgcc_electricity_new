from abc import ABCMeta, abstractmethod

from scripts.notifier.PushPlus import PushPlusNotifier
from scripts.notifier.telegram import TelegramNotifier


class BaseNotifier(metaclass=ABCMeta):

    def __init__(self, user_id, balance):
        self.user_id = user_id
        self.balance = balance

    @abstractmethod
    def send(self):
        pass

    def sendNotify(self, notify_type, args: dict):
        if notify_type is None:
            return
        if notify_type == 'PushPlus':
            PushPlusNotifier(args['pushplus_token'], self.user_id, self.balance).send()
        elif notify_type == 'Telegram':
            TelegramNotifier(args['telegram_token'], args['telegram_chat_id'], self.user_id, self.balance).send()
