import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

# Импорт функциональности из разделенных файлов
import main_menu
import akcii
import order_cancel
import order_status
import how_to_order
import gift_cards
import missing_card
import support
import recommendations

# Загружаем переменные окружения из .env файла
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
OPERATOR_CHAT_ID = int(os.getenv('SUPPORT_CHAT_ID'))

# Проверяем наличие токена
if not BOT_TOKEN:
    raise ValueError("Не указан токен бота. Добавьте BOT_TOKEN в файл .env")

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Инициализация бота и диспетчера с поддержкой новой версии aiogram 3.7.0
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Функция для запуска бота
async def main():
    # Регистрируем все обработчики из модулей
    main_menu.register_handlers(dp)
    akcii.register_handlers(dp)
    order_cancel.register_handlers(dp)
    order_status.register_handlers(dp)
    how_to_order.register_handlers(dp)
    gift_cards.register_handlers(dp)
    missing_card.register_handlers(dp)
    recommendations.register_handlers(dp)
    
    # Регистрация обработчиков поддержки
    support.register_handlers(dp, bot, OPERATOR_CHAT_ID, main_menu.main_menu_kb)
    
    # Запускаем бота
    logging.info("Бот запущен!")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

# Точка входа
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен!")
    except Exception as e:
        logging.error(f"Произошла ошибка при запуске бота: {e}")
