from enum import Enum, auto

from .weather_base import WeatherAPIBase
from .yandex import YandexWeatherAPI


class WeatherAPIType(Enum):
    Yandex = auto()


class WeatherFactory:
    @staticmethod
    def create(type_: WeatherAPIType, token: str) -> WeatherAPIBase:
        if type_ == WeatherAPIType.Yandex:
            return YandexWeatherAPI(token)
        else:
            raise NotImplemented
