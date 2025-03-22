# main.py - Основной файл Telegram бота GoldenAppleBot
# Этот файл отвечает за инициализацию бота, загрузку конфигурации и запуск основного цикла обработки сообщений

# Импорт стандартных библиотек Python
import asyncio  # Библиотека для асинхронного программирования
import logging  # Библиотека для логирования
import os  # Библиотека для работы с операционной системой
import sys  # Библиотека для работы с системными функциями

# Импорт библиотеки aiogram и её компонентов для создания Telegram ботов
from aiogram import Bot, Dispatcher, types, F, Router  # Основные классы для создания бота
from aiogram.enums.parse_mode import ParseMode  # Режимы форматирования текста
from aiogram.fsm.storage.memory import MemoryStorage  # Хранилище состояний в памяти
from aiogram.client.default import DefaultBotProperties  # Настройки бота по умолчанию
from dotenv import load_dotenv  # Загрузка переменных окружения из .env файла
from aiogram.filters import CommandStart  # Фильтр для обработки команды /start
from aiogram.types import Message, BotCommand, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton  # Типы данных Telegram
from aiogram.fsm.context import FSMContext  # Контекст машины состояний
from aiogram.fsm.state import State, StatesGroup  # Классы для создания состояний

# Импорт модулей проекта, каждый отвечает за свою функциональность
import main_menu  # Модуль главного меню
import akcii  # Модуль акций и специальных предложений
import order_cancel  # Модуль отмены заказов
import order_status  # Модуль проверки статуса заказов
import how_to_order  # Модуль инструкций по оформлению заказов
import gift_cards  # Модуль подарочных карт
import missing_card  # Модуль для обработки отсутствующих карт лояльности
import support  # Модуль поддержки пользователей

# Настройка системы логирования для отслеживания работы бота
# level=logging.INFO - будут записываться информационные сообщения и ошибки
# format - определяет формат записи логов: время, имя модуля, уровень важности, сообщение
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Загрузка переменных окружения из файла .env
# Это безопасный способ хранения конфиденциальных данных (токенов, паролей)
load_dotenv()

# Получение токена бота из переменных окружения
# Токен - это уникальный идентификатор бота, полученный от @BotFather
TOKEN = os.getenv("BOT_TOKEN")
print(f"DEBUG: Инициализация бота с токеном: {TOKEN[:5]}...{TOKEN[-5:]}")  # Выводим только начало и конец токена в целях безопасности

# ID чата для операторов - проверяем оба возможных имени переменной окружения
# Это ID чата, куда будут отправляться запросы от пользователей на поддержку
OPERATOR_CHAT_ID = os.getenv("OPERATOR_CHAT_ID") or os.getenv("SUPPORT_CHAT_ID")
print(f"DEBUG: ID чата операторов из переменной окружения: {OPERATOR_CHAT_ID}")

# Преобразуем OPERATOR_CHAT_ID в целое число (int), если это возможно
# Telegram API требует, чтобы ID чата был целым числом
try:
    OPERATOR_CHAT_ID = int(OPERATOR_CHAT_ID)
    print(f"DEBUG: ID чата операторов преобразован в int: {OPERATOR_CHAT_ID}")
except (ValueError, TypeError):
    # Если не удалось преобразовать (например, если переменная не установлена),
    # устанавливаем значение вручную
    print(f"DEBUG: ОШИБКА! Не удалось преобразовать ID чата операторов в int: {OPERATOR_CHAT_ID}")
    OPERATOR_CHAT_ID = 7411289458  # ID пользователя который получает сообщения от бота
    print(f"DEBUG: Установлен ID чата операторов вручную: {OPERATOR_CHAT_ID}")

# Инициализация бота и диспетчера
# Bot - основной класс для взаимодействия с Telegram API
# parse_mode=ParseMode.HTML - позволяет использовать HTML-теги в сообщениях (<b>, <i>, и т.д.)
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

# MemoryStorage - хранилище для состояний пользователей в памяти сервера
# Используется для запоминания на каком этапе диалога находится пользователь
storage = MemoryStorage()

# Dispatcher - обработчик событий, управляет регистрацией обработчиков и маршрутизацией сообщений
dp = Dispatcher(storage=storage)

# Router - маршрутизатор для обработки сообщений (используется в новых версиях aiogram)
router = Router()

print(f"DEBUG: Бот инициализирован: {bot.id}")

# Импортируем модуль рекомендаций после инициализации бота и OPERATOR_CHAT_ID
# Это нужно, потому что модуль рекомендаций использует эти переменные
import recommendations

# Диагностическая функция для проверки возможности отправки сообщений
# Используется для отладки проблем с отправкой сообщений пользователям
async def diagnostic_send(user_id, text):
    """Диагностическая функция для отправки сообщений напрямую через bot.send_message
    
    Args:
        user_id (int): ID пользователя или чата, куда нужно отправить сообщение
        text (str): Текст сообщения для отправки
        
    Returns:
        bool: True если сообщение отправлено успешно, False если произошла ошибка
    """
    print(f"DIAGNOSTIC: Отправка сообщения пользователю {user_id}...")
    try:
        # Этап 1: Проверка соединения с серверами Telegram
        print(f"DIAGNOSTIC: Проверка соединения с Telegram API")
        me = await bot.get_me()  # Получаем информацию о боте
        print(f"DIAGNOSTIC: Соединение установлено, бот: {me.username}")
        
        # Этап 2: Проверка существования пользователя
        # Если пользователь не существует или бот не может с ним взаимодействовать,
        # эта операция вызовет исключение
        print(f"DIAGNOSTIC: Проверка существования пользователя {user_id}")
        try:
            chat = await bot.get_chat(user_id)
            print(f"DIAGNOSTIC: Пользователь существует: {chat.type} {chat.id}")
        except Exception as chat_error:
            print(f"DIAGNOSTIC: Не удалось получить информацию о чате: {chat_error}")
        
        # Этап 3: Отправка тестового сообщения
        print(f"DIAGNOSTIC: Отправка тестового сообщения")
        message = await bot.send_message(
            chat_id=user_id,
            text=f"ДИАГНОСТИЧЕСКОЕ СООБЩЕНИЕ: {text}",
            disable_notification=False  # Явно включаем уведомления
        )
        print(f"DIAGNOSTIC: Сообщение успешно отправлено, ID: {message.message_id}")
        return True
    except Exception as e:
        # Если произошла ошибка на любом этапе, выводим подробную информацию
        print(f"DIAGNOSTIC: ОШИБКА! {type(e).__name__}: {e}")
        # Вывод полного стека ошибки для детального анализа
        import traceback
        traceback.print_exc()
        return False

# Регистрация обработчиков из модуля рекомендаций
from recommendations import register_handlers as register_recommendation_handlers

print("DEBUG: Регистрация обработчиков рекомендаций...")
register_recommendation_handlers(dp)
print("DEBUG: Обработчики рекомендаций зарегистрированы")

# Функция, выполняемая при запуске бота
# Используется для инициализации и проверки работоспособности бота при старте
async def on_startup(bot):
    """Действия, выполняемые при запуске бота
    
    Args:
        bot (Bot): Экземпляр бота для работы с API Telegram
    """
    try:
        print("STARTUP: Запуск диагностики отправки сообщений...")
        # Отправляем тестовое сообщение оператору при запуске
        # Это помогает убедиться, что бот работает и может отправлять сообщения
        await diagnostic_send(OPERATOR_CHAT_ID, "Проверка работы отправки сообщений при запуске бота")
        print("STARTUP: Диагностика завершена")
    except Exception as e:
        print(f"STARTUP: Ошибка при запуске: {e}")

# Обработчик команды /diagnostic
# Позволяет пользователям или администраторам проверить работу отправки сообщений
async def diagnostic_command(message: Message):
    """Обработчик команды /diagnostic для проверки отправки сообщений
    
    Формат команды: 
        /diagnostic [ID пользователя]
    Если ID не указан, отправляет тестовое сообщение отправителю команды.
    
    Args:
        message (Message): Объект сообщения от пользователя
    """
    try:
        print(f"DEBUG: Получена команда /diagnostic от {message.from_user.id}")
        await message.reply("Запуск диагностики отправки сообщений...")
        
        # Парсим команду, чтобы получить ID пользователя для тестирования
        # Если ID не указан, используем ID отправителя команды
        parts = message.text.split()
        test_user_id = int(parts[1]) if len(parts) > 1 else message.from_user.id
        
        # Отправляем тестовое сообщение и проверяем результат
        success = await diagnostic_send(test_user_id, f"Тестовое сообщение от {message.from_user.id}")
        
        # Сообщаем пользователю о результате диагностики
        if success:
            await message.reply(f"✅ Диагностика успешно завершена! Сообщение отправлено пользователю {test_user_id}")
        else:
            await message.reply(f"❌ Диагностика завершилась с ошибкой. Не удалось отправить сообщение пользователю {test_user_id}")
    
    except Exception as e:
        # Обрабатываем возможные ошибки при выполнении диагностики
        await message.reply(f"❌ Ошибка при выполнении диагностики: {e}")

# Основная функция для запуска бота
# Здесь регистрируются все обработчики из разных модулей и запускается поллинг
async def main():
    """Основная функция для запуска бота
    
    Регистрирует обработчики из всех модулей, настраивает команды
    и запускает процесс получения обновлений от Telegram API
    """
    try:
        # Регистрация обработчиков из всех модулей проекта
        # Каждый модуль отвечает за свою функциональность и имеет свои обработчики
        main_menu.register_handlers(dp)  # Обработчики главного меню
        akcii.register_handlers(dp)  # Обработчики акций
        order_cancel.register_handlers(dp)  # Обработчики отмены заказов
        order_status.register_handlers(dp)  # Обработчики статуса заказов
        how_to_order.register_handlers(dp)  # Обработчики инструкций по заказам
        gift_cards.register_handlers(dp)  # Обработчики подарочных карт
        missing_card.register_handlers(dp)  # Обработчики отсутствующих карт
        
        # Регистрация обработчиков поддержки
        # Передаем дополнительные параметры: бот, ID чата оператора и клавиатуру главного меню
        support.register_handlers(dp, bot, OPERATOR_CHAT_ID, main_menu.main_menu_kb)
        
        # Регистрация обработчиков рекомендаций
        recommendations.register_handlers(dp)
        
        # Настройка команд бота, отображаемых в меню Telegram
        # Эти команды будут видны пользователям в меню бота
        await bot.set_my_commands([
            BotCommand(command="start", description="Запустить бота"),
            BotCommand(command="help", description="Получить помощь"),
            BotCommand(command="order", description="Оформить заказ"),
            BotCommand(command="diagnostic", description="Проверить работу бота")
        ])

        # Регистрация диагностического обработчика
        # F.text.startswith("/diagnostic") - фильтр, срабатывающий на команду /diagnostic
        dp.message.register(diagnostic_command, F.text.startswith("/diagnostic"))
        
        # Логирование информации о запуске бота
        print("Бот запущен!")
        logging.info("Бот запущен!")
        
        # Запуск диагностики при старте бота
        await on_startup(bot)
        
        # Запуск поллинга - процесса получения обновлений от Telegram API
        # Бот будет постоянно проверять наличие новых сообщений и обрабатывать их
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        # Обработка ошибок при запуске бота
        logging.error(f"Ошибка при запуске бота: {e}")
        print(f"Ошибка при запуске бота: {e}")
        
    finally:
        # Этот блок выполняется всегда, даже если произошла ошибка
        # Используется для логирования остановки бота
        logging.info("Бот остановлен!")
        print("Бот остановлен!")

# Тестовая функция для прямой отправки сообщений
# Упрощенная версия diagnostic_send для быстрой проверки
async def test_direct_message(user_id, text):
    """Тестовая функция для отправки прямых сообщений без дополнительных проверок
    
    Args:
        user_id (int): ID пользователя или чата
        text (str): Текст сообщения
        
    Returns:
        bool: True в случае успеха, False в случае ошибки
    """
    try:
        print(f"DEBUG: Прямая отправка сообщения пользователю {user_id}")
        result = await bot.send_message(chat_id=user_id, text=text)
        print(f"DEBUG: Результат отправки: {result.message_id}")
        return True
    except Exception as e:
        print(f"DEBUG: Ошибка при прямой отправке: {e}")
        return False

# Точка входа в программу
# Код внутри этого блока выполняется только при прямом запуске файла
if __name__ == "__main__":
    try:
        # Запуск основной функции бота в асинхронном режиме
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        # Обработка прерывания работы бота (Ctrl+C или системный выход)
        logging.info("Бот остановлен!")
    except Exception as e:
        # Обработка других непредвиденных ошибок
        logging.error(f"Произошла ошибка при запуске бота: {e}")
