
"""
Telegram-бот на aiogram 3.x с FSM для сбора отзывов.

Установка зависимости:
    pip install "aiogram>=3.4,<4"

Перед запуском укажите TOKEN, CHANNEL_ID и при необходимости тексты/URL в разделе настроек ниже.
Бот должен быть добавлен в канал как администратор с правом публикации сообщений.
"""

from __future__ import annotations

import asyncio
import logging
import sys
from html import escape
from typing import Any

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

# ---------------------------------------------------------------------------
# Настройки (отредактируйте под себя)
# ---------------------------------------------------------------------------

TOKEN: str = "8783769635:AAHdl1BYLDkTSRRg7nfibrCgBDrX1F8MHBM"
# ID канала (число вида -100...) или @username канала
CHANNEL_ID: str | int = "@chiefirrr_reviews"

# Ссылка на Telegram-канал портфолио (https://t.me/...)
PORTFOLIO_URL: str = "https://t.me/+IU2J2nIvRcNkNTNi"

# Контакт для раздела «Другое» (без @ в значении — @ добавится в тексте)
CONTACT_USERNAME: str = "@chief_ir"

# Минимальная длина отзыва (символов); пользователю не показывается
MIN_REVIEW_COMMENT_LENGTH = 3

# ---------------------------------------------------------------------------
# Тексты интерфейса (легко править)
# ---------------------------------------------------------------------------

TEXT_WELCOME = (
    "👋 Добро пожаловать!\n\n"
    "Рад видеть тебя здесь 🙌\n"
    "Я создаю качественные проекты и всегда открыт к сотрудничеству.\n\n"
    "💡 Здесь ты можешь:\n"
    "— оставить отзыв\n"
    "— узнать больше обо мне\n"
    "— посмотреть мои работы\n"
    "— задать любой вопрос\n\n"
    "Выбирай нужный раздел ниже 👇"
)

TEXT_INFO = (
    "👤 Обо мне\n\n"
    "Я занимаюсь созданием качественных проектов,\n"
    "делаю упор на результат, стиль и удобство.\n\n"
    "📌 Моя цель — чтобы каждый клиент был доволен\n"
    "и хотел вернуться снова.\n\n"
    "Если тебе важно качество — ты по адресу 💯"
)

TEXT_PORTFOLIO = (
    "📁 Моё портфолио\n\n"
    "Здесь собраны мои работы 👇\n"
    "Переходи и посмотри, что я уже сделал.\n\n"
    "Уверен, тебе понравится 😉"
)

TEXT_ASK_RATING = (
    "⭐ Оцени мой сервис\n\n"
    "Насколько тебе всё понравилось?\n"
    "Выбери количество звёзд ниже 👇"
)
TEXT_ASK_COMMENT = (
    "💬 Почти готово!\n\n"
    "Напиши, пожалуйста, небольшой отзыв.\n\n"
    "Твоё мнение помогает мне становиться лучше 💪"
)
TEXT_COMMENT_TOO_SHORT = (
    "⚠️ Слишком короткий отзыв\n\n"
    "Пожалуйста, напиши чуть подробнее.\n\n"
    "Я правда это читаю 👀"
)
TEXT_COMMENT_NOT_TEXT = "Пожалуйста, отправьте отзыв обычным текстом (без стикеров и фото)."
TEXT_CHOOSE_RATING_FIRST = (
    "Сначала выберите оценку кнопками со звёздами под сообщением «⭐ Оцени мой сервис»."
)
TEXT_THANKS_AFTER_REVIEW = (
    "❤️ Спасибо за отзыв!\n\n"
    "Я очень ценю твоё время и обратную связь 🙌\n"
    "Это помогает мне расти и делать ещё лучше.\n\n"
    "Ты всегда можешь вернуться и оставить ещё один отзыв 😉"
)

TEXT_HELP_INTRO = (
    "❓ Помощь\n\n"
    "📌 Кто вы?\n"
    "📝 Как оставить отзыв?\n"
    "📂 Где портфолио?\n"
    "💬 Остались вопросы?\n\n"
    "Выбери тему ниже 👇"
)

TEXT_FAQ_WHO = (
    "<b>📌 Кто вы</b>\n\n"
    "<b>👤 Кто я?</b>\n\n"
    "Я специалист, который делает проекты с упором\n"
    "на качество, детали и результат.\n\n"
    "Работаю с клиентами напрямую и всегда на связи 🤝"
)
TEXT_FAQ_HOW_REVIEW = (
    "<b>📝 Как оставить отзыв</b>\n\n"
    "<b>📝 Как оставить отзыв?</b>\n\n"
    "Всё просто:\n"
    "1. Нажми кнопку «Отзыв»\n"
    "2. Выбери оценку\n"
    "3. Напиши комментарий\n\n"
    "Готово! 💥"
)
TEXT_FAQ_PORTFOLIO_HELP = (
    "<b>📂 Где портфолио</b>\n\n"
    "<b>📂 Где посмотреть работы?</b>\n\n"
    "Нажми кнопку «Портфолио» в главном меню\n"
    "и перейди в мой канал с проектами 👌"
)

TEXT_FAQ_OTHER = (
    "<b>💬 Другое</b>\n\n"
    "<b>💬 Остались вопросы?</b>\n\n"
    "Напиши мне лично 👇\n"
    "@{username}\n\n"
    "Отвечаю максимально быстро ⚡"
)

TEXT_HELP_BACK_HOME = (
    "⬅️ Ты вернулся в главное меню\n\n"
    "Выбирай, что тебе нужно 👇"
)

# Подписи кнопок главного меню
BTN_REVIEW = "⭐ Отзыв"
BTN_INFO = "ℹ️ Информация"
BTN_PORTFOLIO = "📁 Портфолио"
BTN_HELP = "❓ Помощь"

BTN_BACK_HOME = "⬅️ На главную"
BTN_BACK = "⬅️ Назад"

# Кнопки помощи
BTN_HELP_WHO = "📌 Кто вы"
BTN_HELP_REVIEW = "📝 Как оставить отзыв"
BTN_HELP_PORTFOLIO = "📂 Где портфолио"
BTN_HELP_OTHER = "💬 Другое"

# ---------------------------------------------------------------------------
# Логирование
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# FSM: сценарий отзыва
# ---------------------------------------------------------------------------


class ReviewStates(StatesGroup):
    """FSM сценария отзыва: оценка (inline) → комментарий (текст)."""

    waiting_rating = State()
    waiting_comment = State()


# ---------------------------------------------------------------------------
# Callback-данные (короткие строки для inline-кнопок)
# ---------------------------------------------------------------------------

CB_MAIN = "menu:main"
CB_REVIEW = "menu:review"
CB_INFO = "menu:info"
CB_PORTFOLIO = "menu:portfolio"
CB_HELP = "menu:help"

CB_RATE_PREFIX = "rate:"
CB_HELP_WHO = "help:who"
CB_HELP_REVIEW = "help:how_review"
CB_HELP_PORTFOLIO = "help:portfolio"
CB_HELP_OTHER = "help:other"
CB_HELP_BACK = "help:back"


def _stars_label(count: int) -> str:
    return "⭐" * count


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню: 4 кнопки в два ряда."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=BTN_REVIEW, callback_data=CB_REVIEW),
                InlineKeyboardButton(text=BTN_INFO, callback_data=CB_INFO),
            ],
            [
                InlineKeyboardButton(text=BTN_PORTFOLIO, callback_data=CB_PORTFOLIO),
                InlineKeyboardButton(text=BTN_HELP, callback_data=CB_HELP),
            ],
        ]
    )


def rating_keyboard() -> InlineKeyboardMarkup:
    """Пять кнопок с оценкой 1–5 звёзд: столбиком, сверху 5★, снизу 1★."""
    rows = [
        [InlineKeyboardButton(text=_stars_label(i), callback_data=f"{CB_RATE_PREFIX}{i}")]
        for i in range(5, 0, -1)
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def comment_step_keyboard() -> InlineKeyboardMarkup:
    """Шаг ввода комментария: выход на главную без отправки отзыва."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=BTN_BACK_HOME, callback_data=CB_MAIN)],
        ]
    )


def back_home_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=BTN_BACK_HOME, callback_data=CB_MAIN)],
        ]
    )


def help_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=BTN_HELP_WHO, callback_data=CB_HELP_WHO)],
            [InlineKeyboardButton(text=BTN_HELP_REVIEW, callback_data=CB_HELP_REVIEW)],
            [InlineKeyboardButton(text=BTN_HELP_PORTFOLIO, callback_data=CB_HELP_PORTFOLIO)],
            [InlineKeyboardButton(text=BTN_HELP_OTHER, callback_data=CB_HELP_OTHER)],
            [InlineKeyboardButton(text=BTN_BACK, callback_data=CB_HELP_BACK)],
        ]
    )


def portfolio_keyboard() -> InlineKeyboardMarkup:
    """Кнопка-ссылка на канал портфолио + возврат в меню."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔗 Открыть портфолио", url=PORTFOLIO_URL)],
            [InlineKeyboardButton(text=BTN_BACK_HOME, callback_data=CB_MAIN)],
        ]
    )


def help_portfolio_keyboard() -> InlineKeyboardMarkup:
    """Для раздела помощи про портфолио: ссылка и назад."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔗 Портфолио", url=PORTFOLIO_URL)],
            [InlineKeyboardButton(text=BTN_BACK_HOME, callback_data=CB_MAIN)],
        ]
    )


router = Router()


def _format_channel_review(rating: int, comment: str, user: Any) -> str:
    """Текст отзыва для публикации в канале (HTML, текст отзыва экранирован)."""
    safe_comment = escape(comment)
    if user.username:
        user_line = f"👤 Пользователь: @{escape(user.username)}"
    else:
        user_line = f"👤 Пользователь: ID {user.id}"
    return (
        f"⭐ Оценка: {rating}\n"
        f"💬 Отзыв:\n{safe_comment}\n\n"
        f"{user_line}"
    )


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    """Команда /start: приветствие и главное меню."""
    try:
        await state.clear()
        await message.answer(
            TEXT_WELCOME,
            reply_markup=main_menu_keyboard(),
        )
    except TelegramBadRequest as e:
        logger.exception("Ошибка Telegram при /start: %s", e)
    except Exception as e:
        logger.exception("Неожиданная ошибка в cmd_start: %s", e)


@router.callback_query(F.data == CB_MAIN)
async def callback_main_menu(callback: CallbackQuery, state: FSMContext) -> None:
    """Возврат в главное меню."""
    try:
        await callback.answer()
        await state.clear()
        if callback.message:
            await callback.message.edit_text(
                TEXT_WELCOME,
                reply_markup=main_menu_keyboard(),
            )
    except TelegramBadRequest as e:
        logger.warning("Не удалось отредактировать сообщение (шлём новое): %s", e)
        try:
            await state.clear()
            if callback.message:
                await callback.message.answer(
                    TEXT_WELCOME,
                    reply_markup=main_menu_keyboard(),
                )
        except Exception as e2:
            logger.exception("Ошибка при отправке главного меню: %s", e2)
    except Exception as e:
        logger.exception("Ошибка в callback_main_menu: %s", e)


@router.callback_query(F.data == CB_REVIEW)
async def callback_review_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Начало сценария отзыва: запрос оценки."""
    try:
        await callback.answer()
        await state.set_state(ReviewStates.waiting_rating)
        if callback.message:
            await callback.message.edit_text(
                TEXT_ASK_RATING,
                reply_markup=rating_keyboard(),
            )
    except Exception as e:
        logger.exception("Ошибка в callback_review_start: %s", e)


@router.callback_query(F.data.startswith(CB_RATE_PREFIX))
async def callback_rating_chosen(callback: CallbackQuery, state: FSMContext) -> None:
    """Пользователь выбрал оценку — сохраняем и просим комментарий."""
    try:
        await callback.answer()
        raw = callback.data or ""
        rating_str = raw.replace(CB_RATE_PREFIX, "", 1)
        rating = int(rating_str)
        if rating < 1 or rating > 5:
            raise ValueError("Некорректная оценка")

        await state.update_data(rating=rating)
        await state.set_state(ReviewStates.waiting_comment)

        if callback.message:
            await callback.message.edit_text(
                TEXT_ASK_COMMENT,
                reply_markup=comment_step_keyboard(),
            )
    except (ValueError, TypeError) as e:
        logger.warning("Некорректные данные оценки: %s", e)
        try:
            await callback.answer("Ошибка выбора оценки", show_alert=True)
        except Exception:
            pass
    except Exception as e:
        logger.exception("Ошибка в callback_rating_chosen: %s", e)


@router.message(StateFilter(ReviewStates.waiting_comment), F.text)
async def process_review_comment(message: Message, state: FSMContext, bot: Bot) -> None:
    """Приём текста отзыва, проверка длины и отправка в канал."""
    text = (message.text or "").strip()
    if len(text) < MIN_REVIEW_COMMENT_LENGTH:
        try:
            await message.answer(TEXT_COMMENT_TOO_SHORT)
        except Exception as e:
            logger.exception("Ошибка при отправке предупреждения о длине: %s", e)
        return

    data = await state.get_data()
    rating = int(data.get("rating", 0))
    if not (1 <= rating <= 5):
        logger.error("В состоянии комментария нет корректного rating: %s", data)
        await state.clear()
        try:
            await message.answer(
                "Произошла ошибка сессии. Начните отзыв заново: /start",
                reply_markup=main_menu_keyboard(),
            )
        except Exception as e:
            logger.exception("Ошибка при сбросе сессии: %s", e)
        return

    channel_text = _format_channel_review(rating, text, message.from_user)

    try:
        await bot.send_message(
            chat_id=CHANNEL_ID,
            text=channel_text,
            parse_mode=ParseMode.HTML,
        )
    except TelegramBadRequest as e:
        logger.exception("Не удалось отправить отзыв в канал: %s", e)
        try:
            await message.answer(
                "❌ Не удалось отправить отзыв. Попробуйте позже или обратитесь к администратору.",
                reply_markup=main_menu_keyboard(),
            )
        except Exception as e2:
            logger.exception("Ошибка при уведомлении пользователя: %s", e2)
        await state.clear()
        return
    except Exception as e:
        logger.exception("Ошибка при отправке в канал: %s", e)
        try:
            await message.answer(
                "❌ Техническая ошибка при публикации отзыва.",
                reply_markup=main_menu_keyboard(),
            )
        except Exception as e2:
            logger.exception("Ошибка при уведомлении: %s", e2)
        await state.clear()
        return

    await state.clear()
    try:
        await message.answer(
            TEXT_THANKS_AFTER_REVIEW,
            reply_markup=main_menu_keyboard(),
        )
    except Exception as e:
        logger.exception("Ошибка при благодарности: %s", e)


@router.message(StateFilter(ReviewStates.waiting_rating))
async def process_rating_stage_text(message: Message) -> None:
    """На этапе выбора оценки принимаются только нажатия на inline-кнопки."""
    try:
        await message.answer(TEXT_CHOOSE_RATING_FIRST)
    except Exception as e:
        logger.exception("Ошибка в process_rating_stage_text: %s", e)


@router.message(StateFilter(ReviewStates.waiting_comment))
async def process_review_non_text(message: Message) -> None:
    """В состоянии ожидания комментария принимаем только текст."""
    try:
        await message.answer(TEXT_COMMENT_NOT_TEXT)
    except Exception as e:
        logger.exception("Ошибка в process_review_non_text: %s", e)


@router.callback_query(F.data == CB_INFO)
async def callback_info(callback: CallbackQuery, state: FSMContext) -> None:
    """Раздел «Информация»."""
    try:
        await callback.answer()
        await state.clear()
        if callback.message:
            await callback.message.edit_text(
                TEXT_INFO,
                reply_markup=back_home_keyboard(),
                parse_mode=ParseMode.HTML,
            )
    except TelegramBadRequest:
        try:
            if callback.message:
                await callback.message.answer(
                    TEXT_INFO,
                    reply_markup=back_home_keyboard(),
                    parse_mode=ParseMode.HTML,
                )
        except Exception as e:
            logger.exception("Ошибка в callback_info (fallback): %s", e)
    except Exception as e:
        logger.exception("Ошибка в callback_info: %s", e)


@router.callback_query(F.data == CB_PORTFOLIO)
async def callback_portfolio(callback: CallbackQuery, state: FSMContext) -> None:
    """Портфолио: ссылка на канал."""
    try:
        await callback.answer()
        await state.clear()
        if callback.message:
            await callback.message.edit_text(
                TEXT_PORTFOLIO,
                reply_markup=portfolio_keyboard(),
            )
    except Exception as e:
        logger.exception("Ошибка в callback_portfolio: %s", e)


@router.callback_query(F.data == CB_HELP)
async def callback_help(callback: CallbackQuery, state: FSMContext) -> None:
    """Экран помощи с FAQ-кнопками."""
    try:
        await callback.answer()
        await state.clear()
        if callback.message:
            await callback.message.edit_text(
                TEXT_HELP_INTRO,
                reply_markup=help_menu_keyboard(),
            )
    except Exception as e:
        logger.exception("Ошибка в callback_help: %s", e)


@router.callback_query(F.data == CB_HELP_WHO)
async def callback_help_who(callback: CallbackQuery) -> None:
    try:
        await callback.answer()
        if callback.message:
            await callback.message.edit_text(
                TEXT_FAQ_WHO,
                reply_markup=back_home_keyboard(),
                parse_mode=ParseMode.HTML,
            )
    except Exception as e:
        logger.exception("Ошибка в callback_help_who: %s", e)


@router.callback_query(F.data == CB_HELP_REVIEW)
async def callback_help_how_review(callback: CallbackQuery) -> None:
    try:
        await callback.answer()
        if callback.message:
            await callback.message.edit_text(
                TEXT_FAQ_HOW_REVIEW,
                reply_markup=back_home_keyboard(),
                parse_mode=ParseMode.HTML,
            )
    except Exception as e:
        logger.exception("Ошибка в callback_help_how_review: %s", e)


@router.callback_query(F.data == CB_HELP_PORTFOLIO)
async def callback_help_portfolio(callback: CallbackQuery) -> None:
    try:
        await callback.answer()
        if callback.message:
            await callback.message.edit_text(
                TEXT_FAQ_PORTFOLIO_HELP,
                reply_markup=help_portfolio_keyboard(),
                parse_mode=ParseMode.HTML,
            )
    except Exception as e:
        logger.exception("Ошибка в callback_help_portfolio: %s", e)


@router.callback_query(F.data == CB_HELP_OTHER)
async def callback_help_other(callback: CallbackQuery) -> None:
    """«Другое» — контакт для связи."""
    try:
        await callback.answer()
        uname = CONTACT_USERNAME.lstrip("@")
        text = TEXT_FAQ_OTHER.format(username=uname)
        if callback.message:
            await callback.message.edit_text(
                text,
                reply_markup=back_home_keyboard(),
                parse_mode=ParseMode.HTML,
            )
    except Exception as e:
        logger.exception("Ошибка в callback_help_other: %s", e)


@router.callback_query(F.data == CB_HELP_BACK)
async def callback_help_back(callback: CallbackQuery, state: FSMContext) -> None:
    """«Назад» с экрана помощи — в главное меню с текстом возврата."""
    try:
        await callback.answer()
        await state.clear()
        if callback.message:
            await callback.message.edit_text(
                TEXT_HELP_BACK_HOME,
                reply_markup=main_menu_keyboard(),
            )
    except TelegramBadRequest as e:
        logger.warning("Не удалось отредактировать сообщение (шлём новое): %s", e)
        try:
            await state.clear()
            if callback.message:
                await callback.message.answer(
                    TEXT_HELP_BACK_HOME,
                    reply_markup=main_menu_keyboard(),
                )
        except Exception as e2:
            logger.exception("Ошибка при отправке главного меню: %s", e2)
    except Exception as e:
        logger.exception("Ошибка в callback_help_back: %s", e)


async def main() -> None:
    """Точка входа: asyncio + polling."""
    if not TOKEN or TOKEN == "ВАШ_ТОКЕН_БОТА":
        logger.error("Укажите корректный TOKEN в начале файла main.py")
        sys.exit(1)

    bot = Bot(
        token=TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    logger.info("Бот запускается (long polling)...")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.exception("Критическая ошибка polling: %s", e)
        raise
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Остановка по Ctrl+C")
