import datetime
from enum import Enum, auto
from typing import Optional

from pydantic import BaseModel


class Coordinates(BaseModel):
    lat: float  # широта
    lon: float  # долгота


class WeatherCondition(Enum):
    Thunderstorm = auto()
    Drizzle = auto()
    Rain = auto()
    Snow = auto()
    Clear = auto()
    Clouds = auto()


class WindDirection(Enum):
    NW = auto()
    N = auto()
    NE = auto()
    E = auto()
    SE = auto()
    S = auto()
    SW = auto()
    W = auto()


class WeatherPoint(BaseModel):
    time: datetime.datetime  # Время измерения
    temperature: int  # Температура в градусах Цельсия
    pressure: int  # Давление в мм ртутного столба
    condition: WeatherCondition  # Состояние погоды
    wind_speed: float  # Скорость ветра (м/с)
    wind_direction: WindDirection  # Направление ветра
    humidity: int  # Относительная влажность  (%)


class DayPart(Enum):
    Morning = auto()
    Day = auto()
    Evening = auto()
    Night = auto()


class Forecast(BaseModel):
    time: Optional[datetime.datetime] = None  # Время измерения
    part: Optional[DayPart] = None  # Часть суток
    min_temperature: int  # Минимальная температура в градусах Цельсия
    max_temperature: int  # Максимальная температура в градусах Цельсия
    pressure: int  # Давление в мм ртутного столба
    condition: WeatherCondition  # Состояние погоды
    wind_speed: float  # Скорость ветра (м/с)
    wind_direction: WindDirection  # Направление ветра
    humidity: int  # Относительная влажность  (%)
