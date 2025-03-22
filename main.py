import asyncio
import logging
import os
import sys
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv
from aiogram.filters import CommandStart
from aiogram.types import Message, BotCommand, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# Импорт функциональности из разделенных файлов
import main_menu
import akcii
import order_cancel
import order_status
import how_to_order
import gift_cards
import missing_card
import support

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Загрузка переменных окружения
load_dotenv()

# Получение токена бота из переменных окружения
TOKEN = os.getenv("BOT_TOKEN")
print(f"DEBUG: Инициализация бота с токеном: {TOKEN[:5]}...{TOKEN[-5:]}")

# ID чата для операторов - проверяем оба возможных имени переменной окружения
OPERATOR_CHAT_ID = os.getenv("OPERATOR_CHAT_ID") or os.getenv("SUPPORT_CHAT_ID")
print(f"DEBUG: ID чата операторов из переменной окружения: {OPERATOR_CHAT_ID}")

# Преобразуем OPERATOR_CHAT_ID в int, если это возможно
try:
    OPERATOR_CHAT_ID = int(OPERATOR_CHAT_ID)
    print(f"DEBUG: ID чата операторов преобразован в int: {OPERATOR_CHAT_ID}")
except (ValueError, TypeError):
    print(f"DEBUG: ОШИБКА! Не удалось преобразовать ID чата операторов в int: {OPERATOR_CHAT_ID}")
    # Если не удалось преобразовать, устанавливаем жестко в коде
    OPERATOR_CHAT_ID = 7411289458  # ID пользователя который получает сообщения от бота
    print(f"DEBUG: Установлен ID чата операторов вручную: {OPERATOR_CHAT_ID}")

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()

print(f"DEBUG: Бот инициализирован: {bot.id}")

# Теперь импортируем recommendations после объявления OPERATOR_CHAT_ID и bot
import recommendations

# Проверка работы прямой отправки сообщений
async def diagnostic_send(user_id, text):
    """Диагностическая функция для отправки сообщений напрямую через bot.send_message"""
    print(f"DIAGNOSTIC: Отправка сообщения пользователю {user_id}...")
    try:
        # Проверка соединения с серверами Telegram
        print(f"DIAGNOSTIC: Проверка соединения с Telegram API")
        me = await bot.get_me()
        print(f"DIAGNOSTIC: Соединение установлено, бот: {me.username}")
        
        # Проверка существования пользователя
        print(f"DIAGNOSTIC: Проверка существования пользователя {user_id}")
        try:
            chat = await bot.get_chat(user_id)
            print(f"DIAGNOSTIC: Пользователь существует: {chat.type} {chat.id}")
        except Exception as chat_error:
            print(f"DIAGNOSTIC: Не удалось получить информацию о чате: {chat_error}")
        
        # Отправка тестового сообщения
        print(f"DIAGNOSTIC: Отправка тестового сообщения")
        message = await bot.send_message(
            chat_id=user_id,
            text=f"ДИАГНОСТИЧЕСКОЕ СООБЩЕНИЕ: {text}",
            disable_notification=False  # Явно включаем уведомления
        )
        print(f"DIAGNOSTIC: Сообщение успешно отправлено, ID: {message.message_id}")
        return True
    except Exception as e:
        print(f"DIAGNOSTIC: ОШИБКА! {type(e).__name__}: {e}")
        # Вывод полного стека ошибки
        import traceback
        traceback.print_exc()
        return False

# Регистрация других модулей
from recommendations import register_handlers as register_recommendation_handlers

print("DEBUG: Регистрация обработчиков рекомендаций...")
register_recommendation_handlers(dp)
print("DEBUG: Обработчики рекомендаций зарегистрированы")

# Запуск диагностики при старте приложения
async def on_startup(bot):
    """Действия при запуске бота"""
    try:
        print("STARTUP: Запуск диагностики отправки сообщений...")
        # Проверка отправки сообщения оператору
        await diagnostic_send(OPERATOR_CHAT_ID, "Проверка работы отправки сообщений при запуске бота")
        print("STARTUP: Диагностика завершена")
    except Exception as e:
        print(f"STARTUP: Ошибка при запуске: {e}")

# Обработчик команды /diagnostic для проверки отправки сообщений
async def diagnostic_command(message: Message):
    """Обработчик команды /diagnostic для проверки отправки сообщений"""
    try:
        print(f"DEBUG: Получена команда /diagnostic от {message.from_user.id}")
        await message.reply("Запуск диагностики отправки сообщений...")
        
        # Если команда содержит ID пользователя
        parts = message.text.split()
        test_user_id = int(parts[1]) if len(parts) > 1 else message.from_user.id
        
        # Отправляем тестовое сообщение указанному пользователю
        success = await diagnostic_send(test_user_id, f"Тестовое сообщение от {message.from_user.id}")
        
        if success:
            await message.reply(f"✅ Диагностика успешно завершена! Сообщение отправлено пользователю {test_user_id}")
        else:
            await message.reply(f"❌ Диагностика завершилась с ошибкой. Не удалось отправить сообщение пользователю {test_user_id}")
    
    except Exception as e:
        await message.reply(f"❌ Ошибка при выполнении диагностики: {e}")

# Функция для запуска бота
async def main():
    try:
        # Регистрируем все обработчики из модулей
        main_menu.register_handlers(dp)
        akcii.register_handlers(dp)
        order_cancel.register_handlers(dp)
        order_status.register_handlers(dp)
        how_to_order.register_handlers(dp)
        gift_cards.register_handlers(dp)
        missing_card.register_handlers(dp)
        
        # Регистрация обработчиков поддержки
        support.register_handlers(dp, bot, OPERATOR_CHAT_ID, main_menu.main_menu_kb)
        
        # Регистрация обработчиков рекомендаций
        recommendations.register_handlers(dp)
        
        # Регистрация команд бота
        await bot.set_my_commands([
            BotCommand(command="start", description="Запустить бота"),
            BotCommand(command="help", description="Получить помощь"),
            BotCommand(command="order", description="Оформить заказ"),
            BotCommand(command="diagnostic", description="Проверить работу бота")
        ])

        # Регистрация диагностического обработчика
        dp.message.register(diagnostic_command, F.text.startswith("/diagnostic"))
        
        print("Бот запущен!")
        logging.info("Бот запущен!")
        
        # Запуск диагностики при старте
        await on_startup(bot)
        
        # Запуск поллинга
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logging.error(f"Ошибка при запуске бота: {e}")
        print(f"Ошибка при запуске бота: {e}")
        
    finally:
        logging.info("Бот остановлен!")
        print("Бот остановлен!")

# Тестовая функция для отправки сообщений напрямую
async def test_direct_message(user_id, text):
    """Тестовая функция для отправки прямых сообщений"""
    try:
        print(f"DEBUG: Прямая отправка сообщения пользователю {user_id}")
        result = await bot.send_message(chat_id=user_id, text=text)
        print(f"DEBUG: Результат отправки: {result.message_id}")
        return True
    except Exception as e:
        print(f"DEBUG: Ошибка при прямой отправке: {e}")
        return False

# Точка входа
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен!")
    except Exception as e:
        logging.error(f"Произошла ошибка при запуске бота: {e}")
