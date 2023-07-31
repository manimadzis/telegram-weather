import asyncio
import os

from fast_weather_bot.entity import Coordinates
from .yandex import YandexWeatherAPI
import pytest

pytest_plugins = ('pytest_asyncio',)


@pytest.mark.asyncio
async def test_forecast():
    await YandexWeatherAPI(os.environ.get("YANDEX_KEY")).forecast(Coordinates(lat=55.833333, lon=37.616667))

