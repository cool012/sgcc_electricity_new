import logging
import logging.config
import os
import sys
import time
import traceback
from datetime import datetime,timedelta

import dotenv
import schedule

from const import *
from data_fetcher import DataFetcher
from sensor_updator import SensorUpdator

from scripts.notifier.base_notifier import BaseNotifier

BALANCE = 0.0
PUSHPLUS_TOKEN = []
RECHARGE_NOTIFY = False
# 通知类型
NOTIFY_TYPE = None
# Telegram bot token
TELEGRAM_TOKEN = None
# Telegram chat id
TELEGRAM_CHAT_ID = 0


def main():
    # 读取 .env 文件
    dotenv.load_dotenv(verbose=True)
    global BALANCE
    global PUSHPLUS_TOKEN
    global RECHARGE_NOTIFY
    global NOTIFY_TYPE
    global TELEGRAM_TOKEN
    global TELEGRAM_CHAT_ID
    try:
        PHONE_NUMBER = os.getenv("PHONE_NUMBER")
        PASSWORD = os.getenv("PASSWORD")
        HASS_ENABLE = os.getenv("HASS_ENABLE", "false").lower == "true"
        HASS_URL = os.getenv("HASS_URL")
        HASS_TOKEN = os.getenv("HASS_TOKEN")
        JOB_START_TIME = os.getenv("JOB_START_TIME")
        LOG_LEVEL = os.getenv("LOG_LEVEL")
        VERSION = os.getenv("VERSION")
        BALANCE = float(os.getenv("BALANCE"))
        NOTIFY_TYPE = os.getenv("NOTIFY_TYPE")
        TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
        TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
        PUSHPLUS_TOKEN = os.getenv("PUSHPLUS_TOKEN").split(",")
        RECHARGE_NOTIFY = os.getenv("RECHARGE_NOTIFY", "false").lower() == "true"
    except Exception as e:
        logging.error(f"Failing to read the .env file, the program will exit with an error message: {e}.")
        sys.exit()

    logger_init(LOG_LEVEL)
    logging.info(f"The current repository version is {VERSION}, and the repository address is https://github.com/ARC-MX/sgcc_electricity_new.git")

    fetcher = DataFetcher(PHONE_NUMBER, PASSWORD)
    updator = SensorUpdator(HASS_URL, HASS_TOKEN, HASS_ENABLE)
    logging.info(f"The current logged-in user name is {PHONE_NUMBER}, the homeassistant address is {HASS_URL}, and the program will be executed every day at {JOB_START_TIME}.")

    next_run_time = datetime.strptime(JOB_START_TIME, "%H:%M") + timedelta(hours=12)
    logging.info(f'Run job now! The next run will be at {JOB_START_TIME} and {next_run_time.strftime("%H:%M")} every day')
    schedule.every().day.at(JOB_START_TIME).do(run_task, fetcher, updator)
    schedule.every().day.at(next_run_time.strftime("%H:%M")).do(run_task, fetcher, updator)
    run_task(fetcher, updator)

    while True:
        schedule.run_pending()
        time.sleep(1)


def run_task(data_fetcher: DataFetcher, sensor_updator: SensorUpdator):
    try:
        user_id_list, balance_list, last_daily_date_list, last_daily_usage_list, yearly_charge_list, yearly_usage_list, month_list, month_usage_list, month_charge_list = data_fetcher.fetch()
        for i in range(0, len(user_id_list)):
            profix = f"_{user_id_list[i]}" if len(user_id_list) > 1 else ""
            if balance_list[i] is not None:
                sensor_updator.update(BALANCE_SENSOR_NAME + profix, None, balance_list[i], BALANCE_UNIT)
                if balance_list[i] < BALANCE and RECHARGE_NOTIFY:
                    send_notify(user_id_list[i], balance_list[i])
                    logging.info(
                        f'The current balance of user id {user_id_list[i]} is {balance_list[i]} CNY less than {BALANCE}CNY, notice has been sent, please pay attention to check and recharge.')
            if last_daily_usage_list[i] is not None:
                sensor_updator.update(DAILY_USAGE_SENSOR_NAME + profix, last_daily_date_list[i], last_daily_usage_list[i], USAGE_UNIT)
            if yearly_usage_list[i] is not None:
                sensor_updator.update(YEARLY_USAGE_SENSOR_NAME + profix, None, yearly_usage_list[i], USAGE_UNIT)
            if yearly_charge_list[i] is not None:
                sensor_updator.update(YEARLY_CHARGE_SENSOR_NAME + profix, None, yearly_charge_list[i], BALANCE_UNIT)
            if month_charge_list[i] is not None:
                sensor_updator.update(MONTH_CHARGE_SENSOR_NAME + profix, month_list[i], month_charge_list[i], BALANCE_UNIT, month=True)
            if month_usage_list[i] is not None:
                sensor_updator.update(MONTH_USAGE_SENSOR_NAME + profix, month_list[i], month_usage_list[i], USAGE_UNIT, month=True)
        logging.info("state-refresh task run successfully!")
    except Exception as e:
        logging.error(f"state-refresh task failed, reason is {e}")
        traceback.print_exc()


def logger_init(level: str):
    logger = logging.getLogger()
    logger.setLevel(level)
    logging.getLogger("urllib3").setLevel(logging.CRITICAL)
    format = logging.Formatter("%(asctime)s  [%(levelname)-8s] ---- %(message)s", "%Y-%m-%d %H:%M:%S")
    sh = logging.StreamHandler(stream=sys.stdout)
    sh.setFormatter(format)
    logger.addHandler(sh)


def send_notify(user_id, balance):
    args = {
        'pushplus_token': PUSHPLUS_TOKEN,
        'telegram_token': TELEGRAM_TOKEN,
        'telegram_chat_id': TELEGRAM_CHAT_ID
    }
    BaseNotifier(user_id, balance).sendNotify(NOTIFY_TYPE, args)


if __name__ == "__main__":
    main()
