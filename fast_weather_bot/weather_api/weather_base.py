from abc import ABC, abstractmethod
from typing import Sequence

from fast_weather_bot.entity import Coordinates, Forecast, WeatherPoint


class WeatherAPIBase(ABC):
    @abstractmethod
    async def current(self, coordinates: Coordinates) -> WeatherPoint:
        pass

    @abstractmethod
    async def coords_by_city(self, city: str) -> Coordinates:
        pass

    @abstractmethod
    async def forecast(self, coordinates: Coordinates) -> Sequence[Forecast]:
        pass
