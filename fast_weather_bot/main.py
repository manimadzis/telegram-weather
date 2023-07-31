import asyncio
import signal
import threading
import time

import schedule

from fast_weather_bot.bot import Bot
from fast_weather_bot.config import Config
from log import logger


def scheduler_thread(scheduler: schedule.Scheduler, lock: threading.Lock) -> None:
    while not lock.locked():
        logger.trace("Scheduler tick")
        scheduler.run_pending()
        time.sleep(1)


async def main():
    cfg = Config.load()
    scheduler = schedule.Scheduler()
    telegram_bot = Bot(token=cfg.telegram_token, scheduler=scheduler, weather_api_token=cfg.weather_api_token,
                       coordinates=cfg.coordinates)
    lock = threading.Lock()

    def stop_bot():
        nonlocal lock
        logger.info("Stop bot...")
        telegram_bot.stop()
        asyncio.run_coroutine_threadsafe(telegram_bot.close(), loop)
        logger.info("Bye")
        lock.acquire()
        exit()

    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGINT, stop_bot)
    loop.add_signal_handler(signal.SIGTERM, stop_bot)
    loop.run_in_executor(None, scheduler_thread, scheduler, lock)
    await telegram_bot.start()


if __name__ == '__main__':
    asyncio.run(main())
