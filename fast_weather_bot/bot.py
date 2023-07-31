import asyncio
import datetime
from enum import Enum
from typing import Tuple, Optional, Dict

import aiogram
import schedule
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, \
    CallbackQuery
from loguru import logger

from fast_weather_bot.entity import Coordinates, WeatherPoint, WeatherCondition, Forecast
from log import logit
from symbols import wind_direction2arrow, wind_direction2text, weather_condition2text, day_part2text
from weather_api import WeatherFactory, WeatherAPIType


class BotReplyAction(Enum):
    GetWeather = "Погода"
    GetForecast = "Прогноз"
    Settings = "Настройки"
    TurnOnAlarm = "Вкл. оповещение"
    TurnOffAlarm = "Выкл. оповещение"


class BotSettingsAction(Enum):
    ChangeCoord = "Изменить координаты"
    Schedule = "Расписание"


class BotScheduleAction(Enum):
    Add = "Добавить"
    Del = "Удалить"


class AddScheduleEntryState(StatesGroup):
    InputTime = State()


class DelScheduleEntryState(StatesGroup):
    InputTime = State()


class ChangeCoordiantesState(StatesGroup):
    InputCoordinates = State()


class Bot:
    _reply_keyboard_turn_on_alarm = ReplyKeyboardMarkup(resize_keyboard=True).row(
        KeyboardButton(BotReplyAction.GetWeather.value), KeyboardButton(BotReplyAction.GetForecast.value),
    ).add().row(
        KeyboardButton(BotReplyAction.Settings.value), KeyboardButton(BotReplyAction.TurnOnAlarm.value),
    )

    _reply_keyboard_turn_off_alarm = ReplyKeyboardMarkup(resize_keyboard=True).row(
        KeyboardButton(BotReplyAction.GetWeather.value), KeyboardButton(BotReplyAction.GetForecast.value),
    ).add().row(
        KeyboardButton(BotReplyAction.Settings.value), KeyboardButton(BotReplyAction.TurnOffAlarm.value),
    )

    _inner_settings_keyboard = InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton(BotSettingsAction.Schedule.value, callback_data=BotSettingsAction.Schedule.name)
    ).add(
        InlineKeyboardButton(BotSettingsAction.ChangeCoord.value, callback_data=BotSettingsAction.ChangeCoord.name)
    )

    def __init__(self, token: str,
                 scheduler: schedule.Scheduler,
                 weather_api_token: str,
                 coordinates: Coordinates,
                 ):
        self._bot = aiogram.Bot(token=token)
        self._dp = aiogram.Dispatcher(self._bot, storage=MemoryStorage())
        self._scheduler = scheduler
        self._bad_weather_alarm: bool = False
        self._chat_id: int = 0
        self._weather_api_token = weather_api_token
        self._coordinates = coordinates
        self._current_keyboard = self._reply_keyboard_turn_on_alarm
        self._alarm_job: Optional[schedule.Job] = None
        self._schedule_jobs: Dict[datetime.time, schedule.Job] = {}
        self._register_handlers()

    @staticmethod
    def _format_weather(weather: WeatherPoint) -> str:
        text = f"{weather_condition2text[weather.condition]}\n"
        text += f"Температура: {weather.temperature}℃\n"
        text += f"Ветер: {weather.wind_speed} м/с {wind_direction2text[weather.wind_direction]}" \
                f" {wind_direction2arrow[weather.wind_direction]}\n"
        text += f"Давление: {weather.pressure} мм рт.ст.\n"
        text += f"Влажность: {weather.humidity}%\n"
        return text

    @staticmethod
    def _format_forecast(forecast: Forecast) -> str:
        text = ""
        if forecast.part:
            text += f"{day_part2text[forecast.part]}\n"
        else:
            raise NotImplemented

        text += f"{weather_condition2text[forecast.condition]}\n"
        text += f"Температура: от {forecast.min_temperature} до {forecast.max_temperature}℃\n"
        text += f"Ветер: {forecast.wind_speed} м/с {wind_direction2text[forecast.wind_direction]}" \
                f" {wind_direction2arrow[forecast.wind_direction]}\n"
        text += f"Давление: {forecast.pressure} мм рт.ст.\n"
        text += f"Влажность: {forecast.humidity}%\n"
        return text

    @logit()
    async def _set_command_list(self):
        commands = [aiogram.types.BotCommand("/start", "Начать работу с ботом"),
                    aiogram.types.BotCommand("/current", "Текущая погода"),
                    aiogram.types.BotCommand("/forecast", "Прогноз"),
                    aiogram.types.BotCommand("/alarm", "Включить/выключить предупреждение о плохой погоде"),
                    aiogram.types.BotCommand("/settings", "Настройки"),
                    ]
        await self._bot.set_my_commands(commands)

    @logit()
    def _register_handlers(self):
        self._dp.register_message_handler(self._start_handler, commands=["start"])

        self._dp.register_message_handler(self._current_handler,
                                          lambda msg: msg.text == BotReplyAction.GetWeather.value)
        self._dp.register_message_handler(self._current_handler, commands=["current"])

        self._dp.register_message_handler(self._forecast_handler,
                                          lambda msg: msg.text == BotReplyAction.GetForecast.value)
        self._dp.register_message_handler(self._forecast_handler, commands=["forecast"])

        self._dp.register_message_handler(self._turn_on_alarm_handler,
                                          lambda msg: msg.text == BotReplyAction.TurnOnAlarm.value)
        self._dp.register_message_handler(self._turn_off_alarm_handler,
                                          lambda msg: msg.text == BotReplyAction.TurnOffAlarm.value)

        self._dp.register_message_handler(self._settings_handler,
                                          lambda msg: msg.text == BotReplyAction.Settings.value)
        self._dp.register_message_handler(self._settings_handler, commands=["settings"])

        self._dp.register_callback_query_handler(self._schedule_callback_handler,
                                                 lambda cq: cq.data == BotSettingsAction.Schedule.name)

        self._dp.register_callback_query_handler(self._schedule_add_callback_handler,
                                                 lambda cq: cq.data == BotScheduleAction.Add.name)
        self._dp.register_message_handler(self._schedule_add_input_time_handler, state=AddScheduleEntryState.InputTime)

        self._dp.register_callback_query_handler(self._schedule_del_callback_handler,
                                                 lambda cq: cq.data == BotScheduleAction.Del.name)
        self._dp.register_message_handler(self._schedule_del_input_time_handler, state=DelScheduleEntryState.InputTime)

        self._dp.register_callback_query_handler(self._change_coordinates_callback_handler,
                                                 lambda cq: cq.data == BotSettingsAction.ChangeCoord.name)
        self._dp.register_message_handler(self._change_coordinates_handler,
                                          state=ChangeCoordiantesState.InputCoordinates)

    @logit()
    async def _help_handler(self, msg: Message) -> None:
        await msg.answer("HELP", reply_markup=self._current_keyboard)

    @logit()
    async def _start_handler(self, msg: Message) -> None:
        logger.trace(f"Handle /start: {msg}")
        self._chat_id = msg.chat.id
        await self._help_handler(msg)

    @logit()
    async def _current_handler(self, msg: Message) -> None:
        api = WeatherFactory.create(WeatherAPIType.Yandex, self._weather_api_token)
        weather = await api.current(self._coordinates)
        await msg.answer(self._format_weather(weather))

    @logit()
    async def _forecast_handler(self, msg: Message) -> None:
        api = WeatherFactory.create(WeatherAPIType.Yandex, self._weather_api_token)
        forecasts = await api.forecast(self._coordinates)
        text = ""
        for forecast in forecasts:
            text += self._format_forecast(forecast)
            text += "\n"
        aiogram.Bot.set_current(self._bot)
        await msg.answer(text)

    @logit()
    async def _turn_on_alarm_handler(self, msg: Message) -> None:
        self._bad_weather_alarm = True
        self._current_keyboard = self._reply_keyboard_turn_off_alarm
        loop = asyncio.get_event_loop()
        self._alarm_job = self._scheduler.every(5).seconds.do(
            lambda x: asyncio.run_coroutine_threadsafe(x(), loop), self._try_bad_weather_alarm)
        self._jobs = {"Alarm"}
        await msg.answer("Оповещение включено", reply_markup=self._current_keyboard)

    @logit()
    async def _turn_off_alarm_handler(self, msg: Message) -> None:
        self._bad_weather_alarm = False
        self._scheduler.cancel_job(self._alarm_job)
        self._current_keyboard = self._reply_keyboard_turn_on_alarm
        await msg.answer("Оповещение отключено", reply_markup=self._current_keyboard)

    @logit()
    async def _settings_handler(self, msg: Message) -> None:
        await msg.answer("Настройки", reply_markup=self._inner_settings_keyboard)

    @logit()
    async def _schedule_add_callback_handler(self, callback_query: CallbackQuery) -> None:
        await AddScheduleEntryState.next()
        await self._bot.send_message(callback_query.from_user.id, "Введите время в формате часы:минуты (14:48)")
        await callback_query.answer()

    async def _schedule_add_input_time_handler(self, msg: Message, state: FSMContext) -> None:
        await state.finish()
        try:
            hour, minute = (int(x.strip()) for x in msg.text.split(":"))
            t = datetime.time(hour, minute)
        except ValueError:
            await msg.answer("Неверные формат данных")
            return
        loop = asyncio.get_event_loop()
        Message()
        self._schedule_jobs[t] = self._scheduler.every().day.at(t.strftime("%H:%M")).do(
            lambda x: asyncio.run_coroutine_threadsafe(x(msg), loop), self._forecast_handler
        )
        await msg.answer("Успешно добавлено")

    @logit()
    async def _schedule_del_callback_handler(self, callback_query: CallbackQuery) -> None:
        await DelScheduleEntryState.next()
        await self._bot.send_message(callback_query.from_user.id, "Введите время в формате часы:минуты (14:48)")
        await callback_query.answer()

    @logit()
    async def _schedule_del_input_time_handler(self, msg: Message, state: FSMContext) -> None:
        await state.finish()
        try:
            hour, minute = (int(x.strip()) for x in msg.text.split(":"))
            t = datetime.time(hour, minute)
        except ValueError:
            await msg.answer("Неверные формат данных")
            return
        job = self._schedule_jobs.get(t)
        if job:
            self._scheduler.cancel_job(job)
            del self._schedule_jobs[t]

    @logit()
    def _build_schedule_keyboard(self) -> InlineKeyboardMarkup:
        schedule_markup = InlineKeyboardMarkup()
        for time in sorted(self._schedule_jobs.keys()):
            schedule_markup.row(InlineKeyboardButton(time.strftime("%H:%M"), callback_data=time.strftime("%H:%M")))
        return schedule_markup

    @logit()
    async def _schedule_callback_handler(self, callback_query: CallbackQuery) -> None:
        schedule_markup = self._build_schedule_keyboard()
        schedule_markup.row(InlineKeyboardButton(BotScheduleAction.Add.value, callback_data=BotScheduleAction.Add.name))
        schedule_markup.row(InlineKeyboardButton(BotScheduleAction.Del.value, callback_data=BotScheduleAction.Del.name))
        await self._bot.send_message(callback_query.from_user.id, "Расписание", reply_markup=schedule_markup)
        await callback_query.answer()

    @logit()
    async def _try_bad_weather_alarm(self):
        bad, forecast = await self._is_bad_weather()
        if bad:
            await self._bot.send_message(self._chat_id, "Ожидается плохая погода")
            await self._bot.send_message(self._chat_id, self._format_forecast(forecast))

    @logit()
    async def _is_bad_weather(self) -> Tuple[bool, Optional[Forecast]]:
        api = WeatherFactory.create(WeatherAPIType.Yandex, self._weather_api_token)
        forecasts = await api.forecast(self._coordinates)
        for forecast in forecasts:
            if forecast.condition not in (WeatherCondition.Clear, WeatherCondition.Clouds):
                return True, forecast
        return False, None

    @logit()
    async def _change_coordinates_callback_handler(self, callback_query: CallbackQuery) -> None:
        await ChangeCoordiantesState.next()
        await self._bot.send_message(callback_query.from_user.id, "Введите координаты. Пример: 55.833333 37.616667")
        await callback_query.answer()

    @logit()
    async def _change_coordinates_handler(self, msg: Message, state: FSMContext) -> None:
        await state.finish()
        try:
            lat, lon = (float(x) for x in msg.text.split())
        except (IndexError, ValueError):
            await msg.answer("Неверный формат данных")
            return
        self._coordinates = Coordinates(lat=lat, lon=lon)
        await msg.answer("Успешно изменено")

    @logit()
    async def start(self) -> None:
        logger.info("Setting command list")
        await self._set_command_list()
        logger.info("Skipping updates")
        await self._dp.skip_updates()
        logger.info("Starting telegram bot")
        await self._dp.start_polling()

    def stop(self) -> None:
        self._dp.stop_polling()

    async def close(self) -> None:
        await self._dp.wait_closed()
