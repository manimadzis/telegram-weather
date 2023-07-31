import datetime
from typing import Sequence, List

import aiohttp
import yandex_weather_api

from fast_weather_bot.entity import WeatherPoint, Coordinates, WeatherCondition, WindDirection, DayPart, Forecast
from .weather_base import WeatherAPIBase


class YandexWeatherAPI(WeatherAPIBase):
    _wind_direction_conversion = {
        "nw": WindDirection.NW,
        "n": WindDirection.N,
        "ne": WindDirection.NE,
        "e": WindDirection.E,
        "se": WindDirection.SE,
        "s": WindDirection.S,
        "sw": WindDirection.SW,
        "w": WindDirection.W,
    }

    _day_part_conversion = {
        "morning": DayPart.Morning,
        "day": DayPart.Day,
        "evening": DayPart.Evening,
        "night": DayPart.Night,
    }

    def __init__(self, token: str):
        self._token = token

    @staticmethod
    def _convert_condition(condition: str) -> WeatherCondition:
        if condition in ("clear",):
            return WeatherCondition.Clear
        if condition in ("partly-cloudy", "cloudy", "overcast"):
            return WeatherCondition.Clouds
        if condition in ("partly-cloudy-and-rain", "overcast-and-rain", "cloudy-and-rain"):
            return WeatherCondition.Rain
        if condition in ("overcast-thunderstorms-with-rain",):
            return WeatherCondition.Thunderstorm
        if condition in ("partly-cloudy-and-light-rain", "cloudy-and-light-rain", "overcast-and-light-rain"):
            return WeatherCondition.Drizzle
        if condition in ("overcast-and-wet-snow", "partly-cloudy-and-light-snow", "partly-cloudy-and-snow",
                         "overcast-and-snow", "cloudy-and-light-snow", "overcast-and-light-snow", "cloudy-and-snow"):
            return WeatherCondition.Snow

    @staticmethod
    def _convert_wind_direction(wind_direction: str) -> WindDirection:
        return YandexWeatherAPI._wind_direction_conversion[wind_direction]

    async def current(self, coordinates: Coordinates) -> WeatherPoint:
        async with aiohttp.ClientSession() as session:
            res = await yandex_weather_api.async_get(
                session, self._token, lat=str(coordinates.lat),
                lon=str(coordinates.lon), lang="ru_RU")
        fact = res["fact"]

        return WeatherPoint(
            time=datetime.datetime.fromtimestamp(fact["obs_time"]),
            temperature=int(fact["temp"]),
            pressure=int(fact["pressure_mm"]),
            condition=self._convert_condition(fact["condition"]),
            wind_speed=fact["wind_speed"],
            wind_direction=self._convert_wind_direction(fact["wind_dir"]),
            humidity=int(fact["humidity"])
        )

    async def coords_by_city(self, city: str) -> Coordinates:
        pass

    async def forecast(self, coordinates: Coordinates) -> Sequence[Forecast]:
        async with aiohttp.ClientSession() as session:
            res = await yandex_weather_api.async_get(
                session, self._token, lat=str(coordinates.lat),
                lon=str(coordinates.lon), lang="ru_RU")
        forecasts: List[Forecast] = []
        for forecast in res["forecast"][0]["parts"].values():
            print(forecast)
            forecasts.append(
                Forecast(
                    part=self._day_part_conversion[forecast["part_name"]],
                    min_temperature=int(forecast["temp_min"]),
                    max_temperature=int(forecast["temp_max"]),
                    pressure=int(forecast["pressure_mm"]),
                    condition=self._convert_condition(forecast["condition"]),
                    wind_speed=forecast["wind_speed"],
                    wind_direction=self._convert_wind_direction(forecast["wind_dir"]),
                    humidity=int(forecast["humidity"])
                )
            )
        return tuple(forecasts)
