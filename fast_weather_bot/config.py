import os
from dataclasses import dataclass

from fast_weather_bot.entity import Coordinates


@dataclass
class Config:
    telegram_token: str
    weather_api_token: str
    coordinates: Coordinates

    @staticmethod
    def load() -> "Config":
        """
        Загружает данные из переменных окружение. Отсутствующие заполняются дефолтными значениями
        :return: Конфиг
        """

        lat, lon = (float(x) for x in os.getenv("COORDINATES").split())
        return Config(
            telegram_token=os.getenv("TELEGRAM_TOKEN"),
            weather_api_token=os.getenv("YANDEX_KEY"),
            coordinates=Coordinates(lat=lat, lon=lon)
        )
