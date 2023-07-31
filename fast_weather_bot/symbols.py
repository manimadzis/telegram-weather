from typing import Dict

from fast_weather_bot.entity import WindDirection, DayPart, WeatherCondition

wind_direction2arrow: Dict[WindDirection, str] = {
    WindDirection.NW: "↖️",
    WindDirection.N: "⬆️",
    WindDirection.NE: "↗️",
    WindDirection.E: "➡️",
    WindDirection.SE: "↘️",
    WindDirection.S: "⬇️",
    WindDirection.SW: "↙️",
    WindDirection.W: "⬅️",
}

wind_direction2text: Dict[WindDirection, str] = {
    WindDirection.NW: "СЗ",
    WindDirection.N: "С",
    WindDirection.NE: "СВ",
    WindDirection.E: "В",
    WindDirection.SE: "ЮВ",
    WindDirection.S: "Ю",
    WindDirection.SW: "ЮЗ",
    WindDirection.W: "З",
}

day_part2text: Dict[DayPart, str] = {
    DayPart.Morning: "Утро",
    DayPart.Day: "День",
    DayPart.Evening: "Вечер",
    DayPart.Night: "Ночь",
}

weather_condition2text: Dict[WeatherCondition, str] = {
    WeatherCondition.Clear: "☀ Ясно",
    WeatherCondition.Clouds: "🌥 Облачно",
    WeatherCondition.Drizzle: "🌦 Мелкий дождь",
    WeatherCondition.Rain: "🌧 Дождь",
    WeatherCondition.Snow: "🌨 Снег",
    WeatherCondition.Thunderstorm: "⛈ Гроза"
}
